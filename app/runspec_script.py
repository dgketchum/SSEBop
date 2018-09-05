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

import os

from app.config import Config, paths
from app.cli import welcome
from ssebop.ssebop import SSEBopModel


def run_ssebop(cfg_path):
    cfg = Config(cfg_path)
    welcome()
    for runspec in cfg.runspecs:
        paths.build(runspec.root)

        sseb = SSEBopModel(runspec)
        sseb.configure_run()
        sseb.run(overwrite=False)


if __name__ == '__main__':
    home = os.path.expanduser('~')
    root = os.path.join(home, 'PycharmProjects', 'ssebop')
    config_path = os.path.join(root, 'ssebop_config_lc8.yml')
    run_ssebop(config_path)

# ========================= EOF ====================================================================
