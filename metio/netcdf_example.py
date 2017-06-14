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

from netCDF4 import Dataset, num2date
from pydap.client import open_url
import numpy as np

# Montana bounds (lat, lon)
lat_bound = [44, 49]
lon_bound = [-117, -104]


def ganymed():
    rootgrp = Dataset('http://opendap.nccs.nasa.gov:9090/dods/OSSE/G5NR/Ganymed/7km/0.5000_deg/inst/inst01hr_3d_T_Cv',
                      'r')

    print("rootgrp.variables['t'].shape", rootgrp.variables['t'].shape)

    temp = rootgrp.variables['t'][11771, :, 229:280, 99:230]
    print('T.shape:', temp.shape)
    print('max(T): %.4f' % np.max(temp))
    print('min(T): %.4f' % np.min(temp))

    rootgrp.close()

    return None


def get_bounds_rectangle():
    site = 'http://thredds.northwestknowledge.net:8080/thredds/ncss/MET/pet/pet_2016.nc?var=potential_evapotranspiration&horizStride=1&time_start=2016-01-01T00%3A00%3A00Z&time_end=2016-01-02T00%3A00%3A00Z&timeStride=1&addLatLon=true&accept=netcdf4'
    nc = Dataset(site)
    print(nc)


def get_bounds_rectangle_dap():
    site = 'http://thredds.northwestknowledge.net:8080/thredds/dodsC/MET/pet/pet_2011.nc?lon[0:1:1385],lat[0:1:584],day[0:1:364],potential_evapotranspiration[0:1:0][0:1:0][0:1:0]'
    nc = open_url(site)
    print(list(nc.keys()))


if __name__ == '__main__':
    # ganymed()
    get_bounds_rectangle()

# ========================= EOF ====================================================================
