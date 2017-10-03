# ===============================================================================
# Copyright 2017 dgketchum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

import unittest
import json
import requests
from fiona import open as fopen

from metio.agrimet import Agrimet
from sat_image.image import Landsat8


class TestAgrimet(unittest.TestCase):
    def setUp(self):
        self.point_file = 'tests/data/agrimet_test/points/agrimet_test.shp'
        self.station_info = 'https://www.usbr.gov/pn/agrimet/agrimetmap/usbr_map.json'
        self.dirname_image = 'tests/data/image_test/lc8_image'
        self.site_ids = ['umhm', 'robi', 'hntu', 'faln', 'mdxo', 'mdso', 'masw']
        self.fetch_site = 'drlm'

    def test_instantiate_Agrimet(self):

        ag = Agrimet(start_date='2000-01-01', end_date='2000-12-31',
                     station=self.fetch_site,
                     sat_image=Landsat8(self.dirname_image))
        self.assertIsInstance(ag, Agrimet)

    def test_load_station_data(self):
        r = requests.get(self.station_info)
        stations = json.loads(r.text)
        self.assertIsInstance(stations, dict)

    def test_find_closest_station(self):

        coords = []
        with fopen(self.point_file, 'r') as src:
            for feature in src:
                coords.append(feature['geometry']['coordinates'])

        for coord in coords:
            agrimet = Agrimet(lon=coord[0], lat=coord[1])

            self.assertTrue(agrimet.station in self.site_ids)

    def test_find_image_station(self):
        l8 = Landsat8(self.dirname_image)
        agrimet = Agrimet(sat_image=l8)
        self.assertEqual(agrimet.station, self.fetch_site)

    def test_fetch_data(self):
        agrimet = Agrimet(station=self.fetch_site, start_date='2015-01-01',
                          end_date='2015-12-31', interval='daily')

        raw = agrimet.fetch_data(return_raw=True)
        formed = agrimet.fetch_data()

        a = raw.iloc[1, :].tolist()
        b = formed.iloc[1, :].tolist()

        heads = ['DATETIME', 'ET', 'ETOS', 'ETRS', 'MM', 'MN', 'MX', 'PP',
                 'PU', 'SR', 'TA', 'TG', 'UA', 'UD', 'WG', 'WR', 'YM']
        # dates equality
        self.assertEqual(a[0], b[0])
        self.assertEqual(a[0], '2015-01-02')
        # in to mm
        self.assertEqual(a[2], b[2] / 25.4)
        # deg F to deg C
        self.assertAlmostEqual(a[4], (b[4] - 32) / 1.8, delta=0.01)
        # in to mm
        self.assertEqual(a[7], b[7] / 25.4)
        # Langleys to J m-2
        self.assertEqual(a[9], b[9] / 41868.)
        # mph to m sec-1
        self.assertEqual(a[12], b[12] / 0.44704)

if __name__ == '__main__':
    unittest.main()

# ===============================================================================
