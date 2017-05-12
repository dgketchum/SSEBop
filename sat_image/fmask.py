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

import os
import numpy as np
import fmask.fmask

OUT_CODE_NULL = 0
#: Output pixel value for clear land
OUT_CODE_CLEAR = 1
#: Output pixel value for cloud
OUT_CODE_CLOUD = 2
#: Output pixel value for cloud shadow
OUT_CODE_SHADOW = 3
#: Output pixel value for snow
OUT_CODE_SNOW = 4
#: Output pixel value for water
OUT_CODE_WATER = 5


def form_fmask(image):
    ''' Implement fmask algorithm.
    :param image: Landsat image stack LandsatImage object
    :return: fmask object
    '''
    shape = image.b1.shape
    nan = np.full(shape, np.nan)

    if image.sensor_id in ['TM', 'ETM']:
        brightness_temp = image.at_sat_bright_band_6
        # Potential Cloud Layer 1
        # Eqn 1, Basic Test
        ndsi = (image.b2 - image.b5) / (image.b2 + image.b5)
        ndvi = (image.b4 - image.b3) / (image.b4 + image.b3)

        true_array, false_array = np.full(shape, True, dtype=bool), np.full(shape, False, dtype=bool)

        # this is cond and cond AND cond and cond, must meet all criteria
        basic_test = np.where((image.b7 > 0.03) & (brightness_temp < 27), true_array, false_array)
        basic_test = np.where((ndsi < 0.8) & (ndvi < 0.8), basic_test, false_array)

        mean_vis = (image.b1 + image.b2 + image.b3) / 3.

        # Eqn 2, whiteness test
        whiteness = np.zeros(shape)
        for band in [image.b1, image.b2, image.b3]:
            whiteness += np.abs((band - mean_vis) / mean_vis)
        whiteness_test = np.where(whiteness < 0.7, true_array, false_array)

        # Eqn 3, Haze Optimized Transformation (HOT)
        hot_test = np.where(image.b1 - 0.5 * image.b3 - 0.08 > 0, true_array, false_array)

        # Eqn 4
        b_45_test = np.where(image.b4 / image.b5 > 0.75, true_array, false_array)

        # Eqn 5
        # this is cond and cond OR cond and cond, must meet one test or the other
        water_test = np.where((ndvi < 0.01) & (image.b4 < 0.11), true_array, false_array)
        water_test = np.where((ndvi < 0.1) & (image.b4 < 0.05), true_array, water_test)

        # Potential Cloud Pixels
        p_pix = np.where(basic_test & whiteness_test & hot_test & b_45_test, true_array, false_array)

        # Potential Cloud Layer Pass 2
        # Eqn 7, 8, 9; temperature probability for clear-sky water
        clear_sky_water_test = np.where(water_test & (image.b7 < 0.03), true_array, false_array)
        clear_sky_water_bt = np.where(clear_sky_water_test, brightness_temp, np.full(shape, np.nan))
        temp_water = int(np.nanpercentile(clear_sky_water_bt, 82.5))
        water_temp_prob = (temp_water - brightness_temp) / 4.

        # Eqn 10; constrain normalized brightness probability
        water_brightness_prob = np.where(image.b5 > 0.11, np.ones(shape) * 0.11, image.b5) / 0.11

        # Eqn 11, 12, 13; temperature probability for clear-sky land
        water_cloud_prob = water_temp_prob * water_brightness_prob
        clear_sky_land_test = np.where(~p_pix & ~water_test, true_array, false_array)
        clear_sky_land_bt = np.where(clear_sky_land_test, brightness_temp, np.full(shape, np.nan))
        low_temp, high_temp = int(np.nanpercentile(clear_sky_land_bt, 17.5)), int(
            np.nanpercentile(clear_sky_land_bt, 82.5))

        # Eqn 14
        low_temp_prob = (high_temp + 4. - brightness_temp) / (high_temp + 4 - (low_temp - 4))

        saturated_5 = image.quantize_cal_max_band_5
        saturated_3 = image.quantize_cal_max_band_3

        ndsi_mod = np.where((image.b5 == saturated_5) & (image.b5 > image.b2), np.zeros(shape), ndsi)
        ndvi_mod = np.where((image.b3 == saturated_3) & (image.b4 > image.b3), np.zeros(shape), ndvi)

        # Eqn 15, 16, 17
        spect_var_prob = 1 - np.max(np.abs(ndvi_mod), np.abs(ndsi_mod), whiteness)
        land_cloud_prob = low_temp_prob * spect_var_prob
        # find where clear sky land pixels, extract land cloud probability
        lc_prob_clear = np.where(clear_sky_land_test, land_cloud_prob, nan)
        land_threshold = np.nanpercentile(lc_prob_clear, 82.5)

        # Eqn 18
        potential_cloud = np.where(p_pix & water_test & (water_cloud_prob > 0.5), true_array, false_array)
        potential_cloud = np.where(p_pix & ~water_test & (land_cloud_prob > land_threshold), true_array,
                                   potential_cloud)
        potential_cloud = np.where((land_cloud_prob > 0.99) & ~water_test, true_array, potential_cloud)
        potential_cloud = np.where(brightness_temp < low_temp - 35, true_array, potential_cloud)

        # 'spatially improve cloud mask by using the rule that sets a pixel to cloud if five or more
        # neighboring pixels in 3x3 neighborhood are cloud

    # if image.sensor_id == 'OLI_TIRS':
    #     bt = image.

    return None


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
