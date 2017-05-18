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
from sat_image import mtl


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
                print(sub_key.lower(), sub_val)
                setattr(self, sub_key.lower(), sub_val)
        self.satellite = self.landsat_scene_id[:3]
        # create numpy nd_array objects for each band
        self.band_list = []
        for i, tif in enumerate(self.tif_list):
            with rasterio.open(os.path.join(self.obj, tif)) as src:
                dn_array = src.read(1)

            # set all lower case attributes
            tif = tif.lower()
            front_ind = tif.index('b')
            end_ind = tif.index('.tif')
            att_string = tif[front_ind: end_ind]
            count_att_string = '{}_counts'.format(att_string)
            setattr(self, att_string, dn_array)

            setattr(self, count_att_string,
                    {'zero': np.count_nonzero(dn_array == 0),
                     'non_zero': np.count_nonzero(dn_array > 0),
                     'nan': np.count_nonzero(np.isnan(dn_array)),
                     'non_nan': np.count_nonzero(~np.isnan(dn_array))})

            self.band_list.append(att_string)
            self.band_count = i + 1

            if i == 0:
                # get rasterio metadata/geospatial reference for one tif
                rasterio_str = 'rasterio_geometry'.format(att_string)
                meta = src.meta.copy()
                setattr(self, rasterio_str, meta)
                self.shape = dn_array.shape

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

        if self.satellite != 'LT5':
            raise ValueError('Must init Landsat5 object with Landsat5 data, not {}'.format(self.satellite))

        self.ex_atm_irrad = (1957.0, 1826.0, 1554.0,
                             1036.0, 215.0, 1e-6, 80.67)

    def radiance(self, band):
        qcal_min = getattr(self, 'quantize_cal_min_band_{}'.format(band))
        qcal_max = getattr(self, 'quantize_cal_max_band_{}'.format(band))
        l_min = getattr(self, 'radiance_minimum_band_{}'.format(band))
        l_max = getattr(self, 'radiance_maximum_band_{}'.format(band))
        qcal = getattr(self, 'b{}'.format(band))
        rad = ((l_max - l_min) / (qcal_max - qcal_min)) * (qcal - qcal_min) + l_min

        return rad

    def brightness_temp(self, band):

        if band in [1, 2, 3, 4, 5, 7]:
            raise ValueError('LT5 reflectance must be band 6')

        k1 = getattr(self, 'k1_constant_band_{}'.format(band))
        k2 = getattr(self, 'k2_constant_band_{}'.format(band))
        rad = self.radiance(band)
        brightness = k1 / (np.log((k2 / rad) + 1))

        return brightness

    def reflectance(self, band):

        if band == 6:
            raise ValueError('LT5 reflectance must be other than  band 6')

        rad = self.radiance(band)
        esun = self.ex_atm_irrad[band - 1]
        toa_reflect = (np.pi * rad * self.earth_sun_dist ** 2) / (esun * np.cos(self.solar_zenith_rad))

        return toa_reflect


class Landsat7(LandsatImage):
    def __init__(self, obj):
        LandsatImage.__init__(self, obj)

        if self.satellite != 'LE7':
            raise ValueError('Must init Landsat7 object with Landsat5 data, not {}'.format(self.satellite))

        self.ex_atm_irrad = (1969.0, 1840.0, 1551.0, 1044.0,
                             255.700, 1e-6, 1e-6, 82.07, 1368.00)

    def radiance(self, band):
        qcal_min = getattr(self, 'quantize_cal_min_band_{}'.format(band))
        qcal_max = getattr(self, 'quantize_cal_max_band_{}'.format(band))
        l_min = getattr(self, 'radiance_minimum_band_{}'.format(band))
        l_max = getattr(self, 'radiance_maximum_band_{}'.format(band))
        qcal = getattr(self, 'b{}'.format(band))
        rad = ((l_max - l_min) / (qcal_max - qcal_min)) * (qcal - qcal_min) + l_min
        return rad

    def brightness_temp(self, band='vcid_1'):

        if band in [1, 2, 3, 4, 5, 7, 8]:
            raise ValueError('LE7 reflectance must be either vcid_1 or vcid_2')

        k1 = getattr(self, 'k1_constant_band_6_{}'.format(band))
        k2 = getattr(self, 'k2_constant_band_6_{}'.format(band))
        rad = self.radiance(band)
        brightness = k1 / (np.log((k2 / rad) + 1))
        return brightness

    def reflectance(self, band):

        if band in ['b6_vcid_1', 'b6_vcid_2']:
            raise ValueError('LE7 reflectance must be either b6_vcid_1 or b6_vcid_2')

        rad = self.radiance(band)
        esun = self.ex_atm_irrad[band - 1]
        toa_reflect = (np.pi * rad * self.earth_sun_dist ** 2) / (esun * np.cos(self.solar_zenith_rad))
        return toa_reflect


class Landsat8(LandsatImage):
    def __init__(self, obj):
        LandsatImage.__init__(self, obj)

        self.oli_bands = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def brightness_temp(self, band):
        """Calculate brightness temperature of Landsat 8
    as outlined here: http://landsat.usgs.gov/Landsat8_Using_Product.php

    T = K2 / np.log((K1 / L)  + 1)

    and

    L = ML * Q + AL

    where:
        T  = At-satellite brightness temperature (degrees kelvin)
        L  = TOA spectral radiance (Watts / (m2 * srad * mm))
        ML = Band-specific multiplicative rescaling factor from the metadata
             (RADIANCE_MULT_BAND_x, where x is the band number)
        AL = Band-specific additive rescaling factor from the metadata
             (RADIANCE_ADD_BAND_x, where x is the band number)
        Q  = Quantized and calibrated standard product pixel values (DN)
             (ndarray img)
        K1 = Band-specific thermal conversion constant from the metadata
             (K1_CONSTANT_BAND_x, where x is the thermal band number)
        K2 = Band-specific thermal conversion constant from the metadata
             (K1_CONSTANT_BAND_x, where x is the thermal band number)

    Returns
    --------
    ndarray:
        float32 ndarray with shape == input shape
    """
        if band in self.oli_bands:
            raise ValueError('Landsat 8 brightness should be TIRS band (i.e. 10 or 11)')

        k1 = getattr(self, 'k1_constant_band_{}'.format(band))
        k2 = getattr(self, 'k2_constant_band_{}'.format(band))
        rad = self.radiance(band)
        bt = k2 / np.log((k1 / rad) + 1)

        return bt

    def reflectance(self, band):
        """Calculate top of atmosphere reflectance of Landsat 8
        as outlined here: http://landsat.usgs.gov/Landsat8_Using_Product.php
    
        R_raw = MR * Q + AR
    
        R = R_raw / cos(Z) = R_raw / sin(E)
    
        Z = 90 - E (in degrees)
    
        where:
    
            R_raw = TOA planetary reflectance, without correction for solar angle.
            R = TOA reflectance with a correction for the sun angle.
            MR = Band-specific multiplicative rescaling factor from the metadata
                (REFLECTANCE_MULT_BAND_x, where x is the band number)
            AR = Band-specific additive rescaling factor from the metadata
                (REFLECTANCE_ADD_BAND_x, where x is the band number)
            Q = Quantized and calibrated standard product pixel values (DN)
            E = Local sun elevation angle. The scene center sun elevation angle
                in degrees is provided in the metadata (SUN_ELEVATION).
            Z = Local solar zenith angle (same angle as E, but measured from the
                zenith instead of from the horizon).
    
        Returns
        --------
        ndarray:
            float32 ndarray with shape == input shape
    
        """
        if band not in self.oli_bands:
            raise ValueError('Landsat 8 reflectance should OLI band (i.e. 1-8)')

        elev = getattr(self, 'sun_elevation')
        dn = getattr(self, 'b{}'.format(band))
        mr = getattr(self, 'reflectance_mult_band_{}'.format(band))
        ar = getattr(self, 'reflectance_add_band_{}'.format(band))

        if elev < 0.0:
            raise ValueError("Sun elevation must be nonnegative "
                             "(sun must be above horizon for entire scene)")

        rf = ((mr * dn.astype(np.float32)) + ar) / np.sin(np.deg2rad(elev))

        return rf

    def radiance(self, band):
        """Calculate top of atmosphere radiance of Landsat 8
        as outlined here: http://landsat.usgs.gov/Landsat8_Using_Product.php
    
        L = ML * Q + AL
    
        where:
            L  = TOA spectral radiance (Watts / (m2 * srad * mm))
            ML = Band-specific multiplicative rescaling factor from the metadata
                 (RADIANCE_MULT_BAND_x, where x is the band number)
            AL = Band-specific additive rescaling factor from the metadata
                 (RADIANCE_ADD_BAND_x, where x is the band number)
            Q  = Quantized and calibrated standard product pixel values (DN)
                 (ndarray img)
    
        Returns
        --------
        ndarray:
            float32 ndarray with shape == input shape
    """
        ml = getattr(self, 'radiance_mult_band_{}'.format(band))
        al = getattr(self, 'radiance_add_band_{}'.format(band))
        dn = getattr(self, 'b{}'.format(band))
        rs = ml * dn.astype(np.float32) + al

        return rs

# =============================================================================================
