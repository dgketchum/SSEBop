import os
import numpy as np


def reflectance(img, mr, ar, elev, src_nodata=0):
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

    Parameters
    -----------
    img: ndarray
        array of input pixels of shape (rows, cols) or (rows, cols, depth)
    mr: float or list of floats
        multiplicative rescaling factor from scene metadata
    ar: float or list of floats
        additive rescaling factor from scene metadata
    elev: float or numpy array of floats
        local sun elevation angle in degrees

    Returns
    --------
    ndarray:
        float32 ndarray with shape == input shape

    """

    if np.any(elev < 0.0):
        raise ValueError("Sun elevation must be nonnegative "
                         "(sun must be above horizon for entire scene)")

    input_shape = img.shape

    if len(input_shape) > 2:
        img = np.rollaxis(img, 0, len(input_shape))

    rf = ((mr * img.astype(np.float32)) + ar) / np.sin(np.deg2rad(elev))
    if src_nodata is not None:
        rf[img == src_nodata] = 0.0

    if len(input_shape) > 2:
        if np.rollaxis(rf, len(input_shape) - 1, 0).shape != input_shape:
            raise ValueError(
                "Output shape %s is not equal to input shape %s"
                % (rf.shape, input_shape))
        else:
            return np.rollaxis(rf, len(input_shape) - 1, 0)
    else:
        return rf


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


def radiance(img, ml, al, src_nodata=0):
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
    img: ndarray
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

    rs = ml * img.astype(np.float32) + al
    if src_nodata is not None:
        rs[img == src_nodata] = 0.0

    return rs


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
