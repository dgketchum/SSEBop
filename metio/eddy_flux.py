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
import json
import requests
from fiona.crs import from_epsg
from fiona import collection
from bs4 import BeautifulSoup as bs
from pandas import read_csv


class FluxSite(object):
    def __init__(self, site_key=None):

        self.ntsg_url_head = 'http://luna.ntsg.umt.edu.'
        self.ntsg_url_middle = '/data/forDavidKetchum/LaThuile/daily/'
        self.fluxdata_org_head = 'http://www.fluxdata.org:8080/SitePages/'
        self.fluxdata_org_middle = 'siteInfo.aspx?'

        self.site_params = ('Site_name',
                            'Latitude',
                            'Longitude',
                            'Elevation',
                            'Mean Annual Temp (degrees C)',
                            'Mean Annual Precip. (mm)',
                            'Years Of Data Available')

        self.json_file = 'metio/data/flux_locations_lathuille.json'

        self.needs_float_conversion = self.site_params[1:-1]

        if os.path.isfile(self.json_file):
            d = self._load_json(self.json_file)
            self.data = d
        else:
            self.build_network_json(outfile=self.json_file,
                                    country_abvs=None)

        self.site_key = site_key

    def build_network_json(self, outfile=None, country_abvs=None):
        """ Get all LaThuile data available.
        Should be on the order of 200+ sites. This web scraper is slow,
        recommended to run it once, save it locally, and use FluxSite.load_json to 
        load it for each use.
        :param country_abvs: list of uppercase country abbreviation strings, 
        i.e., Canada and US: ['CA', 'US']
        :param outfile: Path (incl. filename) to save json, optional
        :return: dict of flux sites by site abbreviation key.
        """
        req_url = '{}{}'.format(self.ntsg_url_head, self.ntsg_url_middle)
        r = requests.request('GET', req_url, stream=True)
        cont = r.content
        soup = bs(cont, 'lxml')
        sample = soup.find_all('a')
        data = {}
        csv_list = []
        first = True
        for a in sample:
            title = a.string.strip()
            site_abv = title[:6]
            country_abv = title[:2]

            if last_site == site_abv:
                first = False

            if first:
                data[site_abv] = {'csv_url': []}
                first = False

            if title.endswith('.csv'):
                csv_location = '{}{}'.format(self.ntsg_url_head, a.attrs['href'])

                if country_abvs:
                    if country_abv in country_abvs:
                        data[site_abv]['csv_url'].append(csv_location)
                else:
                    data[site_abv]['csv_url'].append(csv_location)

            last_site = site_abv

        for key, val in data.items():
            req_url = '{}{}{}'.format(self.fluxdata_org_head,
                                      self.fluxdata_org_middle,
                                      key)
            r = requests.request('GET', req_url)
            cont = r.content
            soup = bs(cont, 'lxml')
            labels = soup.find_all('td', 'label')
            keys = [(i, self._strip_label(k)) for i, k in enumerate(labels) if self._strip_label(k) in self.site_params]
            values = soup.find_all('td', 'value')
            vals = [self._strip_val(i) for i in values]

            for _ in keys:
                ind, sub_key = _[0], _[1]
                if sub_key in self.needs_float_conversion:
                    try:
                        data[key][sub_key] = float(vals[ind])
                    except TypeError:
                        pass
                else:
                    data[key][sub_key] = vals[ind]

        if outfile:
            with open(outfile, 'w') as f:
                json.dump(data, f)

        return data

    def load_site_data(self):
        if not self.site_key:
            raise ValueError('Must provide a valid site key, e.g., "US-FPe"')

        all_site_meta = self._load_json(self.json_file)

        site_metadata = all_site_meta[self.site_key]

        url = site_metadata['csv_loc']

    @staticmethod
    def _strip_val(i):
        try:
            return i.contents[0]
        except IndexError:
            pass

    @staticmethod
    def _strip_label(i):
        return i.contents[0].string.strip().replace(':', '')

    @staticmethod
    def _load_json(json_file):
        with open(json_file) as f:
            d = json.load(f)
            return d

    @staticmethod
    def write_locations_to_shp(site_dict, outfile, epsg='4326'):
        agri_schema = {'geometry': 'Point',
                       'properties': {
                           'site_id': 'str',
                           'Mean Annual Precip. (mm)': 'float',
                           'Mean Annual Temp (degrees C)': 'float',
                           'csv_url': 'str',
                           'Years Of Data Available': 'str'}}

        cord_ref = from_epsg(epsg)
        shp_driver = 'ESRI Shapefile'

        with collection(outfile, mode='w', driver=shp_driver, schema=agri_schema,
                        crs=cord_ref) as output:
            for key, val in site_dict.items():
                try:
                    output.write({'geometry': {'type': 'Point',
                                               'coordinates':
                                                   (site_dict[key]['Longitude'],
                                                    site_dict[key]['Latitude'])},
                                  'properties': {
                                      'site_id': site_dict[key],
                                      'Mean Annual Precip. (mm)': site_dict[key]['Site_name'],
                                      'Mean Annual Temp (degrees C)': site_dict[key]['Site_name'],
                                      'csv_url': site_dict[key]['Site_name'],
                                      'Years Of Data Available': site_dict[key]['Years Of Data Available']}})
                except KeyError:
                    pass


if __name__ == '__main__':
    flux = FluxSite()
    flux.build_network_json()

# ========================= EOF ====================================================================
