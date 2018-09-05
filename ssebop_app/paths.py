# ===============================================================================
# Copyright 2017 ross, dgketchum
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

from __future__ import print_function

import os
import sys

from dateutil.rrule import rrule, YEARLY


class PathsNotSetExecption(BaseException):
    def __str__(self):
        return 'paths.build(in_root, out_root) needs to be called before the model will run'


class Paths:
    ssebop_root = None
    mask = None
    polygons = None

    def __init__(self):
        self._is_set = False
        self.config = os.path.join(os.path.expanduser('~'), 'ssebop_CONFIG.yml')

    def build(self, parent_root):
        self._is_set = True
        self.ssebop_root = parent_root

    def verify(self):

        if not os.path.exists(self.ssebop_root):
            print('NOT FOUND {}'.format(self.ssebop_root))
            sys.exit(1)

    @staticmethod
    def configure_project_dirs(spec):

        p, r, s = str(spec['path']), str(spec['row']), str(spec['start_date'].year)
        path_row_dir = os.path.join(spec['root'], p, r, s)

        if not os.path.exists(path_row_dir):
            os.mkdir(path_row_dir)
        start, end = spec['start_date'], spec['end_date']

        for dt in rrule(YEARLY, dtstart=start, until=end):
            year_dir = os.path.join(path_row_dir, str(dt.year))
            if not os.path.exists(year_dir):
                os.mkdir(year_dir)

        image_path = spec['image_dir']
        if os.path.exists(image_path):
            if len(os.listdir(image_path)) > 2:
                return True
            else:
                return False
        elif spec['use_existing_images']:
            pass
        else:
            os.mkdir(image_path)
            return False

    def is_set(self):
        return self._is_set


paths = Paths()

# ============= EOF =========================================================
