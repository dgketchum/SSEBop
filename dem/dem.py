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
from future.standard_library import hooks

with hooks():
    from urllib.parse import urlunparse

import os
from rasterio.crs import CRS
from rasterio import open
from xarray import open_dataset
from dem.collect import tiles, download


class Dem(object):
    """ Digital Elevation Model and Dertivatives
    
    :param BBox, bounding box
    """

    def __init__(self, bbox=None):
        self.bbox = bbox

    def thredds_dem(self):
        service = 'thredds.northwestknowledge.net:8080'
        scheme = 'http'

        url = urlunparse([scheme, service,
                          '/thredds/dodsC/MET/elev/metdata_elevationdata.nc',
                          '', '', ''])

        xray = open_dataset(url)

        subset = xray.loc[dict(lat=slice(self.bbox.north, self.bbox.south),
                               lon=slice(self.bbox.west, self.bbox.east))]

        return subset

    def mapzen_tiled_dem(self, zoom):

        bb = self.bbox
        tls = tiles(zoom, bb.south, bb.west, bb.north, bb.east)
        api_key = 'mapzen-JmKu1BF'
        data = download(tls, api_key, bb.north, zoom)

        return data

    @staticmethod
    def save(array, geometry, output_filename, crs=None):
        array = array.reshape(1, array.shape[1], array.shape[2])
        geometry['dtype'] = array.dtype
        if crs:
            geometry['crs'] = CRS({'init': crs})
        with open(output_filename, 'w', **geometry) as dst:
            dst.write(array)
        return None


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
