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
from metio.eddy_flux import FluxSite
import json


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.data_save_loc = 'tests/data/flux_locations.json'
        self.select_sites = ['CA', 'US']

    def tearDown(self):
        pass

    def test_data_all_sites(self):
        flux = FluxSite()
        data_dict = flux.build_data_all_sites(self.data_save_loc)
        self.assertIsInstance(data_dict, dict)
        br = data_dict['BR-Ban']
        self.assertEqual(br['Latitude'], -9.8244)
        self.assertEqual(br['Longitude'], -50.1591)
        with open(self.data_save_loc) as f:
            d = json.load(f)
            self.assertIsInstance()


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
