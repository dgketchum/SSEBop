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
    from urllib.parse import urlunparse, urlencode

from datetime import datetime
from netCDF4 import Dataset

from metio.misc import BBox


class Thredds(object):
    """  Unidata's Thematic Real-time Environmental Distributed Data Services (THREDDS)
    
    """

    def __init__(self, start=None, end=None, date=None, bbox=None):

        self.service = 'thredds.northwestknowledge.net:8080'
        self.scheme = 'http'
        self.start = start
        self.end = end
        self.date = date
        self.bbox = bbox

    def _time(self):

        if self.start and self.end:
            s = datetime.strftime(self.start, '%Y-%m-%dT00:00:00Z')
            e = datetime.strftime(self.end, '%Y-%m-%dT00:00:00Z')
            return s, e
        if self.date:
            d = datetime.strftime(self.date, '%Y-%m-%dT00:00:00Z')
            return d, d


class OpenDap(object):
    """ OpenDap: Open-source Project for a Network Data Access Protocol
    
        " is a data transport architecture and protocol widely used by earth scientists. 
        The protocol is based on HTTP and the current specification is OPeNDAP 2.0 draft"
        
    """

    def __init__(self, start=None, end=None, date=None):

        self.start = start
        self.end = end
        self.date = date

        # doy must be zero-indexed for OpenDap
        for attr in ('start', 'end', 'date'):
            if getattr(self, attr):
                val = getattr(self, attr)
                setattr(self, '{}_doy'.format(attr), val.timetuple().tm_yday - 1)


class TopoWX(Thredds, OpenDap):
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
        OpenDap.__init__(self, start=None, end=None, date=None)

        if self.start:
            pass


class GridMet(Thredds, OpenDap):
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
        OpenDap.__init__(self, start=None, end=None, date=None)
        self.requested_variables = variables

        self.available = ['elev', 'pr', 'rmax', 'rmin', 'sph', 'srad',
                          'th', 'tmmn', 'tmmx', 'pet', 'vs', 'erc', 'bi',
                          'fm100', 'pdsi']

        for key, val in kwargs.items():
            setattr(self, key, val)

        self.variables = []
        if self.requested_variables:
            [setattr(self, var, None) for var in self.requested_variables if var in self.available]
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
            # 'http://thredds.northwestknowledge.net:8080/thredds/dodsC/MET/pet/{}_{}.nc'
            url_test = 'http://thredds.northwestknowledge.net:8080/thredds/dodsC/MET/pet/pet_2016.nc'
            url = self._build_url(var)
            subset = Dataset(url, 'r')
            setattr(self, var, subset)

        return None

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
        url = urlunparse([self.scheme, self.service,
                          '/thredds/dodsC/MET/{0}/{0}_{1}.nc'.format(var, self.date.year),
                          '', self._build_query_str(var), ''])
        if var == 'elev':
            url = urlunparse([self.scheme, self.service,
                              '/thredds/dodsC/MET/{0}/metdata_elevationdata.nc'.format(var, self.date.year),
                              '', self._build_query_str(var), ''])

        return url

# ========================= EOF ====================================================================
