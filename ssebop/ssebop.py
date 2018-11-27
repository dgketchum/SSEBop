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
import sys

abspath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(abspath)
from numpy import where, nan, count_nonzero, isnan
from numpy import nanmean, nanstd, deg2rad

from datetime import datetime

from rasterio import open as rasopen
from rasterio.crs import CRS

from ssebop_app.paths import paths, PathsNotSetExecption
from bounds import RasterBounds
from sat_image.image import Landsat5, Landsat7, Landsat8
from ssebop.collector import SSEBopData
from met.fao import get_net_radiation, air_density, air_specific_heat
from met.fao import canopy_resistance
from met.agrimet import Agrimet


class SSEBopModel(object):
    _satellite = None
    _is_configured = False

    def __init__(self, runspec=None, **kwargs):

        self.image = None
        self.dem = None
        self.bounds = None
        self.image_exists = None
        self.use_existing_images = None
        self.image_geo = None
        self.agrimet_corrected = None
        self.completed = False
        self.override_count = False

        if runspec:
            self.image_dir = runspec.image_dir
            self.parent_dir = runspec.parent_dir
            self.image_exists = runspec.image_exists
            self.image_date = runspec.image_date
            self.satellite = runspec.satellite
            self.path = runspec.path
            self.row = runspec.row
            self.image_id = runspec.image_id
            self.agrimet_corrected = runspec.agrimet_corrected

            if not paths.is_set():
                raise PathsNotSetExecption

            if runspec.verify_paths:
                paths.verify()
        else:
            for name, val in kwargs.items():
                setattr(self, name, val)

        self._info('Constructing/Initializing SSEBop...')

    def configure_run(self):

        self._info('Configuring SSEBop run, checking data...')

        print('----------- CONFIGURATION --------------')
        for attr in ('image_date', 'satellite',
                     'path', 'row', 'image_id', 'image_exists'):
            print('{:<20s}{}'.format(attr, getattr(self, '{}'.format(attr))))
        print('----------- ------------- --------------')

        if not self.image_exists:
            raise NotImplementedError

        self.check_products()

        mapping = {'LT5': Landsat5, 'LE7': Landsat7, 'LC8': Landsat8}
        if not self.image:
            try:
                cls = mapping[self.satellite]
                self.image = cls(self.image_dir)
            except KeyError:
                print('Invalid satellite key: "{}". available key = {}'.format
                      (self.satellite,
                       ','.join(mapping.keys())))

        self._is_configured = True

        self.dc = SSEBopData(image_id=self.image_id,
                                   image_dir=self.image_dir,
                                   transform=self.image.rasterio_geometry['transform'],
                                   profile=self.image.rasterio_geometry,
                                   clip_geo=self.image.get_tile_geometry(),
                                   date=self.image_date)

    def run(self, overwrite=False):
        """ Run the SSEBop algorithm for an image. Check for outputs from previous run.
        :return: 
        """

        if self.completed and not overwrite:
            return None

        ndvi = self.image.ndvi()
	
         


        dt = self.difference_temp()
        ts = self.image.land_surface_temp()
        c = self.c_factor(ts)
        if not c:
            print('moving to next day due to invalid image for t_corr')
            return None
        ta = self.dc.data_check(variable='tmax', temp_units='K')
        tc = c * ta
        th = tc + dt
        etrf = (th - ts) / dt
        pet = self.dc.data_check(variable='pet')
        et = pet * etrf
        fmask = self.dc.data_check(variable='fmask', sat_image=self.image)
        et_mskd = where(fmask == 0, et, nan)

        self.save_array(et_mskd, variable_name='ssebop_et_mskd',
                        output_path=self.image_dir)
        self.save_array(pet, variable_name='pet', output_path=self.image_dir)
        self.save_array(ts, variable_name='lst', output_path=self.image_dir)
        self.save_array(et, variable_name='ssebop_et', output_path=self.image_dir)
        self.save_array(etrf, variable_name='ssebop_etrf',
                        output_path=self.image_dir)

        self.save_array(ndvi, variable_name='ndvi',
                        output_path=self.image_dir)



        if self.agrimet_corrected:
            lat, lon = self.image.scene_coords_deg[0], \
                       self.image.scene_coords_deg[1]
            agrimet = Agrimet(lat=lat, lon=lon)
            # TODO move fetch formed data into instantiation
            # function in both (?) gridmet and agrimet to find bias and correct
        return None

    def c_factor(self, ts):

        ndvi = self.image.ndvi()
        tmax = self.dc.data_check(variable='tmax', temp_units='K')
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

        fmask = self.dc.data_check(variable='fmask', sat_image=self.image)

        t_corr = where(fmask == 0, t_corr, nan)

        test_count = count_nonzero(~isnan(t_corr))

        if test_count < 50 and not self.override_count:
            print('Count of clear pixels {} in {} is insufficient'
                  ' to perform analysis.'.format(test_count, self.image_id))
            return None

        print('You have {} pixels for your temperature '
              'correction scheme.'.format(test_count))

        t_corr_std = nanstd(t_corr)
        c = t_corr_mean - (2 * t_corr_std)

        return c

    def difference_temp(self):
        doy = int(datetime.strftime(self.image.date_acquired, '%j'))
        dem = self.dc.data_check(variable='dem')
        tmin = self.dc.data_check(variable='tmin', temp_units='K')
        tmax = self.dc.data_check(variable='tmax', temp_units='K')
        center_lat = (self.image.corner_ll_lat_product + self.image.corner_ul_lat_product) / 2.
        lat_radians = deg2rad(center_lat)
        albedo = self.image.albedo()
        net_rad = get_net_radiation(tmin=tmin, tmax=tmax, doy=doy,
                                    elevation=dem, lat=lat_radians,
                                    albedo=albedo)

        rho = air_density(tmin=tmin, tmax=tmax, elevation=dem)
        cp = air_specific_heat()
        rah = canopy_resistance()

        dt = (net_rad * rah) / (rho * cp)
        return dt

    @staticmethod
    def _info(msg):
        print('---------------------------------------')
        print(msg)
        print('---------------------------------------')

    def save_array(self, arr, variable_name, crs=None, output_path=None):

        geometry = self.image.rasterio_geometry

        if not output_path:
            output_filename = os.path.join(self.image_dir,
                                           '{}_{}.tif'.format(self.image_id,
                                                              variable_name))
        else:
            output_filename = os.path.join(output_path,
                                           '{}_{}.tif'.format(self.image_id,
                                                              variable_name))

        try:
            arr = arr.reshape(1, arr.shape[1], arr.shape[2])
        except IndexError:
            arr = arr.reshape(1, arr.shape[0], arr.shape[1])

        geometry['dtype'] = str(arr.dtype)

        if crs:
            geometry['crs'] = CRS({'init': crs})
        with rasopen(output_filename, 'w', **geometry) as dst:
            dst.write(arr)

        return None

    def check_products(self):
        products = ['ssebop_et_mskd', 'pet', 'lst', 'ssebop_et', 'ssebop_etrf', 'ndvi']
        for p in products:
            raster = os.path.join(self.image_dir, '{}_{}.tif'.format(self.image_id, p))
            if os.path.isfile(raster):
                print('This analysis has been done for at least {}'.format(p))
                self.completed = True
                return None

# ========================= EOF ====================================================================
