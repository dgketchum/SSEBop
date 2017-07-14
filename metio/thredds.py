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

from future.standard_library import hooks

with hooks():
    from urllib.parse import urlunparse

import os
import copy
from tempfile import mkdtemp
from numpy import empty, float32
from rasterio import open as rasopen
from rasterio.crs import CRS
from rasterio.transform import Affine
from rasterio.mask import mask
from rasterio.warp import reproject, Resampling
from rasterio.warp import calculate_default_transform as cdt
from xlrd.xldate import xldate_from_date_tuple
from xarray import open_dataset
from pandas import date_range

from bounds.bounds import GeoBounds


class Thredds(object):
    """  Unidata's Thematic Real-time Environmental Distributed Data Services (THREDDS)
    
    """

    def __init__(self, start=None, end=None, date=None, bounds=None, target_profile=None):
        self.service = 'thredds.northwestknowledge.net:8080'
        self.scheme = 'http'
        self.start = start
        self.end = end
        self.date = date

        self.target_profile = target_profile
        self.bbox = bounds


class TopoWX(Thredds):
    """ TopoWX Surface Temperature, return as numpy array in daily stack unless modified.

    Available variables: [ 'tmmn', 'tmmx']
    
    ----------
    Observation elements to access. Currently available elements:
    - 'tmmn' : daily minimum air temperature [K]
    - 'tmmx' : daily maximum air temperature [K]

    :param start: datetime object start of period of data
    :param end: datetime object end of period of data
    :param variables: List  of available variables. At lease one. 
    :param date: single-day datetime date object
    :param bounds: metio.misc.BBox object representing spatial bounds, default to conterminous US
    :return: numpy.ndarray
    
    """

    def __init__(self):
        Thredds.__init__(self, start=None, end=None, date=None, bounds=None)

        if self.start:
            pass


class GridMet(Thredds):
    """ U of I Gridmet, return as numpy array per met variable in daily stack unless modified.
    
    Available variables: ['bi', 'elev', 'erc', 'fm100', fm1000', 'pdsi', 'pet', 'pr', 'rmax', 'rmin', 'sph', 'srad',
                          'th', 'tmmn', 'tmmx', 'vs']
        ----------
        Observation elements to access. Currently available elements:
        - 'bi' : burning index [-]
        - 'elev' : elevation above sea level [m]
        - 'erc' : energy release component [-]
        - 'fm100' : 100-hour dead fuel moisture [%]
        - 'fm1000' : 1000-hour dead fuel moisture [%]
        - 'pdsi' : Palmer Drough Severity Index [-]
        - 'pet' : daily reference potential evapotranspiration [mm]
        - 'pr' : daily accumulated precipitation [mm]
        - 'rmax' : daily maximum relative humidity [%]
        - 'rmin' : daily minimum relative humidity [%]
        - 'sph' : daily mean specific humidity [kg/kg]
        - 'srad' : daily maximum relative humidity [%]
        - 'prcp' : daily total precipitation [mm]
        - 'srad' : daily mean downward shortwave radiation at surface [W m-2]
        - 'th' : daily mean wind direction clockwise from North [degrees] 
        - 'tmmn' : daily minimum air temperature [K]
        - 'tmmx' : daily maximum air temperature [K]
        - 'vs' : daily mean wind speed [m -s]
            
    :param start: datetime object start of period of data
    :param end: datetime object end of period of data
    :param variables: List  of available variables. At lease one. 
    :param date: single-day datetime date object
    :param bbox: metio.misc.BBox object representing spatial bounds, default to conterminous US
    :return: numpy.ndarray
    
    Must have either start and end, or date.
    Must have at least one valid variable. Invalid variables will be excluded gracefully.

    note: NetCDF dates are in xl '1900' format, i.e., number of days since 1899-12-31 23:59
          xlrd.xldate handles this for the time being
          
    """

    def __init__(self, variables, **kwargs):
        Thredds.__init__(self)

        for key, val in kwargs.items():
            setattr(self, key, val)

        self.temp_dir = mkdtemp()

        self.requested_variables = variables
        self.available = ['elev', 'pr', 'rmax', 'rmin', 'sph', 'srad',
                          'th', 'tmmn', 'tmmx', 'pet', 'vs', 'erc', 'bi',
                          'fm100', 'pdsi']

        self.kwords = {'bi': 'burning_index_g',
                       'elev': '',
                       'erc': 'energy_release_component-g',
                       'fm100': 'dead_fuel_moisture_100hr',
                       'fm1000': 'dead_fuel_moisture_1000hr',
                       'pdsi': 'palmer_drought_severity_index',
                       'pet': 'potential_evapotranspiration',
                       'pr': 'precipitation_amount',
                       'rmax': 'relative_humidity',
                       'rmin': 'relative_humidity',
                       'sph': 'specific_humidity',
                       'srad': 'surface_downwelling_shortwave_flux_in_air',
                       'th': 'wind_from_direction',
                       'tmmn': 'air_temperature',
                       'tmmx': 'air_temperature',
                       'vs': 'wind_speed', }

        if self.date:
            self.start = self.date
            self.end = self.date

        self.variables = []
        if self.requested_variables:
            [setattr(self, var, None) for var in self.requested_variables if var in self.available]
            [self.variables.append(var) for var in self.requested_variables if var in self.available]
            [Warning('Variable {} is not available'.
                     format(var)) for var in self.requested_variables if var not in self.available]

        self.year = self.start.year

        if not self.bbox:
            self.bbox = GeoBounds()

    def get_data_subset(self, grid_conform=False):

        for var in self.variables:

            url = self._build_url(var)
            xray = open_dataset(url)

            start_xl, end_xl = self._dtime_to_xldate()

            subset = xray.loc[dict(day=slice(start_xl, end_xl),
                                   lat=slice(self.bbox.north, self.bbox.south),
                                   lon=slice(self.bbox.west, self.bbox.east))]

            subset.rename({'day': 'time'}, inplace=True)
            date_ind = self._date_index()
            subset['time'] = date_ind
            setattr(self, 'width', subset.dims['lon'])
            setattr(self, 'height', subset.dims['lat'])
            if not grid_conform:
                setattr(self, var, subset)
            else:
                array = subset[self.kwords[var]].values
                affine = self.get_source_affine(subset, array)
                conformed_array = self.conform(array)
                setattr(self, var, conformed_array)
        return None

    def get_source_affine(self, subset):
        lat_min, lat_max = min(subset.lat.values), max(subset.lat.values)
        pix_height = (lat_max - lat_min) / self.height

    def conform(self, subset):
        self.reproject(subset)
        self.mask()
        self.resample()
        result = self.resample
        return result

    def reproject(self, subset):

        home = os.path.expanduser('~')
        reproj_path = os.path.join(home, 'images', 'sandbox', 'tiled_reproj.tif')
        # reproj_path = os.path.join(self.temp_dir, 'tiled_reproj.tif')
        setattr(self, 'reprojection', reproj_path)

        profile = copy.deepcopy(self.target_profile)
        profile['dtype'] = float32
        bb = self.bbox.as_tuple()
        bounds = (bb[0], bb[1],
                  bb[2], bb[3])
        dst_affine, dst_width, dst_height = cdt(CRS({'init': 'epsg:4326'}),
                                                profile['crs'],
                                                subset.shape[1],
                                                subset.shape[2],
                                                *bounds)

        profile.update({'crs': profile['crs'],
                        'transform': dst_affine,
                        'width': dst_width,
                        'height': dst_height})

        with rasopen(reproj_path, 'w', **profile) as dst:
            dst_array = empty((1, dst_height, dst_width), dtype=float32)

            reproject(subset, dst_array, src_transform=profile['transform'],
                      src_crs=CRS({'init': 'epsg:4326'}), dst_crs=self.target_profile['crs'],
                      dst_transform=dst_affine, resampling=Resampling.cubic,
                      num_threads=2)

            dst.write(dst_array.reshape(1, dst_array.shape[1], dst_array.shape[2]))

        delattr(self, 'merged_array')

    def mask(self):

        temp_path = os.path.join(self.temp_dir, 'masked_dem.tif')

        with rasopen(self.reprojection) as src:
            out_arr, out_trans = mask(src, self.clip_feature, crop=True,
                                      all_touched=True)
            out_meta = src.meta.copy()
            out_meta.update({'driver': 'GTiff',
                             'height': out_arr.shape[1],
                             'width': out_arr.shape[2],
                             'transform': out_trans})

        with rasopen(temp_path, 'w', **out_meta) as dst:
            dst.write(out_arr)

        setattr(self, 'mask', temp_path)
        delattr(self, 'reprojection')

    def resample(self):

        temp_path = os.path.join(self.temp_dir, 'resample.tif')

        with rasopen(self.mask, 'r') as src:
            array = src.read(1)
            profile = src.profile
            res = src.res
            target_res = self.target_profile['transform'].a
            res_coeff = res[0] / target_res

            new_array = empty(shape=(1, round(array.shape[0] * res_coeff - 2),
                                     round(array.shape[1] * res_coeff)), dtype=float32)
            aff = src.transform
            new_affine = Affine(aff.a / res_coeff, aff.b, aff.c, aff.d, aff.e / res_coeff, aff.f)

            profile['transform'] = self.target_profile['transform']
            profile['width'] = self.target_profile['width']
            profile['height'] = self.target_profile['height']
            profile['dtype'] = new_array.dtype

            delattr(self, 'mask')

            with rasopen(temp_path, 'w', **profile) as dst:
                reproject(array, new_array, src_transform=aff, dst_transform=new_affine, src_crs=src.crs,
                          dst_crs=src.crs, resampling=Resampling.bilinear)

                dst.write(new_array)

            return new_array

            # add no-data values TODO

    def _build_url(self, var):

        # ParseResult('scheme', 'netloc', 'path', 'params', 'query', 'fragment')
        url = urlunparse([self.scheme, self.service,
                          '/thredds/dodsC/MET/{0}/{0}_{1}.nc'.format(var, self.year),
                          '', '', ''])

        return url

    def _dtime_to_xldate(self):
        s_sup, e_sup = self.start.timetuple(), self.end.timetuple()
        s_tup, e_tup = (s_sup[0], s_sup[1], s_sup[2]), (e_sup[0], e_sup[1], e_sup[2])
        sxl, exl = xldate_from_date_tuple(s_tup, 0), xldate_from_date_tuple(e_tup, 0)
        return sxl, exl

    def _date_index(self):

        date_ind = date_range(self.start, self.end, freq='d')

        return date_ind

# ========================= EOF ====================================================================
