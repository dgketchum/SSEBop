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
from datetime import datetime
from xarray import Dataset

from bounds.bounds import GeoBounds, RasterBounds
from metio.thredds import GridMet, TopoWX
from sat_image.image import Landsat5


class TestTopoWX(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2011, 4, 1)
        self.date = datetime(2011, 4, 1)
        self.end = datetime(2011, 10, 31)
        self.image_shape = (1, 7431, 8161)

        self.dir_name_LT5 = 'tests/data/image_test/lt5_image'

    def test_conforming_array(self):
        """ Test Thredds.TopoWx conforming array has equal shape to Landsat image
        :return: 
        """
        home = os.path.expanduser('~')
        tif_dir = os.path.join(home, 'images', 'LT5', 'image_test', 'full_image')
        for t in ['tmin', 'tmax']:
            out_file = os.path.join(home, 'images', 'sandbox',
                                    'thredds', '{}_{}_{}_{}.tif'.format(t, self.date.year,
                                                                        self.date.month, self.date.day))
            l5 = Landsat5(tif_dir)
            polygon = l5.get_tile_geometry()
            bounds = RasterBounds(affine_transform=l5.transform, profile=l5.profile, latlon=True)
            topowx = TopoWX(date=self.date, bbox=bounds, target_profile=l5.profile,
                            clip_feature=polygon)
            temp = topowx.get_data_subset(grid_conform=True, var=t, out_file=out_file)
            self.assertEqual(temp.shape, self.image_shape)


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
