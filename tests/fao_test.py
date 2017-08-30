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

from metio import fao

#: Solar constant [ MJ m-2 min-1]
SOLAR_CONSTANT = 0.0820

# Stefan Boltzmann constant [MJ K-4 m-2 day-1]
STEFAN_BOLTZMANN_CONSTANT = 0.000000004903
"""Stefan Boltzmann constant [MJ K-4 m-2 day-1]"""

SPECIFIC_HEAT_AIR = 1.013
""" Specific heat of air at constant temperature [KJ kg-1 degC-1]"""

GAS_CONSTANT = 287.
""" 287 J kg-1 K--1"""

TEST_CANOPY_RESISTANCE = 110.
""" Senay (2013; p. 583) [s m-1]"""


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.doy = 80

    def tearDown(self):
        pass

    def test_avp_from_tmin(self):
        self.assertEqual(True, False)

    def test_sol_dec(self):
        self.assertEqual(True, False)

    def test_sunset_hour_angle(self):
        self.assertEqual(True, False)

    def test_et_rad(self):
        self.assertEqual(True, False)

    def test_cs_rad(self):
        self.assertEqual(True, False)

    def test_inv_rel_dist_earth_sun(self):
        self.assertEqual(True, False)

    def test_sol_rad_from_t(self):
        self.assertEqual(True, False)

    def test_air_density(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
