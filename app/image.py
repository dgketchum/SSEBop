# ===============================================================================
# Copyright 2018 dgketchum
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

import os
import sys

abspath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(abspath)
from ssebop.ssebop import SSEBopModel


def get_image(image_dir=None, parent_dir=None, image_exists=None,
              image_date=None, satellite=None, path=None, row=None,
              image_id=None):
    spec = {'image_dir': image_dir, 'parent_dir': parent_dir, 'image_exists': image_exists,
            'image_date': image_date, 'satellite': satellite, 'path': path, 'row': row,
            'image_id': image_id}

    sseb = SSEBopModel(spec)
    sseb.configure_run()
    sseb.run(overwrite=False)


if __name__ == '__main__':
    pass
# ========================= EOF ====================================================================
