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
from xarray import Dataset

from bounds.bounds import GeoBounds, RasterBounds
from metio.thredds import GridMet, TopoWX
from sat_image.image import Landsat5


class TestGridMet(unittest.TestCase):
    def setUp(self):
        self.bbox = GeoBounds(west_lon=-116.4, east_lon=-103.0,
                              south_lat=44.3, north_lat=49.1)

        self.vars = ['pr', 'pet', 'not_a_var', 'elev', 'srad']
        self.test_url_str = 'http://thredds.northwestknowledge.net:8080/thredds/ncss/MET/pet/pet_2011.nc?' \
                            'var=potential_evapotranspiration&north=49.1&west=-116.4&east=-103.0&south=44.3&' \
                            '&horizStride=1&time_start=2011-01-01T00%3A00%3A00Z&' \
                            'time_end=2011-12-31T00%3A00%3A00Z&timeStride=1&accept=netcdf4'

        self.start = datetime(2011, 4, 1)
        self.date = datetime(2011, 4, 1)
        self.end = datetime(2011, 10, 31)
        self.image_shape = (1, 7431, 8161)

        self.dir_name_LT5 = 'tests/data/image_test/lt5_image'

    def test_instantiate(self):
        gridmet = GridMet(self.vars, start=self.start, end=self.end,
                          bbox=self.bbox)
        self.assertIsInstance(gridmet, GridMet)

    def test_get_data_date(self):
        gridmet = GridMet(self.vars, date=self.date,
                          bbox=self.bbox)
        gridmet.get_data_subset()
        self.assertIsInstance(gridmet.pet, Dataset)
        self.assertEqual(gridmet.pet.dims['lon'], 322)
        self.assertEqual(gridmet.pet.dims['time'], 1)

    def test_get_data_date_range(self):
        gridmet = GridMet(self.vars, start=self.start, end=self.end,
                          bbox=self.bbox)
        gridmet.get_data_subset()
        self.assertIsInstance(gridmet.pet, Dataset)
        self.assertEqual(gridmet.pet.dims['lon'], 322)
        self.assertEqual(gridmet.pet.dims['time'], 214)

    def test_conforming_array(self):
        home = os.path.expanduser('~')
        tif_dir = os.path.join(home, 'images', 'LT5', 'image_test', 'full_image')
        l5 = Landsat5(tif_dir)
        polygon = l5.get_tile_geometry()
        bounds = RasterBounds(affine_transform=l5.transform, profile=l5.profile)
        gridmet = GridMet(self.vars, date=self.date, bbox=bounds,
                          target_profile=l5.profile, clip_feature=polygon)
        gridmet.get_data_subset(grid_conform=True)
        self.assertEqual(gridmet.pr.shape, self.image_shape)


class TestTopoWX(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2011, 4, 1)
        self.date = datetime(2011, 4, 1)
        self.end = datetime(2011, 10, 31)
        self.image_shape = (1, 7431, 8161)

        self.dir_name_LT5 = 'tests/data/image_test/lt5_image'

    def test_conforming_array(self):
        home = os.path.expanduser('~')
        tif_dir = os.path.join(home, 'images', 'LT5', 'image_test', 'full_image')
        out_file = os.path.join(home, 'images', 'sandbox', 'thredds', 'tmax_{}_{}_{}.tif'.format(
            self.date.year, self.date.month, self.date.day))
        l5 = Landsat5(tif_dir)
        polygon = l5.get_tile_geometry()
        bounds = RasterBounds(affine_transform=l5.transform, profile=l5.profile, latlon=True)
        topowx = TopoWX(date=self.date, bbox=bounds, target_profile=l5.profile,
                        clip_feature=polygon)
        topowx.get_data_subset(grid_conform=True, var='tmax', out_file=out_file)
        self.assertEqual(topowx.tmax.shape, self.image_shape)


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
