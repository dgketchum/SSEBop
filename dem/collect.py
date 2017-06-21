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
from numpy import pi, log, tan, cos
from itertools import product
from rasterio.io import MemoryFile
from rasterio.merge import merge
from requests import get

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


def tiles(zoom, lat1, lon1, lat2, lon2):
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


def download(tiles, api_key, lat, zoom):
    """ Open Rasterio.DatasetReader objects for each tile, merge, return np.array.
    """

    raster_readers = []

    for (z, x, y) in tiles:

        url = TILE_URL.format(z=z, x=x, y=y, k=api_key)
        req = get(url, verify=False)

        first = True

        with MemoryFile(req.content) as memfile:

            with memfile.open() as dataset:
                raster_readers.append(dataset)

                if first:
                    geo = dataset.profile
                    setattr(geo, 'res', ground_resolution(lat, zoom))
                    first = False

    array, transform = merge(raster_readers)

    return array, transform


def ground_resolution(lat, zoom):
    """ Get tile resolution.
    :param lat: Float
    :param zoom: Int
    :return: ground resolution of tile pixels.
    """
    res = (cos(lat * pi / 180.) * 2 * pi * 6378137) / (256 * 2 ** zoom)
    return res

if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
