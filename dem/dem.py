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
from scipy.misc import imread
import xml.etree.ElementTree as ETree
from owslib.wms import WebMapService

from xarray import open_dataset


class Dem(object):
    """ Digital Elevation Model and Dertivatives
    
    :param BBox, bounding box
    """

    def __init__(self, bbox=None):
        self.bbox = bbox

    def thredds_dem(self, elevation=None, slope=None, aspect=None):
        service = 'thredds.northwestknowledge.net:8080'
        scheme = 'http'

        url = urlunparse([scheme, service,
                          '/thredds/dodsC/MET/elev/metdata_elevationdata.nc',
                          '', '', ''])

        xray = open_dataset(url)

        subset = xray.loc[dict(lat=slice(self.bbox.north, self.bbox.south),
                               lon=slice(self.bbox.west, self.bbox.east))]

        if aspect:
            pass

        if slope:
            pass

        if elevation:
            return subset

    def gibs(self):

        bb = self.bbox
        wms = WebMapService('https://webmap.ornl.gov/ogcbroker/wms?', version='1.1.1')
        dem = wms.getmap(layers='10008_2',
                         srs='EPSG:4326',
                         bbox=(bb.west, bb.south, bb.east, bb.north),
                         size=(300, 250),
                         format='image/gtiff',
                         transparent=True, timeout=60)
        arr = imread(dem, mode='F')
        return arr


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
