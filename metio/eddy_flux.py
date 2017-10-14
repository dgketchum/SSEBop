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

import requests
from bs4 import BeautifulSoup as bs
import json


class FluxSite(object):
    def __init__(self):

        self.ntsg_url_head = 'http://luna.ntsg.umt.edu.'
        self.ntsg_url_middle = '/data/forDavidKetchum/LaThuile/daily/'
        self.fluxdata_org_head = 'http://www.fluxdata.org:8080/SitePages/'
        self.fluxdata_org_middle = 'siteInfo.aspx?'

        self.site_keys = ('Site_name',
                          'Latitude',
                          'Longitude',
                          'Elevation',
                          'Mean Annual Temp (degrees C)',
                          'Mean Annual Precip. (mm)',
                          'Years Of Data Available')
        self.needs_conversion = self.site_keys[1:-1]

    def load_json(self):
        pass

    def build_data_all_sites(self, outfile=None, country_abvs=None):
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
        for a in sample:
            title = a.string.strip()
            if title.endswith('.csv'):
                csv_location = '{}{}'.format(self.ntsg_url_head, a.attrs['href'])
                site_abv = title[:6]
                country_abv = title[:2]

                if country_abvs:
                    if country_abv in country_abvs:
                        data[site_abv] = {'csv_loc': csv_location}
                else:
                    data[site_abv] = {'csv_loc': csv_location}

        for key, val in data.items():
            req_url = '{}{}{}'.format(self.fluxdata_org_head,
                                      self.fluxdata_org_middle,
                                      key)
            r = requests.request('GET', req_url)
            cont = r.content
            soup = bs(cont, 'lxml')
            labels = soup.find_all('td', 'label')
            keys = [(i, self._strip_label(k)) for i, k in enumerate(labels) if self._strip_label(k) in self.site_keys]
            values = soup.find_all('td', 'value')
            vals = [self._strip_val(i) for i in values]

            for _ in keys:
                ind, sub_key = _[0], _[1]
                if sub_key in self.needs_conversion:
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

    @staticmethod
    def _strip_val(i):
        try:
            return i.contents[0]
        except IndexError:
            pass

    @staticmethod
    def _strip_label(i):
        return i.contents[0].string.strip().replace(':', '')


if __name__ == '__main__':
    flux = FluxSite()
    flux.build_data_all_sites()

# ========================= EOF ====================================================================
