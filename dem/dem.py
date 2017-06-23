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
import shutil
from numpy import pi, log, tan
from itertools import product
from rasterio import open as rasopen
from rasterio.merge import merge
from rasterio.mask import mask
from rasterio.warp import reproject
from rasterio.crs import CRS
from requests import get
from tempfile import mkdtemp
from xarray import open_dataset


class Dem(object):
    def __init__(self):
        pass

    @staticmethod
    def save(array, geometry, output_filename, crs=None):
        array = array.reshape(1, array.shape[1], array.shape[2])
        geometry['dtype'] = array.dtype
        if crs:
            geometry['crs'] = CRS({'init': crs})
        with open(output_filename, 'w', **geometry) as dst:
            dst.write(array)
        return None


class SubsetDem(Dem):
    """ Digital Elevation Model and Dertivatives
    
    :param BBox, bounding box
    """

    def __init__(self, bbox=None):
        Dem.__init__(self)
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


class MapzenDem(Dem):
    def __init__(self, zoom=None, target_profile=None, bounds=None, clip_object=None,
                 api_key=None):
        Dem.__init__(self)

        self.zoom = zoom
        self.target_profile = target_profile
        self.bbox = bounds
        self.clip_feature = clip_object
        self.key = api_key
        self.url = 'https://tile.mapzen.com'
        self.base_gtiff = '/mapzen/terrain/v1/geotiff/{z}/{x}/{y}.tif?api_key={k}'
        self.temp_dir = mkdtemp(prefix='collected-')
        self.files = []

    def get_conforming_dem(self, out_file=None):
        self.get_tiles()
        self.merge_tiles()
        self.reproject_tiles()
        self.mask_dem()

        with rasopen(self.mask_path, 'r') as src:
            dem = src.read()

        if out_file:
            self.save(dem, self.target_profile, out_file)

        shutil.rmtree(self.temp_dir)
        return dem

    @staticmethod
    def mercator(lat, lon, zoom):
        """ Convert latitude, longitude to z/x/y tile coordinate at given zoom.
        """
        # convert to radians
        x1, y1 = lon * pi / 180, lat * pi / 180

        # project to mercator
        x2, y2 = x1, log(tan(0.25 * pi + 0.5 * y1))

        # transform to tile space
        tiles, diameter = 2 ** zoom, 2 * pi
        x3, y3 = int(tiles * (x2 + pi) / diameter), int(tiles * (pi - y2) / diameter)

        return zoom, x3, y3

    def find_tiles(self):
        """ Convert geographic bounds into a list of tile coordinates at given zoom.
        """
        lat1, lat2 = self.bbox.south, self.bbox.north
        lon1, lon2 = self.bbox.west, self.bbox.east
        # convert to geographic bounding box
        minlat, minlon = min(lat1, lat2), min(lon1, lon2)
        maxlat, maxlon = max(lat1, lat2), max(lon1, lon2)

        # convert to tile-space bounding box
        _, xmin, ymin = self.mercator(maxlat, minlon, self.zoom)
        _, xmax, ymax = self.mercator(minlat, maxlon, self.zoom)

        # generate a list of tiles
        xs, ys = range(xmin, xmax + 1), range(ymin, ymax + 1)
        tile_list = [(self.zoom, x, y) for (y, x) in product(ys, xs)]

        return tile_list

    def get_tiles(self):
        url = '{}{}'.format(self.url, self.base_gtiff)

        for (z, x, y) in self.find_tiles():
            url = url.format(z=z, x=x, y=y, k=self.key)
            req = get(url, verify=False, stream=True)

            temp_path = os.path.join(self.temp_dir, '{}-{}-{}.tif'.format(z, x, y))
            with open(temp_path, 'wb') as f:
                f.write(req.content)
                self.files.append(temp_path)

    def merge_tiles(self):
        raster_readers = [rasopen(f) for f in self.files]
        array, transform = merge(raster_readers)
        setattr(self, 'merged_array', array)
        setattr(self, 'merged_transform', transform)

        with rasopen(self.files[0], 'r') as f:
            setattr(self, 'temp_profile', f.profile)

    def reproject_tiles(self):
        reproj_path = os.path.join(self.temp_dir, 'tiled_reproj.tif')

        setattr(self, 'reproject', reproj_path)

        reproject(self.merged_array, reproj_path, src_transform=self.merged_transform,
                  src_crs=self.temp_profile['crs'], dst_crs=self.target_profile['crs'],
                  dst_transform=self.target_profile['transform'])

    def mask_dem(self):
        temp_path = os.path.join(self.temp_dir, 'masked_dem.tif')

        with rasopen(temp_path, **self.target_profile) as src:
            out_arr, out_trans = mask(src, self.clip_feature, crop=True,
                                      all_touched=True)
            out_prof = src.meta.copy()
            out_prof.update({'driver': 'GTiff',
                             'height': out_arr.shape[1],
                             'width': out_arr.shape[2],
                             'transform': out_trans})

        with rasopen(temp_path, 'w', **out_prof) as dst:
            dst.write(out_arr)

        setattr(self, 'mask_path', temp_path)


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
