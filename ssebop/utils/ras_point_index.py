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

import fiona
import rasterio
from sat_image.image import LandsatImage

from numpy import ndarray


def raster_point_row_col(raster, points):
    pt_data = {}

    with fiona.open(points, 'r') as src:
        for feature in src:
            pt_data[feature['id']] = feature

    if isinstance(raster, LandsatImage):
        a = raster.rasterio_geometry['affine']
    if isinstance(raster, str):
        with rasterio.open(raster, 'r') as src:
            a = src.affine

    for key, val in pt_data.items():
        x, y = val['geometry']['coordinates'][0], val['geometry']['coordinates'][1]
        col, row = ~a * (x, y)
        val['index'] = row, col

    return pt_data


if __name__ == '__main__':
    pass

# ========================= EOF ====================================================================
