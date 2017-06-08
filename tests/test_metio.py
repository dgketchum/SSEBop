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
from future.standard_library import hooks

with hooks():
    import urllib.parse as parse
from datetime import datetime
from metio.misc import BBox
from metio.thredds import GridMet

from netCDF4 import Dataset


class TestGridMet(unittest.TestCase):
    def setUp(self):
        self.bbox = BBox(west_lon=-116.4, east_lon=-103.0,
                         south_lat=44.3, north_lat=49.1)

        self.vars = ['pr', 'pet', 'not_a_var']
        self.test_url_str = 'http://thredds.northwestknowledge.net:8080/thredds/ncss/MET/pet/pet_2011.nc?' \
                            'var=potential_evapotranspiration&north=49.1&west=-116.4&east=-103.0&south=44.3&' \
                            '&horizStride=1&time_start=2011-01-01T00%3A00%3A00Z&' \
                            'time_end=2011-12-31T00%3A00%3A00Z&timeStride=1&accept=netcdf4'

        self.start = datetime(2011, 1, 1)
        self.end = datetime(2011, 12, 31)
        self.gridmet = GridMet(self.vars, start=self.start, end=self.end,
                               bbox=self.bbox)

    def test_instantiate(self):
        self.assertIsInstance(self.gridmet, GridMet)

    def test_url_query(self):
        url = self.gridmet._build_url('pet')
        code_parse, test_parse = parse.urlparse(url).query, parse.urlparse(self.test_url_str).query
        code_d, test_d = parse.parse_qs(code_parse), parse.parse_qs(test_parse)
        self.assertEqual(code_d, test_d)

    def test_get_data(self):
        self.gridmet.get_data()
        self.assertIsInstance(self.gridmet.get_data(), Dataset)


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
