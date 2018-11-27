# ===============================================================================
# Copyright 2018 dgketchum
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
from bounds import RasterBounds
from met.thredds import GridMet
from sat_image.image import Landsat8
from datetime import datetime

class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.start = datetime(2014, 8, 15)
        self.end = datetime(2014, 8, 20)
        self.dir_name_LC8 = '/home/dgketchum/IrrigationGIS/tests/gridmet/LC80380272014227LGN01'

    def test_daily_gridmet_conforming(self):
        l8 = Landsat8(self.dir_name_LC8)
        polygon = l8.get_tile_geometry()
        bounds = RasterBounds(affine_transform=l8.rasterio_geometry['transform'], profile=l8.rasterio_geometry)
        gridmet = GridMet(self.var, date=self.date, bbox=bounds,
                          target_profile=l8.rasterio_geometry, clip_feature=polygon)
        pet = gridmet.get_data_subset()
        shape = 1, l8.rasterio_geometry['height'], l8.rasterio_geometry['width']
        self.assertEqual(pet.shape, shape)


if __name__ == '__main__':
    unittest.main()
# ========================= EOF ====================================================================
