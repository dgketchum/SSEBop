import os
from requests import get
from tempfile import mkdtemp
from rasterio import open as rasopen
from rasterio.merge import merge

TILES = [(8, 46, 90), (8, 47, 90), (8, 48, 90), (8, 46, 91), (8, 47, 91),
         (8, 48, 91), (8, 46, 92), (8, 47, 92), (8, 48, 92)]

KEY = 'mapzen-JmKu1BF'
URL = 'https://tile.mapzen.com/mapzen/terrain/v1/geotiff/{z}/{x}/{y}.tif?api_key={k}'


def merge_tiles(tiles, url, key):
    temp_dir = mkdtemp('mapzen_tile_')
    tile_files = []

    for (z, x, y) in tiles:
        url = url.format(z=z, x=x, y=y, k=key)
        req = get(url, verify=False, stream=True)

        temp_path = os.path.join(temp_dir, '{}-{}-{}.tif'.format(z, x, y))
        with open(temp_path, 'wb') as f:
            f.write(req.content)
            tile_files.append(temp_path)

    raster_readers = [rasopen(f) for f in tile_files]
    array, transform = merge(raster_readers)

    print(array.shape, transform)


if __name__ == '__main__':
    home = os.path.expanduser('~')
    merge_tiles(TILES, URL, KEY)

# ========================= EOF ====================================================================
