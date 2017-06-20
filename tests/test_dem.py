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

from dem.dem import Dem
from metio.misc import BBox
from dem.collect import tiles, download


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.bbox = BBox(west_lon=-116.5, east_lon=-111.0,
                         south_lat=44.3, north_lat=47.)
        self.dem = Dem(self.bbox)
        self.zoom = 10
        self.api_key = 'mapzen-JmKu1BF'

    def test_tiles(self):
        bb = self.bbox
        tls = tiles(self.zoom, bb.south, bb.east, bb.north, bb.west)
        self.assertEqual(tls[0], (10, 180, 360))

    def test_downlaod(self):
        bb = self.bbox
        tls = tiles(self.zoom, bb.south, bb.east, bb.north, bb.west)
        arr, geo = download(tls, self.api_key)
        self.assertEqual(arr.shape, (1, 10, 10))

    def test_gibs(self):
        self.assertIsInstance(self.dem, Dem)
        array, geo = self.dem.gibs()
        self.dem.save(array, geo, os.path.join(os.path.expanduser('~'), 'images', 'sandbox', 'dem.tif'))
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
