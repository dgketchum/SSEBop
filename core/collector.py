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
from __future__ import print_function

import os
import numpy as np

from rasterio import open as rasopen

from landsat.usgs_download import down_usgs_by_list as down

from app.paths import paths, PathsNotSetExecption
from dem.dem import MapzenDem
from sat_image.image import Landsat5, Landsat7, Landsat8
from metio.thredds import TopoWX
from bounds.bounds import RasterBounds
from metio.fao import avp_from_tmin, net_out_lw_rad, sunset_hour_angle
from metio.fao import sol_dec, inv_rel_dist_earth_sun, et_rad
import os


class Collector(object):
    def __init__(self):

    def data_check(self):

        image_exists, path = paths.configure_project_dirs(self.cfg, image_dir=image)

        if not image_exists:
            down([image], path, self.usgs_creds)

        directory = (os.path.join(path, image))
        setattr(self.image_data, 'dir', directory)

        dem_file = '{}_dem.tif'.format(image)
        if dem_file not in os.listdir(self.image_data.dir):
            clip_shape = self.image.get_tile_geometry()
            bounds = RasterBounds(affine_transform=self.image.transform,
                                  profile=self.image.profile, latlon=True)
            dem = MapzenDem(bounds=bounds, clip_object=clip_shape,
                            target_profile=self.image.rasterio_geometry, zoom=8,
                            api_key=self.cfg.api_key)
            out_file = os.path.join(self.image_data.dir, dem_file)
            dem.terrain(attribute='elevation', out_file=out_file)
            return None

        tmax_file = '{}_tmax.tif'.format(image)
        if tmax_file not in os.listdir(self.image_data[image]['dir']):
            topowx = TopoWX(date=self.image.date_acquired, bbox=self.image.bounds,
                            target_profile=self.image.profile,
                            clip_feature=self.image.get_tile_geometry())
            met_data = topowx.get_data_subset(grid_conform=True)
            return met_data.tmax


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
