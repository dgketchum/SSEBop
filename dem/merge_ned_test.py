import os
from rasterio.merge import merge
from rasterio import open as rasopen


def merge_ned(directory):
    tifs = os.listdir(folder)
    tiles = [os.path.join(directory, tif) for tif in tifs]
    raster_readers = [rasopen(f) for f in tiles]
    array, transform = merge(raster_readers)

    print(array.shape, transform)


if __name__ == '__main__':
    home = os.path.expanduser('~')
    folder = os.path.join(home, 'images', 'sandbox', 'ned')
    merge_ned(folder)

# ========================= EOF ====================================================================
