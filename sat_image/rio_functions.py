import os
import numpy as np





def brightness_temp(img, ml, al, k1, k2, src_nodata=0):
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


    Parameters
    -----------
    img: ndarray
        array of input pixels
    ml: float
        multiplicative rescaling factor from scene metadata
    al: float
        additive rescaling factor from scene metadata
    k1: float
        thermal conversion constant from scene metadata
    k2: float
        thermal conversion constant from scene metadata

    Returns
    --------
    ndarray:
        float32 ndarray with shape == input shape
    """
    L = radiance(img, ml, al, src_nodata=0)
    L[img == src_nodata] = np.NaN

    T = k2 / np.log((k1 / L) + 1)

    return T


def radiance(sat, dn, ml=None, al=None, qcal_min=None, qcal_max=None,
             l_min=None, l_max=None, src_nodata=0):
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

    Parameters
    -----------
    dn: ndarray
        array of input pixels
    ml: float
        multiplicative rescaling factor from scene metadata
    al: float
        additive rescaling factor from scene metadata

    Returns
    --------
    ndarray:
        float32 ndarray with shape == input shape
    """

    if sat == 'LC8':
        rs = ml * dn.astype(np.float32) + al
        if src_nodata is not None:
            rs[dn == src_nodata] = 0.0
        return rs

    elif sat in ['LT5', 'LE7']:
        rs = ((l_max - l_min) / (qcal_max - qcal_min)) * (dn - qcal_min) + l_min

    return rs


def radiance57(qcal, qcal_min, qcal_max, l_min, l_max):



if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
