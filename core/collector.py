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

from rasterio import open as rasopen

from metio.thredds import TopoWX
from bounds.bounds import RasterBounds
from dem.dem import MapzenDem


def anc_data_check_dem(model_geo):
    dem_file = '{}_dem.tif'.format(model_geo.image_id)

    if dem_file not in os.listdir(model_geo.image_dir):

        print('Downloading dem for {}...'.format(model_geo.image_id))
        clip_shape = model_geo.clip

        bounds = RasterBounds(affine_transform=model_geo.transform,
                              profile=model_geo.profile, latlon=True)

        dem = MapzenDem(bounds=bounds, clip_object=clip_shape,
                        target_profile=model_geo.geometry, zoom=8,
                        api_key=model_geo.api_key)

        out_file = os.path.join(model_geo.image_dir, dem_file)

        dem = dem.terrain(attribute='elevation', out_file=out_file,
                          save_and_return=True)

        return dem

    else:
        print('Found dem for {}...'.format(model_geo.image_id))
        image_file = os.path.join(model_geo.image_dir, dem_file)
        with rasopen(image_file, 'r') as src:
            dem = src.read()

        return dem


def anc_data_check_tmax(model_geo):
    tmax_file_name = '{}_tmax.tif'.format(model_geo.image_id)
    tmax_file = os.path.join(model_geo.image_dir, tmax_file_name)

    if tmax_file_name not in os.listdir(model_geo.image_dir):
        bounds = RasterBounds(affine_transform=model_geo.transform, profile=model_geo.profile, latlon=True)
        topowx = TopoWX(date=model_geo.date, bbox=bounds,
                        target_profile=model_geo.profile,
                        clip_feature=model_geo.clip, out_file=tmax_file)

        tmax = topowx.get_data_subset(grid_conform=True, out_file=tmax_file)

        return tmax

    else:

        with rasopen(tmax_file, 'r') as src:
            tmax = src.read()
            return tmax


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
