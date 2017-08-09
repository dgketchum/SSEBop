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
from landsat.download_composer import download_landsat as down

import yaml

from app.paths import paths

DEFAULT_CFG = '''

path: 40
row: 28
root: /path/to/parent_directory
input_root: /path/to/inputs
output_root: /path/to/output

api_key: 'set your Mapzen API Key'

satellite: LT5
year: None
single_date: False
start_date: 4/1/2010
end_date: 11/1/2010
k_factor: 1.25
verify_paths: True

# Add the path relative to /input_root/ or /root/
# They will be joined to input_root.
# Parameters mask and polygon are optional, put None if None
polygons: None
mask: None
'''

DATETIME_FMT = '%Y%m%d'


class RunSpec:
    _obj = None

    path, row = None, None

    root = None
    api_key = None

    year = None
    single_date = False
    start_date = None
    end_date = None

    mask = None
    polygons = None
    satellite = None
    k_factor = None
    verify_paths = None

    def __init__(self, obj):
        self._obj = obj

        attrs = ('path', 'row', 'root',
                 'api_key', 'usgs_creds',
                 'mask', 'polygons',
                 'satellite',
                 'start_date', 'end_date',
                 'k_factor', 'verify_paths',)

        time_attrs = ('start_date', 'end_date')

        for attr in attrs:

            if attr in time_attrs:
                dt_str = str(self._obj.get(attr))
                dt = datetime.strptime(dt_str, DATETIME_FMT)
                setattr(self, attr, dt)

            else:
                setattr(self, attr, self._obj.get(attr))

    @property
    def save_dates(self):
        sd = self._obj.get('save_dates')
        if sd:
            return [datetime.strptime(s, DATETIME_FMT) for s in sd]

    @property
    def date_range(self):
        return (self.start_date,
                self.end_date)

    @property
    def image_list(self):
        super_list = []
        for sat in ['LT5', 'LE7', 'LC8']:
            images = down((self.start_date, self.end_date), satellite=sat,
                          path_row_list=[(self.path, self.row)],
                          dry_run=True)
            if images:
                super_list.append(images)
        try:
            flat_list = [item for sublist in super_list for item in sublist]
            return flat_list
        except TypeError:
            return super_list


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
        print('\n***** The config file {} does not exist. A default one will be written'.format(path))

        with open(path, 'w') as wfile:
            print('-------------- DEFAULT CONFIG -----------------')
            print(DEFAULT_CFG)
            print('-----------------------------------------------')
            wfile.write(DEFAULT_CFG)

        print('***** Please edit the config file at {} and run the model *****\n'.format(
            os.path.join(os.getcwd(), path)))

        sys.exit()

# ============= EOF =============================================
