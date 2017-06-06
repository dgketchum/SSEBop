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

# checkout rasterio.rio.options creation_options for mixins todo

from app.paths import paths
from app.config import Config, check_config
from core.ssebop import SSEBopModel

pp = os.path.realpath(__file__)
sys.path.append(os.path.dirname(os.path.dirname(pp)))

logger = logging.getLogger('core')


@click.group()
def cli():
    pass


@click.command('mkconfig', help='Create a template configuration file')
@click.option('--path', '-p', 'path', default=None, type=click.Path(exists=False, writable=True))
def configure(path):
    """ Create a template configuration file.
    
    :param name: Name of ssebop_config file, :type str
    :param path: Output path and filename for template configuration, if this argument is omitted,
     generic file name will bu used and output saved to root directory. :type str
    :return: None 
    """

    if path:
        click.echo('Creating a config file "{}" '.format(path))
        check_config(path=path)

    else:
        click.echo('Creating a config file "ssebop_config.yml" and sending to home directory')
        check_config(path=None)


@click.command('run', help='Run the SSEBop model')
@click.argument('config_path', default=None, type=click.Path(exists=True))
def run(config_path):
    """ Run the SSEBop model.
    
    :param config_path: Path to a configuration file, if the file does not exist
                     a blank template will be created at your root directory. :type str
    :return: None
    """

    click.echo('Configuration file: {}'.format(config_path))
    click.echo('Running Model')

    cfg = Config(config_path)
    for runspec in cfg.runspecs:
        paths.build(runspec.input_root, runspec.output_root)

        welcome()

        sseb = SSEBopModel(runspec)
        sseb.configure_run(runspec)
        sseb.run()


cli.add_command(configure)
cli.add_command(run)


def welcome():
    print(
        '''
        =======================================================================================
        
            Welcome to SSEBop 
            
        =======================================================================================
        Developed by David Ketchum, 2017
        Original Research by Gabriel Senay, 2007, 2013, 2016
        
        Montana Department of Natural Resources and Conservation
        
        Available commands are enumerated using "ssebop"
        
        For more information regarding a specific command use "help <command>". Replace <command>
        with the command of interest.
        ''')

# ============= EOF =============================================
