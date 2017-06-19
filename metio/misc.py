from future.standard_library import hooks

with hooks():
    from urllib.parse import urlunparse

import os
from xarray import open_dataset


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

    def remove_outbnds_df(self, df):
        mask_bnds = ((df.latitude >= self.south) &
                     (df.latitude <= self.north) &
                     (df.longitude >= self.west) &
                     (df.longitude <= self.east))

        df = df[mask_bnds].copy()

        return df


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


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
