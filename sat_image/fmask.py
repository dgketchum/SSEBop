# =============================================================================================
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
# =============================================================================================
'''
Implement the cloud and shadow algorithms known collectively as Fmask, 
as published in 

Zhu, Z. and Woodcock, C.E. (2012). 
Object-based cloud and cloud shadow detection in Landsat imagery
Remote Sensing of Environment 118 (2012) 83-94. 
    
and
    
Zhu, Z., Wang, S. and Woodcock, C.E. (2015).
Improvement and expansion of the Fmask algorithm: cloud, cloud
shadow, and snow detection for Landsats 4-7, 8, and Sentinel 2 images
Remote Sensing of Environment 159 (2015) 269-277.
'''
from __future__ import print_function, division

import numpy as np
from scipy.ndimage import generic_filter, grey_dilation, label


# import fmask.fmask


class Fmask(object):
    ''' Implement fmask algorithm.
    :param image: Landsat image stack LandsatImage object
    :return: fmask object
    '''

    def __init__(self, image):
        self.image = image
        self.shape = image.b1.shape
        self.nan = np.full(self.shape, np.nan)
        self.brightness_temp = image.at_sat_bright_band_6
        self.ndsi = (image.b2 - image.b5) / (image.b2 + image.b5)
        self.ndvi = (image.b4 - image.b3) / (image.b4 + image.b3)

        self.trues, self.false = np.full(self.shape, True, dtype=bool), np.full(self.shape, False, dtype=bool)

        for attr, code in zip(['code_null', 'code_clear', 'code_cloud', 'code_shadow', 'code_snow',
                               'code_water'], range(6)):
            setattr(self, attr, code)

    def get_fmask(self):
        potential_cloud_layer = self.get_potential_cloud_layer()
        potential_shadow_layer = self.get_potential_shadow_layer()
        potential_snow_layer = self.get_potential_snow_layer()
        fmask = np.full(self.shape, self.code_clear)
        fmask = np.where(potential_cloud_layer, self.code_cloud, fmask)
        fmask = np.where(potential_snow_layer, self.code_snow, fmask)
        fmask = np.where(potential_shadow_layer, self.code_shadow, fmask)
        return fmask

    def get_potential_cloud_layer(self):
        potential_pixels, water, white = self._do_first_pass_tests()
        pot_cloud_lyr = self._do_second_pass_tests(potential_pixels, water, white)
        return pot_cloud_lyr

    def get_potential_snow_layer(self):
        potential_snow = np.where(self.ndsi > 0.15, self.trues, self.false)
        potential_snow = np.where(self.brightness_temp < 3.8, self.trues, self.false)
        potential_snow = np.where(self.image.b4 > 0.11, self.trues, self.false)
        potential_snow = np.where(self.image.b2 > 0.1, self.trues, self.false)

        return potential_snow

    def get_potential_shadow_layer(self):
        band = self.b4_nan_unset
        max_dn, min_dn = np.max(band), np.min(band[band > 0])
        null_mask = np.where(band == 0, 1, 0)
        dilated = grey_dilation(null_mask, size=(3, 3))
        inner_bound = dilated - null_mask
        boundary_value = max(np.percentile(band[band > 0], 17.5), min_dn)
        marker = np.where(inner_bound, max_dn, boundary_value)
        marker = np.where(null_mask, 0, marker)
        potential_shadow = np.where(marker - band > 0.02, 1, 0)
        return potential_shadow

    def _do_cloud_shadow_match(self, cloud, shadow):
        c_labels = label(cloud)

    def _do_first_pass_tests(self):
        # Potential Cloud Layer 1
        # Eqn 1, Basic Test
        # this is cond and cond AND cond and cond, must meet all criteria
        basic_test = np.where((self.image.b7 > 0.03) & (self.brightness_temp < 27), self.trues, self.false)
        basic_test = np.where((self.ndsi < 0.8) & (self.ndvi < 0.8), basic_test, self.false)

        mean_vis = (self.image.b1 + self.image.b2 + self.image.b3) / 3.

        # Eqn 2, whiteness test
        whiteness = np.zeros(self.shape)
        for band in [self.image.b1, self.image.b2, self.image.b3]:
            whiteness += np.abs((band - mean_vis) / mean_vis)
        whiteness_test = np.where(whiteness < 0.7, self.trues, self.false)

        # Eqn 3, Haze Optimized Transformation (HOT)
        hot_test = np.where(self.image.b1 - 0.5 * self.image.b3 - 0.08 > 0, self.trues, self.false)

        # Eqn 4
        b_45_test = np.where(self.image.b4 / self.image.b5 > 0.75, self.trues, self.false)

        # Eqn 5
        # this is cond and cond OR cond and cond, must meet one test or the other
        water_test = np.where((self.ndvi < 0.01) & (self.image.b4 < 0.11), self.trues, self.false)
        water_test = np.where((self.ndvi < 0.1) & (self.image.b4 < 0.05), self.trues, water_test)

        # Potential Cloud Pixels
        p_pix = np.where(basic_test & whiteness_test & hot_test & b_45_test, self.trues, self.false)

        return p_pix, water_test, whiteness

    def _do_second_pass_tests(self, p_pix, water_test, whiteness):
        # Potential Cloud Layer Pass 2
        # Eqn 7, 8, 9; temperature probability for clear-sky water
        clear_sky_water_test = np.where(water_test & (self.image.b7 < 0.03), self.trues, self.false)
        clear_sky_water_bt = np.where(clear_sky_water_test, self.brightness_temp, np.full(self.shape, np.nan))
        temp_water = int(np.nanpercentile(clear_sky_water_bt, 82.5))
        water_temp_prob = (temp_water - self.brightness_temp) / 4.

        # Eqn 10; constrain normalized brightness probability
        water_brightness_prob = np.where(self.image.b5 > 0.11, np.ones(self.shape) * 0.11, self.image.b5) / 0.11

        # Eqn 11, 12, 13; temperature probability for clear-sky land
        water_cloud_prob = water_temp_prob * water_brightness_prob
        clear_sky_land_test = np.where(~p_pix & ~water_test, self.trues, self.false)
        clear_sky_land_bt = np.where(clear_sky_land_test, self.brightness_temp, np.full(self.shape, np.nan))
        low_temp, high_temp = int(np.nanpercentile(clear_sky_land_bt, 17.5)), int(
            np.nanpercentile(clear_sky_land_bt, 82.5))

        # Eqn 14
        low_temp_prob = (high_temp + 4. - self.brightness_temp) / (high_temp + 4 - (low_temp - 4))

        saturated_5 = self.image.quantize_cal_max_band_5
        saturated_3 = self.image.quantize_cal_max_band_3

        ndsi_mod = np.where((self.image.b5 == saturated_5) & (self.image.b5 > self.image.b2), np.zeros(self.shape),
                            self.ndsi)
        ndvi_mod = np.where((self.image.b3 == saturated_3) & (self.image.b4 > self.image.b3), np.zeros(self.shape),
                            self.ndvi)

        # Eqn 15, 16, 17
        spect_var_prob = 1 - np.max(np.abs(ndvi_mod), np.abs(ndsi_mod), whiteness)
        land_cloud_prob = low_temp_prob * spect_var_prob
        # find where clear sky land pixels, extract land cloud probability
        lc_prob_clear = np.where(clear_sky_land_test, land_cloud_prob, self.nan)
        land_threshold = np.nanpercentile(lc_prob_clear, 82.5)

        # Eqn 18
        potential_cloud = np.where(p_pix & water_test & (water_cloud_prob > 0.5), self.trues, self.false)
        potential_cloud = np.where(p_pix & ~water_test & (land_cloud_prob > land_threshold), self.trues,
                                   potential_cloud)
        potential_cloud = np.where((land_cloud_prob > 0.99) & ~water_test, self.trues, potential_cloud)
        potential_cloud = np.where(self.brightness_temp < low_temp - 35, self.trues, potential_cloud)

        # 'spatially improve cloud mask by using the rule that sets a pixel to cloud if five or more
        # neighboring pixels in 3x3 neighborhood are cloud'

        def do_filter(input_arr, count):
            def func(arr):
                return bool(np.count_nonzero(arr) > count)

            return generic_filter(input_arr, func, footprint=np.ones((3, 3)), mode='mirror')

        potential_cloud = do_filter(potential_cloud, 5)

        return potential_cloud

# ========================= EOF ====================================================================
