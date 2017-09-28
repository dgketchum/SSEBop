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
verify_paths: True
down_images_only: False
'''

DATETIME_FMT = '%Y%m%d'
JULIAN_FMT = '%Y%j'


class Config:
    _obj = None

    path, row = None, None

    root = None
    api_key = None
    runspecs = None
    satellite = None
    start_date = None
    end_date = None
    usgs_creds = None
    verify_paths = None
    down_images_only = None

    def __init__(self, path=None):
        self.load(path=path)

        p, r = str(self.path).zfill(3), str(self.row).zfill(3)
        self.path_row_dir = os.path.join(self.root, '{}_{}'.format(p, r))

        self.set_runspecs()

    def load(self, path=None):
        if path is None:
            path = paths.config

        if isinstance(path, str):
            check_config(path)
            rfile = path
        else:
            rfile = path

        with open(rfile, 'r') as stream:
            try:
                self._obj = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

            attrs = ('path', 'row', 'root',
                     'api_key', 'usgs_creds',
                     'start_date', 'end_date',
                     'satellite',
                     'verify_paths',
                     'down_images_only')

            time_attrs = ('start_date', 'end_date')

            for attr in attrs:

                if attr in time_attrs:
                    dt_str = str(self._obj.get(attr))
                    dt = datetime.strptime(dt_str, DATETIME_FMT)
                    setattr(self, attr, dt)

                else:
                    setattr(self, attr, self._obj.get(attr))

    def set_runspecs(self):

        images = self.get_image_list()

        self.runspecs = [RunSpec(image, self) for image in images]

    def get_image_list(self):

        super_list = []
        images = down((self.start_date, self.end_date), satellite=self.satellite,
                      path_row_list=[(self.path, self.row)],
                      dry_run=True)
        if images:
            super_list.append(images)
            try:
                flat_list = [item for sublist in super_list for item in sublist]
                return flat_list
            except TypeError:
                return super_list
        else:
            raise AttributeError('No images for this time-frame and satellite....')


class RunSpec(object):
    def __init__(self, image, cfg):
        self.image_id = image
        attrs = ('path', 'row',
                 'satellite', 'api_key',
                 'usgs_creds', 'verify_paths',
                 'root',
                 'start_date', 'end_date',
                 'down_images_only')

        for attr in attrs:
            cfg_attr = getattr(cfg, attr)
            setattr(self, attr, cfg_attr)

        self.image_date = date = datetime.strptime(image[9:16], JULIAN_FMT)
        self.parent_dir = os.path.join(cfg.path_row_dir, str(date.year))
        self.image_dir = os.path.join(self.parent_dir, image)


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
