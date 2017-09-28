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
from numpy import where, nan, count_nonzero, isnan
from numpy import nanmean, nanstd

from rasterio import open as rasopen
from rasterio.crs import CRS

from app.paths import paths, PathsNotSetExecption
from bounds.bounds import RasterBounds
from sat_image.image import Landsat5, Landsat7, Landsat8
from landsat.usgs_download import down_usgs_by_list as down
from core.collector import data_check
from metio.fao import get_net_radiation, air_density, air_specific_heat
from metio.fao import canopy_resistance


class SSEBopModel(object):
    _satellite = None
    _is_configured = False

    def __init__(self, runspec):

        self.image = None
        self.dem = None
        self.bounds = None
        self.image_exists = None

        self.image_dir = runspec.image_dir
        self.parent_dir = runspec.parent_dir
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

        self._is_configured = True

        self.image_geo = SSEBopGeo(image_id=self.image_id,
                                   image_dir=self.image_dir,
                                   transform=self.image.transform,
                                   profile=self.image.profile,
                                   clip_geo=self.image.get_tile_geometry(),
                                   api_key=self.api_key,
                                   date=self.image_date)

    def run(self):
        """ Run the SSEBop algorithm.
        :return: 
        """

        dt = self.difference_temp()
        ts = self.image.land_surface_temp()
        c = self.c_factor(ts)
        ta = data_check(self.image_geo, variable='tmax', temp_units='K')
        tc = c * ta
        th = tc + dt
        etrf = (th - ts) / dt
        pet = data_check(self.image_geo, variable='pet')
        et = pet * etrf
        fmask = data_check(self.image_geo, variable='fmask',
                           sat_image=self.image, fmask_clear_val=1)
        et_mskd = where(fmask, et, nan)

        self.save_array(et_mskd, 'ssebop_et_mskd', self.image_dir)
        self.save_array(pet, 'pet', self.image_dir)
        self.save_array(ts, 'lst', self.image_dir)
        self.save_array(et, 'ssebop_et', self.image_dir)
        self.save_array(etrf, 'ssebop_etrf', self.image_dir)

        return None

    def c_factor(self, ts):

        ndvi = self.image.ndvi()
        tmax = data_check(self.image_geo, variable='tmax', temp_units='K')
        if len(tmax.shape) > 2:
            tmax = tmax.reshape(tmax.shape[1], tmax.shape[2])

        loc = where(ndvi > 0.7)
        temps = []
        for j, k in zip(loc[0], loc[1]):
            temps.append(tmax[j, k])
        ind = loc[0][0], loc[1][0]

        ta = tmax[ind]
        t_corr_orig = ts / ta
        t_corr_mean = nanmean(t_corr_orig)
        t_diff = ts - ta
        ta = None

        t_corr = where((ndvi >= 0.7) & (ndvi <= 1.0), t_corr_orig, nan)
        ndvi = None
        t_corr_orig = None

        t_corr = where(ts > 270., t_corr, nan)
        ts = None

        t_corr = where((t_diff > 0) & (t_diff < 30), t_corr, nan)
        t_diff = None

        fmask = data_check(self.image_geo, variable='fmask',
                           sat_image=self.image, fmask_clear_val=1)

        t_corr = where(fmask == 1, t_corr, nan)

        test_count = count_nonzero(~isnan(t_corr))

        if test_count < 50:
            raise Warning('Count of clear pixels in {} is insufficient'
                          ' to perform analysis.'.format(self.image_id))
        print('You have {} pixels for your temperature '
              'correction scheme.'.format(test_count))

        t_corr_std = nanstd(t_corr)
        c = t_corr_mean - (2 * t_corr_std)

        return c

    def difference_temp(self):
        doy = self.image.doy
        dem = data_check(self.image_geo, variable='dem')
        tmin = data_check(self.image_geo, variable='tmin', temp_units='K')
        tmax = data_check(self.image_geo, variable='tmax', temp_units='K')
        center_lat = self.image.scene_coords_rad[0]
        albedo = self.image.albedo()

        net_rad = get_net_radiation(tmin=tmin, tmax=tmax, doy=doy,
                                    elevation=dem, lat=center_lat,
                                    albedo=albedo)
        rho = air_density(tmin=tmin, tmax=tmax, elevation=dem)
        cp = air_specific_heat()
        rah = canopy_resistance()

        dt = (net_rad * rah) / (rho * cp)
        dt = self.image.mask_by_image(arr=dt)
        return dt

    @staticmethod
    def _info(msg):
        print('---------------------------------------')
        print(msg)
        print('---------------------------------------')

    def down_image(self):
        down([self.image_id], output_dir=self.parent_dir,
             usgs_creds_txt=self.usgs_creds)

    def save_array(self, arr, variable_name, crs=None, output_path=None):

        geometry = self.image.rasterio_geometry

        if not output_path:
            output_filename = os.path.join(self.image_dir, '{}_{}.tif'.format(self.image_id,
                                                                              variable_name))
        else:
            output_filename = os.path.join(output_path, '{}_{}.tif'.format(self.image_id,
                                                                           variable_name))

        try:
            arr = arr.reshape(1, arr.shape[1], arr.shape[2])
        except IndexError:
            arr = arr.reshape(1, arr.shape[0], arr.shape[1])

        geometry['dtype'] = arr.dtype

        if crs:
            geometry['crs'] = CRS({'init': crs})
        with rasopen(output_filename, 'w', **geometry) as dst:
            dst.write(arr)

        return None


class SSEBopGeo:
    def __init__(self, image_id, image_dir, transform,
                 profile, clip_geo, api_key, date):
        self.image_id = image_id
        self.image_dir = image_dir
        self.transform = transform
        self.profile = profile
        self.clip_geo = clip_geo
        self.bounds = RasterBounds(affine_transform=self.transform,
                                   profile=self.profile, latlon=True)
        # add utm and latlon bounds to RasterBounds TODO
        self.api_key = api_key
        self.date = date

# ========================= EOF ====================================================================
