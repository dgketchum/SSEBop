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
import os
from pandas import read_csv, date_range, Series


DROP = ['SPACECRAFT_ID', 'SENSOR_ID', 'COLLECTION_NUMBER',
        'COLLECTION_CATEGORY', 'SENSING_TIME', 'DATA_TYPE',
        'WRS_PATH', 'WRS_ROW', 'CLOUD_COVER', 'NORTH_LAT',
        'SOUTH_LAT', 'WEST_LON', 'EAST_LON', 'TOTAL_SIZE',
        'BASE_URL']

NOT_DROP = ['SCENE_ID', 'PRODUCT_ID']


def reform_images_table(csv, daily_data):
    csv = read_csv(csv, index_col=5, parse_dates=[5], header=0)
    odx = csv.index
    ndx = date_range(odx.min(), odx.max(), freq='D')
    df = csv.reindex(odx.union(ndx)).reindex(ndx).drop(columns=DROP)
    _files = [(os.path.join(daily_data, x), x.replace('.tif', '')[-10:]) for x in os.listdir(daily_data)]
    _files.sort(key=lambda x: x[1])
    series = Series()

    pass


def interpolate():
    pass


if __name__ == '__main__':
    pass
# ========================= EOF ====================================================================
