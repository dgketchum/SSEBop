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

import os
import fiona
import rasterio
import numpy as np
from pprint import pprint


def raster_point_coords(raster, points):
    with rasterio.open(raster, 'r') as ras:
        array = ras.read()
        meta = ras.meta.copy()

    array = array.reshape(array.shape[1], array.shape[2])
    shape = array.shape


if __name__ == '__main__':
    ras = 'tests/data/lt5_cloud/LT05_040028_B1.TIF'
    pts = 'tests/data/point_data/butte_lt5_extract.shp'
    raster_point_coords(ras, pts)

# ========================= EOF ====================================================================
