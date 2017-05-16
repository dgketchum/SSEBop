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
import fiona
from pprint import pprint

from sat_image.image import Landsat5


class FmaskTestCaseL5(unittest.TestCase):
    def setUp(self):
        self.dirname_cloud = 'tests/data/lt5_cloud'
        self.image = Landsat5(self.dirname_cloud)
        point_extract = 'tests/data/point_data/butte_lt5_extract.shp'

        self.point_data = {}
        with fiona.open(point_extract) as src:
            for feature in src:
                self.point_data[feature['id']] = feature
        pprint(self.point_data)

    def tearDown(self):
        pass

    def test_instantiat_fmask(self):
        self.assertIsInstance(self.image, Landsat5)


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
