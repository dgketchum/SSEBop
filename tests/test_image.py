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
        self.dir_name_LT5 = 'tests/data/lt5_cloud'
        # results from fmask.exe
        self.exp_reflect = 'tests/data/lt5_cloud/LT5_reflct_1000x.tif'
        self.l5 = Landsat5(self.dir_name_LT5)

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
        toa_reflect = self.l5.reflectance(1)[150, 150]
        qcal = self.l5.b1[150, 150]
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
            reflct = src.read(1) / 10000.

        self.assertAlmostEqual(reflct[150, 150], toa_reflect)
        at_sat_bright_temp = self.l5.brightness_temp(6)[150, 150]
        self.assertAlmostEqual(at_sat_bright_temp, )


class Landsat7TestCase(unittest.TestCase):
    def setUp(self):
        self.dir_name_LT7 = 'tests/data/d_38_27_l7'
        self.l7 = Landsat7(self.dir_name_LT7)

    def test_instantiate_scene(self):
        self.assertEqual(self.l7.mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['FILE_NAME_BAND_1'],
                         'LE70380272007136EDC00_B1.TIF')
        self.assertEqual(self.l7.band_count, 9)
        self.assertEqual(self.l7.utm_zone, 12)
        self.assertEqual(self.l7.ex_atm_irrad, (1970.0, 1842.0, 1547.0, 1044.0,
                                                255.700, np.nan, np.nan, 82.06, 1369.00))

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
        at_sat_bright_temp = self.l7.brightness_temp()[150, 150]
        self.assertAlmostEqual(at_sat_bright_temp, 299.150658873)


class Landsat8TestCase(unittest.TestCase):
    def setUp(self):
        self.dirname_cloud = 'tests/data/lc8_cloud'
        # results from rio-toa
        self.ex_bright = os.path.join(self.dirname_cloud, 'LC8_brightemp_B10.TIF')
        self.ex_reflect = os.path.join(self.dirname_cloud, 'LC8_reflct_B2.TIF')

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
        self.assertAlmostEqual(ex_br[100, 100],
                               bright[100, 100],
                               delta=0.001)

    def test_toa_reflectance(self):
        l8 = Landsat8(self.dirname_cloud)
        with rasterio.open(self.ex_reflect, 'r') as src:
            expected_reflectance = src.read(1)
        reflectance = l8.reflectance(2)

        print('nan counts expect: {}, calculated: {}'.format(np.count_nonzero(expected_reflectance),
                                                             np.count_nonzero(reflectance)))

        print('expected mean: {}, min: {}, max: {}'.format(np.nanmean(expected_reflectance),
                                                           np.nanmin(expected_reflectance),
                                                           np.nanmax(expected_reflectance)))

        print('calculated mean: {}, min: {}, max: {}'.format(np.nanmean(reflectance),
                                                             np.nanmin(reflectance),
                                                             np.nanmax(reflectance)))

        self.assertAlmostEqual(expected_reflectance[100, 100],
                               reflectance[100, 100],
                               delta=0.001)


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
