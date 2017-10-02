# =============================================================================================
# Copyright 2017 dgketchum
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================================

import json
import requests
from fiona import collection
from fiona.crs import from_epsg
from geopy.distance import vincenty
from climata.hydromet import AgrimetRecentIO


STATION_INFO_URL = 'https://www.usbr.gov/pn/agrimet/agrimetmap/usbr_map.json'
# in km
EARTH_RADIUS = 6371.


class Agrimet(object):
    def __init__(self):
        pass


def fetch_agrimet(start, end, sat_image=None,
                  lat=None, lon=None, station=None):
    if station:
        data = AgrimetRecentIO(station=station, start_date=start, end_date=end)
    elif lat and lon:
        station = find_closest_station(lat, lon)
        data = AgrimetRecentIO(station=station, start_date=start, end_date=end)
    elif sat_image:
        centroid = sat_image.scene_coords_deg
        lat, lon = centroid[0], centroid[1]
        station = find_closest_station(lat, lon)
        data = AgrimetRecentIO(station=station, start_date=start, end_date=end)

    return data


def find_closest_station(target_lat, target_lon):
    """ The two-argument inverse tangent function.
    :param station_data: 
    :param target_lat: 
    :param target_lon: 
    :return: 
    """
    distances = {}
    station_data = load_stations()
    for feat in station_data['features']:
        stn_crds = feat['geometry']['coordinates']
        stn_site_id = feat['properties']['siteid']
        lat_stn, lon_stn = stn_crds[1], stn_crds[0]
        dist = vincenty((target_lat, target_lon), (lat_stn, lon_stn)).km
        distances[stn_site_id] = dist
    k = min(distances, key=distances.get)
    return k


def load_stations():
    r = requests.get(STATION_INFO_URL)
    stations = json.loads(r.text)
    return stations


def write_shp(json_data, epsg, out):
    agri_schema = {'geometry': 'Point',
                   'properties': {
                       'program': 'str',
                       'url': 'str',
                       'siteid': 'str',
                       'title': 'str',
                       'state': 'str',
                       'type': 'str',
                       'region': 'str',
                       'install': 'str'}}

    cord_ref = from_epsg(epsg)
    shp_driver = 'ESRI Shapefile'

    with collection(out, mode='w', driver=shp_driver, schema=agri_schema,
                    crs=cord_ref) as output:
        for rec in json_data['features']:
            try:
                output.write({'geometry': {'type': 'Point',
                                           'coordinates':
                                               (rec['geometry']['coordinates'][0],
                                                rec['geometry']['coordinates'][1])},
                              'properties': {
                                  'program': rec['properties']['program'],
                                  'url': rec['properties']['url'],
                                  'siteid': rec['properties']['siteid'],
                                  'title': rec['properties']['title'],
                                  'state': rec['properties']['state'],
                                  'type': rec['properties']['type'],
                                  'region': rec['properties']['region'],
                                  'install': rec['properties']['install']}})
            except KeyError:
                pass


if __name__ == '__main__':
    pass

# ========================= EOF ====================================================================
