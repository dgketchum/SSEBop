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
from sat_image.fmask import Fmask


def data_check(model_geo, variable='tmax', sat_image=None,
               fmask_cloud_val=1):
    if variable == 'tmax':
        file_name = '{}_tmax.tif'.format(model_geo.image_id)
        file_path = os.path.join(model_geo.image_dir, file_name)

    elif variable == 'tmin':
        file_name = '{}_tmin.tif'.format(model_geo.image_id)
        file_path = os.path.join(model_geo.image_dir, file_name)

    elif variable == 'dem':
        file_name = '{}_dem.tif'.format(model_geo.image_id)
        file_path = os.path.join(model_geo.image_dir, file_name)

    elif variable == 'fmask':
        file_name = '{}_fmask.tif'.format(model_geo.image_id)
        file_path = os.path.join(model_geo.image_dir, file_name)

    if file_name not in os.listdir(model_geo.image_dir):

        bounds = RasterBounds(affine_transform=model_geo.transform,
                              profile=model_geo.profile, latlon=True)

        if variable in ['tmax', 'tmin']:
            print('Downloading new {}.....'.format(variable))
            topowx = TopoWX(date=model_geo.date, bbox=bounds,
                            target_profile=model_geo.profile,
                            clip_feature=model_geo.clip, out_file=file_path)

            var = topowx.get_data_subset(grid_conform=True, var=variable,
                                         out_file=file_path)

        elif variable == 'dem':
            print('Downloading new {}.....'.format(variable))

            clip_shape = model_geo.clip

            dem = MapzenDem(bounds=bounds, clip_object=clip_shape,
                            target_profile=model_geo.geometry, zoom=8,
                            api_key=model_geo.api_key)

            var = dem.terrain(attribute='elevation', out_file=file_path,
                              save_and_return=True)

        elif variable == 'fmask':
            if not sat_image:
                raise Exception('If calling fmask, must provide a Landsat image object')

            f = Fmask(sat_image)
            combo = f.cloud_mask(combined=True, min_filter=(3, 3),
                                 max_filter=(40, 40), cloud_value=fmask_cloud_val,
                                 output_file=file_path)
            var = combo

        return var

    else:

        with rasopen(file_path, 'r') as src:
            temp = src.read()
            return temp


# def data_check_dem(model_geo):
#     dem_file = '{}_dem.tif'.format(model_geo.image_id)
#
#     if dem_file not in os.listdir(model_geo.image_dir):
#
#         print('Downloading dem for {}...'.format(model_geo.image_id))
#         clip_shape = model_geo.clip
#
#         bounds = RasterBounds(affine_transform=model_geo.transform,
#                               profile=model_geo.profile, latlon=True)
#
#         dem = MapzenDem(bounds=bounds, clip_object=clip_shape,
#                         target_profile=model_geo.geometry, zoom=8,
#                         api_key=model_geo.api_key)
#
#         out_file = os.path.join(model_geo.image_dir, dem_file)
#
#         dem = dem.terrain(attribute='elevation', out_file=out_file,
#                           save_and_return=True)
#
#         return dem
#
#     else:
#         print('Found dem for {}...'.format(model_geo.image_id))
#         image_file = os.path.join(model_geo.image_dir, dem_file)
#         with rasopen(image_file, 'r') as src:
#             dem = src.read()
#
#         return dem
#
#
# def data_check_temp(model_geo, variable='tmax'):
#     if variable == 'tmax':
#
#         temp_file_name = '{}_tmax.tif'.format(model_geo.image_id)
#         temp_file = os.path.join(model_geo.image_dir, temp_file_name)
#
#     elif variable == 'tmin':
#
#         temp_file_name = '{}_tmin.tif'.format(model_geo.image_id)
#         temp_file = os.path.join(model_geo.image_dir, temp_file_name)
#
#     if temp_file_name not in os.listdir(model_geo.image_dir):
#         bounds = RasterBounds(affine_transform=model_geo.transform,
#                               profile=model_geo.profile, latlon=True)
#         topowx = TopoWX(date=model_geo.date, bbox=bounds,
#                         target_profile=model_geo.profile,
#                         clip_feature=model_geo.clip, out_file=temp_file)
#
#         temp = topowx.get_data_subset(grid_conform=True, var=variable,
#                                       out_file=temp_file)
#
#         return temp
#
#     else:
#
#         with rasopen(temp_file, 'r') as src:
#             temp = src.read()
#             return temp


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
