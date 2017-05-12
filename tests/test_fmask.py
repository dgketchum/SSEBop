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
import numpy as np


class MyTestCase(unittest.TestCase):
    def setUp(self):
        shape = (10, 10)
        true_arr, false_arr = np.full(shape, True, dtype=bool), np.full(shape, False, dtype=bool)


    def tearDown(self):
        pass

    def test_form_fmask(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
