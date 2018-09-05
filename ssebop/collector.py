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

from met.thredds import TopoWX, GridMet
from dem import AwsDem
from sat_image.fmask import Fmask


def data_check(model_geo, variable, sat_image=None, temp_units='C'):
    valid_vars = ['tmax', 'tmin', 'dem', 'fmask', 'pet']

    if variable not in valid_vars:
        raise KeyError('Variable {} is invalid, choose from {}'.format(variable,
                                                                       valid_vars))
    file_name = '{}_{}.tif'.format(model_geo.image_id, variable)
    file_path = os.path.join(model_geo.image_dir, file_name)

    if file_name not in os.listdir(model_geo.image_dir):

        if variable == 'tmax':
            var = fetch_temp(model_geo, 'tmax', temp_units, file_path)
        if variable == 'tmin':
            var = fetch_temp(model_geo, 'tmin', temp_units, file_path)
        if variable == 'dem':
            var = fetch_dem(model_geo, file_path)
        if variable == 'fmask':
            var = fetch_fmask(sat_image, file_path)
        if variable == 'pet':
            var = fetch_gridmet(model_geo, 'pet', file_path)

        return var

    else:

        with rasopen(file_path, 'r') as src:
            var = src.read()
            return var


def fetch_gridmet(model_geo, variable='pet', file_path=None):
    gridmet = GridMet(variable, date=model_geo.date,
                      bbox=model_geo.bounds,
                      target_profile=model_geo.profile,
                      clip_feature=model_geo.clip_geo)

    var = gridmet.get_data_subset(out_filename=file_path)

    return var


def fetch_temp(model_geo, variable='tmax', temp_units='C', file_path=None):
    print('Downloading new {}.....'.format(variable))
    topowx = TopoWX(date=model_geo.date, bbox=model_geo.bounds,
                    target_profile=model_geo.profile,
                    clip_feature=model_geo.clip_geo, out_file=file_path)

    var = topowx.get_data_subset(grid_conform=True, var=variable,
                                 out_file=file_path,
                                 temp_units_out=temp_units)
    return var


def fetch_dem(model_geo, file_path=None):
    dem = AwsDem(bounds=model_geo.bounds, clip_object=model_geo.clip_geo,
                 target_profile=model_geo.profile, zoom=8)

    var = dem.terrain(attribute='elevation', out_file=file_path,
                      save_and_return=True)
    return var


def fetch_fmask(sat_image, file_path):

    f = Fmask(sat_image)
    combo = f.cloud_mask(min_filter=(3, 3), max_filter=(40, 40), combined=True)
    f.save_array(combo, file_path)

    return combo


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
