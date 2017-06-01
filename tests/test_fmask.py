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
import rasterio
import numpy as np

from pprint import pprint

from sat_image.image import Landsat5, Landsat7, Landsat8
from sat_image.fmask import Fmask
from ssebop.utils.ras_point_index import raster_point_row_col


class FmaskTestCaseL5(unittest.TestCase):
    def setUp(self):
        self.dirname_cloud = 'tests/data/lt5_image'
        self.image = Landsat5(self.dirname_cloud)

    def test_instantiate_fmask(self):
        self.assertIsInstance(self.image, Landsat5)

    def test_get_potential_cloud_layer(self):
        f = Fmask(self.image)
        self.assertIsInstance(f, Fmask)
        cloud, shadow, water = f.cloud_mask()
        c_ct, s_ct = np.count_nonzero(cloud), np.count_nonzero(shadow)
        w_ct = np.count_nonzero(water)
        self.assertEqual(c_ct, 128564)
        self.assertEqual(s_ct, 117770)
        self.assertEqual(w_ct, 1456)
        # home = os.path.expanduser('~')
        # outdir = os.path.join(home, 'images', 'sandbox')
        # f.save_array(cloud, os.path.join(outdir, 'cloud_mask.tif'))
        # f.save_array(shadow, os.path.join(outdir, 'shadow_mask.tif'))
        # f.save_array(water, os.path.join(outdir, 'water_mask.tif'))


class FmaskTestCaseL7(unittest.TestCase):
    def setUp(self):
        self.dirname_cloud = 'tests/data/le7_image'
        self.image = Landsat7(self.dirname_cloud)

    def test_instantiate_fmask(self):
        self.assertIsInstance(self.image, Landsat7)

    def test_get_potential_cloud_layer(self):
        f = Fmask(self.image)
        self.assertIsInstance(f, Fmask)
        cloud, shadow, water = f.cloud_mask()
        # c_ct, s_ct = np.count_nonzero(cloud), np.count_nonzero(shadow)
        # w_ct = np.count_nonzero(water)
        # self.assertEqual(c_ct, 128564)
        # self.assertEqual(s_ct, 117770)
        # self.assertEqual(w_ct, 1456)
        home = os.path.expanduser('~')
        outdir = os.path.join(home, 'images', 'sandbox')
        f.save_array(cloud, os.path.join(outdir, 'cloud_mask.tif'))
        f.save_array(shadow, os.path.join(outdir, 'shadow_mask.tif'))
        f.save_array(water, os.path.join(outdir, 'water_mask.tif'))


class FmaskTestCaseL8(unittest.TestCase):
    def setUp(self):
        self.dirname_cloud = 'tests/data/lc8_image'
        self.image = Landsat8(self.dirname_cloud)

    def test_instantiate_fmask(self):
        self.assertIsInstance(self.image, Landsat8)

    def test_get_potential_cloud_layer(self):
        # cloud and shadow have been visually inspected
        # test have-not-changed
        f = Fmask(self.image)
        self.assertIsInstance(f, Fmask)
        cloud, shadow = f.cloud_mask()
        c_ct, s_ct = np.count_nonzero(cloud), np.count_nonzero(shadow)
        self.assertEqual(c_ct, 222601)
        self.assertEqual(s_ct, 163867)


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
