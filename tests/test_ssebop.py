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

from app.config import Config
from app.paths import paths

from core.ssebop import SSEBopModel


class SSEBopModelTestCase(unittest.TestCase):
    def setUp(self):
        self.config_path = 'tests/ssebop_config_test.yml'
        self.cfg = Config(self.config_path)

    def test_config(self):
        self.assertIsInstance(self.cfg, Config)

    def test_runspecs(self):
        for runspec in self.cfg.runspecs:
            paths.build(runspec.input_root, runspec.output_root)
            self.assertEqual(runspec.k_factor, 1.25)

    def test_instantiate_ssebop(self):
        for runspec in self.cfg.runspecs:
            paths.build(runspec.input_root, runspec.output_root)
            sseb = SSEBopModel(runspec)
            self.assertIsInstance(sseb, SSEBopModel)
            sseb.configure_run(runspec)
            self.assertTrue(sseb._is_configured, True)
            self.assertEqual(sseb._satellite, 'LT5')
            self.assertEqual(runspec.date_range, sseb._date_range)

if __name__ == '__main__':
    unittest.main()

# ===============================================================================
