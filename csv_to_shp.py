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
import csv
from shapely.geometry import Point, mapping
from fiona import collection

schema = {'geometry': 'Point', 'properties': {'description': 'str'}}
with collection(
        "/data01/images/vector_data/agrimet.shp", "w",
        "ESRI Shapefile", schema) as output:
    with open('/data01/images/agrimet/agrimet_sites.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            point = Point(float(row['longitude']), float(row['latitude']))
            output.write({
                'properties': {
                    'description': row['description']
                },
                'geometry': mapping(point)
            })

if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
