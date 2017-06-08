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
from datetime import datetime
from urllib.parse import ParseResult, urlunparse, urlencode
import numpy as np
from netCDF4 import Dataset
from xlrd import xldate

from metio.misc import BBox


class GridMet(object):
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

    def __init__(self, variables, start=None, end=None, date=None, bbox=None, **kwargs):

        self.requested_variables = variables
        self.start = start
        self.end = end
        self.date = date
        self.bbox = bbox

        self.available = ['elev', 'pr', 'rmax', 'rmin', 'sph', 'srad',
                          'th', 'tmmn', 'tmmx', 'pet', 'vs', 'erc', 'bi',
                          'fm100', 'pdsi']

        for key, val in kwargs.items():
            setattr(self, key, val)

        self.variables = []
        if self.requested_variables:
            [setattr(self, var, True) for var in self.requested_variables if var in self.available]
            [self.variables.append(var) for var in self.requested_variables if var in self.available]
            [Warning('Variable {} is not available'.
                     format(var)) for var in self.requested_variables if var not in self.available]

        if not self.start and not self.date:
            raise ValueError('Must include a start and end, or a date.')
        if self.start and self.end and self.date:
            raise ValueError('Must include a start and end, or a date.')
        if not self.bbox:
            self.bbox = BBox()

    def get_data(self):

        for var in self.variables:
            self._build_url(var)


    def _time(self):

        if self.start and self.end:
            s = datetime.strftime(self.start, '%Y-%m-%dT00:00:00Z')
            e = datetime.strftime(self.end, '%Y-%m-%dT00:00:00Z')
            return s, e
        if self.date:
            d = datetime.strftime(self.date, '%Y-%m-%dT00:00:00Z')
            return d, d

    def _build_query_str(self, var):

        kwords = {'bi': 'burning_index_g',
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

        if self.start:
            params = {'west': [self.bbox.west_str], 'north': [self.bbox.north_str],
                      'east': [self.bbox.east_str], 'south': [self.bbox.south_str],
                      'timeStride': ['1'], 'horizStride': ['1'],
                      'accept': ['netcdf4'], 'time_start': [self._time()[0]],
                      'time_end': [self._time()[1]], 'var': kwords[var]}
            # check if None value works in query, join conditionals into one statement todo
        elif self.date:
            params = {'west': [self.bbox.west_str], 'north': [self.bbox.north_str],
                      'east': [self.bbox.east_str], 'south': [self.bbox.south_str],
                      'timeStride': ['1'], 'horizStride': ['1'],
                      'accept': ['netcdf4'], 'time': [self._time()[0]],
                      'var': kwords[var]}

        else:
            params = None

        query = urlencode(params, doseq=True)

        return query

    def _build_url(self, var):

        # ParseResult('scheme', 'netloc', 'path', 'params', 'query', 'fragment')
        url = urlunparse(['http', 'thredds.northwestknowledge.net:8080',
                          '/thredds/ncss/MET/{0}/{0}_{1}.nc'.format(var, self.start.year),
                          '', self._build_query_str(var), ''])
        if var == 'elev':
            url = urlunparse(['http', 'thredds.northwestknowledge.net:8080',
                              '/thredds/ncss/MET/{0}/metdata_elevationdata.nc'.format(var, self.start.year),
                              '', self._build_query_str(var), ''])

        return url


        # nc = Dataset(site)
        # print(nc.variables.keys())
        #
        # date_tup = (day.year, day.month, day.day)
        # excel_date = xldate.xldate_from_date_tuple(date_tup, 0)
        # print('excel date from datetime: {}'.format(excel_date))
        #
        # time_arr = nc.variables['day'][:]
        # date_index = np.argmin(np.abs(time_arr - excel_date))
        #
        # # find indices of lat lon bounds in nc file
        # lats = nc.variables['lat'][:]
        # lons = nc.variables['lon'][:]
        # lat_lower = np.argmin(np.abs(lats - lat_bound[1]))
        # lat_upper = np.argmin(np.abs(lats - lat_bound[0]))
        # lon_lower = np.argmin(np.abs(lons - lon_bound[0]))
        # lon_upper = np.argmin(np.abs(lons - lon_bound[1]))
        #
        # subset = nc.variables['potential_evapotranspiration'][date_index, :, :]  # lat_lower:lat_upper, lon_lower:lon_upper]
        # nc.close()
        # print('variable of type {} has shape {}'.format(type(subset), subset.shape))


# ========================= EOF ====================================================================
