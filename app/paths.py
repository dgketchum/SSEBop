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

    def set_mask_path(self, path):
        self.mask = path

    def set_polygons_path(self, path):
        self.polygons = path

    def verify(self):

        if not os.path.exists(self.ssebop_root):
            print('NOT FOUND {}'.format(self.ssebop_root))
            sys.exit(1)

        if self.polygons:
            if not os.path.exists(self.ssebop_root):
                print('NOT FOUND {}'.format(self.ssebop_root))
                sys.exit(1)

        if self.mask:
            if not os.path.exists(self.ssebop_root):
                print('NOT FOUND {}'.format(self.ssebop_root))
                sys.exit(1)

    def configure_project_dirs(self, runspec):

        p, r = str(runspec.path).zfill(3), str(runspec.row).zfill(3)
        path_row_dir = os.path.join(self.ssebop_root, '{}_{}'.format(p, r))

        if not os.path.exists(path_row_dir):
            os.mkdir(path_row_dir)
        start, end = runspec.start_date, runspec.end_date

        for dt in rrule(YEARLY, dtstart=start, until=end):
            year_dir = os.path.join(path_row_dir, str(dt.year))
            if not os.path.exists(year_dir):
                os.mkdir(year_dir)

        image_path = runspec.image_dir
        if os.path.exists(image_path):
            if len(os.listdir(image_path)) > 2:
                return True
            else:
                return False

        else:
            os.mkdir(image_path)
            return False

    def is_set(self):
        return self._is_set


paths = Paths()

# ============= EOF =========================================================
