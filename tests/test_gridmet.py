# ===============================================================================
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
# ===============================================================================
import unittest
import os
from datetime import datetime
from xarray import open_dataset, Dataset
from fiona import open as fopen
from rasterio import open as rasopen

from bounds.bounds import GeoBounds, RasterBounds
from metio.thredds import GridMet
from sat_image.image import Landsat8


class TestGridMet(unittest.TestCase):
    def setUp(self):
        self.bbox = GeoBounds(west_lon=-116.4, east_lon=-103.0,
                              south_lat=44.3, north_lat=49.1)

        self.var = 'pet'
        self.bad_var = 'rain'
        self.test_url_str = 'http://thredds.northwestknowledge.net:' \
                            '8080/thredds/ncss/MET/pet/pet_2011.nc?' \
                            'var=potential_evapotranspiration&north=' \
                            '49.1&west=-116.4&east=-103.0&south=44.3&' \
                            '&horizStride=1&time_start=2011-01-01T00%3A00%3A00Z&' \
                            'time_end=2011-12-31T00%3A00%3A00Z&timeSt' \
                            'ride=1&accept=netcdf4'

        self.start = datetime(2014, 8, 15)
        self.date = datetime(2014, 8, 20)
        self.end = datetime(2014, 10, 31)

        self.agrimet_var = 'pet'
        self.agri_loc = 47.0585365, -109.9507523
        self.grimet_raster_dir = 'tests/data/agrimet_test/gridmet_rasters'
        self.grid_vals = [('2014-4-23', 5.13205), ('2014-4-24', 1.49978), ('2014-4-20', 12.0076)]
        # time series test points here are agrimet stations
        self.all_agri_points = 'tests/data/agrimet_test/points/agrimet_sites.shp'
        # agrimet_test.shp are points between sites to test location
        self.point_file = 'tests/data/agrimet_test/points/agrimet_test.shp'
        self.dir_name_LC8 = 'tests/data/ssebop_test/lc8/038_027/2014/LC80380272014227LGN01'

    def test_instantiate(self):
        gridmet = GridMet(self.var, start=self.start, end=self.end)
        self.assertIsInstance(gridmet, GridMet)

    def test_conforming_array(self):
        l8 = Landsat8(self.dir_name_LC8)
        polygon = l8.get_tile_geometry()
        bounds = RasterBounds(affine_transform=l8.transform, profile=l8.profile)
        gridmet = GridMet(self.var, date=self.date, bbox=bounds,
                          target_profile=l8.profile, clip_feature=polygon)
        pr = gridmet.get_data_subset()
        shape = 1, l8.rasterio_geometry['height'], l8.rasterio_geometry['width']
        self.assertEqual(pr.shape, shape)

    def test_save_to_netcdf(self):
        gridmet = GridMet(self.var, date=self.date)
        out = 'tests/data/agrimet_test/{}-{}-{}_pet.nc'.format(self.date.year,
                                                               self.date.month,
                                                               self.date.day)
        gridmet.write_netcdf(outputroot=out)
        self.assertTrue(os.path.exists(out))
        data = open_dataset(out)
        self.assertIsInstance(data, Dataset)
        os.remove(out)

    def test_save_native_dataset(self):
        self.assertEqual(True, False)

    def test_get_time_series(self):

        rasters = os.listdir(self.grimet_raster_dir)

        for ras in rasters:
            dt = datetime.strptime(ras[:9], '%Y-%m-%d')
            ras = os.path.join(self.grimet_raster_dir, ras)
            points = raster_point_extract(ras, self.all_agri_points, dt)

            for key, val in points:

            gridmet = GridMet(self.agrimet_var, date=dt,
                              lat=self.agri_loc[0], lon=self.agri_loc[1])
            gridmet = None
        series = gridmet.get_point_timeseries()
        for date, val in self.grid_vals:
            self.assertAlmostEqual(series.loc[date][0], val, delta=0.1)


# ============================================================================

def raster_point_extract(raster, points, dtime):
    point_data = {}
    with fopen(points, 'r') as src:
        for feature in src:
            name = feature['properties']['siteid']
            point_data[name] = {'coords': feature['geometry']['coordinates']}

        with rasopen(raster, 'r') as rsrc:
            rass_arr = rsrc.read()
            rass_arr = rass_arr.reshape(rass_arr.shape[1], rass_arr.shape[2])
            affine = rsrc.transform

        for key, val in point_data.items():
            x, y = val['coords']
            col, row = ~affine * (x, y)
            val = rass_arr[int(row), int(col)]
            point_data[key][dtime] = [val, None]

        return point_data


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
