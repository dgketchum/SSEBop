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

from metio.thredds import TopoWX
from bounds.bounds import RasterBounds
from dem.dem import MapzenDem


def anc_data_check(model_run):
    dem_file = '{}_dem.tif'.format(model_run.image_id)
    if dem_file not in os.listdir(model_run.image_dir):
        clip_shape = model_run.image.get_tile_geometry()

        bounds = RasterBounds(affine_transform=model_run.image.transform,
                              profile=model_run.image.profile, latlon=True)

        dem = MapzenDem(bounds=bounds, clip_object=clip_shape,
                        target_profile=model_run.image.rasterio_geometry, zoom=8,
                        api_key=model_run.cfg.api_key)

        out_file = os.path.join(model_run.image_dir, dem_file)

        dem.terrain(attribute='elevation', out_file=out_file)

        return None

    tmax_file = '{}_tmax.tif'.format(model_run.image)
    if tmax_file not in os.listdir(model_run.image_dir):
        topowx = TopoWX(date=model_run.image_date, bbox=model_run.image.bounds,
                        target_profile=model_run.image.profile,
                        clip_feature=model_run.image.get_tile_geometry())

        met_data = topowx.get_data_subset(grid_conform=True)

        return met_data.tmax


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
