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

import os
import json
from requests import get
from fiona import collection
from fiona.crs import from_epsg
from shapely.geometry import Point, mapping
from climata.hydromet import AgrimetRecentIO

STATION_INFO_URL = 'https://www.usbr.gov/pn/agrimet/agrimetmap/usbr_map.json'


def fetch_agrimet_by_lat_lon(station, lat, lon):
    stations = load_stations()
    data = AgrimetRecentIO(station=station)
    for row in data:
        pass
    data = row
    x = None


def load_stations():
    r = get(STATION_INFO_URL)
    stations = json.loads(r.text)
    write_shp(stations, 4326, '/data01/images/vector_data/agrimet_sites.shp')
    return stations


def write_shp(json_data, epsg, out):
    agri_schema = {
        'geometry': {
            'coordinates': [
                'float',
                'float'
            ],
            'type': 'Point'
        },
        'id': 'str',
        'properties': {
            'program': 'str',
            'url': 'str',
            'siteid': 'str',
            'title': 'str',
            'state': 'str',
            'type': 'str',
            'region': 'str',
            'install': 'str'
        },
        'type': 'str'
    }
    cord_ref = from_epsg(epsg)
    shp_driver = 'ESRI Shapefile'

    with collection(out, mode='w', driver=shp_driver, schema=agri_schema,
                    crs=cord_ref) as output:
        for rec in json_data['features']:
            point = Point(rec['geometry']['coordinates'])
            output.write({'properties': {
                'program': rec['properties']['program'],
                'url': rec['properties']['url'],
                'siteid': rec['properties']['siteid'],
                'title': rec['properties']['title'],
                'state': rec['properties']['state'],
                'type': rec['properties']['type'],
                'region': rec['properties']['region'],
                'install': rec['properties']['install']
            },
                'geometry': mapping(point)
            })


if __name__ == '__main__':
    statn = 'COVM'
    fetch_agrimet_by_lat_lon(statn, 1, 2)


# ========================= EOF ====================================================================
