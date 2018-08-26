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

try:
    import StringIO
except ImportError:
    from io import StringIO

from app.config import Config


class MyTestCase(unittest.TestCase):
    def setUp(self):
        config_text = '''
        input_root: /path/to/data
        output_root: /path/to/output
        start_date: 12/1/2013
        end_date: 12/31/2013
        mask: masks/please_set_me.tif
        polygons: poly/please_set_me.shp
        satellite: LT5
        image_directory: /path/to/landsat_scenes
        esun_table: /path/to/earth_sun_distance_table
        k_factor: 1.25
        dem_folder: /path/to/dem
        use_verify_paths: True
        
        '''
        path = StringIO(config_text)
        self._cfg = Config(path)

    def tearDown(self):
        pass

    def test_run_specs(self):
        self.assertEqual(len(self._cfg.runspecs), 1)

    def test_start_year(self):
        r = self._cfg.runspecs[0]
        s, e = r.date_range
        self.assertEqual(s.year, 2013)

    def test_end_year(self):
        r = self._cfg.runspecs[0]
        s, e = r.date_range
        self.assertEqual(e.year, 2013)

if __name__ == '__main__':
    unittest.main()

# ===============================================================================
