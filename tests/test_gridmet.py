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
from dateutil.rrule import rrule, DAILY
from pyproj import Proj
from numpy import mean

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
        self.end = datetime(2014, 8, 20)

        self.date = datetime(2014, 8, 20)

        self.grimet_raster_dir = 'tests/data/met_test/gridmet_rasters'
        # time series test points here are agrimet stations
        self.agri_points = 'tests/data/points/agrimet_test_sites.shp'
        # met_test.shp are points between sites to test location
        self.search_point_file = 'tests/data/points/agrimet_location_test.shp'
        # 41_25 points are used to test native gridmet raster to conforming array,
        # these have been projected to the native CRS (i.e., 4326)
        self.scene_points = 'tests/data/points/038_027_US_Mj_manypoints_4326.shp'
        self.dir_name_LC8 = '/data01/images/sandbox/ssebop_analysis/038_027/2014/LC80380272014227LGN01'

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
        out = 'tests/data/met_test/{}-{}-{}_pet.nc'.format(self.date.year,
                                                           self.date.month,
                                                           self.date.day)
        gridmet.write_netcdf(outputroot=out)
        self.assertTrue(os.path.exists(out))
        data = open_dataset(out)
        self.assertIsInstance(data, Dataset)
        os.remove(out)

    def test_get_time_series(self):

        rasters = os.listdir(self.grimet_raster_dir)
        for ras in rasters:
            if ras.endswith('pet.tif'):
                dt = datetime.strptime(ras[:10], '%Y-%m-%d')
                raster = os.path.join(self.grimet_raster_dir, ras)
                points = raster_point_extract(raster, self.agri_points, dt)

                for key, val in points.items():
                    lon, lat = val['coords']
                    _, var = ras.split('_')
                    var = var.replace('.tif', '')
                    gridmet = GridMet(var, date=dt,
                                      lat=lat, lon=lon)
                    gridmet_pet = gridmet.get_point_timeseries()
                    val[dt][1] = gridmet_pet.iloc[0, 0]
                for key, val in points.items():
                    self.assertEqual(val[dt][0], val[dt][1])

    def test_conforming_array_to_native(self):
        l8 = Landsat8(self.dir_name_LC8)
        polygon = l8.get_tile_geometry()
        bounds = RasterBounds(affine_transform=l8.transform,
                              profile=l8.profile, latlon=True)

        for day in rrule(DAILY, dtstart=self.start, until=self.end):
            gridmet = GridMet(self.var, date=day, bbox=bounds,
                              target_profile=l8.profile,
                              clip_feature=polygon)
            date_str = datetime.strftime(day, '%Y-%m-%d')
            met_arr = os.path.join(self.grimet_raster_dir,
                                   'met_{}_{}.tif'.format(date_str,
                                                          self.var))
            met = gridmet.get_data_subset(out_filename=met_arr)
            native = os.path.join(self.grimet_raster_dir,
                                  '{}_pet.tif'.format(date_str))

            points_dict = multi_raster_point_extract(local_raster=met_arr,
                                                     geographic_raster=native,
                                                     points=self.scene_points,
                                                     image_profile=l8.profile)
            geo_list, local_list = [], []
            for key, val in points_dict.items():
                geo_list.append(val['geo_val'])
                local_list.append(val['local_val'])
            ratio = mean(geo_list) / mean(local_list)
            print('Ratio on {} of CONUSRaster:LocalRaster calculated is {}.'.format(
                datetime.strftime(day, '%Y-%m-%d'), ratio))
            self.assertAlmostEqual(ratio, 1.0, delta=0.005)
            os.remove(met_arr)


# ========= ANCILLARY FUNCTIONS ==============================================================


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


def multi_raster_point_extract(local_raster, geographic_raster, points,
                               image_profile):
    point_data = {}
    with fopen(points, 'r') as src:
        for feature in src:
            try:
                name = feature['properties']['Name']
            except KeyError:
                name = feature['properties']['FID']
            geo_coords = feature['geometry']['coordinates']
            image_crs = image_profile['crs']
            in_proj = Proj(image_crs)
            utm = in_proj(geo_coords[0], geo_coords[1])
            point_data[name] = {'coords': {'geo': geo_coords, 'utm': utm}}

        with rasopen(local_raster, 'r') as srrc:
            local_arr = srrc.read()
            local_arr = local_arr.reshape(local_arr.shape[1],
                                          local_arr.shape[2])
            local_affine = srrc.transform

        with rasopen(geographic_raster, 'r') as ssrc:
            geo_raster = ssrc.read()
            geo_raster = geo_raster.reshape(geo_raster.shape[1],
                                            geo_raster.shape[2])
            geo_affine = ssrc.transform

        for key, val in point_data.items():
            i, j = val['coords']['utm']
            col, row = ~local_affine * (i, j)
            local_val = local_arr[int(row), int(col)]
            point_data[key]['local_val'] = local_val
            point_data[key]['local_row_col'] = int(row), int(col)

            x, y, z = val['coords']['geo']
            col, row = ~geo_affine * (x, y)
            geo_val = geo_raster[int(row), int(col)]
            point_data[key]['geo_val'] = geo_val
            point_data[key]['geo_row_col'] = int(row), int(col)

        return point_data


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
