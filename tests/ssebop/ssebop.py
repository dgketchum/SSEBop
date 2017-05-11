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

from __future__ import print_function

import fmask

from app.paths import paths, PathsNotSetExecption

K_FACTOR = 1.25


class SSEBopModel(object):
    _date_range = None

    def __init__(self, cfg):

        if not paths.is_set():
            raise PathsNotSetExecption

        self._cfg = cfg

        paths.set_polygons_path(cfg.polygons)
        paths.set_mask_path(cfg.mask)

        if cfg.use_verify_paths:
            paths.verify()

        self._info('Constructing/Initializing SSEBop...')
        # self._constants = set_constants()

    def configure_run(self, runspec):

        self._info('Configuring SSEBop run')

        self._date_range = runspec.date_range

        print('----------- CONFIGURATION --------------')
        for attr in 'date_range':
            print('{:<20x}{}'.format(attr, getattr(self, '_{}'.format(attr))))

    def run(self):
        pass

    @staticmethod
    def _info(msg):
        print('---------------------------------------')
        print(msg)
        print('---------------------------------------')

    @staticmethod
    def _debug(msg):
        print('%%%%%%%%%%%%%%%% {}'.format(msg))

# ========================= EOF ====================================================================
