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

from app.paths import paths, PathsNotSetExecption
from sat_image.image import Landsat5, Landsat7, Landsat8
from landsat.usgs_download import down_usgs_by_list as down
from core.collector import anc_data_check

from metio.fao import avp_from_tmin, net_out_lw_rad, sunset_hour_angle
from metio.fao import sol_dec, inv_rel_dist_earth_sun, et_rad


class SSEBopModel(object):
    _satellite = None
    _is_configured = False

    def __init__(self, cfg, runspec):

        self.image = None
        self.dem = None
        self.bounds = None
        self.image_exists = None

        self.cfg = cfg
        self.runspec = runspec

        self.image_dir = runspec.image_dir
        self.image_date = runspec.image_date
        self.satellite = runspec.satellite
        self.path = runspec.path
        self.row = runspec.row
        self.image_id = runspec.image_id

        self.k_factor = cfg.k_factor
        self.usgs_creds = cfg.usgs_creds

        if not paths.is_set():
            raise PathsNotSetExecption

        paths.set_polygons_path(cfg.polygons)
        paths.set_mask_path(cfg.mask)

        if cfg.verify_paths:
            paths.verify()

        self.image_exists = paths.configure_project_dirs(cfg, runspec)

        self._info('Constructing/Initializing SSEBop...')

    def configure_run(self):

        self._info('Configuring SSEBop run, checking data...')

        print('----------- CONFIGURATION --------------')
        for attr in ('image_date', 'satellite', 'k_factor',
                     'path', 'row', 'image_id', 'image_exists'):
            print('{:<20s}{}'.format(attr, getattr(self, '{}'.format(attr))))
        print('----------- ------------- --------------')

        self._is_configured = True

    def run(self):
        """ Run the SSEBop algorithm.
        :return: 
        """
        if not self.image_exists:
            self.down_image()

        print('Instantiating image...')

        sat = self.satellite
        if sat == 'LT5':
            self.image = Landsat5(self.image_dir)
        elif sat == 'LE7':
            self.image = Landsat7(self.image_dir)
        elif sat == 'LC8':
            self.image = Landsat8(self.image_dir)

        anc_data_check(self)

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

    def down_image(self):
        if not self.image_exists:
            down([self.image_id], output_dir=self.image_dir,
                 usgs_creds_txt=self.usgs_creds)

# ========================= EOF ====================================================================
