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

from metio.agrimet import haversine, load_stations, find_closest_station


class TestAgrimet(unittest.TestCase):
    def setUp(self):
        self.point_file = 'tests/data/agrimet_test/points/agrimet_test.shp'
        self.station_info = 'https://www.usbr.gov/pn/agrimet/agrimetmap/usbr_map.json'

        self.site_ids = ['umhm', 'robi', 'hntu', 'faln', 'mdxo', 'masw']

    def test_loat_station_data(self):
        r = requests.get(self.station_info)
        stations = json.loads(r.text)
        self.assertIsInstance(stations, dict)

    def test_great_circle_dist(self):
        # two eastern-most sites in MT
        lat1, lon1 = 46.778, -105.298
        lat2, lon2 = 46.988, -104.803
        # dist = great_circle_distance(lat1, lon1, lat2, lon2)
        dist = haversine(lat1, lon1, lat2, lon2)
        self.assertAlmostEqual(60., dist, delta=5)

    def test_find_closest_station(self):

        data = load_stations()

        coords = []
        with fopen(self.point_file, 'r') as src:
            for feature in src:
                coords.append(feature['geometry']['coordinates'])

        for coord in coords:
            stn = find_closest_station(data, target_lon=coord[0], target_lat=coord[1])
            self.assertTrue(stn in self.site_ids)

if __name__ == '__main__':
    unittest.main()

# ===============================================================================
