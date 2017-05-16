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
import rasterio
import fiona
import rasterio.tools.mask


def clip_w_poly(rasters, polygon, out):
    files = os.listdir(rasters)
    tifs = [x for x in files if x.endswith('.TIF')]
    with fiona.open(polygon, 'r') as shapefile:
        features = [feature['geometry'] for feature in shapefile]

    for tif in tifs:
        with rasterio.open(os.path.join(rasters, tif)) as src:
            out_image, out_transform = rasterio.tools.mask.mask(src, features, crop=True)
            out_meta = src.meta.copy()

            out_meta.update({'driver': 'GTiff', 'height': out_image.shape[1],
                             'width': out_image.shape[2], 'transform': out_transform})

        new_tif_name = os.path.join(out, '{}{}{}'.format(tif[:5], tif[10:16], tif[-7:]))
        with rasterio.open(new_tif_name, 'w', **out_meta) as dst:
            dst.write(out_image)


if __name__ == '__main__':
    home = os.path.expanduser('~')

    raster_dir = os.path.join(home, 'images', 'LT5', 'cloudtest', 'full_image')

    test_data = os.path.join(home, 'images', 'test_data', 'cloudtest')
    shape = os.path.join(test_data, 'test_cloud_butte.shp')
    # print(os.path.isdir(raster_dir))
    clip_w_poly(raster_dir, shape, test_data)

# LT05_L1TP_040028_20060706_20160909_01_T1_B7

# ========================= EOF ====================================================================
