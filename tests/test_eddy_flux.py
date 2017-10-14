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

import os
import json
from fiona import open as fopen

from metio.eddy_flux import FluxSite


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.data_save_loc = 'tests/data/flux_locations.json'
        self.data_perm = 'metio/data/flux_locations.json'
        self.select_sites = ['BR']
        self.shape_out = 'metio/data/flux_locations.shp'

    def tearDown(self):
        pass

    def test_data_collector_few_sites(self):
        flux = FluxSite()
        data_dict = flux.build_data_all_sites(self.data_save_loc,
                                              country_abvs=self.select_sites)
        self.assertIsInstance(data_dict, dict)
        br = data_dict['BR-Ban']
        self.assertEqual(br['Latitude'], -9.8244)
        self.assertEqual(br['Longitude'], -50.1591)
        with open(self.data_save_loc) as f:
            d = json.load(f)
            self.assertIsInstance(d, dict)
        os.remove(self.data_save_loc)

    def test_data_collector_many_sites(self):
        flux = FluxSite()
        data_dict = flux.build_data_all_sites(self.data_save_loc)
        self.assertEqual(len(data_dict.keys()), 252)
        with open(self.data_save_loc) as f:
            d = json.load(f)
            self.assertIsInstance(d, dict)
        os.remove(self.data_save_loc)

    def test_local_json_loader(self):
        flux = FluxSite(json_file=self.data_perm)
        data = flux.data
        self.assertEqual(len(data.keys()), 252)
        self.assertIsInstance(data, dict)

    def test_write_shapefile(self):
        flux = FluxSite(self.data_perm)
        data = flux.data
        flux.write_locations_to_shp(data, self.shape_out)
        with fopen(self.shape_out, 'r') as shp:
            count = 0
            for feature in shp:
                count += 1
            self.assertEqual(count, 252)

if __name__ == '__main__':
    unittest.main()

# ===============================================================================
