# --------------------------------------------------------------------------
# SSEBop_Landsat_OverpassETa.py
# Updated: 2017-3-22
# Author: Mac Friedrichs, SGT Inc. and Matt Schauer, Innovate!, Inc., USGS EROS
# Credit: Gabriel Senay, USGS EROS
# Email: mackenzie.friedrichs.ctr@usgs.gov, matthew.schauer.ctr@usgs.gov, or senay@usgs.gov
# Usage: Land Surface Temperature, Normalized Difference Vegetation Index, and Actual Evapotranspiration (SSEBop)
#             raster calculation using Landsat 5,7 and/or 8 data
# Description: Uses landsat .tar.gz files and extracts bands, calculates and saves NDVI, LST, ETa rasters (in geotiff)
# NOTE: This script is designed to handle Pre-Collection 1 Landsat filenames. Collection 1 uses 2 digit month and date instead of day of year in their filenames.

# NOTE: In order to help avoid script errors do NOT use spaces in filepaths

# NOTE: Model procedures, code, data, and products are provisional and subject to change.
#            Please refer to Senay et al, 2013 or email for more information about SSEBop Evapotranspiration
#            for consumptive use estimates through remote sensing capabilities.
# --------------------------------------------------------------------------

# Import system modules
import arcpy
from arcpy.sa import *
from arcpy import env
import string, glob, os
import sys, tarfile
import itertools
import traceback
from itertools import izip
import math, fnmatch
import shutil, datetime
import subprocess
from subprocess import Popen, PIPE
import numpy as np
import numpy.ma as ma

# Check out necessary licenses, Set Environment settings
arcpy.CheckOutExtension("spatial")
arcpy.gp.overwriteOutput = True
arcpy.env.extent = "MINOF"
arcpy.env.cellSize = "MINOF"
Coordsystem = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"

try:
    # ----------------------------------------
    # USER INPUTS:

    # Scaling coefficient (k)
    Kfactor = 1.25  # 1.25 for grass reference ET, else use 1

    # Directory with all unzipped landsat .tar files (directory can contain just one scene or any number of scenes, and it will loop through them)
    directory = raw_input(
        "Enter directory with zipped (.tar.gz) Landsat scene(s):")  # These are the scenes to be processed.  REQUIRES DIRECTORY CONTAINING L1T SCENES. This can be hardcoded by placing the string file path here instead.

    # Earth-Sun distance lookup table
    esuntable = raw_input(
        "Enter folder path containing Earth-Sun distance table:") + os.sep + "EarthSunDistanceTable.txt"  # This can be hardcoded by placing the string file path here instead.

    demfolder = raw_input('Directory with DEM elevation file:')
    dem = arcpy.Raster(demfolder + os.sep + 'gmted2010' + '.tif')

    # Set working directory
    env.workspace = directory
    dirpath = env.workspace

    # Scratch Workspace
    scratch_folder = directory + os.sep + "scratch"  # raw_input("Enter a scratch folder path:")
    if not os.path.exists(scratch_folder):
        os.mkdir(scratch_folder)
    env.workspace = scratch_folder

    # Create scene folders and place corresponding unzipped .tar.gz files there
    for filename in os.listdir(dirpath):
        if fnmatch.fnmatch(filename, '*.gz'):  # skips over scratch folder
            print filename
            scenepath = dirpath + os.sep + filename
            scenedate = str(filename)[-19:-12]  # returns YYYYJJJ (ie 2013307)
            scenefolder = directory + os.sep + str(scenedate)
            if not os.path.exists(scenefolder):
                os.mkdir(scenefolder)
            shutil.move(scenepath, scenefolder)

    # Create output directory
    outputfolder = raw_input(
        'Enter any folder path directory for new output rasters:')  # directory + os.sep + "SavedOutputs"
    if not os.path.exists(outputfolder):
        os.mkdir(outputfolder)

    # ----------------Set up workspace and read landsat scene info------------
    for file in sorted(os.listdir(dirpath)):
        if file.startswith(('1',
                            '2')):  # only loops through the numbered folders with landsat .tar.gz files needing to be processed.
            print "--------------------------------------------------"
            print 'scene being processed is ' + str(file)
            env.workspace = directory + os.sep + file
            input = env.workspace
            for filename in os.listdir(input):
                openfile = input + os.sep + filename

            metafilepath = input + os.sep + "*.txt"
            inputtable = esuntable
            Landsat = str(filename)[2:3]  # Identify which Landsat type
            Year = str(filename)[-19:-15]  # Identify which Year
            Jdate = str(filename)[-15:-12]  # Identify which DOY
            scenedate = Year + Jdate
            remfolder = dirpath + os.sep + scenedate

            # ----------------------------------------------------------------
            # ----------------------------------------------------------------
            #   Fmask Cloud masking executable can be
            #   called by uncommenting the code below.
            #
            #   NOTE: Only prerequisite is downloading and installing
            #   the Fmask.exe file per installation instructions found
            #   at https://code.google.com/p/fmask/
            #
            #   Alternatively,
            #   The CFmask cloud mask product can be freely obtained through
            #   USGS ESPA (http://espa.cr.usgs.gov/) or via Earth Explorer
            #   Surface Reflectance orders of Landsat data.
            # ----------------------------------------------------------------
            # ----------------------------------------------------------------

            print 'Not creating cloud mask.'

            ##        # ---------------------------Run Fmask Process----------------------
            # Copy Fmask.exe to directory and run Fmask
            #            try:
            #                fmask_dir = raw_input("Enter folder containing Fmask.exe file:") # Or change this directory to point to the fmask.exe file location
            #                fmask = '%s\Fmask.exe' %fmask_dir
            #                fmask_out = outputfolder + os.sep + 'Fmask'
            #                if not os.path.exists(fmask_out):
            #                    os.mkdir(fmask_out)
            #                shutil.copy(fmask, input)
            #                print 'Beginning Fmask processing...'
            #                #print "Fmask.exe copied."
            #
            #                defdir = os.getcwd() #remember default directory
            #                os.chdir(input)  # change dir to run fmask.exe
            #                p = subprocess.Popen(['Fmask.exe'], stdout=subprocess.PIPE)
            #                output = p.communicate()[0]
            #                #print output
            #
            #                for file in os.listdir(input):
            #                    if fnmatch.fnmatch(file, "*_MTLFmask"):
            #                        mtlf = input + os.sep + file
            #
            #                os.rename(mtlf, mtlf + '.tif')
            #                fmask_new = mtlf + '.tif'
            #                fmask_hdr = mtlf + '.hdr'
            #                rasname = os.path.split(str(mtlf))[1] + '.tif'
            #                shutil.move(fmask_new, fmask_out)
            #                shutil.move(fmask_hdr, fmask_out)
            #                os.remove('%s\Fmask.exe' %input)
            #                os.chdir(defdir) #change back to default directory
            #
            #            except:
            #                print 'Fmask tool did not run properly.'
            #                print traceback.print_exc()
            #
            #            # Reclassify fmask and save
            #            reclassfolder = fmask_out + os.sep + 'Reclassified'
            #            if not os.path.exists(reclassfolder):
            #                os.mkdir(reclassfolder)
            #            fmask_reclass = reclassfolder + os.sep + str(scenedate) + "_Fmask_reclass" + '.tif'
            #            env.workspace = fmask_out
            #            masklist = arcpy.ListRasters()
            #            for mask in masklist:
            #                if str(mask) == rasname:
            #                    fmask1 = Raster(fmask_out + os.sep + mask)
            #                    #print fmask1
            #            outReclass = Reclassify(fmask1, "Value", RemapRange([[0,1,0],[2,4,1],[5,255,0]])) #Cloud and shadow becomes value of 1, all else becomes value of 0
            #            outReclass.save(fmask_reclass)
            #
            #            print 'Completed Fmask.'

            # ----------Set up Daily Input Data Directories-----------------
            # Will use a created Median MODIS Albedo product, 1km.    (MCD43B3)
            Albedo_folder = raw_input("Enter folder containing Albedo input rasters:")
            env.workspace = Albedo_folder
            Albedo = arcpy.ListRasters("*" + Jdate + "*", "All")[0]
            print Albedo

            # Will use a created Median Daymet Tmax product, 800m.  (http://www.scrimhub.org/resources/topowx/)
            Tmax_folder = raw_input("Enter folder containing Max Air Temp input rasters:")
            env.workspace = Tmax_folder
            Tmax = arcpy.ListRasters("*" + Jdate + "*", "All")[0]
            print Tmax

            # Will use a created Median DT (from Daymet) product, 1km.    (Senay et al, 2013)
            dT_folder = raw_input("Enter folder containing Temperature Difference (DT) input rasters:")
            env.workspace = dT_folder
            dT = arcpy.ListRasters("*" + Jdate + "*", "All")[0]
            print dT

            # Will use a created Median GDAS Ref ET product, 4km.   (http://metdata.northwestknowledge.net/)
            ETom_folder = raw_input("Enter folder containing Reference (Potential) ET input rasters:")
            env.workspace = ETom_folder
            ETom = arcpy.ListRasters("*" + Jdate + "*", "All")[0]
            print ETom

            print "Landsat " + str(Landsat)
            print "Year is " + str(Year)
            print "Day is " + str(Jdate)
            print "Unzipping bands..."

            # --------------Unzip/Extract .TAR file ----> Bands,Metadata table
            try:
                tar = tarfile.open(openfile)
                for item in tar:
                    tar.extract(item, path=input)
            except:
                name = os.path.basename(sys.argv[1])
                print name[:name.rfind('.')], '<filename>'

            print 'Beginning NDVI processing...'
            # --------Process Landsat scene according to sensor type --> Landsat 5, 7, or 8 only------------

            if Landsat == '5':
                # Bands 3,4,6 Radiance Constants (landsat 5)
                Lmax3 = 264
                Lmin3 = -1.17
                Ldiff3 = 265.17
                Lmax4 = 221
                Lmin4 = -1.51
                Ldiff4 = 222.51
                Lmax6 = 15.303
                Lmin6 = 1.238
                Ldiff6 = 14.065
                Qcalmax = 255
                Qcalmin = 1
                Qcaldiff = 254

                # LST Radiance to Temperature Constants (landsat 5)
                K1 = 607.76
                K2 = 1260.56

                # NDVI Reflectance Coefficients
                esun3 = 1533  # Band 3 Spectral Irradiance
                esun4 = 1039  # Band 4 Spectral Irradiance

                # Open metadata file and get sun elevation value
                for textfile in glob.glob(metafilepath):
                    if fnmatch.fnmatch(textfile, '*MTL.txt'):
                        metafile = open(textfile, 'r')
                for line in metafile:
                    if "SUN_ELEVATION" in line:
                        elevalue = line.split()[-1]
                metafile.close()

                sunelev = float(elevalue)
                zenith = math.cos(90 - sunelev)

                # Get Earth-Sun distance based on julian date
                esdtable = open(inputtable)
                for line in esdtable.readlines():
                    if line.startswith(Jdate):
                        esdvalue = line.split()[-1]
                esdtable.close()

                d2 = float(esdvalue) * float(esdvalue)  # earth sun distance--squared

                # --------------Create NDVI and LST grids-----------------

                env.workspace = input
                BandList = arcpy.ListRasters()
                for Band in BandList:
                    # LST calculation (1/2)
                    if "B6" in Band:
                        lst = ((Ldiff6 / Qcaldiff) * (Raster(Band) - Qcalmin) + Lmin6)  # Conversion to TOA Radiance

                # NDVI calculation
                for Band in BandList:
                    if "B3" in Band:
                        ndvi30 = Raster(Band)
                        ndvi30rad = ((Ldiff3 / Qcaldiff) * (Raster(Band) - Qcalmin) + Lmin3)  # Conversion to Radiance
                        ndvi30ref = (3.14159 * ndvi30rad * d2) / (esun3 * zenith)  # Radiance to Reflectance
                for Band in BandList:
                    if "B4" in Band:
                        ndvi40 = Raster(Band)
                        ndvi40rad = ((Ldiff4 / Qcaldiff) * (Raster(Band) - Qcalmin) + Lmin4)  # Conversion to Radiance
                        ndvi40ref = (3.14159 * ndvi40rad * d2) / (esun4 * zenith)  # Radiance to Reflectance

                        ndvi = (Float(ndvi40ref - ndvi30ref)) / (Float(ndvi40ref + ndvi30ref))  # TOA NDVI

                # Set up output folders and save NDVI output
                outNDVI = outputfolder + os.sep + "NDVI"
                if not os.path.exists(outNDVI):
                    os.mkdir(outNDVI)
                outLST = outputfolder + os.sep + "LST"
                if not os.path.exists(outLST):
                    os.mkdir(outLST)
                outNDVI_file = outNDVI + os.sep + "ndvi" + scenedate + ".tif"
                arcpy.ProjectRaster_management(ndvi, outNDVI_file, Coordsystem)  # Reprojects output as GCS_WGS 1984

                print 'Created NDVI file.'
                print 'Beginning LST processing...'

                # LST calculation (2/2) -- created using corrected thermal radiance
                # This is a combination of correction methods from Sobrino (2004) & Allen (2007).

                tnb = 0.866  # narrow band transmissivity of air
                rp = 0.91  # path radiance
                rsky = 1.32  # narrow band downward thermal radiation from a clear sky

                # Emissivity correction algorithm based on NDVI, not LAI
                ndviRangevalue = Con((ndvi >= 0.2) & (ndvi <= 0.5), ndvi)
                Pv = ((ndviRangevalue - 0.2) / 0.3) ** 2
                dE = ((1 - 0.97) * (1 - Pv) * (0.55) * (
                    0.99))  # Assuming typical Soil Emissivity of 0.97 and Veg Emissivity of 0.99 and shape Factor mean value of 0.553
                RangeEmiss = ((0.99 * Pv) + (0.97 * (1 - Pv)) + dE)
                Emissivity = Con(ndvi < 0, 0.985, Con((ndvi >= 0) & (ndvi < 0.2), 0.977, Con(ndvi > 0.5, 0.99, Con(
                    (ndvi >= 0.2) & (ndvi <= 0.5), RangeEmiss))))
                rc = ((lst - rp) / tnb) - ((rsky) * (1 - Emissivity))
                lst2 = (K2 / Ln(((K1 * Emissivity) / rc) + 1))
                lstfinal = Con(lst2 > 200, lst2)

                # Save LST output
                outLST_file = outLST + os.sep + "lst" + scenedate + ".tif"
                arcpy.ProjectRaster_management(lstfinal, outLST_file, Coordsystem)  # Reprojects output as GCS_WGS 1984

                print 'Created LST file.'

                # Move the .tar.gz file to dirpath, delete unzipped contents of subfolders
                tar.close()
                shutil.move(openfile, dirpath)
            ##                deleterasters = arcpy.ListRasters()
            ##                for ras in deleterasters:
            ##                    arcpy.Delete_management(ras)

            elif Landsat == '7':
                # Bands 3,4,6 Radiance Constants (landsat 7)
                Qcalmax = 255
                Qcalmin = 1
                Qcaldiff = 254

                # LST Radiance to Temperature Constants (landsat 7)
                K1 = 666.09
                K2 = 1282.71

                # NDVI Reflectance Coefficients
                esun3 = 1533  # Band 3 Spectral Irradiance
                esun4 = 1039  # Band 4 Spectral Irradiance

                # Open metadata file and get sun elevation value & band radiance coefficients
                for textfile in glob.glob(metafilepath):
                    if fnmatch.fnmatch(textfile, '*MTL.txt'):
                        metafile = open(textfile, 'r')
                for line in metafile:
                    if "SUN_ELEVATION" in line:
                        elevalue = line.split()[-1]
                    if "RADIANCE_MINIMUM_BAND_3" in line:
                        Lmin3value = line.split()[-1]
                        Lmin3 = float(Lmin3value)
                    if "RADIANCE_MAXIMUM_BAND_3" in line:
                        Lmax3value = line.split()[-1]
                        Lmax3 = float(Lmax3value)
                    if "RADIANCE_MINIMUM_BAND_4" in line:
                        Lmin4value = line.split()[-1]
                        Lmin4 = float(Lmin4value)
                    if "RADIANCE_MAXIMUM_BAND_4" in line:
                        Lmax4value = line.split()[-1]
                        Lmax4 = float(Lmax4value)
                    if "RADIANCE_MINIMUM_BAND_6_VCID_1" in line:
                        Lmin6value = line.split()[-1]
                        Lmin6_1 = float(Lmin6value)
                    if "RADIANCE_MAXIMUM_BAND_6_VCID_1" in line:
                        Lmax6value = line.split()[-1]
                        Lmax6_1 = float(Lmax6value)
                metafile.close()

                Ldiff3 = Lmax3 - Lmin3
                Ldiff4 = Lmax4 - Lmin4
                Ldiff6_1 = Lmax6_1 - Lmin6_1

                sunelev = float(elevalue)
                zenith = math.cos(90 - sunelev)

                # Get Earth-Sun distance based on julian date
                esdtable = open(inputtable)
                for line in esdtable.readlines():
                    if line.startswith(Jdate):
                        esdvalue = line.split()[-1]
                esdtable.close()
                d2 = float(esdvalue) * float(esdvalue)  # earth sun distance--squared

                # --------------Create NDVI and LST grids-------------

                env.workspace = input
                BandList = arcpy.ListRasters()
                # print BandList
                for Band in BandList:
                    # LST calculation (1/2)
                    if "B6_VCID_1" in Band:
                        lst = ((Ldiff6_1 / Qcaldiff) * (Raster(Band) - Qcalmin) + Lmin6_1)  # Conversion to TOA Radiance

                        # NDVI calculation
                for Band in BandList:
                    if "B3" in Band:
                        ndvi30 = Raster(Band)
                        ndvi30rad = ((Ldiff3 / Qcaldiff) * (Raster(Band) - Qcalmin) + Lmin3)  # Conversion to Radiance
                        ndvi30ref = (3.14159 * ndvi30rad * d2) / (esun3 * zenith)  # Radiance to Reflectance

                for Band in BandList:
                    if "B4" in Band:
                        ndvi40 = Raster(Band)
                        ndvi40rad = ((Ldiff4 / Qcaldiff) * (Raster(Band) - Qcalmin) + Lmin4)  # Conversion to Radiance
                        ndvi40ref = (3.14159 * ndvi40rad * d2) / (esun4 * zenith)  # Radiance to Reflectance

                        ndvi = (Float(ndvi40ref - ndvi30ref)) / (Float(ndvi40ref + ndvi30ref))  # TOA NDVI

                # Save NDVI output
                outNDVI = outputfolder + os.sep + "NDVI"
                if not os.path.exists(outNDVI):
                    os.mkdir(outNDVI)
                outNDVI_file = outNDVI + os.sep + "ndvi" + scenedate + ".tif"
                arcpy.ProjectRaster_management(ndvi, outNDVI_file, Coordsystem)  # Reprojects output as GCS_WGS 1984

                print 'Created NDVI file.'
                print 'Beginning LST processing...'

                # LST calculation (2/2) -- created using corrected thermal radiance
                # This is a combination of correction methods from Sobrino (2004) & Allen (2007).

                tnb = 0.866  # narrow band transmissivity of air
                rp = 0.91  # path radiance
                rsky = 1.32  # narrow band downward thermal radiation from a clear sky

                # Emissivity correction algorithm based on NDVI, not LAI
                ndviRangevalue = Con((ndvi >= 0.2) & (ndvi <= 0.5), ndvi)
                Pv = ((ndviRangevalue - 0.2) / 0.3) ** 2
                dE = ((1 - 0.97) * (1 - Pv) * (0.55) * (
                    0.99))  # Assuming typical Soil Emissivity of 0.97 and Veg Emissivity of 0.99 and shape Factor mean value of 0.553
                RangeEmiss = ((0.99 * Pv) + (0.97 * (1 - Pv)) + dE)
                Emissivity = Con(ndvi < 0, 0.985, Con((ndvi >= 0) & (ndvi < 0.2), 0.977, Con(ndvi > 0.5, 0.99, Con(
                    (ndvi >= 0.2) & (ndvi <= 0.5), RangeEmiss))))
                rc = ((lst - rp) / tnb) - ((rsky) * (1 - Emissivity))
                lst2 = (K2 / Ln(((K1 * Emissivity) / rc) + 1))
                lstfinal = Con(lst2 > 200, lst2)

                # Save LST output
                outLST = outputfolder + os.sep + "LST"
                if not os.path.exists(outLST):
                    os.mkdir(outLST)
                outLST_file = outLST + os.sep + "lst" + scenedate + ".tif"
                arcpy.ProjectRaster_management(lstfinal, outLST_file, Coordsystem)  # Reprojects output as GCS_WGS 1984

                print 'Created LST file.'

                # Move the .tar.gz file to dirpath, delete unzipped contents of subfolders
                tar.close()
                shutil.move(openfile, dirpath)
            ##                deleterasters = arcpy.ListRasters()
            ##                for ras in deleterasters:
            ##                    arcpy.Delete_management(ras)

            elif Landsat == '8':
                # LST Radiance to Temperature Coefficients (Landsat 8 Constants)
                K1_10 = 774.89  # band 10
                K2_10 = 1321.08  # band 10
                K1_11 = 480.89  # band 11
                K2_11 = 1201.14  # band 11

                # Bands 4 and 5 reflectance rescale values
                MP4value = 0.00002
                AP4value = -0.1
                MP5value = 0.00002
                AP5value = -0.1

                # Open metadata file and get coefficients and scaling factor values
                for textfile in glob.glob(metafilepath):
                    if fnmatch.fnmatch(textfile, '*MTL.txt'):
                        metafile = open(textfile, 'r')
                for line in metafile:
                    if "SUN_ELEVATION" in line:
                        elevalue = line.split()[-1]
                    if "EARTH_SUN_DISTANCE" in line:
                        esdvalue = line.split()[-1]
                    if "RADIANCE_MULT_BAND_4" in line:
                        ML4 = line.split()[-1]
                        ML4value = float(ML4)
                    if "RADIANCE_ADD_BAND_4" in line:
                        AL4 = line.split()[-1]
                        AL4value = float(AL4)
                    if "RADIANCE_MULT_BAND_5" in line:
                        ML5 = line.split()[-1]
                        ML5value = float(ML5)
                    if "RADIANCE_ADD_BAND_5" in line:
                        AL5 = line.split()[-1]
                        AL5value = float(AL5)
                    if "RADIANCE_MULT_BAND_10" in line:
                        ML10 = line.split()[-1]
                        ML10value = float(ML10)
                    if "RADIANCE_ADD_BAND_10" in line:
                        AL10 = line.split()[-1]
                        AL10value = float(AL10)
                    if "RADIANCE_MULT_BAND_11" in line:
                        ML11 = line.split()[-1]
                        ML11value = float(ML11)
                    if "RADIANCE_ADD_BAND_11" in line:
                        AL11 = line.split()[-1]
                        AL11value = float(AL11)
                metafile.close()

                sunelev = float(elevalue)
                zenith = math.cos(90 - sunelev)

                # ---------------Create NDVI and LST grids---------------

                env.workspace = input
                BandList = arcpy.ListRasters()  # (lists each extracted scene band)
                for Band in BandList:
                    # LST calculation (1/2)
                    # Band 10 DN conversion to TOA Radiance
                    if "B10" in Band:
                        lst10_rad = ((Raster(Band) * ML10value) + AL10value)  # Conversion to TOA Radiance

                        # NDVI calculation
                        # Band 4 DN conversion to TOA Reflectance
                for Band in BandList:
                    if "B4" in Band:
                        ndvi40 = (
                            (Raster(Band) * MP4value) + AP4value)  # TOA reflectance w/o correction for solar angle
                        ndvi40ref = (ndvi40 / zenith)  # TOA planetary reflectance

                        # Band 5 DN conversion to TOA Reflectance
                for Band in BandList:
                    if "B5" in Band:
                        ndvi50 = (
                            (Raster(Band) * MP5value) + AP5value)  # TOA reflectance w/o correction for solar angle
                        ndvi50ref = (ndvi50 / zenith)  # TOA planetary reflectance

                        ndvi = (Float(ndvi50ref - ndvi40ref)) / (Float(ndvi50ref + ndvi40ref))  # TOA NDVI

                # Save NDVI output
                outNDVI = outputfolder + os.sep + "NDVI"
                if not os.path.exists(outNDVI):
                    os.mkdir(outNDVI)
                outNDVI_file = outNDVI + os.sep + "ndvi" + scenedate + ".tif"
                arcpy.ProjectRaster_management(ndvi, outNDVI_file, Coordsystem)  # Reprojects output as GCS_WGS 1984

                print 'Created NDVI file.'
                print 'Beginning LST processing...'

                # LST calculation (2/2) -- created using corrected thermal radiance
                # This is a combination of correction methods from Sobrino (2004) & Allen (2007).

                tnb = 0.866  # narrow band transmissivity of air
                rp = 0.91  # path radiance
                rsky = 1.32  # narrow band downward thermal radiation from a clear sky

                # Emissivity correction algorithm based on NDVI, not LAI
                ndviRangevalue = Con((ndvi >= 0.2) & (ndvi <= 0.5), ndvi)
                Pv = ((ndviRangevalue - 0.2) / 0.3) ** 2
                dE = ((1 - 0.97) * (1 - Pv) * (0.55) * (
                    0.99))  # Assuming typical Soil Emissivity of 0.97 and Veg Emissivity of 0.99 and shape Factor mean value of 0.553
                RangeEmiss = ((0.99 * Pv) + (0.97 * (1 - Pv)) + dE)
                Emissivity = Con(ndvi < 0, 0.985, Con((ndvi >= 0) & (ndvi < 0.2), 0.977, Con(ndvi > 0.5, 0.99, Con(
                    (ndvi >= 0.2) & (ndvi <= 0.5), RangeEmiss))))

                # lst10 radiance to LST
                rc10 = ((lst10_rad - rp) / tnb) - ((rsky) * (1 - Emissivity))
                lst10_final = (K2_10 / Ln(((
                                               K1_10 * Emissivity) / rc10) + 1))  # <------At-satellite brightness temperature which is emissivity-and-atmoshperically-corrected to represent actual Land Surface Temperature
                lstfinal = Con(lst10_final > 200, lst10_final)

                # Save LST output
                outLST10 = outputfolder + os.sep + "LST"
                if not os.path.exists(outLST10):
                    os.mkdir(outLST10)
                outLST_file = outLST10 + os.sep + "lst" + scenedate + ".tif"
                arcpy.ProjectRaster_management(lstfinal, outLST_file, Coordsystem)  # Reprojects output as GCS_WGS 1984

                print 'Created LST file.'

                # Move the .tar.gz file to dirpath, delete subfolder contents
                tar.close()
                shutil.move(openfile, dirpath)
            ##                deleterasters = arcpy.ListRasters()
            ##                for ras in deleterasters:
            ##                    arcpy.Delete_management(ras)

            # ---------Process SSEBop ETa using input data and surface temperature from landsat---------

            # In order to correspond the maximum air temperature with cold/wet limiting environmental conditions,
            # the SSEBop model uses a correction coefficient (C-factor) uniquely calculated for each Landsat scene
            # from well-watered/vegetated pixels. This temperature correction component is based on a ratio of Tmax
            # and Land Surface Temperature that has passed through several conditions such as NDVI limits. 

            # Make sure the correct inputs are available for image DOY
            try:
                if ETom[-7:-4] == Jdate and dT[-7:-4] == Jdate and Tmax[-7:-4] == Jdate and Albedo[
                                                                                            -7:-4] == Jdate:  # These match up based on input naming convention + .tif or .img
                    dt = Raster(dT_folder + os.sep + dT)
                    albedo = Raster(Albedo_folder + os.sep + Albedo)
                    eto = Raster(ETom_folder + os.sep + ETom)
                    tmax = Raster(Tmax_folder + os.sep + Tmax)
                    # print dTras
                    # print Albedoras
                    # print ETomras
                    # print Tmaxras
                    print 'Beginning ETa processing...'
                    lst = arcpy.Raster(outLST_file)
                    ndvi = arcpy.Raster(outNDVI_file)

                    k = Kfactor

                    env.workspace = scratch_folder

                    print 'Beginning c factor calculation...'
                    # This calculates a unique c factor for each landsat scene
                    tcorr = (lst / tmax)  # Use a sample of this ratio to create the Cold Boundary condition
                    tdiff = (
                        tmax - lst)  # Tdiff is used both as a c factor condition as well as a supplement to the cloud mask
                    var = [0.70, 1.00]  # NDVI limits
                    var2 = [0, 1, 10, 270]  # Tcorr Condition Limits
                    # Filter the Tcorr by Tdiff between 0 and 10, NDVI greater than 0.7, and LST greater than 270 K
                    tcorr2 = Con(
                        (lst > var2[3]) & (tdiff > var2[0]) & (tdiff <= var2[2]) & (ndvi >= var[0]) & (ndvi < var[1]),
                        tcorr)
                    # Collect the mean and the standard deviation of the conditioned Tcorr raster                    
                    mean = tcorr2.mean
                    std = tcorr2.standardDeviation
                    if mean > 0.0 and std > 0.0:  # Check to make sure there are valid values
                        # The c factor is the mean minus 2 standard deviations of the conditioned Tcorr raster
                        cfactor = mean - (std * 2)
                        print 'The c factor is: ' + str(cfactor)

                        # Create a mask based on temperature difference from Tdiff 
                        # Can use this in conjunction with a cloud mask or individually (default)

                        # clouds = Con((fmask == 1)&(lst>200),1,0) # If using Fmask, uncomment this line
                        tdiffCon = Con((lst > 200) & (tdiff > 10) & (ndvi > 0), 1,
                                       0)  # Creates a mask with valid LST pixels, Tdiff greater than +10, and positive NDVI (not water)
                        # lst = Con((clouds < 1)&(tdiffCon < 1), lst) # If using Fmask, uncomment this line
                        lst = Con(tdiffCon < 1,
                                  lst)  # Excludes any LST pixels with Tdiff greater than 10 (very cold!) # If using Fmask, comment out this line

                        # Sets dT thresholds to between 6 and 25 K                        
                        dtcon = Con(dt < 6, 6, dt)
                        dtcon2 = Con(dtcon > 25, 25, dtcon)

                        # Environmental Lapse Rate Correction to correct for colder temperatures at higher elevation
                        # Uses the elevation raster for pixels above elevation limit in meters 
                        # corrects the Tmax by three degrees Kelvin for every kilometer rise.
                        tmax = Con(dem > 1500, tmax - (0.003 * (dem - 1500)), tmax)

                        # Standard SSEBop ET process using the conditioned LST, Tmax, and dT rasters and unique c factor

                        # Temperature Cold & Hot calculation
                        Tcold = tmax * cfactor
                        Thot = Tcold + dtcon2

                        # LSTa calculation: albedo corrected surface temperature in very bright desert-like areas, using a Median Albedo value assumes little change over time.
                        lstCon = Con((albedo >= 250) & (albedo <= 1000), lst + 0.1 * (albedo - 250), lst)

                        # ETx is the scene 'ET fraction' grid used with reference ET data for actual ET estimates
                        ETf = (Thot - lstCon) / dt
                        ETfCon = Con(ETf < 0, 0,
                                     Con((ETf >= 0) & (ETf <= 1.05), ETf, Con((ETf > 1.05) & (ETf < 1.3), 1.05)))

                        # It is recommended to use Fmask (or CFmask) to mask out clouds and create NoData value (e.g. -999)
                        #                        ETfCon = Con(ETf < 0, 0, Con((ETf >= 0) & (ETf <= 1.05), ETf, Con((ETf > 1.05) & (ETf < 1.3), 1.05, -999)))
                        #                        MaskETfCON = Con((fmask) > 0, -999, ETxCon)
                        #                        NoDataRaster = IsNull(MaskETxCON)
                        #                        MaskETxCON1 = Con(NoDataRaster == 1, -999, MaskETxCON)
                        #                        ETx = MaskETxCON1
                        #                        print "NoData converted to -999"

                        ETx = ETfCon

                        ETx_path = outputfolder + os.sep + "ETf"
                        if not os.path.exists(ETx_path):
                            os.mkdir(ETx_path)
                        MaskETxfile = ETx_path + os.sep + "etf" + scenedate + ".tif"
                        arcpy.CopyRaster_management(ETx, MaskETxfile, "", "", "", "", "", "32_BIT_FLOAT")
                        print 'Saved ETf raster'

                        # ETa calculation + Save Overpass ETa

                        ETa = ETx * (
                            eto * k)  # Multiplies the Landsat overpass ET fraction times the reference ET gridded raster to create actual ET on day of overpass.

                        ETacon = Con(ETa < 0, 0, ETa)  # Sets the lower limit of ETa to zero

                        ETa_path = outputfolder + os.sep + "ETa"
                        if not os.path.exists(ETa_path):
                            os.mkdir(ETa_path)
                        ETafile = ETa_path + os.sep + "aet" + scenedate + ".tif"
                        arcpy.CopyRaster_management(ETacon, ETafile, "", "", "", "", "", "32_BIT_FLOAT")

                        print 'Created Overpass ETa file.'

                    else:
                        # SSEBop Temperature Correction factor
                        print 'Cannot calculate c factor. Using a median c factor...'
                        medianCfactor = 0.978  # Temperature correction coefficient (c-factor).  0.978 is a recommended median value. Subject to variability.
                        cfactor = medianCfactor

                        # Create a mask based on temperature difference from Tdiff 
                        # Can use this in conjunction with a cloud mask or individually

                        # clouds = Con((fmask == 1)&(lst>200),1,0) # If using Fmask, uncomment this line
                        tdiffCon = Con((lst > 200) & (tdiff > 10) & (ndvi > 0), 1,
                                       0)  # Creates a mask with valid LST pixels, Tdiff greater than +10, and positive NDVI (not water)
                        # lst = Con((clouds < 1)&(tdiffCon < 1), lst) # If using Fmask, uncomment this line
                        lst = Con(tdiffCon < 1,
                                  lst)  # Excludes any LST pixels with Tdiff greater than 10 (very cold) # If using Fmask, comment out this line

                        # Sets dT thresholds to between 6 and 25 K                        
                        dtcon = Con(dt < 6, 6, dt)
                        dtcon2 = Con(dtcon > 25, 25, dtcon)

                        # Environmental Lapse Rate Correction to correct for colder temperatures at higher elevation
                        # Uses the elevation raster for pixels above elevation limit in meters 
                        # corrects the Tmax by three degrees Kelvin for every kilometer rise
                        tmax = Con(dem > 1500, tmax - (0.003 * (dem - 1500)), tmax)

                        # Standard SSEBop ET process using the conditioned LST, Tmax, and dT rasters and unique c factor

                        # Temperature Cold & Hot calculation
                        Tcold = tmax * cfactor
                        Thot = Tcold + dtcon2

                        # LSTa calculation: albedo corrected surface temperature in very bright desert-like areas, using a Median Albedo value assumes little change over time.
                        lstCon = Con((albedo >= 250) & (albedo <= 1000), lst + 0.1 * (albedo - 250), lst)

                        # ETx is the scene 'ET fraction' grid used with reference ET data for actual ET estimates
                        ETf = (Thot - lstCon) / dt
                        ETfCon = Con(ETf < 0, 0,
                                     Con((ETf >= 0) & (ETf <= 1.05), ETf, Con((ETf > 1.05) & (ETf < 1.3), 1.05)))

                        # It is recommended to use Fmask (or CFmask) to mask out clouds and create NoData value (e.g. -999)
                        #                        ETfCon = Con(ETf < 0, 0, Con((ETf >= 0) & (ETf <= 1.05), ETf, Con((ETf > 1.05) & (ETf < 1.3), 1.05, -999)))
                        #                        MaskETfCON = Con((fmask) > 0, -999, ETxCon)
                        #                        NoDataRaster = IsNull(MaskETxCON)
                        #                        MaskETxCON1 = Con(NoDataRaster == 1, -999, MaskETxCON)
                        #                        ETx = MaskETxCON1
                        #                        print "NoData converted to -999"

                        ETx = ETfCon

                        ETx_path = outputfolder + os.sep + "ETf"
                        if not os.path.exists(ETx_path):
                            os.mkdir(ETx_path)
                        MaskETxfile = ETx_path + os.sep + "etf" + scenedate + ".tif"
                        arcpy.CopyRaster_management(ETx, MaskETxfile, "", "", "", "", "", "32_BIT_FLOAT")
                        print 'Saved ETf raster'

                        # ETa calculation + Save Overpass ETa

                        ETa = ETx * (
                            eto * k)  # Multiplies the Landsat overpass ET fraction times the reference ET gridded raster to create actual ET on day of overpass.

                        ETacon = Con(ETa < 0, 0, ETa)  # Sets the lower limit of ETa to zero

                        ETa_path = outputfolder + os.sep + "ETa"
                        if not os.path.exists(ETa_path):
                            os.mkdir(ETa_path)
                        ETafile = ETa_path + os.sep + "aet" + scenedate + ".tif"
                        arcpy.CopyRaster_management(ETacon, ETafile, "", "", "", "", "", "32_BIT_FLOAT")

                        print 'Created Overpass ETa file.'

                else:
                    print 'Input datasets do not match filename DOY ' + str(Jdate) + '.'
                    break
            except:
                tb = sys.exc_info()[2]
                tbinfo = traceback.format_tb(tb)[0]
                pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n    " + str(
                    sys.exc_type) + ": " + str(sys.exc_value) + "\n"
                arcpy.AddError(pymsg)
                print pymsg

    print 'Overpass ETa completed for landsat scene(s).'

except:
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n    " + str(sys.exc_type) + ": " + str(
        sys.exc_value) + "\n"
    arcpy.AddError(pymsg)
    print pymsg
