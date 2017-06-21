from future.standard_library import hooks

with hooks():
    from urllib.parse import urlunparse

import os
from pyproj import transform
from rasterio import open as rasopen
from rasterio import features
from rasterio.crs import CRS


class BBox(object):
    """Spatial bounding box
    
    By default, represents a buffered bounding box around the conterminous U.S.   
     
     
    """

    def __init__(self, west_lon=-126.0, south_lat=22.0, east_lon=-64.0,
                 north_lat=53.0):
        self.west = west_lon
        self.south = south_lat
        self.east = east_lon
        self.north = north_lat


class RasterBounds(object):
    def __init__(self, raster, latlon=True):
        with rasopen(raster, 'r') as src:
            data = src.read()
            transform = src.transform
            profile = src.profile

        shapes = features.shapes(data, transform=transform)
        shape = next(shapes)

        if latlon and profile['crs'] != CRS({'init': 'epsg:32612'}):
            n, s, w, e = (shape[0]['coordinates'][0][0][1],
                          shape[0]['coordinates'][0][1][1],
                          shape[0]['coordinates'][0][0][0],
                          shape[0]['coordinates'][0][2][1])
            in_proj = profile['crs']['init']
            out_proj = 'epsg:4326'
            n, w = transform(in_proj, out_proj, n, w)
            s, e = transform(in_proj, out_proj, s, e)
            self.north, self.south, self.west, self.east = n, s, w, e

        else:
            self.north, self.south, self.west, self.east = (shape[0]['coordinates'][0][0][1],
                                                            shape[0]['coordinates'][0][1][1],
                                                            shape[0]['coordinates'][0][0][0],
                                                            shape[0]['coordinates'][0][2][1])


if __name__ == '__main__':
# home = os.path.expanduser('~')
# tif = os.path.join(home, 'images', 'LT5', 'image_test', 'full_image',
#                    'LT05_L1TP_040028_20060706_20160909_01_T1_B5.TIF')
# BBox.raster_bounds(tif)

# ========================= EOF ====================================================================
