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
import click
import logging

from rasterio.rio.options import creation_options

from app.paths import paths
from app.config import Config, check_config
from ssebop.ssebop import SSEBopModel

pp = os.path.realpath(__file__)
sys.path.append(os.path.dirname(os.path.dirname(pp)))

logger = logging.getLogger('ssebop')


@click.group('ssebop')
def ssebop():
    """ Evapotranspiration model for satellite data.
    """
    pass


@click.command('ssebop')
@click.argument('config_path', type=click.Path(exits=False),
                help='Use a configuration file to easily re-run model, type'
                     '"ssebop config" to create a template configuration file')
@click.argument('src_path', type=click.Path(exits=False),
                help='Path containing zipped or unzipped source images')
@click.argument('dst_path', type=click.Path(exists=False),
                help='Path to save results')
@click.argument('dem_path', type=click.Path(exists=False),
                help='Path to DEM file')
@click.argument('albedo_path', type=click.Path(exists=False),
                help='Path to albedo folder')
@click.argument('tmax_path', type=click.Path(exists=False),
                help='Path to max temperature folder')
@click.argument('dt_path', type=click.Path(exists=False),
                help='Path to dT folder', default=None)
@click.argument('eto_path', type=click.Path(exists=False),
                help='Path to reference ET folder', default=None)
@click.option('--verbose', 'v', is_flag=True, default=False)
@click.pass_context
@creation_options
def run_model(ctx, cfg_path=None):
    print('Running Model')
    cfg = Config()
    for runspec in cfg.runspecs:
        paths.build(runspec.input_root, runspec.output_root)

        sseb = SSEBopModel(runspec)
        sseb.configure_run(runspec)
        sseb.run()


def run_help():
    print('help')


def run_commands():
    keys = ('model', 'rew', 'help')
    print('Available Commands: {}'.format(','.join(keys)))


def welcome():
    print('''====================================================================================

    Welcome to SSEBop 
    
====================================================================================
Developed by David Ketchum, 2017
Original Research by Gabriel Senay, 2007, 2013, 2016

Montana Department of Natural Resources and Conservation

Available commands are enumerated using "commands"

For more information regarding a specific command use "help <command>". Replace <command>
with the command of interest.
''')


def run(cfg_path=None):
    # check for a configuration file
    check_config(cfg_path)

    welcome()

    run_model()


if __name__ == '__main__':
    run()
# ============= EOF =============================================
