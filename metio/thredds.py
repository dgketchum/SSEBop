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

import numpy as np
from datetime import datetime
# from netCDF4 import Dataset
from xlrd import xldate
from xarray import open_dataset, decode_cf, DataArray
from pandas import DatetimeIndex

from metio.misc import BBox


class Thredds(object):
    """  Unidata's Thematic Real-time Environmental Distributed Data Services (THREDDS)
    
    """

    start_doy = None
    end_doy = None
    date_doy = None

    def __init__(self, start=None, end=None, date=None, bbox=None):

        self.service = 'thredds.northwestknowledge.net:8080'
        self.scheme = 'http'
        self.start = start
        self.end = end
        self.date = date
        self.bbox = bbox

        # day of year; doy
        # doy must be zero-indexed
        for attr in ('start', 'end', 'date'):
            if getattr(self, attr):
                val = getattr(self, attr)
                setattr(self, '{}_doy'.format(attr), val.timetuple().tm_yday - 1)


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
    :param bbox: metio.misc.BBox object representing spatial bounds, default to conterminous US
    :return: numpy.ndarray
    
    """

    def __init__(self):
        Thredds.__init__(self, start=None, end=None, date=None, bbox=None)

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
        Thredds.__init__(self, start=None, end=None, date=None, bbox=None)
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

        for key, val in kwargs.items():
            setattr(self, key, val)

        self.dates_fmt = {'day': 'days since 1900-01-01'}

        self.variables = []
        if self.requested_variables:
            [setattr(self, var, None) for var in self.requested_variables if var in self.available]
            [self.variables.append(var) for var in self.requested_variables if var in self.available]
            [Warning('Variable {} is not available'.
                     format(var)) for var in self.requested_variables if var not in self.available]

        if self.start:
            self.year = self.start.year
        else:
            self.year = self.date.year

        if not self.start and not self.date:
            raise ValueError('Must include a start and end, or a date.')
        if self.start and self.end and self.date:
            raise ValueError('Must include a start and end, or a date.')
        if not self.bbox:
            self.bbox = BBox()

    def get_data(self):

        for var in self.variables:
            url = self._build_url(var)
            xray = open_dataset(url)
            xldates = [int(x) for x in xray['day']]
            dates = [xldate.xldate_as_datetime(date, 0) for date in xldates]
            date_index = DatetimeIndex(dates)

            if self.date:
                subset = xray.loc[dict(day=slice(self.date_doy),
                                       lat=slice(self.bbox.north, self.bbox.south),
                                       lon=slice(self.bbox.west, self.bbox.east))]
                subset.rename({'day': 'time'}, inplace=True)
                subset = DataArray(subset[self.kwords[var]],
                                   coords=(dict(time=date_index, lat=subset['lat'], lon=subset['lon'])),
                                   name=var)
            elif self.start:
                subset = xray.loc[dict(day=slice(self.start_doy, self.end_doy),
                                       lat=slice(self.bbox.north, self.bbox.south),
                                       lon=slice(self.bbox.west, self.bbox.east))]
                subset.rename({'day': 'time'}, inplace=True)
                subset = DataArray(subset[self.kwords[var]],
                                   coords=(dict(time=date_index, lat=subset['lat'], lon=subset['lon'])),
                                   name=var)

            else:
                raise ValueError('Must havve start or date parameter filled.')

            setattr(self, var, subset)

        return None

    def _build_url(self, var):

        # ParseResult('scheme', 'netloc', 'path', 'params', 'query', 'fragment')
        url = urlunparse([self.scheme, self.service,
                          '/thredds/dodsC/MET/{0}/{0}_{1}.nc'.format(var, self.year),
                          '', '', ''])
        if var == 'elev':
            url = urlunparse([self.scheme, self.service,
                              '/thredds/dodsC/MET/{0}/metdata_elevationdata.nc'.format(var, self.year),
                              '', '', ''])

        return url

# ========================= EOF ====================================================================
