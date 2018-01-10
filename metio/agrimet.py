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
from requests.compat import urlencode, OrderedDict
from datetime import datetime
from fiona import collection
from fiona.crs import from_epsg
from geopy.distance import vincenty
from pandas import read_table, to_datetime, date_range

STATION_INFO_URL = 'https://www.usbr.gov/pn/agrimet/agrimetmap/usbr_map.json'
AGRIMET_REQ_SCRIPT = 'https://www.usbr.gov/pn-bin/agrimet.pl'
# in km
EARTH_RADIUS = 6371.

WEATHER_PARAMETRS_UNCONVERTED = [('DATETIME', 'Date - [YYYY-MM-DD]'),
                                 ('ET', 'Evapotranspiration Kimberly-Penman - [in]'),
                                 ('ETos', 'Evapotranspiration ASCE-EWRI Grass - [in]'),
                                 ('ETrs', 'Evapotranspiration ASCE-EWRI Alfalfa - [in]'),
                                 ('MM', 'Mean Daily Air Temperature - [F]'),
                                 ('MN', 'Minimum Daily Air Temperature - [F]'),
                                 ('MX', 'Maximum Daily Air Temperature - [F]'),
                                 ('PC', 'Accumulated Precipitation Since Recharge/Reset - [in]'),
                                 ('PP', 'Daily (24 hour) Precipitation - [in]'),
                                 ('PU', 'Accumulated Water Year Precipitation - [in]'),
                                 ('SR', 'Daily Global Solar Radiation - [langleys]'),
                                 ('TA', 'Mean Daily Humidity - [%]'),
                                 ('TG', 'Growing Degree Days - [base 50F]'),
                                 ('YM', 'Mean Daily Dewpoint Temperature - [F]'),
                                 ('UA', 'Daily Average Wind Speed - [mph]'),
                                 ('UD', 'Daily Average Wind Direction - [deg az]'),
                                 ('WG', 'Daily Peak Wind Gust - [mph]'),
                                 ('WR', 'Daily Wind Run - [miles]'),
                                 ]

WEATHER_PARAMETRS = [('DATETIME', 'Date', '[YYYY-MM-DD]'),
                     ('ET', 'Evapotranspiration Kimberly-Penman', '[mm]'),
                     ('ETos', 'Evapotranspiration ASCE-EWRI Grass', '[mm]'),
                     ('ETrs', 'Evapotranspiration ASCE-EWRI Alfalfa', '[mm]'),
                     ('MM', 'Mean Daily Air Temperature', '[C]'),
                     ('MN', 'Minimum Daily Air Temperature', '[C]'),
                     ('MX', 'Maximum Daily Air Temperature', '[C]'),
                     ('PC', 'Accumulated Precipitation Since Recharge/Reset', '[mm]'),
                     ('PP', 'Daily (24 hour) Precipitation', '[mm]'),
                     ('PU', 'Accumulated Water Year Precipitation', '[mm]'),
                     ('SR', 'Daily Global Solar Radiation', '[W m-2]'),
                     ('TA', 'Mean Daily Humidity', '[%]'),
                     ('TG', 'Growing Degree Days', '[base 50F]'),
                     ('YM', 'Mean Daily Dewpoint Temperature', '[C]'),
                     ('UA', 'Daily Average Wind Speed', '[m sec-1]'),
                     ('UD', 'Daily Average Wind Direction - [deg az]', '[deg az]'),
                     ('WG', 'Daily Peak Wind Gust', '[m sec-1]'),
                     ('WR', 'Daily Wind Run', '[m]')]


class Agrimet(object):
    def __init__(self, start_date=None, end_date=None, station=None,
                 interval=None, lat=None, lon=None, sat_image=None,
                 write_stations=False, return_raw=False):

        self.station_info_url = STATION_INFO_URL
        self.station = station

        self.empty_df = True

        if not station and not write_stations:
            if not lat and not sat_image:
                raise ValueError('Must initialize agrimet with a station, '
                                 'an Image, or some coordinates.')
            if not sat_image:
                self.station = self.find_closest_station(lat, lon)
            else:
                centroid = sat_image.scene_coords_deg
                lat, lon = centroid[0], centroid[1]
                self.station = self.find_closest_station(lat, lon)

        self.interval = interval

        if start_date and end_date:
            self.start = datetime.strptime(start_date, '%Y-%m-%d')
            self.end = datetime.strptime(end_date, '%Y-%m-%d')
            self.today = datetime.now()
            self.start_index = (self.today - self.start).days - 1

        self.data = self.fetch_data(raw=return_raw)

    @property
    def params(self):
        return urlencode(OrderedDict([
            ('cbtt', self.station),
            ('interval', self.interval),
            ('format', 1),
            ('back', self.start_index)
        ]))

    def find_closest_station(self, target_lat, target_lon):
        """ The two-argument inverse tangent function.
        :param station_data: 
        :param target_lat: 
        :param target_lon: 
        :return: 
        """
        distances = {}
        station_data = self.load_stations()
        for feat in station_data['features']:
            stn_crds = feat['geometry']['coordinates']
            stn_site_id = feat['properties']['siteid']
            lat_stn, lon_stn = stn_crds[1], stn_crds[0]
            dist = vincenty((target_lat, target_lon), (lat_stn, lon_stn)).km
            distances[stn_site_id] = dist
        k = min(distances, key=distances.get)
        return k

    def load_stations(self):
        r = requests.get(self.station_info_url)
        stations = json.loads(r.text)
        return stations

    def to_csv(self, path_or_buf):
        self.data.to_csv(path_or_buf)

    def fetch_data(self, raw=False):
        url = '{}?{}'.format(AGRIMET_REQ_SCRIPT, self.params)
        raw_df = read_table(url, skip_blank_lines=True,
                            header=1, sep=r'\,|\t', engine='python')
        raw_df.index = date_range(self.start, periods=raw_df.shape[0])
        raw_df = raw_df[to_datetime(self.start): to_datetime(self.end)]

        if raw_df.shape[0] > 3:
            self.empty_df = False

        if raw:
            return raw_df

        reformed_data = self._reformat_dataframe(raw_df)

        return reformed_data

    def _reformat_dataframe(self, df):

        old_cols = df.columns.values.tolist()
        head_1 = []
        head_2 = []
        head_3 = []
        for x in old_cols:
            end = x.replace('{}_'.format(self.station), '')
            for j, k, l in WEATHER_PARAMETRS:
                if end.upper() == j.upper():
                    head_1.append(j.upper())
                    head_2.append(k)
                    head_3.append(l)
                    break
        df.columns = [head_1, head_2, head_3]

        for i, col in enumerate(head_1, start=0):
            try:
                # convert to standard units
                if col in ['ET', 'ETRS', 'ETOS', 'PC', 'PP', 'PU']:
                    # in to mm
                    df[col] *= 25.4
                if col in ['MN', 'MX', 'MM', 'YM']:
                    # F to C
                    df[col] = (df[col] - 32) * 5 / 9
                if col in ['UA', 'WG']:
                    # mph to m s-1
                    df[col] *= 0.44704
                if col == 'WR':
                    # mi to m
                    df['WR'] *= 1609.34
                if col == 'SR':
                    # Langleys to W m-2
                    df['SR'] *= 41868.
            except KeyError:
                head_1.remove(head_1[i])
                head_2.remove(head_2[i])
                head_3.remove(head_3[i])

        df.columns = [head_1, head_2, head_3]

        return df

    @staticmethod
    def write_agrimet_sation_shp(json_data, epsg, out):
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
