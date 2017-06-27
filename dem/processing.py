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

import warnings
import gc
import numpy as np

import os
import numba

# from reader.gdal_reader import GdalReader
# from utils import mk_dx_dy_from_geotif_layer, get_fn
# 
# try:
#     from cyfuncs import cyutils
# 
#     CYTHON = True
# except:
#     CYTHON = False
#     warnings.warn("Cython functions are not compiled. UCA calculation will be,"
#                   " slow. Consider compiling cython functions using: "
#                   "python setup.py build_ext --inplace", RuntimeWarning)
# CYTHON = False

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
    uca = None  # upstream contributing area
    twi = None  # topographic wetness index
    elev = None  # elevation data
    A = None  # connectivity matrix

    # Gives the quadrant used for determining the d_infty mag/direction
    section = None  # save for debugging purposes, not useful output otherwise
    # Give the proportion of the area to drain to the first pixel in quadrant
    proportion = None  # Also saved for debugging
    done = None  # Marks if edges are done

    plotflag = False  # Debug plots
    # Use uniform values for dx/dy or obtain from geotiff
    dx_dy_from_file = True
    file_name = None  # Elevation data filename

    dx = None  # delta x
    dy = None  # delta y

    flats = None  # Boolean array indicating location of flats

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

        self.data = data
        try:  # if masked array
            self.data.mask[(np.isnan(self.data))
                           | (self.data < -9998)] = True
            self.data[data.mask] = FILL_VALUE
        except:
            self.data = np.ma.masked_array(self.data,
                                           mask=(np.isnan(self.data))
                                                | (self.data < -9998))

        self.dx = profile['transform'].a
        self.dy = profile['transform'].a

    # def get_fn(self, name=None):
    #     return get_fn(self.elev, name)
    # 
    # def get_full_fn(self, name, rootpath='.'):
    #     return os.path.join(rootpath, name, self.get_fn(name))
    # 
    # def save_array(self, array, name=None, partname=None, rootpath='.',
    #                raw=False, as_int=True):
    #     """
    #     Standard array saving routine
    #     Parameters
    #     -----------
    #     array : array
    #         Array to save to file
    #     name : str, optional
    #         Default 'array.tif'. Filename of array to save. Over-writes
    #         partname.
    #     partname : str, optional
    #         Part of the filename to save (with the coordinates appended)
    #     rootpath : str, optional
    #         Default '.'. Which directory to save file
    #     raw : bool, optional
    #         Default False. If true will save a .npz of the array. If false,
    #         will save a geotiff
    #     as_int : bool, optional
    #         Default True. If true will save array as an integer array (
    #         excellent compression). If false will save as float array.
    #     """
    #     if name is None and partname is not None:
    #         fnl_file = self.get_full_fn(partname, rootpath)
    #         tmp_file = os.path.join(rootpath, partname,
    #                                 self.get_fn(partname + '_tmp'))
    #     elif name is not None:
    #         fnl_file = name
    #         tmp_file = fnl_file + '_tmp.tiff'
    #     else:
    #         fnl_file = 'array.tif'
    #     if not raw:
    #         s_file = self.elev.clone_traits()
    #         s_file.raster_data = np.ma.masked_array(array)
    #         count = 10
    #         while count > 0 and (s_file.raster_data.mask.sum() > 0 \
    #                                      or np.isnan(s_file.raster_data).sum() > 0):
    #             s_file.inpaint()
    #             count -= 1
    # 
    #         s_file.export_to_geotiff(tmp_file)
    # 
    #         if as_int:
    #             cmd = "gdalwarp -multi -wm 2000 -co BIGTIFF=YES -of GTiff -co compress=lzw -ot Int16 -co TILED=YES -wo OPTIMIZE_SIZE=YES -r near -t_srs %s %s %s" \
    #                   % (self.save_projection, tmp_file, fnl_file)
    #         else:
    #             cmd = "gdalwarp -multi -wm 2000 -co BIGTIFF=YES -of GTiff -co compress=lzw -co TILED=YES -wo OPTIMIZE_SIZE=YES -r near -t_srs %s %s %s" \
    #                   % (self.save_projection, tmp_file, fnl_file)
    #         print("<<" * 4, cmd, ">>" * 4)
    #         subprocess.call(cmd)
    #         os.remove(tmp_file)
    #     else:
    #         np.savez_compressed(fnl_file, array)
    # 
    # def save_uca(self, rootpath, raw=False, as_int=False):
    #     """ Saves the upstream contributing area to a file
    #     """
    #     self.save_array(self.uca, None, 'uca', rootpath, raw, as_int=as_int)
    # 
    # def save_twi(self, rootpath, raw=False, as_int=True):
    #     """ Saves the topographic wetness index to a file
    #     """
    #     self.twi = np.ma.masked_array(self.twi, mask=self.twi <= 0,
    #                                   fill_value=-9999)
    #     #  self.twi = self.twi.filled()
    #     self.twi[self.flats] = 0
    #     self.twi.mask[self.flats] = True
    #     # self.twi = self.flats
    #     self.save_array(self.twi, None, 'twi', rootpath, raw, as_int=as_int)
    # 
    # def save_slope(self, rootpath, raw=False, as_int=False):
    #     """ Saves the magnitude of the slope to a file
    #     """
    #     self.save_array(self.mag, None, 'mag', rootpath, raw, as_int=as_int)
    # 
    # def save_direction(self, rootpath, raw=False, as_int=False):
    #     """ Saves the direction of the slope to a file
    #     """
    #     self.save_array(self.direction, None, 'ang', rootpath, raw, as_int=as_int)
    # 
    # def save_outputs(self, rootpath='.', raw=False):
    #     """Saves TWI, UCA, magnitude and direction of slope to files.
    #     """
    #     self.save_twi(rootpath, raw)
    #     self.save_uca(rootpath, raw)
    #     self.save_slope(rootpath, raw)
    #     self.save_direction(rootpath, raw)
    # 
    # def load_array(self, fn, name):
    #     """
    #     Can only load files that were saved in the 'raw' format.
    #     Loads previously computed field 'name' from file
    #     Valid names are 'mag', 'direction', 'uca', 'twi'
    #     """
    # 
    #     if os.path.exists(fn + '.npz'):
    #         array = np.load(fn + '.npz')
    #         try:
    #             setattr(self, name, array['arr_0'])
    #         except Exception as e:
    #             print(e)
    #         finally:
    #             array.close()
    # 
    #     else:
    #         raise RuntimeError("File %s does not exist." % (fn + '.npz'))
    # 
    # def load_direction(self, fn):
    #     """Loads pre-computed slope direction from file
    #     """
    #     self.load_array(fn, 'direction')
    # 
    # def load_uca(self, fn):
    #     """Loads pre-computed uca from file
    #     """
    #     self.load_array(fn, 'uca')

    # def _get_chunk_edges(self, NN, chunk_size, chunk_overlap):
    #     """
    #     Given the size of the array, calculate and array that gives the
    #     edges of chunks of nominal size, with specified overlap
    #     Parameters
    #     ----------
    #     NN : int
    #         Size of array
    #     chunk_size : int
    #         Nominal size of chunks (chunk_size < NN)
    #     chunk_overlap : int
    #         Number of pixels chunks will overlap
    #     Returns
    #     -------
    #     start_id : array
    #         The starting id of a chunk. start_id[i] gives the starting id of
    #         the i'th chunk
    #     end_id : array
    #         The ending id of a chunk. end_id[i] gives the ending id of
    #         the i'th chunk
    #     """
    #     left_edge = np.arange(0, NN - chunk_overlap, chunk_size)
    #     left_edge[1:] -= chunk_overlap
    #     right_edge = np.arange(0, NN - chunk_overlap, chunk_size)
    #     right_edge[:-1] = right_edge[1:] + chunk_overlap
    #     right_edge[-1] = NN
    #     right_edge = np.minimum(right_edge, NN)
    #     # return left_edge, right_edge

    # def _assign_chunk(self, data, arr1, arr2, te, be, le, re, ovr, add=False):
    #     """
    #     Assign data from a chunk to the full array. The data in overlap regions
    #     will not be assigned to the full array
    #     Parameters
    #     -----------
    #     data : array
    #         Unused array (except for shape) that has size of full tile
    #     arr1 : array
    #         Full size array to which data will be assigned
    #     arr2 : array
    #         Chunk-sized array from which data will be assigned
    #     te : int
    #         Top edge id
    #     be : int
    #         Bottom edge id
    #     le : int
    #         Left edge id
    #     re : int
    #         Right edge id
    #     ovr : int
    #         The number of pixels in the overlap
    #     add : bool, optional
    #         Default False. If true, the data in arr2 will be added to arr1,
    #         otherwise data in arr2 will overwrite data in arr1
    #     """
    #     if te == 0:
    #         i1 = 0
    #     else:
    #         i1 = ovr
    #     if be == data.shape[0]:
    #         i2 = 0
    #         i2b = None
    #     else:
    #         i2 = -ovr
    #         i2b = -ovr
    #     if le == 0:
    #         j1 = 0
    #     else:
    #         j1 = ovr
    #     if re == data.shape[1]:
    #         j2 = 0
    #         j2b = None
    #     else:
    #         j2 = -ovr
    #         j2b = -ovr
    #     if add:
    #         arr1[te + i1:be + i2, le + j1:re + j2] += arr2[i1:i2b, j1:j2b]
    #     else:
    #         arr1[te + i1:be + i2, le + j1:re + j2] = arr2[i1:i2b, j1:j2b]

    # def find_flats(self):
    #     flats = self._find_flats_edges(self.data, self.dx, self.dy,
    #                                    self.mag, self.direction)
    #     self.direction[flats] = FLAT_ID
    #     self.mag[flats] = FLAT_ID
    #     self.flats = flats

    def calc_slopes_directions(self, plotflag=False):
        """
        Calculates the magnitude and direction of slopes and fills
        self.mag, self.direction
        """
        # %% Calculate the slopes and directions based on the 8 sections from
        # Tarboton http://www.neng.usu.edu/cee/faculty/dtarb/96wr03137.pdf
        if self.data.shape[0] <= self.chunk_size_slp_dir and \
                        self.data.shape[1] <= self.chunk_size_slp_dir:
            print
            "starting slope/direction calculation"
            self.mag, self.direction = self._slopes_directions(
                self.data, self.dx, self.dy, 'tarboton')
            # Find the flat regions. This is mostly simple (look for mag < 0),
            # but the downstream pixel at the edge of a flat will have a
            # calcuable angle which will not be accurate. We have to also find
            # these edges and set their magnitude to -1 (that is, the flat_id)

            self.find_flats()
        else:
            self.direction = np.ones(self.data.shape) * FLAT_ID_INT
            self.mag = np.ones_like(self.direction) * FLAT_ID_INT
            self.flats = np.zeros(self.data.shape, bool)
            top_edge, bottom_edge = \
                self._get_chunk_edges(self.data.shape[0],
                                      self.chunk_size_slp_dir,
                                      self.chunk_overlap_slp_dir)
            left_edge, right_edge = \
                self._get_chunk_edges(self.data.shape[1],
                                      self.chunk_size_slp_dir,
                                      self.chunk_overlap_slp_dir)
            ovr = self.chunk_overlap_slp_dir
            count = 1
            for te, be in zip(top_edge, bottom_edge):
                for le, re in zip(left_edge, right_edge):
                    print
                    "starting slope/direction calculation for chunk", \
                    count, "[%d:%d, %d:%d]" % (te, be, le, re)
                    count += 1
                    mag, direction = \
                        self._slopes_directions(self.data[te:be, le:re],
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

        gc.collect()  # Just in case
        return self.mag, self.direction

    def _slopes_directions(self, data, dx, dy, method='tarboton'):
        """ Wrapper to pick between various algorithms
        """
        # %%
        if method == 'tarboton':
            return self.tarboton_slopes_directions(data, dx, dy)
        elif method == 'central':
            return self._central_slopes_directions(data, dx, dy)

    def tarboton_slopes_directions(self, data, dx, dy):
        """
        Calculate the slopes and directions based on the 8 sections from
        Tarboton http://www.neng.usu.edu/cee/faculty/dtarb/96wr03137.pdf
        """

        return self._tarboton_slopes_directions(data, dx, dy,
                                                self.facets, self.ang_adj)

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
    def _tarboton_slopes_directions(self, data, dx, dy, facets, ang_adj):
        """
        Calculate the slopes and directions based on the 8 sections from
        Tarboton http://www.neng.usu.edu/cee/faculty/dtarb/96wr03137.pdf
        """
        shp = np.array(data.shape) - 1

        direction = np.ones(data.shape) * FLAT_ID_INT
        mag = np.ones_like(direction) * FLAT_ID_INT

        slc0 = [slice(1, -1), slice(1, -1)]
        for ind in range(8):
            e1 = facets[ind][1]
            e2 = facets[ind][2]
            ang = ang_adj[ind]
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
            e1 = facets[ind][1]
            e2 = facets[ind][2]
            ang = ang_adj[ind]
            slc1 = [slice(1 + e1[0], shp[0] + e1[0]), slice(e1[1], 1 + e1[1])]
            slc2 = [slice(1 + e2[0], shp[0] + e2[0]), slice(e2[1], 1 + e2[1])]
            d1, d2, theta = self._get_d1_d2(dx, dy, ind, e1, e2, shp)
            mag, direction = self._calc_direction(self, data, mag, direction, ang, d1, d2,
                                                  theta, slc0, slc1, slc2)
        # right edge
        slc0 = [slice(1, -1), slice(-1, None)]
        for ind in [2, 3, 4, 5]:
            e1 = facets[ind][1]
            e2 = facets[ind][2]
            ang = ang_adj[ind]
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
            e1 = facets[ind][1]
            e2 = facets[ind][2]
            ang = ang_adj[ind]
            slc1 = [slice(e1[0], 1 + e1[0]), slice(1 + e1[1], shp[1] + e1[1])]
            slc2 = [slice(e2[0], 1 + e2[0]), slice(1 + e2[1], shp[1] + e2[1])]
            d1, d2, theta = self._get_d1_d2(dx, dy, ind, e1, e2, shp, 'top')
            mag, direction = self._calc_direction(self, data, mag, direction, ang, d1, d2,
                                                  theta, slc0, slc1, slc2)
        # bottom edge
        slc0 = [slice(-1, None), slice(1, -1)]
        for ind in [0, 1, 2, 3]:
            e1 = facets[ind][1]
            e2 = facets[ind][2]
            ang = ang_adj[ind]
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
            e1 = facets[ind][1]
            e2 = facets[ind][2]
            ang = ang_adj[ind]
            slc1 = [slice(e1[0], 1 + e1[0]), slice(e1[1], 1 + e1[1])]
            slc2 = [slice(e2[0], 1 + e2[0]), slice(e2[1], 1 + e2[1])]
            d1, d2, theta = self._get_d1_d2(dx, dy, ind, e1, e2, shp, 'top')
            mag, direction = self._calc_direction(self, data, mag, direction, ang, d1, d2,
                                                  theta, slc0, slc1, slc2)
        # top-right corner
        slc0 = [slice(0, 1), slice(-1, None)]
        for ind in [4, 5]:
            e1 = facets[ind][1]
            e2 = facets[ind][2]
            ang = ang_adj[ind]
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
            e1 = facets[ind][1]
            e2 = facets[ind][2]
            ang = ang_adj[ind]
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
            e1 = facets[ind][1]
            e2 = facets[ind][2]
            ang = ang_adj[ind]
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
                d1 = dx[slice((e2[0] + 1) / 2, shp[0] + (e2[0] - 1) / 2)]
                d2 = dy[slice((e2[0] + 1) / 2, shp[0] + (e2[0] - 1) / 2)]
                if d1.size == 0:
                    d1 = np.array([dx[0]])
                    d2 = np.array([dy[0]])
            else:
                d2 = dx[slice((e1[0] + 1) / 2, shp[0] + (e1[0] - 1) / 2)]
                d1 = dy[slice((e1[0] + 1) / 2, shp[0] + (e1[0] - 1) / 2)]
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


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
