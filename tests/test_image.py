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
import numpy as np

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

        toa_reflect = self.l5.toa_reflectance_band_1[150, 150]
        # independent method on yceo.yal.edu/how-to-convert-landsat-dns-top-atmosphere-toa-reflectance:
        # 3.2.1 Spectral radiance scaling method L = ((lmax - limn) / (qcalmax - qcalmin)) * (qcal - qcalmin) + lmin
        # lmin/lmax: radiance_min/max_band_x,
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
        atsat_bright_temp = self.l5.atsat_bright_band_6[150, 150]
        self.assertAlmostEqual(atsat_bright_temp, 289.253709377)


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

        toa_reflect = self.l7.toa_reflectance_band_1[150, 150]
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
        atsat_bright_temp = self.l7.atsat_bright_band_6_vcid_1[150, 150]
        self.assertAlmostEqual(atsat_bright_temp, 299.150658873)


class Landsat8TestCase(unittest.TestCase):
    def setUp(self):
        self.dir_name_LC8 = 'tests/data/d_39_27_l8'

    def test_instantiate_scene(self):
        l8 = Landsat8(self.dir_name_LC8)
        self.assertEqual(l8.mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['FILE_NAME_BAND_1'],
                         'LC08_L1TP_039027_20140518_20170307_01_T1_B1.TIF')
        self.assertEqual(l8.band_count, 11)
        self.assertEqual(l8.utm_zone, 12)
        self.assertEqual(l8.reflectance_mult_band_1, 2.0000E-05)
        not_nan = np.count_nonzero(~np.isnan(l8.b1_nan_unset))
        is_nan = np.count_nonzero(np.isnan(l8.b1_nan_unset))
        zero_count = np.count_nonzero(l8.b1_nan_unset == 0)
        non_zero_count = np.count_nonzero(l8.b1_nan_unset > 0)
        self.assertEqual(not_nan, l8.b1_counts['non_nan'])
        self.assertEqual(is_nan, l8.b1_counts['nan'])
        self.assertEqual(zero_count, l8.b1_counts['zero'])
        self.assertEqual(non_zero_count, l8.b1_counts['non_zero'])

    def test_toa_reflectance(self):
        l8 = Landsat8(self.dir_name_LC8)
        self.assertAlmostEqual(l8.toa_reflectance_band_1[150, 150], 0.454697365494, delta=0.0001)
        mp = l8.reflectance_mult_band_1
        ap = l8.reflectance_add_band_1
        qcal = l8.b1[150, 150]
        sun_el = l8.sun_elevation * np.pi / 180
        toa_reflct_test = ((mp * qcal) + ap) / np.sin(sun_el)
        self.assertAlmostEqual(toa_reflct_test, l8.toa_reflectance_band_1[150, 150], delta=0.0001)
        self.assertAlmostEqual(l8.toa_reflectance_band_1[150, 150], 0.454697365494)
        self.assertEqual(l8.k1_constant_band_10, 774.8853)
        self.assertEqual(l8.k2_constant_band_10, 1321.0789)
        self.assertAlmostEqual(l8.atsat_bright_band_10[150, 150], 254.315403913, delta=0.0001)


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
