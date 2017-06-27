# -*- coding: utf-8 -*-
"""
   Copyright 2015 Creare
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
Digital Elevation Model Processing Module
==========================================
This module implements Tarboton (96,
http://www.neng.usu.edu/cee/faculty/dtarb/96wr03137.pdf) Digital Elevation
Model (DEM) processing algorithms for calculating the magnitude and direction
(or aspect) of slopes given the DEM elevation data. This implementation
takes into account the supplied coordinate system, so it does not make an
assumption of a rectangular grid for improved accuracy.
It also implements a novel Upstream Contributing Area (UCA) calculation
algorithm that can operator on chunks of an input file, and accurately handle
the fluxes at edges of chunks.
Finally, it can calculate the Topographic Wetness Index (TWI) based on the UCA
and slope magnitude. Flats and no-data areas are in-painted, the maximum
value for TWI is capped, and the output is multiplied by 10 to get higher
accuracy when storing the array as an integer.
Usage Notes
-------------
This module consists of 3 classes, and 3 helper functions. General users should
only need to be concerned with the DEMProcessor class.
It has only been tested in USGS geotiff files.
It presently only supports WGS84 coordinate systems
Developer Notes
-----------------
The Edge and TileEdge classes keep track of the edge information for tiles
Development Notes
------------------
TODO: Implement this for the elevation data http://pastebin.com/umNmSrE2 .
    Generally the DEM data is stored as integers. So in areas with flat terrain
    due to rounding there may be large flats. We can create interpolated
    floating point values in those regions so that we can still get good
    answers
TODO: Replace complete file loading with partial loading from disk to RAM.
    Presently, an entire geotiff is loaded into memory, which makes the
    chunk calculation less useful because the memory restriction is still
    present
TODO: Improve general memory usage (following from previous TODO).
TODO: Cythonize magnitude and slope calculations
TODO: Implement pit-removal algorithm so that we can start from raw elevation
    tiles.
Created on Wed Jun 18 14:19:04 2014
@author: mpu
"""

import gc
import numpy as np

import os
import numba
import scipy.ndimage as spndi
from rasterio import open as rasopen

# A test aspect ration between dx and dy coordinates
TEST_DIV = 1 / 1.1  # 0.001
FLAT_ID = np.nan  # This is the fill value for flats in float arrays
FLAT_ID_INT = -1  # This is the fill value for flats in int arrays

# Used to extend flat region downstream when calculating angle
FLATS_KERNEL1 = np.ones((3, 3))
FLATS_KERNEL2 = np.ones((3, 3))  # Convolution used to find edges to the flats
# This is the only choice for FLATS_KERNEL3 because otherwise it won't play
# nicely with the pit-filling algorithm
FLATS_KERNEL3 = np.ones((3, 3))  # Kernel used to connect flats and edges
FILL_VALUE = -9999  # This is the integer fill value for no-data values


class DEMProcessor(object):
    """
    This class processes elevation data, and returns the magnitude of slopes,
    the direction of slopes, the upstream contributing area, and the
    topographic wetness index.
    """
    # Flag that when true will ensure edge UCA is continuous across chunks
    resolve_edges = True
    #    apply_uca_limit_edges = True
    #    apply_twi_limits = True
    #    apply_twi_limits_on_uca = True

    # When resolving drainage across edges, if maximum UCA is reached, should
    # edge be marked as completed?

    apply_uca_limit_edges = False
    # When calculating TWI, should TWI be limited to max value?
    apply_twi_limits = False
    # When calculating TWI, should UCA be limited to max value?
    apply_twi_limits_on_uca = False

    direction = None  # Direction of slope in radians
    mag = None  # magnitude of slopes m/m
    elev = None  # elevation data

    # Gives the quadrant used for determining the d_infty mag/direction
    section = None  # save for debugging purposes, not useful output otherwise
    # Give the proportion of the area to drain to the first pixel in quadrant
    proportion = None  # Also saved for debugging
    done = None  # Marks if edges are done

    plotflag = False  # Debug plots

    dx = None  # delta x
    dy = None  # delta y

    uca_saturation_limit = 32  # units of area
    twi_min_slope = 1e-3  # Used for TWI max limiting
    twi_min_area = np.inf  # Finds min area in tile
    chunk_size_slp_dir = 512  # Size of chunk (without overlaps)
    # This has to be > 1 to avoid edge effects for flats
    chunk_overlap_slp_dir = 4  # Overlap when calculating magnitude/directions
    chunk_size_uca = 512  # Size of chunks when calculating UCA
    chunk_overlap_uca = 32  # Number of overlapping pixels for UCA calculation
    # Mostly deprecated, but maximum number of iterations used to try and
    # resolve circular drainage patterns (which should never occur)
    circular_ref_maxcount = 50

    # The pixel coordinates for the different facets used to calculate the
    # D_infty magnitude and direction (from Tarboton)
    facets = [
        [(0, 0), (0, 1), (-1, 1)],
        [(0, 0), (-1, 0), (-1, 1)],
        [(0, 0), (-1, 0), (-1, -1)],
        [(0, 0), (0, -1), (-1, -1)],
        [(0, 0), (0, -1), (1, -1)],
        [(0, 0), (1, 0), (1, -1)],
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 1)],
    ]
    # Helper for magnitude/direction calculation (modified from Tarboton)
    ang_adj = np.array([
        [0, 1],
        [1, -1],
        [1, 1],
        [2, -1],
        [2, 1],
        [3, -1],
        [3, 1],
        [4, -1]
    ])

    #    def __del__(self):
    #        self.elev_file = None #Close the elevation file

    def __init__(self, data, profile):
        """
        """
        # %%
        self.profile = profile
        if len(data.shape) == 3:
            data = np.reshape(data, (data.shape[1], data.shape[2]))

        self.data = data
        try:  # if masked array
            self.data.mask[(np.isnan(self.data))
                           | (self.data < -9998)] = True
            self.data[data.mask] = FILL_VALUE
        except:
            self.data = np.ma.masked_array(self.data,
                                           mask=(np.isnan(self.data))
                                                | (self.data < -9998))

        shp = np.array(self.data.shape) - 1
        self.dx = np.ones((data.shape[0] - 1)) / (shp[1])
        self.dy = np.ones((data.shape[0] - 1)) / (shp[0])

    def calc_slopes_directions(self, plotflag=False):
        """
        Calculates the magnitude and direction of slopes and fills
        self.mag, self.direction
        """
        # %% Calculate the slopes and directions based on the 8 sections from
        # Tarboton http://www.neng.usu.edu/cee/faculty/dtarb/96wr03137.pdf

        self.direction = np.ones(self.data.shape) * FLAT_ID_INT
        self.mag = np.ones_like(self.direction) * FLAT_ID_INT
        self.flats = np.zeros(self.data.shape, bool)
        top_edge, bottom_edge = self._get_chunk_edges(self.data.shape[0],
                                                      self.chunk_size_slp_dir,
                                                      self.chunk_overlap_slp_dir)
        left_edge, right_edge = self._get_chunk_edges(self.data.shape[1],
                                                      self.chunk_size_slp_dir,
                                                      self.chunk_overlap_slp_dir)
        ovr = self.chunk_overlap_slp_dir
        count = 1
        for te, be in zip(top_edge, bottom_edge):
            for le, re in zip(left_edge, right_edge):
                print('starting slope/direction calculation for chunk', count, "[%d:%d, %d:%d]" % (te, be, le, re))
                count += 1
                mag, direction = self._slopes_directions(self.data[te:be, le:re],
                                                         self.dx[te:be - 1],
                                                         self.dy[te:be - 1])

                flats = self._find_flats_edges(self.data[te:be, le:re],
                                               self.dx[te:be - 1],
                                               self.dy[te:be - 1], mag,
                                               direction)
                direction[flats] = FLAT_ID
                mag[flats] = FLAT_ID
                self._assign_chunk(self.data, self.mag, mag,
                                   te, be, le, re, ovr)
                self._assign_chunk(self.data, self.direction, direction,
                                   te, be, le, re, ovr)
                self._assign_chunk(self.data, self.flats, flats,
                                   te, be, le, re, ovr)

        if plotflag:
            self._plot_debug_slopes_directions()

        gc.collect()

        with rasopen('/data01/images/sandbox/slope_proc.tif', 'w', **self.profile) as dst:
            dst.write(mag)

        with rasopen('/data01/images/sandbox/slope_proc.tif', 'w', **self.profile) as dst:
            dst.write(direction)

        return self.mag, self.direction

    def _slopes_directions(self, data, dx, dy, method='tarboton'):
        """ Wrapper to pick between various algorithms
        """
        # %%
        if method == 'tarboton':
            return self._tarboton_slopes_directions(data, dx, dy)
        elif method == 'central':
            return self._central_slopes_directions(data, dx, dy)

    def _central_slopes_directions(self, data, dx, dy):
        """
        Calculates magnitude/direction of slopes using central difference
        """
        shp = np.array(data.shape) - 1

        direction = np.ones(data.shape) * FLAT_ID_INT
        mag = np.ones_like(direction) * FLAT_ID_INT

        ind = 0
        d1, d2, theta = self._get_d1_d2(dx, dy, ind, [0, 1], [1, 1], shp)
        s2 = (data[0:-2, 1:-1] - data[2:, 1:-1]) / d2
        s1 = -(data[1:-1, 0:-2] - data[1:-1, 2:]) / d1
        direction[1:-1, 1:-1] = np.arctan2(s2, s1) + np.pi
        mag = np.sqrt(s1 ** 2 + s2 ** 2)

        return mag, direction

    @numba.jit
    def _tarboton_slopes_directions(self, data, dx, dy):
        """
        Calculate the slopes and directions based on the 8 sections from
        Tarboton http://www.neng.usu.edu/cee/faculty/dtarb/96wr03137.pdf
        """
        shp = np.array(data.shape) - 1

        direction = np.ones(data.shape) * FLAT_ID_INT
        mag = np.ones_like(direction) * FLAT_ID_INT

        slc0 = [slice(1, -1), slice(1, -1)]
        for ind in range(8):
            e1 = self.facets[ind][1]
            e2 = self.facets[ind][2]
            ang = self.ang_adj[ind]
            slc1 = [slice(1 + e1[0], shp[0] + e1[0]),
                    slice(1 + e1[1], shp[1] + e1[1])]
            slc2 = [slice(1 + e2[0], shp[0] + e2[0]),
                    slice(1 + e2[1], shp[1] + e2[1])]

            d1, d2, theta = self._get_d1_d2(dx, dy, ind, e1, e2, shp)
            mag, direction = self._calc_direction(self, data, mag, direction, ang, d1, d2,
                                                  theta, slc0, slc1, slc2)

        # %%Now do the edges
        # if the edge is lower than the interior, we need to copy the value
        # from the interior (as an approximation)
        ids1 = (direction[:, 1] > np.pi / 2) \
               & (direction[:, 1] < 3 * np.pi / 2)
        direction[ids1, 0] = direction[ids1, 1]
        mag[ids1, 0] = mag[ids1, 1]
        ids1 = (direction[:, -2] < np.pi / 2) \
               | (direction[:, -2] > 3 * np.pi / 2)
        direction[ids1, -1] = direction[ids1, -2]
        mag[ids1, -1] = mag[ids1, -2]
        ids1 = (direction[1, :] > 0) & (direction[1, :] < np.pi)
        direction[0, ids1] = direction[1, ids1]
        mag[0, ids1] = mag[1, ids1]
        ids1 = (direction[-2, :] > np.pi) & (direction[-2, :] < 2 * np.pi)
        direction[-1, ids1] = direction[-2, ids1]
        mag[-1, ids1] = mag[-2, ids1]

        # Now update the edges in case they are higher than the interior (i.e.
        # look at the downstream angle)

        # left edge
        slc0 = [slice(1, -1), slice(0, 1)]
        for ind in [0, 1, 6, 7]:
            e1 = self.facets[ind][1]
            e2 = self.facets[ind][2]
            ang = self.ang_adj[ind]
            slc1 = [slice(1 + e1[0], shp[0] + e1[0]), slice(e1[1], 1 + e1[1])]
            slc2 = [slice(1 + e2[0], shp[0] + e2[0]), slice(e2[1], 1 + e2[1])]
            d1, d2, theta = self._get_d1_d2(dx, dy, ind, e1, e2, shp)
            mag, direction = self._calc_direction(self, data, mag, direction, ang, d1, d2,
                                                  theta, slc0, slc1, slc2)
        # right edge
        slc0 = [slice(1, -1), slice(-1, None)]
        for ind in [2, 3, 4, 5]:
            e1 = self.facets[ind][1]
            e2 = self.facets[ind][2]
            ang = self.ang_adj[ind]
            slc1 = [slice(1 + e1[0], shp[0] + e1[0]),
                    slice(shp[1] + e1[1], shp[1] + 1 + e1[1])]
            slc2 = [slice(1 + e2[0], shp[0] + e2[0]),
                    slice(shp[1] + e2[1], shp[1] + 1 + e2[1])]
            d1, d2, theta = self._get_d1_d2(dx, dy, ind, e1, e2, shp)
            mag, direction = self._calc_direction(self, data, mag, direction, ang, d1, d2,
                                                  theta, slc0, slc1, slc2)
        # top edge
        slc0 = [slice(0, 1), slice(1, -1)]
        for ind in [4, 5, 6, 7]:
            e1 = self.facets[ind][1]
            e2 = self.facets[ind][2]
            ang = self.ang_adj[ind]
            slc1 = [slice(e1[0], 1 + e1[0]), slice(1 + e1[1], shp[1] + e1[1])]
            slc2 = [slice(e2[0], 1 + e2[0]), slice(1 + e2[1], shp[1] + e2[1])]
            d1, d2, theta = self._get_d1_d2(dx, dy, ind, e1, e2, shp, 'top')
            mag, direction = self._calc_direction(self, data, mag, direction, ang, d1, d2,
                                                  theta, slc0, slc1, slc2)
        # bottom edge
        slc0 = [slice(-1, None), slice(1, -1)]
        for ind in [0, 1, 2, 3]:
            e1 = self.facets[ind][1]
            e2 = self.facets[ind][2]
            ang = self.ang_adj[ind]
            slc1 = [slice(shp[0] + e1[0], shp[0] + 1 + e1[0]),
                    slice(1 + e1[1], shp[1] + e1[1])]
            slc2 = [slice(shp[0] + e2[0], shp[0] + 1 + e2[0]),
                    slice(1 + e2[1], shp[1] + e2[1])]
            d1, d2, theta = self._get_d1_d2(dx, dy, ind, e1, e2, shp, 'bot')
            mag, direction = self._calc_direction(self, data, mag, direction, ang, d1, d2,
                                                  theta, slc0, slc1, slc2)
        # top-left corner
        slc0 = [slice(0, 1), slice(0, 1)]
        for ind in [6, 7]:
            e1 = self.facets[ind][1]
            e2 = self.facets[ind][2]
            ang = self.ang_adj[ind]
            slc1 = [slice(e1[0], 1 + e1[0]), slice(e1[1], 1 + e1[1])]
            slc2 = [slice(e2[0], 1 + e2[0]), slice(e2[1], 1 + e2[1])]
            d1, d2, theta = self._get_d1_d2(dx, dy, ind, e1, e2, shp, 'top')
            mag, direction = self._calc_direction(self, data, mag, direction, ang, d1, d2,
                                                  theta, slc0, slc1, slc2)
        # top-right corner
        slc0 = [slice(0, 1), slice(-1, None)]
        for ind in [4, 5]:
            e1 = self.facets[ind][1]
            e2 = self.facets[ind][2]
            ang = self.ang_adj[ind]
            slc1 = [slice(e1[0], 1 + e1[0]),
                    slice(shp[1] + e1[1], shp[1] + 1 + e1[1])]
            slc2 = [slice(e2[0], 1 + e2[0]),
                    slice(shp[1] + e2[1], shp[1] + 1 + e2[1])]
            d1, d2, theta = self._get_d1_d2(dx, dy, ind, e1, e2, shp, 'top')
            mag, direction = self._calc_direction(self, data, mag, direction, ang, d1, d2,
                                                  theta, slc0, slc1, slc2)
        # bottom-left corner
        slc0 = [slice(-1, None), slice(0, 1)]
        for ind in [0, 1]:
            e1 = self.facets[ind][1]
            e2 = self.facets[ind][2]
            ang = self.ang_adj[ind]
            slc1 = [slice(shp[0] + e1[0], shp[0] + 1 + e1[0]),
                    slice(e1[1], 1 + e1[1])]
            slc2 = [slice(shp[0] + e2[0], shp[0] + 1 + e2[0]),
                    slice(e2[1], 1 + e2[1])]
            d1, d2, theta = self._get_d1_d2(dx, dy, ind, e1, e2, shp, 'bot')
            mag, direction = self._calc_direction(self, data, mag, direction, ang, d1, d2,
                                                  theta, slc0, slc1, slc2)
        # bottom-right corner
        slc0 = [slice(-1, None), slice(-1, None)]
        for ind in [3, 4]:
            e1 = self.facets[ind][1]
            e2 = self.facets[ind][2]
            ang = self.ang_adj[ind]
            slc1 = [slice(shp[0] + e1[0], shp[0] + 1 + e1[0]),
                    slice(shp[1] + e1[1], shp[1] + 1 + e1[1])]
            slc2 = [slice(shp[0] + e2[0], shp[0] + 1 + e2[0]),
                    slice(shp[1] + e2[1], shp[1] + 1 + e2[1])]
            d1, d2, theta = self._get_d1_d2(dx, dy, ind, e1, e2, shp, 'bot')
            mag, direction = self._calc_direction(self, data, mag, direction, ang, d1, d2,
                                                  theta, slc0, slc1, slc2)

        mag[mag > 0] = np.sqrt(mag[mag > 0])

        return mag, direction

    # Let's calculate the slopes!
    @numba.jit
    def _calc_direction(self, data, mag, direction, ang, d1, d2, theta,
                        slc0, slc1, slc2):
        """
        This function gives the magnitude and direction of the slope based on
        Tarboton's D_\infty method. This is a helper-function to
        _tarboton_slopes_directions
        """
        s1 = (data[slc0] - data[slc1]) / d1
        s2 = (data[slc1] - data[slc2]) / d2
        sd = (data[slc0] - data[slc2]) / np.sqrt((d1 * d1 + d2 * d2))
        r = np.arctan2(s2, s1)
        rad2 = (s1) ** 2 + (s2) ** 2

        # Handle special cases
        # should be on diagonal
        I1 = ((s1 <= 0) & (s2 > 0)) | (r > np.arctan2(d2, d1))
        rad2[I1] = sd[I1] ** 2
        r[I1] = theta.repeat(I1.shape[1], 1)[I1]
        I2 = ((s1 > 0) & (s2 <= 0)) | (r < 0)  # should be on straight section
        rad2[I2] = s1[I2] ** 2
        r[I2] = 0
        I3 = (s1 <= 0) & ((s2 <= 0) | ((s2 > 0) & (sd <= 0)))  # upslope or flat
        rad2[I3] = -1

        I4 = rad2 > mag[slc0]
        mag[slc0][I4] = rad2[I4]
        direction[slc0][I4] = r[I4] * ang[1] + ang[0] * np.pi / 2

        return mag, direction

    @staticmethod
    def _get_d1_d2(dx, dy, ind, e1, e2, shp, topbot=None):
        """
        This finds the distances along the patch (within the eight neighboring
        pixels around a central pixel) given the difference in x and y coordinates
        of the real image. This is the function that allows real coordinates to be
        used when calculating the magnitude and directions of slopes.
        """
        if not topbot:
            if ind in [0, 3, 4, 7]:
                d1 = dx[slice(int((e2[0] + 1) / 2), int(shp[0] + (e2[0] - 1) / 2))]
                d2 = dy[slice(int((e2[0] + 1) / 2), int(shp[0] + (e2[0] - 1) / 2))]
                if d1.size == 0:
                    d1 = np.array([dx[0]])
                    d2 = np.array([dy[0]])
            else:
                d2 = dx[slice(int((e1[0] + 1) / 2), int(shp[0] + (e1[0] - 1) / 2))]
                d1 = dy[slice(int((e1[0] + 1) / 2), int(shp[0] + (e1[0] - 1) / 2))]
                if d1.size == 0:
                    d2 = dx[0]
                    d1 = dy[0]
        elif topbot == 'top':
            if ind in [0, 3, 4, 7]:
                d1, d2 = dx[0], dy[0]
            else:
                d2, d1 = dx[0], dy[0]
        elif topbot == 'bot':
            if ind in [0, 3, 4, 7]:
                d1, d2 = dx[-1], dy[-1]
            else:
                d2, d1 = dx[-1], dy[-1]

        theta = np.arctan2(d2, d1)

        return d1.reshape(d1.size, 1), d2.reshape(d2.size, 1), theta.reshape(theta.size, 1)

    @staticmethod
    def _get_chunk_edges(NN, chunk_size, chunk_overlap):
        """
        Given the size of the array, calculate and array that gives the
        edges of chunks of nominal size, with specified overlap
        Parameters
        ----------
        NN : int
            Size of array
        chunk_size : int
            Nominal size of chunks (chunk_size < NN)
        chunk_overlap : int
            Number of pixels chunks will overlap
        Returns
        -------
        start_id : array
            The starting id of a chunk. start_id[i] gives the starting id of
            the i'th chunk
        end_id : array
            The ending id of a chunk. end_id[i] gives the ending id of
            the i'th chunk
        """
        left_edge = np.arange(0, NN - chunk_overlap, chunk_size)
        left_edge[1:] -= chunk_overlap
        right_edge = np.arange(0, NN - chunk_overlap, chunk_size)
        right_edge[:-1] = right_edge[1:] + chunk_overlap
        right_edge[-1] = NN
        right_edge = np.minimum(right_edge, NN)
        return left_edge, right_edge

    @staticmethod
    def _assign_chunk(data, arr1, arr2, te, be, le, re, ovr, add=False):
        """
        Assign data from a chunk to the full array. The data in overlap regions
        will not be assigned to the full array
        Parameters
        -----------
        data : array
            Unused array (except for shape) that has size of full tile
        arr1 : array
            Full size array to which data will be assigned
        arr2 : array
            Chunk-sized array from which data will be assigned
        te : int
            Top edge id
        be : int
            Bottom edge id
        le : int
            Left edge id
        re : int
            Right edge id
        ovr : int
            The number of pixels in the overlap
        add : bool, optional
            Default False. If true, the data in arr2 will be added to arr1,
            otherwise data in arr2 will overwrite data in arr1
        """
        if te == 0:
            i1 = 0
        else:
            i1 = ovr
        if be == data.shape[0]:
            i2 = 0
            i2b = None
        else:
            i2 = -ovr
            i2b = -ovr
        if le == 0:
            j1 = 0
        else:
            j1 = ovr
        if re == data.shape[1]:
            j2 = 0
            j2b = None
        else:
            j2 = -ovr
            j2b = -ovr
        if add:
            arr1[te + i1:be + i2, le + j1:re + j2] += arr2[i1:i2b, j1:j2b]
        else:
            arr1[te + i1:be + i2, le + j1:re + j2] = arr2[i1:i2b, j1:j2b]

    def _find_flats_edges(self, data, dX, dY, mag, direction):
        """
        Extend flats 1 square downstream
        Flats on the downstream side of the flat might find a valid angle,
        but that doesn't mean that it's a correct angle. We have to find
        these and then set them equal to a flat
        """

        flats = mag == FLAT_ID_INT
        assigned, n_flats = spndi.label(flats, FLATS_KERNEL3)
        # Perhaps the code below will be faster?
        #        edges = ndimage.convolve(flats, FLATS_KERNEL1) - flats
        #        edges = ndimage.convolve(edges, FLATS_KERNEL1) & flats
        #        assigned, n_flats = spndi.label(edges, FLATS_KERNEL3)
        nn, mm = flats.shape
        flat_ids, flat_coords, flat_labelsf = self._get_flat_ids(assigned)
        for ii in range(n_flats):
            ids_flats = flat_ids[flat_coords[ii]:flat_coords[ii + 1]]
            elev_flat = data.ravel()[flat_ids[flat_coords[ii]]]
            if elev_flat is np.ma.masked:
                continue
            j = ids_flats % mm
            i = ids_flats // mm
            for iii in [-1, 0, 1]:
                for jjj in [-1, 0, 1]:
                    i_2 = i + iii
                    j_2 = j + jjj

                    ids_tmp = (i_2 >= 0) & (j_2 >= 0) & (i_2 < nn) & (j_2 < mm)
                    ids_tmp2 = data[i_2[ids_tmp], j_2[ids_tmp]] == elev_flat
                    flats[i_2[ids_tmp][ids_tmp2], j_2[ids_tmp][ids_tmp2]] \
                        += FLATS_KERNEL3[iii + 1, jjj + 1]

        return flats

    @staticmethod
    def _get_flat_ids(assigned):
        """
        This is a helper function to recover the coordinates of regions that have
        been labeled within an image. This function efficiently computes the
        coordinate of all regions and returns the information in a memory-efficient
        manner.
        Parameters
        -----------
        assigned : ndarray[ndim=2, dtype=int]
            The labeled image. For example, the result of calling
            scipy.ndimage.label on a binary image
        Returns
        --------
        I : ndarray[ndim=1, dtype=int]
            Array of 1d coordinate indices of all regions in the image
        region_ids : ndarray[shape=[n_features + 1], dtype=int]
            Indexing array used to separate the coordinates of the different
            regions. For example, region k has xy coordinates of
            xy[region_ids[k]:region_ids[k+1], :]
        labels : ndarray[ndim=1, dtype=int]
            The labels of the regions in the image corresponding to the coordinates
            For example, assigned.ravel()[I[k]] == labels[k]
        """
        # MPU optimization:
        # Let's segment the regions and store in a sparse format
        # First, let's use where once to find all the information we want
        ids_labels = np.arange(len(assigned.ravel()), dtype=int)
        I = ids_labels[assigned.ravel().astype(bool)]
        labels = assigned.ravel()[I]
        # Now sort these arrays by the label to figure out where to segment
        sort_id = np.argsort(labels)
        labels = labels[sort_id]
        I = I[sort_id]
        # this should be of size n_features-1
        region_ids = np.where(labels[1:] - labels[:-1] > 0)[0] + 1
        # This should be of size n_features + 1
        region_ids = np.concatenate(([0], region_ids, [len(labels)]))

        return [I, region_ids, labels]

if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
