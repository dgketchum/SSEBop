# ===============================================================================
# Copyright 2018 dgketchum
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

from pandas import read_csv, date_range


def reform_images_table(csv):
    csv = read_csv(csv, index_col=5, parse_dates=[5], header=0)
    odx = csv.index
    ndx = date_range(odx.min(), odx.max(), freq='D')
    df = csv.reindex(odx.union(ndx)).interpolate('index').reindex(ndx)
    pass


if __name__ == '__main__':
    pass
# ========================= EOF ====================================================================
