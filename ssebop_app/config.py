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
from landsat.google_download import GoogleDownload

import yaml

from ssebop_app.paths import paths

DEFAULT_CFG = '''
# SSEBop config file
path: 39
row: 27
root: /home/dgketchum/IrrigationGIS/western_states_irrgis/MT/
output_root: /home/dgketchum/IrrigationGIS/western_states_irrgis/MT/39/27/2013/
satellite: 8
start_date: 20130401
end_date: 20131001
verify_paths: True
agrimet_corrected: True
down_images_only: False
use_existing_images: True
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

        p, r, s = str(self.path), str(self.row), str(self.start_date.year)
        self.path_row_dir = os.path.join(self.root, p, r)

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
                     'start_date', 'end_date',
                     'satellite',
                     'verify_paths',
                     'down_images_only',
                     'agrimet_corrected',
                     'use_existing_images')

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

        if self.down_images_only:

            for spec in self.runspecs:
                pass

            self.runspecs = None

    def get_image_list(self, max_cloud_pct=20):

        super_list = []
        s = datetime.strftime(self.start_date, '%Y-%m-%d')
        e = datetime.strftime(self.end_date, '%Y-%m-%d')
        sat_key = int(self.satellite[-1])
        g = GoogleDownload(start=s, end=e, satellite=sat_key,
                           path=self.path, row=self.row, max_cloud_percent=max_cloud_pct)
        images = g.scene_ids
        if images:
            super_list.append(images)
            try:
                flat_list = [item for sublist in super_list for item in sublist]
                flat_list.reverse()
                return flat_list
            except TypeError:
                super_list.reverse()
                return super_list
        else:
            raise AttributeError('No images for this time-frame and satellite....')


class RunSpec(object):
    def __init__(self, image, cfg):
        self.image_id = image
        attrs = ('path', 'row',
                 'satellite',
                 'api_key',
                 'verify_paths',
                 'root',
                 'start_date',
                 'end_date',
                 'down_images_only',
                 'agrimet_corrected',
                 'use_existing_images')

        for attr in attrs:
            cfg_attr = getattr(cfg, attr)
            setattr(self, attr, cfg_attr)

        self.image_date = date = datetime.strptime(image[9:16], JULIAN_FMT)
        self.parent_dir = os.path.join(cfg.path_row_dir, str(date.year))
        self.image_dir = os.path.join(self.parent_dir, image)
        pseudo_spec = {'path': self.path,
                       'row': self.row,
                       'start_date': self.start_date,
                       'end_date': self.end_date,
                       'image_dir': self.image_dir,
                       'root': self.root,
                       'agrimet_corrected': self.agrimet_corrected,
                       'use_existing_images': self.use_existing_images}
        self.image_exists = paths.configure_project_dirs(pseudo_spec)


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
