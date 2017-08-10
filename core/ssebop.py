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

import numpy as np

from landsat.usgs_download import down_usgs_by_list as down

from app.paths import paths, PathsNotSetExecption
from dem.dem import MapzenDem
from sat_image.image import Landsat5, Landsat7, Landsat8
from metio.thredds import TopoWX
from bounds.bounds import RasterBounds
from metio.fao import avp_from_tmin, net_out_lw_rad, sunset_hour_angle
from metio.fao import sol_dec, inv_rel_dist_earth_sun, et_rad


class SSEBopModel(object):
    _date_range = None
    _k_factor = None
    _satellite = None
    _api_key = None

    _is_configured = False

    def __init__(self, cfg):

        self.image = None
        self.dem = None
        self.bounds = None

        self.met_variables = ['elev', 'pr', 'rmax', 'rmin', 'sph', 'srad',
                              'th', 'tmmn', 'tmmx', 'pet', 'vs', ]
        if not paths.is_set():
            raise PathsNotSetExecption

        self.cfg = cfg

        self.date_range = self.cfg.date_range
        self.image_list = self.cfg.image_list
        self.k_factor = self.cfg.k_factor
        self.satellite = self.cfg.satellite
        self.usgs_creds = self.cfg.usgs_creds

        self.api_key = self.cfg.api_key

        paths.set_polygons_path(cfg.polygons)
        paths.set_mask_path(cfg.mask)

        if cfg.verify_paths:
            paths.verify()

        paths.configure_project_dirs(cfg=cfg)

        self._info('Constructing/Initializing SSEBop...')

    def configure_run(self):

        self._info('Configuring SSEBop run')

        print('----------- CONFIGURATION --------------')
        for attr in ('date_range', 'satellite', 'k_factor'):
            print('{:<20s}{}'.format(attr, getattr(self, '{}'.format(attr))))
        print('----------- ------------- --------------')
        self._is_configured = True

    def data_check(self):
        for image in self.image_list:
            image_exists, path = paths.configure_project_dirs(self.cfg, image_dir=image)
            if not image_exists:
                down([image], path, self.usgs_creds)

    def run(self):
        """ Run the SSEBop algorithm.
        :return: 
        """
        print('Instantiating image...')
        if self._satellite == 'LT5':
            self.image = Landsat5(paths.image)
        elif self._satellite == 'LE7':
            self.image = Landsat7(paths.image)
        elif self._satellite == 'LC8':
            self.image = Landsat8(paths.image)

        else:
            raise ValueError('Must choose a valid satellite in config.')

        clip_shape = self.image.get_tile_geometry()

        bounds = RasterBounds(affine_transform=self.image.transform,
                              profile=self.image.profile, latlon=True)

        dem = MapzenDem(bounds=bounds, clip_object=clip_shape,
                        target_profile=self.image.rasterio_geometry, zoom=8,
                        api_key=self.cfg.api_key)

        elevation = dem.terrain(attribute='elevation')

        topowx = TopoWX(date=self.date, bbox=self.image.bounds,
                        target_profile=self.image.profile,
                        clip_feature=self.image.get_tile_geometry())

        met_data = topowx.get_data_subset(grid_conform=True)

        albedo = self.image.albedo()
        emissivity = self._emissivity_ndvi()

        # net_rad = self._net_radiation(topowx.tmin, self.image.doy)

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
