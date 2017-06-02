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
import numpy as np
import rasterio

from sat_image.image import LandsatImage, Landsat5, Landsat7, Landsat8


class LandsatImageTestCase(unittest.TestCase):
    def setUp(self):
        self.dir_name_LT5 = 'tests/data/image_test/lc8_image'

    def test_earth_sun(self):
        landsat = LandsatImage(self.dir_name_LT5)
        dist_au = landsat.earth_sun_dist
        self.assertAlmostEqual(dist_au, 1.01387, delta=0.01)


class Landsat5TestCase(unittest.TestCase):
    def setUp(self):
        self.dir_name_LT5 = 'tests/data/image_test/lt5_image'
        # results from fmask.exe
        # bitbucket.org/chchrsc/python-fmask/
        self.exp_reflect = 'tests/data/image_test/lt5_image/LT5_reflct_10000x_b1.tif'
        self.l5 = Landsat5(self.dir_name_LT5)
        self.cell = 150, 150

    def test_instantiate_scene(self):
        self.assertTrue(self.l5.isdir)
        self.assertEqual(self.l5.mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['FILE_NAME_BAND_1'],
                         'LT05_L1TP_040028_20060706_20160909_01_T1_B1.TIF')
        self.assertEqual(self.l5.b1.shape, (727, 727))
        self.assertEqual(self.l5.utm_zone, 12)
        self.assertEqual(self.l5.ex_atm_irrad, (1958.0, 1827.0, 1551.0,
                                                1036.0, 214.9, np.nan, 80.65))

        self.assertEqual(self.l5.rasterio_geometry['height'], 727)
        self.assertEqual(self.l5.rasterio_geometry['driver'], 'GTiff')
        self.assertEqual(self.l5.rasterio_geometry['dtype'], 'uint16')
        self.assertEqual(self.l5.rasterio_geometry['transform'], (367035.0, 30.0, 0.0, 5082585.0, 0.0, -30.0))

    def test_reflectance(self):
        toa_reflect = self.l5.reflectance(1)[self.cell]
        qcal = self.l5.b1[self.cell]
        qcal_min = self.l5.quantize_cal_min_band_1
        qcal_max = self.l5.quantize_cal_max_band_1
        l_min = self.l5.radiance_minimum_band_1
        l_max = self.l5.radiance_maximum_band_1
        radiance = ((l_max - l_min) / (qcal_max - qcal_min)) * (qcal - qcal_min) + l_min
        toa_reflect_test = (np.pi * radiance) / ((1 / (self.l5.earth_sun_dist ** 2)) * self.l5.ex_atm_irrad[0] * np.cos(
            self.l5.solar_zenith_rad))
        self.assertAlmostEqual(toa_reflect_test, toa_reflect, delta=0.001)
        self.assertAlmostEqual(toa_reflect, 0.1105287, delta=0.001)

        with rasterio.open(self.exp_reflect, 'r') as src:
            reflct = src.read(1)
            reflct = np.array(reflct, dtype=np.float32)
            reflct[reflct == 32767.] = np.nan
            reflct *= 1 / 10000.

        self.assertAlmostEqual(reflct[self.cell], toa_reflect, delta=0.01)

    def test_brightness(self):
        bright = self.l5.brightness_temp(6)
        self.assertEqual(bright[self.cell], 263)


class Landsat7TestCase(unittest.TestCase):
    def setUp(self):
        # results from fmask.exe
        # bitbucket.org/chchrsc/python-fmask/
        self.dir_name_LT7 = 'tests/data/image_test/le7_image'
        self.exp_reflect = 'tests/data/image_test/le7_image/LE7_reflct_10000x_b1.tif'
        self.l7 = Landsat7(self.dir_name_LT7)
        self.cell = 300, 300

    def test_instantiate_scene(self):
        self.assertEqual(self.l7.mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['FILE_NAME_BAND_1'],
                         'LE07_L1TP_039028_20100702_20160915_01_T1_B1.TIF')
        self.assertEqual(self.l7.utm_zone, 12)
        self.assertEqual(self.l7.ex_atm_irrad, (1970.0, 1842.0, 1547.0, 1044.0,
                                                255.700, np.nan, np.nan, 82.06, 1369.00))
        self.assertEqual(self.l7.rasterio_geometry['height'], 727)
        self.assertEqual(self.l7.rasterio_geometry['driver'], 'GTiff')
        self.assertEqual(self.l7.rasterio_geometry['dtype'], 'uint8')
        self.assertEqual(self.l7.rasterio_geometry['transform'], (367035.0, 30.0, 0.0, 5082585.0, 0.0, -30.0))

    def test_reflectance(self):
        toa_reflect = self.l7.reflectance(1)

        with rasterio.open(self.exp_reflect, 'r') as src:
            reflct = src.read(1)
            reflct = np.array(reflct, dtype=np.float32)
            reflct[reflct == 32767.] = np.nan
            reflct *= 1 / 10000.

        toa_reflect = np.where(np.isnan(reflct), reflct, toa_reflect)

        self.assertAlmostEqual(reflct[self.cell], toa_reflect[self.cell], delta=0.01)

    def test_brightness(self):
        bright = self.l7.brightness_temp(6)
        self.assertEqual(bright[self.cell], 263)


class Landsat8TestCase(unittest.TestCase):
    def setUp(self):
        self.dirname_cloud = 'tests/data/image_test/lc8_image'
        # results from rio-toa
        self.ex_bright = os.path.join(self.dirname_cloud, 'LC8_brightemp_B10.TIF')
        self.ex_reflect = os.path.join(self.dirname_cloud, 'LC8_reflct_B1.TIF')
        self.cell = 300, 300

    def test_instantiate_scene(self):
        l8 = Landsat8(self.dirname_cloud)
        self.assertEqual(l8.mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['FILE_NAME_BAND_1'],
                         'LC80400282014193LGN00_B1.TIF')
        self.assertEqual(l8.utm_zone, 12)
        self.assertEqual(l8.reflectance_mult_band_1, 2.0000E-05)
        not_nan = np.count_nonzero(~np.isnan(l8.b1))
        is_nan = np.count_nonzero(np.isnan(l8.b1))
        zero_count = np.count_nonzero(l8.b1 == 0)
        non_zero_count = np.count_nonzero(l8.b1 > 0)
        self.assertEqual(not_nan, l8.b1_counts['non_nan'])
        self.assertEqual(is_nan, l8.b1_counts['nan'])
        self.assertEqual(zero_count, l8.b1_counts['zero'])
        self.assertEqual(non_zero_count, l8.b1_counts['non_zero'])

        self.assertEqual(l8.rasterio_geometry['height'], 727)
        self.assertEqual(l8.rasterio_geometry['driver'], 'GTiff')
        self.assertEqual(l8.rasterio_geometry['dtype'], 'uint16')
        self.assertEqual(l8.rasterio_geometry['transform'], (367035.0, 30.0, 0.0, 5082585.0, 0.0, -30.0))

    def test_toa_brightness(self):
        l8 = Landsat8(self.dirname_cloud)

        with rasterio.open(self.ex_bright, 'r') as src:
            ex_br = src.read(1)
        bright = l8.brightness_temp(10)
        self.assertEqual(bright.shape, ex_br.shape)
        self.assertAlmostEqual(ex_br[self.cell],
                               bright[self.cell],
                               delta=0.001)

    def test_toa_reflectance(self):
        l8 = Landsat8(self.dirname_cloud)
        with rasterio.open(self.ex_reflect, 'r') as src:
            expected_reflectance = src.read(1)
        reflectance = l8.reflectance(1)

        self.assertAlmostEqual(expected_reflectance[self.cell],
                               reflectance[self.cell],
                               delta=0.001)


if __name__ == '__main__':
    unittest.main()


# ===============================================================================
