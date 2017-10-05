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

from bounds.bounds import GeoBounds
from dem.dem import MapzenDem
from sat_image.image import Landsat8


class MapzenDemTestCase(unittest.TestCase):
    def setUp(self):
        self.bbox = GeoBounds(west_lon=-116.5, east_lon=-111.0,
                              south_lat=44.3, north_lat=47.)
        self.api_key = 'mapzen-JmKu1BF'
        self.dir_name_LC8 = '/data01/images/sandbox/ssebop_analysis/' \
                            '038_027/2014/LC80380272014227LGN01'

    def test_dem(self):
        l8 = Landsat8(self.dir_name_LC8)
        polygon = l8.get_tile_geometry()
        profile = l8.rasterio_geometry

        dem = MapzenDem(zoom=10, bounds=l8.bounds, target_profile=profile,
                        clip_object=polygon,
                        api_key=self.api_key)

        elev = dem.terrain(attribute='elevation',
                           out_file='/data01/images/sandbox/'
                                    'ssebop_testing/mapzen_'
                                    '{}_{}.tif'.format(l8.target_wrs_path,
                                                       l8.target_wrs_row))
        self.assertEqual(elev.shape, (1, 7429, 8163))

        aspect = dem.terrain(attribute='aspect')
        self.assertEqual(aspect.shape, (7429, 8163))

        slope = dem.terrain(attribute='slope')
        self.assertEqual(slope.shape, (1, 7429, 8163))


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
