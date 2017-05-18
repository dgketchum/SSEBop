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
        self.dir_name_LT5 = 'tests/data/d_36_29_l5'

    def test_earth_sun(self):
        landsat = LandsatImage(self.dir_name_LT5)
        dist_au = landsat.earth_sun_dist
        self.assertAlmostEqual(dist_au, 1.01387, delta=0.01)


class Landsat5TestCase(unittest.TestCase):
    def setUp(self):
        self.dir_name_LT5 = 'tests/data/d_36_29_l5'
        self.l5 = Landsat5(self.dir_name_LT5)

    def test_instantiate_scene(self):
        self.assertTrue(self.l5.isdir)
        self.assertEqual(self.l5.mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['FILE_NAME_BAND_1'],
                         'LT50360292007146PAC01_B1.TIF')
        self.assertEqual(self.l5.b1.shape, (300, 300))
        self.assertEqual(self.l5.band_count, 7)
        self.assertEqual(self.l5.utm_zone, 13)
        self.assertEqual(self.l5.ex_atm_irrad, (1957.0, 1826.0, 1554.0,
                                                1036.0, 215.0, 1e-6, 80.67))

        self.assertEqual(self.l5.rasterio_geometry['height'], 300)
        self.assertEqual(self.l5.rasterio_geometry['driver'], 'GTiff')
        self.assertEqual(self.l5.rasterio_geometry['dtype'], 'uint8')
        self.assertEqual(self.l5.rasterio_geometry['transform'], (176385.0, 822.1, 0.0, 5055315.0, 0.0, -742.1))

    def test_reflectance(self):
        toa_reflect = self.l5.reflectance(1)[150, 150]
        qcal = self.l5.b1[150, 150]
        qcal_min = self.l5.quantize_cal_min_band_1
        qcal_max = self.l5.quantize_cal_max_band_1
        l_min = self.l5.radiance_minimum_band_1
        l_max = self.l5.radiance_maximum_band_1
        radiance = ((l_max - l_min) / (qcal_max - qcal_min)) * (qcal - qcal_min) + l_min
        toa_reflect_test = (np.pi * radiance) / ((1 / (self.l5.earth_sun_dist ** 2)) * self.l5.ex_atm_irrad[0] * np.cos(
            self.l5.solar_zenith_rad))
        self.assertEqual(toa_reflect_test, toa_reflect)
        self.assertAlmostEqual(toa_reflect, 0.140619859807, delta=0.00001)
        at_sat_bright_temp = self.l5.brightness_temp(6)[150, 150]
        self.assertAlmostEqual(at_sat_bright_temp, 289.253709377)


class Landsat7TestCase(unittest.TestCase):
    def setUp(self):
        self.dir_name_LT7 = 'tests/data/d_38_27_l7'
        self.l7 = Landsat7(self.dir_name_LT7)

    def test_instantiate_scene(self):
        self.assertEqual(self.l7.mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['FILE_NAME_BAND_1'],
                         'LE70380272007136EDC00_B1.TIF')
        self.assertEqual(self.l7.band_count, 9)
        self.assertEqual(self.l7.utm_zone, 12)
        self.assertEqual(self.l7.ex_atm_irrad, (1969.0, 1840.0, 1551.0, 1044.0,
                                                255.700, 1e-6, 1e-6, 82.07, 1368.00))

        self.assertEqual(self.l7.rasterio_geometry['height'], 300)
        self.assertEqual(self.l7.rasterio_geometry['driver'], 'GTiff')
        self.assertEqual(self.l7.rasterio_geometry['dtype'], 'uint8')
        self.assertEqual(self.l7.rasterio_geometry['transform'], (491985.0, 808.1, 0.0, 5364915.0, 0.0, -723.1))

    def test_reflectance(self):
        toa_reflect = self.l7.reflectance(1)[150, 150]
        # independent method on yceo.yal.edu/how-to-convert-landsat-dns-top-atmosphere-toa-reflectance:
        # 3.2.1 Spectral radiance scaling method L = ((lmax - limn) / (qcalmax - qcalmin)) * (qcal - qcalmin) + lmin
        # lmin/lmax: radiance_min/max_band_x,
        qcal = self.l7.b1[150, 150]
        qcal_min = self.l7.quantize_cal_min_band_1
        qcal_max = self.l7.quantize_cal_max_band_1
        l_min = self.l7.radiance_minimum_band_1
        l_max = self.l7.radiance_maximum_band_1
        radiance = ((l_max - l_min) / (qcal_max - qcal_min)) * (qcal - qcal_min) + l_min
        toa_reflect_test = (np.pi * radiance) / ((1 / (self.l7.earth_sun_dist ** 2)) * self.l7.ex_atm_irrad[0] * np.cos(
            self.l7.solar_zenith_rad))
        self.assertAlmostEqual(toa_reflect_test, toa_reflect, delta=0.00001)
        self.assertAlmostEqual(toa_reflect, 0.112894940522, delta=0.00001)
        self.assertTrue(k1_constant_band_6_vcid_1)
        at_sat_bright_temp = self.l7.brightness_temp()[150, 150]
        self.assertAlmostEqual(at_sat_bright_temp, 299.150658873)


class Landsat8TestCase(unittest.TestCase):
    def setUp(self):
        self.dirname_cloud = 'tests/data/lc8_cloud'
        self.dir_name_LC8 = 'tests/data/d_39_27_l8'
        self.ex_bright = os.path.join(self.dirname_cloud, 'LC8_brightemp_B10.TIF')
        self.ex_reflect = os.path.join(self.dirname_cloud, 'LC8_reflct_B2.TIF')

    def test_instantiate_scene(self):
        l8 = Landsat8(self.dir_name_LC8)
        self.assertEqual(l8.mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['FILE_NAME_BAND_1'],
                         'LC08_L1TP_039027_20140518_20170307_01_T1_B1.TIF')
        self.assertEqual(l8.band_count, 11)
        self.assertEqual(l8.reflectance_mult_band_1, 2.0000E-05)
        non_zero_count = np.count_nonzero(l8.b1 > 0)
        self.assertEqual(non_zero_count, l8.b1_counts['non_zero'])
        self.assertEqual(l8.rasterio_geometry['transform'], (381885.0, 784.1, 0.0, 5373915.0, 0.0, -795.1))

    def test_toa_brightness(self):
        l8 = Landsat8(self.dir_name_LC8)

        with rasterio.open(self.ex_bright, 'r') as src:
            expected_bright = src.read(1)
        bright = l8.brightness_temp(10)
        self.assertAlmostEqual(expected_bright[100, 100],
                               bright[100, 100],
                               delta=0.001)

    def test_toa_reflectance(self):
        l8 = Landsat8(self.dir_name_LC8)
        with rasterio.open(self.ex_reflect, 'r') as src:
            expected_reflectance = src.read(1)
        reflectance = l8.reflectance(2)
        self.assertAlmostEqual(expected_reflectance[100, 100],
                               reflectance[100, 100],
                               delta=0.001)

if __name__ == '__main__':
    unittest.main()

# ===============================================================================
