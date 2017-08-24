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


class SSEBopModel(object):

    _satellite = None

    _is_configured = False

    def __init__(self, cfg, runspec):

        self.image = None
        self.dem = None
        self.bounds = None

        if not paths.is_set():
            raise PathsNotSetExecption

        self.satellite = runspec.satellite

        paths.set_polygons_path(cfg.polygons)
        paths.set_mask_path(cfg.mask)

        if cfg.verify_paths:
            paths.verify()

        image_exists = paths.configure_project_dirs(cfg, runspec)

        self._info('Constructing/Initializing SSEBop...')

    def configure_run(self):

        self._info('Configuring SSEBop run')

        print('----------- CONFIGURATION --------------')
        for attr in ('date_range', 'satellite', 'k_factor'):
            print('{:<20s}{}'.format(attr, getattr(self, '{}'.format(attr))))
        print('----------- ------------- --------------')
        self._is_configured = True

    def data_check(self):

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

    def run(self):
        """ Run the SSEBop algorithm.
        :return: 
        """
        print('Instantiating image...')
        for image, dct in self.image_data.items():
            sat = dct['sat']
            if sat == 'LT5':
                self.image = Landsat5(dct['dir'])
            elif sat == 'LE7':
                self.image = Landsat7(dct['dir'])
            elif sat == 'LC8':
                self.image = Landsat8(dct['dir'])

            self.data_check()

            elevation = self._get_elevation(image)
            tmax = self._get_temps(self.image)

            albedo = self.image.albedo()
            emissivity = self._emissivity_ndvi()

            net_rad = self._net_radiation(topowx.tmin, self.image.doy)

    def _get_temps(self, image):

        if self.image_data[image]['tmax_exists']:
            with rasopen(self.image_data[image]['tmax']) as src:
                temp = src.read()
                return temp

    def _get_elevation(self, image):

        if self.image_data[image]['dem_exists']:
            with rasopen(self.image_data[image]['dem']) as src:
                elevation = src.read()
                return elevation

    def _emissivity_ndvi(self):
        ndvi = self.image.ndvi()
        bound_ndvi = np.where((ndvi >= 0.2) & (ndvi <= 0.5), ndvi, np.nan)
        return bound_ndvi

    def _net_radiation(self, tmin, doy):
        avp = avp_from_tmin(tmin)
        return None

    @staticmethod
    def _info(msg):
        print('---------------------------------------')
        print(msg)
        print('---------------------------------------')

    @staticmethod
    def _debug(msg):
        print('%%%%%%%%%%%%%%%% {}'.format(msg))

# ========================= EOF ====================================================================
