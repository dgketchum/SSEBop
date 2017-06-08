# Adapted from work by Jared Oyler, https://github.com/jaredwo
import os


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

        self.west_str = str(self.west)
        self.south_str = str(self.south)
        self.east_str = str(self.east)
        self.north_str = str(self.north)

    def remove_outbnds_df(self, df):
        mask_bnds = ((df.latitude >= self.south) &
                     (df.latitude <= self.north) &
                     (df.longitude >= self.west) &
                     (df.longitude <= self.east))

        df = df[mask_bnds].copy()

        return df


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
