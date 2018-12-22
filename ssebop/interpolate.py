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

from rasterio import open as rasopen
from pandas import read_csv, date_range, DataFrame, to_datetime, merge, notna

from sat_image.warped_vrt import warp_vrt, warp_single_image

DROP = ['SPACECRAFT_ID', 'SENSOR_ID', 'COLLECTION_NUMBER',
        'COLLECTION_CATEGORY', 'SENSING_TIME', 'DATA_TYPE',
        'WRS_PATH', 'WRS_ROW', 'CLOUD_COVER', 'NORTH_LAT',
        'SOUTH_LAT', 'WEST_LON', 'EAST_LON', 'TOTAL_SIZE',
        'BASE_URL', 'Unnamed: 0']

NOT_DROP = ['SCENE_ID', 'PRODUCT_ID']


class Interpolator(object):

    def __init__(self, images, data_dir):
        self.data_dir = data_dir
        self.image_table = images
        self.daily_data = os.path.join(self.data_dir, 'daily_data')

        self.image_table = read_csv(self.image_table, index_col=5,
                                    parse_dates=[5], header=0).drop(columns=DROP)

        etrf_dirs = [os.path.join(self.data_dir, x) for x in self.image_table['SCENE_ID'].values]

        self.image_table['etrf_path'] = [[os.path.join(y, x) for x in os.listdir(y) if x.endswith(
            'etrf.tif')][0] for y in etrf_dirs]

        odx = self.image_table.index
        ndx = date_range(odx.min(), odx.max(), freq='D')
        df = self.image_table.reindex(odx.union(ndx)).reindex(ndx)

        etr_files = [(os.path.join(self.daily_data, x), x.replace('.tif', '')[-10:]) for x in os.listdir(
            self.daily_data) if x.endswith('.tif')]

        etr_files.sort(key=lambda x: x[1])
        series = DataFrame([x[0] for x in etr_files], columns=['etr_path'],
                           index=to_datetime([x[1] for x in etr_files]))

        interp_days = []
        count = 0
        for i, r in df.iterrows():
            if notna(r['SCENE_ID']):
                interp_days.append(0)
                count = 0
            else:
                count += 1
                interp_days.append(count)
        df['interp_days'] = interp_days

        self.base_table = merge(df, series, how='inner', left_index=True, right_index=True)
        self._warp()

    def _warp(self):
        profile = warp_vrt(self.data_dir, return_profile=True)
        if not profile:
            with open(os.path.join(self.data_dir, 'resample_meta.txt')) as f:
                f.read()

        for i, r in self.base_table.iterrows():
            with rasopen(r['etr_path'], 'r') as src:
                #if src.profile != profile:
                    #warp_single_image(r[3], profile=profile)
                warp_single_image(r[2], src.profile)

    def interpolate(self):
        pass


if __name__ == '__main__':
    pass
# ========================= EOF ====================================================================
