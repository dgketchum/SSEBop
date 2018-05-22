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
        self.doy = 246
        self.elevation = 1800
        self.tmin = 19.1
        self.tmax = 25.1
        self.latitude = -0.35
        self.albedo = 0.23

    def tearDown(self):
        pass

    def test_atm_pressure(self):
        p = fao.atm_pressure(self.elevation)
        self.assertAlmostEqual(p, 81.8, delta=0.05)

    def test_avp_from_tmin(self):
        avp = fao.avp_from_tmin(self.tmin)
        self.assertAlmostEqual(avp, 2.21, delta=0.05)

    def test_eq_et_rad(self):
        ird = fao.inv_rel_dist_earth_sun(day_of_year=187)
        sol_dec = fao.sol_dec(day_of_year=187)
        sha = fao.sunset_hour_angle(latitude=0.785, sol_dec=sol_dec)
        ext_rad = fao.et_rad(latitude=0.785, sol_dec=sol_dec, sha=sha, ird=ird)
        self.assertAlmostEqual(41.37, ext_rad, delta=0.1)

    def test_et_rad(self):
        ird = fao.inv_rel_dist_earth_sun(self.doy)
        self.assertAlmostEqual(ird, 0.985, delta=0.001)
        sol_dec = fao.sol_dec(self.doy)
        self.assertAlmostEqual(sol_dec, 0.120, delta=0.001)
        sha = fao.sunset_hour_angle(self.latitude, sol_dec)
        self.assertAlmostEqual(sha, 1.527, delta=0.001)
        ext_rad = fao.et_rad(self.latitude, sol_dec, sha, ird)
        self.assertAlmostEqual(ext_rad, 32.2, delta=0.1)

    def test_net_longwave(self):
        nl = fao.net_lw_radiation(self.tmin, self.tmax, self.doy, self.elevation,
                                  self.latitude)
        self.assertAlmostEqual(nl, 1.59, delta=0.05)

    def test_net_shortwave(self):
        sw = fao.net_sw_radiation(self.elevation, self.albedo, self.doy, self.latitude)
        self.assertAlmostEqual(sw, 19.47, delta=0.015)

if __name__ == '__main__':
    unittest.main()

# ===============================================================================
