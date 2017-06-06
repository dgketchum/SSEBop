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
from datetime import datetime

import yaml

from app.paths import paths

DEFAULT_CFG = '''
        input_root: /path/to/data
        output_root: /path/to/output
        start_date: 12/1/2013
        end_date: 12/31/2013
        mask: masks/please_set_me.tif
        satellite: LT5
        image_directory: /path/to/landsat_scenes
        k_factor: 1.25
        dem_folder: /path/to/dem
        max_temp_folder: 
        dt_folder:
        eto_folder:
        use_verify_paths: True
        '''

DATETIME_FMT = '%m/%d/%Y'


class RunSpec:
    _obj = None
    dem_name = None
    mask = None
    polygons = None
    input_root = None
    output_root = None
    output_path = None
    use_verify_paths = None

    def __init__(self, obj):
        self._obj = obj
        attrs = ('mask', 'polygons', 'input_root', 'output_root',
                 'output_path', 'use_verify_paths', 'dem_name')

        for attr in attrs:
            setattr(self, attr, self._obj.get(attr))

    @property
    def save_dates(self):
        sd = self._obj.get('save_dates')
        if sd:
            return [datetime.strptime(s, DATETIME_FMT) for s in sd]

    @property
    def date_range(self):
        obj = self._obj
        if 'start_year' in obj:
            return (datetime(obj['start_year'],
                             obj['start_month'],
                             obj['start_day']),
                    datetime(obj['end_year'],
                             obj['end_month'],
                             obj['end_day']))
        else:
            return (datetime.strptime(obj['start_date'], DATETIME_FMT),
                    datetime.strptime(obj['end_date'], DATETIME_FMT))


class Config:
    runspecs = None

    def __init__(self, path=None):
        self.load(path=path)

    def load(self, path=None):
        if path is None:
            path = paths.config

        if isinstance(path, str):
            check_config(path)
            rfile = open(path, 'r')
        else:
            rfile = path

        self.runspecs = [RunSpec(doc) for doc in yaml.load_all(rfile)]
        rfile.close()


def check_config(path=None):
    if path is None:
        path = paths.config

    if not os.path.isfile(path):
        print('***** The config file {} does not exist. A default one will be written'.format(path))

        with open(path, 'w') as wfile:
            print('-------------- DEFAULT CONFIG -----------------')
            print(DEFAULT_CFG)
            print('-----------------------------------------------')
            wfile.write(DEFAULT_CFG)

        print('***** Please edit the config file at {} and rerun the model'.format(path))
        sys.exit()

# ============= EOF =============================================
