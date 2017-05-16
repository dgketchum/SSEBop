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
import rasterio
import numpy as np

from sat_image import mtl, fmask


class UnmatchedStackGeoError(ValueError):
    pass


class InvalidObjectError(TypeError):
    pass


class LandsatImage(object):
    '''
    Object to process landsat images. The parent class: LandsatImage takes a directory 
    containing untarred files, for now this ingests images that have been downloaded
    from USGS earth explorer, using our Landsat578 package.
    
    '''

    def __init__(self, obj):
        ''' 
        :param obj: Directory containing an unzipped Landsat 5, 7, or 8 image.  This should include at least
        a tif for each band, and a .mtl file.
        '''
        self.obj = obj
        if os.path.isdir(obj):
            self.isdir = True

        self.file_list = os.listdir(obj)
        self.tif_list = [x for x in os.listdir(obj) if x.endswith('.TIF')]
        self.tif_list.sort()

        # parse metadata file into attributes
        # structure: {HEADER: {SUBHEADER: {key(attribute), val(attribute value)}}}
        self.mtl = mtl.parsemeta(obj)
        self.meta_header = list(self.mtl)[0]
        self.super_dict = self.mtl[self.meta_header]

        for key, val in self.super_dict.items():
            for sub_key, sub_val in val.items():
                # print(sub_key.lower(), sub_val)
                setattr(self, sub_key.lower(), sub_val)

        # create numpy nd_array objects for each band
        self.band_list = []
        for i, tif in enumerate(self.tif_list):
            with rasterio.open(os.path.join(self.obj, tif)) as src:
                np_array = src.read()
                # reshape to 2-d array from 3d.shape = (1, x, y)
                shape = np_array.shape
                np_array = np_array.reshape(shape[1], shape[2])

            # set all lower case attributes
            tif = tif.lower()
            front_ind = tif.index('b')
            end_ind = tif.index('.tif')
            att_string = tif[front_ind: end_ind]
            count_att_string = '{}_counts'.format(att_string)
            nan_unset = '{}_nan_unset'.format(att_string)

            setattr(self, att_string, np.where(np_array == 0, np.nan, np_array))

            setattr(self, count_att_string,
                    {'zero': np.count_nonzero(np_array == 0),
                     'non_zero': np.count_nonzero(np_array > 0),
                     'nan': np.count_nonzero(np.isnan(np_array)),
                     'non_nan': np.count_nonzero(~np.isnan(np_array))})

            setattr(self, nan_unset, np_array)

            self.band_list.append(att_string)
            self.band_count = i + 1

        self.solar_zenith = 90. - self.sun_elevation
        self.solar_zenith_rad = self.solar_zenith * np.pi / 180
        self.sun_elevation_rad = self.sun_elevation * np.pi / 180
        self.earth_sun_dist = self.earth_sun_d(self.date_acquired)

    @staticmethod
    def earth_sun_d(dtime):
        """ Earth-sun distance in AU
        
        :param dtime time, e.g. datetime.datetime(2007, 5, 1)
        :type datetime object
        :return float(distance from sun to earth in astronomical units)
        """
        doy = int(dtime.strftime('%j'))
        rad_term = 0.9856 * (doy - 4) * np.pi / 180
        distance_au = 1 - 0.01672 * np.cos(rad_term)
        return distance_au


class Landsat5(LandsatImage):
    def __init__(self, obj):
        LandsatImage.__init__(self, obj)

        self.ex_atm_irrad = (1957.0, 1826.0, 1554.0,
                             1036.0, 215.0, 1e-6, 80.67)

        for i, esun in enumerate(self.ex_atm_irrad, start=1):
            qcal_min = getattr(self, 'quantize_cal_min_band_{}'.format(i))
            qcal_max = getattr(self, 'quantize_cal_max_band_{}'.format(i))
            l_min = getattr(self, 'radiance_minimum_band_{}'.format(i))
            l_max = getattr(self, 'radiance_maximum_band_{}'.format(i))
            qcal = getattr(self, 'b{}'.format(i))
            radiance = ((l_max - l_min) / (qcal_max - qcal_min)) * (qcal - qcal_min) + l_min

            if i != 6:
                toa_reflect = (np.pi * radiance * self.earth_sun_dist ** 2) / (esun * np.cos(
                    self.solar_zenith_rad))
                setattr(self, 'toa_reflectance_band_{}'.format(i), toa_reflect)

            else:
                atsat_bright_temp = 1260.56 / (np.log((607.76 / radiance) + 1))
                setattr(self, 'atsat_bright_band_{}'.format(i), atsat_bright_temp)

    def get_fmask(self):
        mask = fmask.form_fmask(self)
        return mask


class Landsat7(LandsatImage):
    def __init__(self, obj):
        LandsatImage.__init__(self, obj)

        self.ex_atm_irrad = (1969.0, 1840.0, 1551.0, 1044.0,
                             255.700, 1e-6, 1e-6, 82.07, 1368.00)

        for band, esun in zip(self.band_list, self.ex_atm_irrad):
            # use band string attribute to handle 'vcid' instances
            qcal_min = getattr(self, 'quantize_cal_min_band_{}'.format(band.replace('b', '')))
            qcal_max = getattr(self, 'quantize_cal_max_band_{}'.format(band.replace('b', '')))
            l_min = getattr(self, 'radiance_minimum_band_{}'.format(band.replace('b', '')))
            l_max = getattr(self, 'radiance_maximum_band_{}'.format(band.replace('b', '')))
            qcal = getattr(self, '{}'.format(band))
            radiance = ((l_max - l_min) / (qcal_max - qcal_min)) * (qcal - qcal_min) + l_min

            if band not in ['b6_vcid_1', 'b6_vcid_2']:
                toa_reflect = (np.pi * radiance * self.earth_sun_dist ** 2) / (esun * np.cos(
                    self.solar_zenith_rad))
                setattr(self, 'toa_reflectance_band_{}'.format(band.replace('b', '')), toa_reflect)

            else:
                atsat_bright_temp = 1260.56 / (np.log((607.76 / radiance) + 1))
                setattr(self, 'atsat_bright_band_{}'.format(band.replace('b', '')), atsat_bright_temp)

    def get_fmask(self):
        mask = fmask.form_fmask(self)
        return mask


class Landsat8(LandsatImage):
    def __init__(self, obj):
        LandsatImage.__init__(self, obj)

        self.oli_bands = ['1', '2', '3', '4', '5', '6', '7', '8', '9']

        for oli, band in zip(self.oli_bands, self.band_list):
            multi_band_reflect = getattr(self, 'reflectance_mult_band_{}'.format(oli))  # Mp
            reflect_add_band = getattr(self, 'reflectance_add_band_{}'.format(oli))  # Ap
            sun_elevation = getattr(self, 'sun_elevation') * np.pi / 180.  # sea
            dn_array = getattr(self, '{}'.format(band))
            toa_reflect = (((dn_array * multi_band_reflect) + reflect_add_band) / (np.sin(sun_elevation)))
            setattr(self, 'toa_reflectance_band_{}'.format(band.replace('b', '')), toa_reflect)

        for band in ['10', '11']:
            dn_array = getattr(self, 'b{}'.format(band))
            ml = getattr(self, "radiance_mult_band_{}".format(band))
            al = getattr(self, "radiance_add_band_{}".format(band))
            radiance = (dn_array * ml) + al
            # now convert to at-sattelite brightness temperature
            k1 = getattr(self, "k1_constant_band_{}".format(band))
            k2 = getattr(self, "k2_constant_band_{}".format(band))
            atsat_bright_temp = k2 / (np.log((k1 / radiance) + 1))
            setattr(self, 'atsat_bright_band_{}'.format(band.replace('b', '')), atsat_bright_temp)

    def get_fmask(self):
        mask = fmask.Fmask(self)
        fmask_array = mask.get_fmask()
        return fmask_array

# =============================================================================================
