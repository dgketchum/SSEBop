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

from numpy import where, nanpercentile

from app.paths import paths, PathsNotSetExecption
from sat_image.image import Landsat5, Landsat7, Landsat8
from landsat.usgs_download import down_usgs_by_list as down
from core.collector import anc_data_check_dem, data_check_temp
from metio.fao import get_net_radiation, air_density, air_specific_heat
from metio.fao import canopy_resistance, difference_temp


class SSEBopModel(object):
    _satellite = None
    _is_configured = False

    def __init__(self, runspec):

        self.image = None
        self.dem = None
        self.bounds = None
        self.image_exists = None

        self.image_dir = runspec.image_dir
        self.image_date = runspec.image_date
        self.satellite = runspec.satellite
        self.path = runspec.path
        self.row = runspec.row
        self.image_id = runspec.image_id

        self.image_geo = None

        self.k_factor = runspec.k_factor
        self.usgs_creds = runspec.usgs_creds
        self.api_key = runspec.api_key

        if not paths.is_set():
            raise PathsNotSetExecption

        paths.set_polygons_path(runspec.polygons)
        paths.set_mask_path(runspec.mask)

        if runspec.verify_paths:
            paths.verify()

        self.image_exists = paths.configure_project_dirs(runspec)

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

        mapping = {'LT5': Landsat5, 'LE7': Landsat7, 'LC8': Landsat8}
        try:
            cls = mapping[self.satellite]
            self.image = cls(self.image_dir)
        except KeyError:
            print('Invalid satellite key: "{}". available key = {}'.format
                  (self.satellite,
                   ','.join(mapping.keys())))

        self.image_geo = SSEBopGeo(self.image_id, self.image_dir,
                                   self.image.get_tile_geometry(),
                                   self.image.transform, self.image.profile,
                                   self.image.rasterio_geometry,
                                   self.image.bounds, self.api_key, self.image_date)

        dt = self.difference_temp()
        ts = self.image.land_surface_temp()
        cold = self.cold_reference()
        x = None

    def cold_reference(self):
        ndvi = self.image.ndvi()
        loc = where(ndvi == nanpercentile(ndvi, 99.9))
        ind = loc[0][0], loc[1][0]
        test = ndvi[ind]
        tmax = data_check_temp(self.image_geo, variable='tmax')
        # get ts at ind location and tmax, compute c, then tc
        return tmax

    def difference_temp(self):
        doy = self.image.doy
        dem = anc_data_check_dem(self.image_geo)
        tmin = data_check_temp(self.image_geo, variable='tmin')
        tmax = data_check_temp(self.image_geo, variable='tmax')
        center_lat = self.image.scene_coords_rad[0]
        albedo = self.image.albedo()

        net_rad = get_net_radiation(tmin=tmin, tmax=tmax, doy=doy,
                                    elevation=dem, lat=center_lat, albedo=albedo)
        rho = air_density(tmin=tmin, tmax=tmax, elevation=dem)
        cp = air_specific_heat()
        rah = canopy_resistance()

        dt = difference_temp(rn=net_rad, rho=rho, cp=cp, rah=rah)
        dt = self.image.mask_by_image(arr=dt)
        return dt

    @staticmethod
    def _info(msg):
        print('---------------------------------------')
        print(msg)
        print('---------------------------------------')

    @staticmethod
    def _debug(msg):
        print('%%%%%%%%%%%%%%%% {}'.format(msg))

    def down_image(self):
        down([self.image_id], output_dir=self.image_dir,
             usgs_creds_txt=self.usgs_creds)


class SSEBopGeo:
    def __init__(self, image_id, image_dir, clip, transform,
                 profile, geometry, bounds, api_key, date):
        self.image_id = image_id
        self.image_dir = image_dir
        self.clip = clip
        self.transform = transform
        self.profile = profile
        self.geometry = geometry
        self.bounds = bounds
        # add utm and latlon bounds to RasterBounds TODO
        self.api_key = api_key
        self.date = date

# ========================= EOF ====================================================================
