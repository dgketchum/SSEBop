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

from bounds.bounds import GeoBounds, RasterBounds


class BoundsTestCase(unittest.TestCase):
    def setUp(self):
        self.bbox = GeoBounds(west_lon=-116.5, east_lon=-111.0,
                              south_lat=44.3, north_lat=47.)
        self.img = 'tests/data/image_test/lt5_image/LT05_040028_B1.TIF'

    def test_geobounds(self):
        bb = self.bbox
        bb_found = [bb.west, bb.east, bb.south, bb.north]
        bb_exp = [-116.5, -111.0, 44.3, 47.]
        for val, exp in zip(bb_found, bb_exp):
            self.assertEqual(val, exp)

    def test_rasterbounds(self):
        bb = RasterBounds(self.img)
        bb_exp = [45.691, -112.427, 45.883, -112.713]
        bb_found = [bb.south, bb.east, bb.north, bb.west]
        for val, exp in zip(bb_exp, bb_found):
            self.assertAlmostEqual(val, exp, delta=0.01)


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
