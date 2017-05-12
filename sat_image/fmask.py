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

    if image.sensor_id in ['TM', 'ETM']:
        bt = image.at_sat_bright_band_6
        # Eqn 1, Basic Test
        ndsi = (image.b2 - image.b5) / (image.b2 + image.b5)
        ndvi = (image.b4 - image.b3) / (image.b4 + image.b3)

        true_array, false_array = np.full(shape, True, dtype=bool), np.full(shape, False, dtype=bool)

        basic_test = np.where((image.b7 > 0.03) & (bt < 27), true_array, false_array)
        basic_test = np.where((ndsi < 0.8) & (ndvi < 0.8), true_array, basic_test)

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
        water_test = np.where((ndvi < 0.01) & (image.b4 < 0.11), true_array, false_array)
        water_test = np.where((ndvi < 0.1) & (image.b4 < 0.05), true_array, water_test)

    # if image.sensor_id == 'OLI_TIRS':
    #     bt = image.

    return None


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
