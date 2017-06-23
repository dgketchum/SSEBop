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

import os
import shutil
from numpy import pi, log, tan
from itertools import product
from rasterio import open as rasopen
from rasterio.merge import merge
from rasterio.mask import mask
from requests import get
from tempfile import mkdtemp

# four formats are available, let's use GeoTIFF
TILE_URL = 'https://tile.mapzen.com/mapzen/terrain/v1/geotiff/{z}/{x}/{y}.tif?api_key={k}'


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


def find_tiles(zoom, lat1, lon1, lat2, lon2):
    """ Convert geographic bounds into a list of tile coordinates at given zoom.
    """
    # convert to geographic bounding box
    minlat, minlon = min(lat1, lat2), min(lon1, lon2)
    maxlat, maxlon = max(lat1, lat2), max(lon1, lon2)

    # convert to tile-space bounding box
    _, xmin, ymin = mercator(maxlat, minlon, zoom)
    _, xmax, ymax = mercator(minlat, maxlon, zoom)

    # generate a list of tiles
    xs, ys = range(xmin, xmax + 1), range(ymin, ymax + 1)
    tile_list = [(zoom, x, y) for (y, x) in product(ys, xs)]

    return tile_list


def get_dem(tiles, key, clip_feature=None, output_filepath=None):
    """ Open Rasterio.DatasetReader objects for each tile, merge.
    
    :param output_filepath: Str filepath to save dem.
    :param clip_feature: Shapeley Polygon object
    :param tiles: list of 3-tuples with (zoom, x, y) see https://msdn.microsoft.com/en-us/library/bb259689.aspx
    :param key: Mapzen free api key from  https://mapzen.com/documentation/overview/api-keys/
    """

    if not output_filepath:
        temp_dir = mkdtemp(prefix='collected-')
    else:
        temp_dir = output_filepath

    files = []

    for (z, x, y) in tiles:
        url = TILE_URL.format(z=z, x=x, y=y, k=key)
        req = get(url, verify=False, stream=True)

        temp_path = os.path.join(temp_dir, '{}-{}-{}.tif'.format(z, x, y))
        with open(temp_path, 'wb') as f:
            f.write(req.content)
            files.append(temp_path)

    raster_readers = [rasopen(f) for f in files]
    array, transform = merge(raster_readers)

    with rasopen(files[0], 'r') as f:
        profile = f.profile

    profile['transform'] = transform
    profile['height'] = array.shape[1]
    profile['width'] = array.shape[2]

    if clip_feature:
        temp_path = os.path.join(temp_dir, 'dem_reproj.tif')
        features = [clip_feature]
        with rasopen(temp_path, 'w') as src:
            out_arr, out_trans = mask(src, features, crop=True,
                                      all_touched=True)
            out_prof = src.meta.copy()
            out_prof.update({'driver': 'GTiff',
                             'height': out_arr.shape[1],
                             'width': out_arr.shape[2],
                             'transform': out_trans})
        if output_filepath:
            with rasopen(output_filepath, 'w', **out_prof) as dst:
                dst.write(out_arr)
            return None
        else:
            shutil.rmtree(temp_dir)
            return out_arr, out_trans


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
