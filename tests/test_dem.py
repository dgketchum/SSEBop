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

import os
import unittest

from bbox.bounds import GeoBounds, RasterBounds
from dem.collect import find_tiles, get_dem
from dem.dem import Dem
from sat_image.image import Landsat5


class DemTestCase(unittest.TestCase):
    def setUp(self):
        self.bbox = GeoBounds(west_lon=-116.5, east_lon=-111.0,
                              south_lat=44.3, north_lat=47.)
        self.dem = Dem(self.bbox)
        self.zoom = 10
        self.api_key = 'mapzen-JmKu1BF'

    def test_tiles(self):
        bb = self.bbox
        tls = find_tiles(self.zoom, bb.south, bb.east, bb.north, bb.west)
        self.assertEqual(tls[0], (10, 180, 360))

    def test_downlaod(self):
        home = os.path.expanduser('~')
        tif_dir = os.path.join(home, 'images', 'LT5', 'image_test', 'full_image')
        tif = os.path.join(tif_dir, 'LT05_L1TP_040028_20060706_20160909_01_T1_B5.TIF')

        bb = RasterBounds(tif)
        tls = find_tiles(self.zoom, bb.south, bb.east, bb.north, bb.west)
        bb_exp = [45.037, -111.489, 46.983, -114.726]
        bb_found = [bb.south, bb.east, bb.north, bb.west]
        for val, exp in zip(bb_exp, bb_found):
            self.assertAlmostEqual(val, exp, delta=0.01)

        image = Landsat5(tif_dir)
        arr, geo = get_dem(tls, self.api_key, warp_param=image.rasterio_geometry)
        self.dem.save(arr, geo, '/data01/images/sandbox/merged_dem.tif')
        self.assertEqual(arr.shape, (1, 10, 10))

    def test_gibs(self):
        self.assertIsInstance(self.dem, Dem)
        array, geo = self.dem.mapzen_tiled_dem(zoom=self.zoom)
        self.dem.save(array, geo, os.path.join(os.path.expanduser('~'), 'images', 'sandbox', 'dem.tif'))
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
