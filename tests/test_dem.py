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

from bounds.bounds import GeoBounds, RasterBounds
from dem.dem import MapzenDem
from sat_image.image import Landsat5


class ThreddsDemTestCase(unittest.TestCase):
    def setUp(self):
        pass


class MapzenDemTestCase(unittest.TestCase):
    def setUp(self):
        self.bbox = GeoBounds(west_lon=-116.5, east_lon=-111.0,
                              south_lat=44.3, north_lat=47.)
        self.api_key = 'mapzen-JmKu1BF'

    def test_dem(self):
        home = os.path.expanduser('~')
        tif_dir = os.path.join(home, 'images', 'LT5', 'image_test', 'full_image')
        tif = os.path.join(tif_dir, 'LT05_L1TP_040028_20060706_20160909_01_T1_B5.TIF')

        l5 = Landsat5(tif_dir)
        bb = RasterBounds(tif)
        polygon = l5.get_tile_geometry()
        profile = l5.rasterio_geometry

        dem = MapzenDem(zoom=10, bounds=bb, target_profile=profile, clip_object=polygon,
                        api_key=self.api_key)

        elev = dem.terrain(attribute='elevation')
        self.assertEqual(elev.shape, (1, 7429, 8163))

        aspect = dem.terrain(attribute='aspect')
        self.assertEqual(aspect.shape, (7429, 8163))

        slope = dem.terrain(attribute='slope')
        self.assertEqual(slope.shape, (1, 7429, 8163))


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
