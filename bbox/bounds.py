from pyproj import Proj
from rasterio import open as rasopen
from rasterio.crs import CRS


class BBox(object):
    def __init__(self):
        self.west = None
        self.east = None
        self.north = None
        self.south = None

    def as_tuple(self, order='wsen'):
        """ Find 4-tuple of extent
        :param order: order of cardinal directions, default='wsen'
        :return: 4-Tuple
        """
        if order == 'wsen':
            return self.west, self.south, self.east, self.north
        elif order == 'swne':
            return self.south, self.west, self.north, self.east


class GeoBounds(BBox):
    """Spatial bounding box
    
    By default, represents a buffered bounding box around the conterminous U.S.   
     
     
    """

    def __init__(self, west_lon=-126.0, south_lat=22.0, east_lon=-64.0,
                 north_lat=53.0):
        BBox.__init__(self)
        self.west = west_lon
        self.south = south_lat
        self.east = east_lon
        self.north = north_lat


class RasterBounds(BBox):
    """ Spatial bounding box from raster extent.
    
    :param raster
    
    """

    def __init__(self, raster, latlon=True):
        BBox.__init__(self)
        with rasopen(raster, 'r') as src:
            aff_transform = src.transform
            profile = src.profile

            col, row = 0, 0
            w, n = aff_transform * (col, row)
            col, row = profile['width'], profile['height']
            e, s = aff_transform * (col, row)

        if latlon and profile['crs'] != CRS({'init': 'epsg:4326'}):
            in_proj = Proj(init=profile['crs']['init'])
            self.west, self.north = in_proj(w, n, inverse=True)
            self.east, self.south = in_proj(e, s, inverse=True)

        else:
            self.north, self.west, self.south, self.east = n, w, s, e


if __name__ == '__main__':
    pass
# ========================= EOF ====================================================================
