#Name:  rsi_tool.py
#Purpose:  ArcGIS Script Tool for calculating Regional Snowfall Index
#Usage: This script is designed to run from RSITool Script Tool in ArcGIS, but
#       it can also run interactively from the command prompt.
#
#Command Prompt Usage:  rsi_tool.py <snowstorms> <popGrid> <regions> <output>
#Command Prompt Example:
#  rsi_tool.py "C:/Temp/GHCND_19930312_19930315_C.shp" "C:/Temp/pop_grid" \
#              "C:/Temp/regions.shp" "C:/Temp/output"
#
#Author:  Jon Burroughs (jdburrou)
#Date: 4/29/2012

import sys, os, datetime, traceback, arcpy

from rsi_parameters import parameters

def isScriptTool() :
    """Checks to see if tool is running from a Script Tool context"""
    param = arcpy.GetParameter(0)
    if param :
        return True
    else :
        return False    

def getArgs() :
    """Gets arguments from either Script Tool or sys.argv, depending on runtime context"""
    # Check if running from Script Tool
    args = {}
    if isScriptTool() :
        args['log'] = arcpy.AddMessage
        args['snowStorms'] = arcpy.GetParameterAsText(0).split(';')
        args['popGrid'] = arcpy.GetParameterAsText(1)
        args['regions'] = arcpy.GetParameterAsText(2)
        args['netCDF'] = arcpy.GetParameter(3)
        args['outputBase'] = os.path.normpath(arcpy.GetParameterAsText(4))
        args['cellSize'] = arcpy.GetParameter(5)
        args['weight'] = arcpy.GetParameter(6)
        args['searchRadius'] = arcpy.GetParameter(7)
    else :
        # We're running from the command line
        args['log'] = lambda msg: sys.stdout.write(msg + "\n")
        args['snowStorms'] = sys.argv[1].split(';')
        args['popGrid'] = sys.argv[2]
        args['regions'] = sys.argv[3]
        args['outputBase'] = sys.argv[4]
        
        # rest are hard-coded... change if you must
        args['netCDF'] = True
        args['cellSize'] = "5000"
        args['weight'] = 2.0
        args['searchRadius'] = "FIXED 100000"
    return args

def getStormId(snowStorm) :
    """Converts long storm name into short grid name"""
    # Derive storm ID from input file.
    # Based on storm start date and duration (in days)
    # ID Format is:
    #    YYYYMMDDdd
    #    YYYY = start year
    #    MM = start month
    #    DD = start day
    #    dd = storm duration in days    
    file = os.path.basename(snowStorm)
    startDate = datetime.date(
        int(file[6:10]),
        int(file[10:12]),
        int(file[12:14]))
    endDate = datetime.date(
        int(file[15:19]),
        int(file[19:21]),
        int(file[21:23]))
    duration = (endDate - startDate).days
    stormId = startDate.strftime("%Y%m%d") + "%02d" % (duration)
    return stormId

def convertNetCDF(grid, ncFile) :
    """Converts grid to NetCDF"""
    arcpy.RasterToNetCDF_md(grid, ncFile)
    log("--> NetCDF Output: %s" % os.path.normpath(ncFile))

def rsiToCategory(index) :
    """Converts Regional Snowfall Index to Category"""
    if index < 1 :
        rcat = 0
    elif index < 3 :
        rcat = 1
    elif index < 6 :
        rcat = 2
    elif index < 10 :
        rcat = 3
    elif index < 18 :
        rcat = 4
    else :
        rcat = 5
    return rcat

class RSITool :
    """Calculates Regional Snowfall Index"""
    
    def __init__(self, snowStorm, regions, popGrid, parameters, outputDir) :
        """Initializes RSITool"""
        self.stormId = getStormId(snowStorm)
        msg = "Initializing stormId=%s" % self.stormId
        log(msg)
        self.snowStorm = snowStorm
        self.regions = regions
        self.popGrid = popGrid
        self.parameters = parameters
        self.outputDir = outputDir
        
        # defaults
        self.cellSize = "5000"
        self.snowField = "Snowfall"
        self.weight = 2.0
        self.searchRadius = "FIXED 100000"
        self.netCDF = True

        # Prep output directory
        if not os.path.exists(outputDir) :
            os.mkdir(outputDir)
        
    def checkForSnow(self) :
        """Checks regions for snow"""
        msg = "Checking regions for snow.  stormId=%s" % self.stormId
        arcpy.SetProgressorLabel(msg)
        log(msg)

        # do point-in-polygon check for at least 1 snow observation       
        poly_sc = arcpy.SearchCursor(self.regions)
        hadSnow = {}
        for poly_row in poly_sc :
            poly = poly_row.Shape
            regionId = poly_row.regionId
            hadSnow[regionId] = False
            point_sc = arcpy.SearchCursor(self.snowStorm)
            for point_row in point_sc :
                point = point_row.Shape
                if poly.contains(point) :
                    hadSnow[regionId] = True
                    break
            del point_row
            del point_sc
        del poly_row
        del poly_sc
        self.hadSnow = hadSnow
        
    def calculateRSI(self) :
        """Calculate Regional Snowfall Index"""
        msg = "Calculating RSI for stormId=%s" % self.stormId
        arcpy.SetProgressorLabel(msg)
        log(msg)
        regionIds = self.parameters.keys()
        self.rindex = {}
        self.rcategory = {}

        # check regions for snow
        self.checkForSnow()

        # process each region
        for id in regionIds :
            if self.hadSnow[id] :

                # get reclassed snowfall and zonal stats
                cgrid = self.classifySnow(id)
                stats = self.calculateStats(cgrid, id)

                # calculate RSI
                cum_areas = []
                cum_pops = []
                normAreas = []
                normPops = []
                meanAreas = self.parameters[id]['meanArea']
                meanPops = self.parameters[id]['meanPop']

                rindex = 0
                i = 0
                sc = arcpy.SearchCursor(stats)
                for row in sc :
                    if row.VALUE == 0 :
                        continue
                    normArea = row.CUM_AREA / float(meanAreas[i])
                    normPop = row.CUM_POP / float(meanPops[i])
                    rindex += (normArea + normPop)
                    i += 1
                del row
                del sc
                self.rindex[id] = rindex
                self.rcategory[id] = rsiToCategory(rindex)
            else :
                log("Skipping regionId=%s.  No Snow." % id)
                self.rindex[id] = 0
                self.rcategory[id] = 0
                
    def interpolateSnow(self) :
        """Uses IDW to interpolate snowfall totals to grid"""
        msg = "Interpolating snowfall.  stormId=%s" % self.stormId
        log(msg)
        arcpy.SetProgressorLabel(msg)

        # interpolate snowfall using IDW        
        arcpy.env.extent = self.regions
        gridFile = self.outputDir + "/S" + self.stormId
        grid = arcpy.sa.Idw(
            self.snowStorm,
            self.snowField,
            self.cellSize,
            self.weight,
            self.searchRadius)
        arcpy.SetProgressorLabel("Saving output...")
        grid.save(gridFile)
        self.snowGrid = gridFile
        log("--> GRID Output: %s" % os.path.normpath(gridFile))

        # save to NetCDF if option is checked        
        if self.netCDF :
            ncFile = gridFile + ".nc"
            convertNetCDF(grid, ncFile)

    def classifySnow(self, regionId) :
        """Reclassifies snowfall for a single region based on regional parameters"""
        msg = "Classifying snowfall.  regionId=%s" % regionId
        log(msg)
        arcpy.SetProgressorLabel(msg)

        # Reclassify snowfall for this region        
        thresholds = arcpy.sa.RemapRange(self.parameters[regionId]['thresholds'])
        regionLyr = "%s_lyr" % regionId
        arcpy.MakeFeatureLayer_management(self.regions, regionLyr, "regionId = '%s'" % regionId)
        gridFile = self.outputDir + "/" + regionId + self.stormId
        grid = arcpy.sa.Reclassify(self.snowGrid, "Value", thresholds)
        maskedGrid = arcpy.sa.ExtractByMask(grid, regionLyr)
        maskedGrid.save(gridFile)
        log("--> GRID Output: %s" % os.path.normpath(gridFile))

        # create NetCDF if option is checked        
        if self.netCDF :
            ncFile = gridFile + ".nc"
            convertNetCDF(maskedGrid, ncFile)
        return gridFile
    
    def calculateStats(self, categoryGrid, regionId) :
        """Calculates zonal snowfall/population statistics for a single region."""
        msg = "Calculating statistics.  regionId=%s" % regionId
        log(msg)
        arcpy.SetProgressorLabel(msg)

        # calculate zonal stats        
        regionIds = self.parameters.keys()
        statsTable = self.outputDir + "/" + regionId + self.stormId + ".dbf"
        arcpy.sa.ZonalStatisticsAsTable(
            categoryGrid, "VALUE", self.popGrid, statsTable, "#", "SUM")
        arcpy.AddField_management(statsTable, "AreaSqMi", "DOUBLE")
        arcpy.AddField_management(statsTable, "CUM_POP", "LONG")
        arcpy.AddField_management(statsTable, "CUM_AREA", "DOUBLE")
        arcpy.CalculateField_management(
            statsTable, "AreaSqMi", "([AREA] / 1000000) * 0.3844")

        # accumulate area and population for each threshold
        pops = []
        areas = []
        sc = arcpy.SearchCursor(statsTable)
        for row in sc :
            pops.append(row.SUM)
            areas.append(row.AreaSqMi)
        del row
        del sc

        areas.reverse()
        pops.reverse()

        uc = arcpy.UpdateCursor(statsTable)
        for row in uc :
            row.CUM_AREA = sum(areas)
            row.CUM_POP = sum(pops)
            uc.updateRow(row)
            areas.pop()
            pops.pop()
        del row
        del uc

        log("--> Table Output: %s" % os.path.normpath(statsTable))
        return statsTable       

    def save(self) :
        """Saves RSI data to output table"""
        log("Saving results.")

        # use region file as the base, add RSI fields        
        outputFile = self.outputDir + "/rsi" + self.stormId + ".shp"
        arcpy.CopyFeatures_management(self.regions, outputFile)
        arcpy.AddField_management(outputFile, "Category", "LONG")
        arcpy.AddField_management(outputFile, "RSI", "DOUBLE")

        # Add RSI data        
        uc = arcpy.UpdateCursor(outputFile)
        for row in uc :
            regionId = row.regionId
            if self.rindex.has_key(regionId) :
                row.RSI = self.rindex[regionId]
                row.Category = self.rcategory[regionId]
                uc.updateRow(row)
                log("RSI: %3.2f, Category: %d, stormId=%s, regionId=%s" % \
                    (self.rindex[regionId], self.rcategory[regionId], self.stormId, regionId))

        del row
        del uc
        self.rsiOutput = outputFile
        log("--> Table Output: %s" % os.path.normpath(outputFile))

if __name__ == '__main__' :

    # Checkout spatial extensions
    arcpy.CheckOutExtension("Spatial")
    
    # Get Arguments
    args = getArgs()
    log = args['log']

    # Environment
    arcpy.env.overwriteOutput = True
    arcpy.env.extent = args['regions']
    arcpy.env.mask = args['regions']

    # Loop through snowstorms and calculate RSI
    rsiOutputs = []
    gridOutputs = []
    for snowStorm in args['snowStorms'] :
        try :
            rsi = RSITool(
                snowStorm, args['regions'], args['popGrid'],
                parameters, args['outputBase'])
            rsi.netCDF = args['netCDF']
            rsi.interpolateSnow()
            rsi.calculateRSI()
            rsi.save()
            log("Finished.  stormId=%s" % rsi.stormId)
            rsiOutputs.append(rsi.rsiOutput)
            gridOutputs.append(rsi.snowGrid)
        except :
            log(traceback.format_exc())
            raise Exception("RSI Tool Failed")

    # Send RSI feature(s) back to ArcMap
    arcpy.SetParameter(8, ";".join(gridOutputs))
    arcpy.SetParameter(9, ";".join(rsiOutputs))