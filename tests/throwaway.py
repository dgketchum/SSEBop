# =============================================================================================
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
# =============================================================================================

import os
from sat_image.fmask import Fmask
from sat_image.image import Landsat8


def test_get_potential_cloud_layer():
    dirname_cloud = '/data01/PycharmProjects/ssebop/tests/data/ssebop_test/lc8/038_027/2014/LC80380272014227LGN01'
    image = Landsat8(dirname_cloud)
    f = Fmask(image)
    combo = f.cloud_mask(min_filter=(3, 3), max_filter=(40, 40), combined=True, clear_value=1)
    home = os.path.expanduser('~')
    outdir = os.path.join(home, 'images', 'sandbox')
    f.save_array(combo, os.path.join(outdir, 'combo_mask.tif'))


if __name__ == '__main__':
    test_get_potential_cloud_layer()

# ========================= EOF ====================================================================
