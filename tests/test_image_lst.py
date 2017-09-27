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
from fiona import open as fopen
from rasterio import open as rasopen

from sat_image.image import Landsat8, Landsat5, Landsat7, LandsatImage


class TestImageLST5(unittest.TestCase):
    def setUp(self):
        self.dir_name_LT5 = 'tests/data/ssebop_test/lt5/041_025/2000/LT50410252000194AAA01'
        self.l5 = Landsat5(self.dir_name_LT5)


    def test_something(self):
        self.assertEqual(True, False)


class TestImageLST7(unittest.TestCase):
    def setUp(self):
        self.dir_name_LT7 = 'tests/data/ssebop_test/le7/041_025/2000/LE70410252000234PAC00'
        self.l7 = Landsat7(self.dir_name_LT7)

    def test_something(self):
        self.assertEqual(True, False)


class TestImageLST8(unittest.TestCase):
    def setUp(self):
        self.dir_name_LT8 = 'tests/data/ssebop_test/lt5/041_025/2000/LT50410252000194AAA01'
        self.l8 = Landsat8(self.dir_name_LT8)

    def test_something(self):
        self.assertEqual(True, False)


def raster_point_row_col(raster, points):
    pt_data = {}

    with fopen(points, 'r') as src:
        for feature in src:
            pt_data[feature['id']] = feature

    if isinstance(raster, LandsatImage):
        a = raster.rasterio_geometry['affine']
    if isinstance(raster, str):
        with rasopen(raster, 'r') as src:
            a = src.affine

    for key, val in pt_data.items():
        x, y = val['geometry']['coordinates'][0], val['geometry']['coordinates'][1]
        col, row = ~a * (x, y)
        val['index'] = row, col

    return pt_data

if __name__ == '__main__':
    unittest.main()

# ===============================================================================
