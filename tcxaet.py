#!/usr/bin/env python
#
# Copyright (c) 2020 Stefano Franchi
#
# TCXHeartRateZones is free software: you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published by 
# the Free Software Foundation, either version 3 of the License, 
# or (at your option) any later version.
#
# TCXHeartRateZones txtis distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with TCXHeartRateZones. If not, see http://www.gnu.org/licenses/.


# COLLECTED FRAGMENTS OF THE NOTEBOOK TOWARD AN AeT CALCULATOR
# STILL MISSING:
#
# 0. VIP: CARDIAC DRIFT PROCESSING ON THE BASIS OF HEARTRATE ONLY (FOR TREADMILL-BASED TESTS)
#         IN WHICH CASE PACE AND ELEVATION IS ASSUMED TO BE CONSTANT 
#         (AS PER THE STANDARD TREADMILL TEST PROTOCOL: https://www.uphillathlete.com/heart-rate-drift/)
#         WHILE HEART RATE IS LEFT FREE TO CHANGE.
#         GARMIN TCX FILES REPORT 'RUNNING' AS ACTIVITY TYPE ALSO FOR INDOOR RUNNING OR 
#         TREADMILL RUNNING, SO WE WILL USE A COMMAND LINE FLAG THAT SETS SPEED TO A DUMMY CONSTANT 
# 1. PROCESSING OF INPUT
# 2. PROCESSING OF MULTIPLE FILES
# 3. COLLECTION OF RESULTS INTO A PANDAS (FOR POSSIBLE FURTHER PROCESSING)
# 4. WRITING OUT IN CSV FORMAT
# 5. FACTORIZATION OF CODE INTO FUNCTIONS

from __future__ import print_function
from ntpath import  basename 
import sys, re, os
from datetime import datetime, timedelta
from argparse import ArgumentParser, SUPPRESS, REMAINDER
import lxml.etree as ET
import pandas as pd
from imath import floor

# Constants    
# Defining a dictionary of Garmin's TCX format namespaces
# All non-default namespaces defined in Garmin's TCX files asof Jan 2020, for future reference 
#NSMAP = {"ns5" : "http://www.garmin.com/xmlschemas/ActivityGoals/v1",
         #"ns3" : "http://www.garmin.com/xmlschemas/ActivityExtension/v2",
         #"ns2" : "http://www.garmin.com/xmlschemas/UserProfile/v2",
         #"tcd" : "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
         #"xsi" : "http://www.w3.org/2001/XMLSchema-instance", 
         #"ns4" : "http://www.garmin.com/xmlschemas/ProfileExtension/v1"}

# Garmin's TCX format default namespace
NSMAP = {"tcd" : "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
# Other useful constant
METERS2MILES = 1609.34
MIN2SECS = 60 # for clarity in formulas

# Parsing command line arguments, using options for required zone arguments
# Disable default help
parser = ArgumentParser(description='Read speed and heart rate data from (a list of) TCX files and compues the cardiac drift between the lap\'s first and second half', add_help=False)
required = parser.add_argument_group('required arguments')
optional = parser.add_argument_group('optional arguments')

# Add back help 
optional.add_argument('-h','--help',action='help',default=SUPPRESS,help='show this help message and exit')

# Add command line arguments
required.add_argument("file_list", nargs=REMAINDER, help="One or more TCX or FIT files containing heart rate data for one or more activities", type=str)
optional.add_argument("-v", "--verbose", action="count", default=0, help = "Turn on verbose output")
optional.add_argument("-c", "--columns", action="store_true", default=False, help="Print column headers in output")
optional.add_argument("-d", "--details", action="store_true", default=False, help="Prepend activity's or activities' details to zone data (date, time, activity, etc.)")
optional.add_argument("-t", "--treadmill", action="store_true", default=False, help="Interpret data as treadmill data (set speed/pace to a program defined constant)")
args = parser.parse_args()

# filename="/home/stefano/Dropbox/Running/Training/Uphill-Athlete-20-weeks-SUMMER-2020-TRAIL/TCX-Files/Week_0_02/activity_4485827501.tcx"
# with open(filename,"r+") as tcx_file:
#      etree = ET.parse(tcx_file)

# FUNCTIONS
# def meter_sec_2_min_miles_string(n):
#     """Convert m/s speed into a minutes/mil pace string """
#     miles_a_minute = n/METERS2MILES*60
#     return miles_a_minute
    
def mil_min_val_to_mil_min_string(val):
    """Convert a decimal miles/min value into a standard formatted string."""
    if val == 0:
        return "00:00"
    else:
        delta = timedelta(minutes=val)
        l = str(delta).split(":")
        return l[-2]+":"+str(round(float(l[-1]))).zfill(2)

    
def meter_sec_2_min_miles(n):
    """Convert m/s speed into a minutes/mil pace value (i.e. decimal minutes) """
    miles_a_minute = n/METERS2MILES*60
    if miles_a_minute == 0:
        return 0
    else:
        return  1/miles_a_minute

    
# PARSE MULTIPLE FILES INTO COLLECTIONS OF LAPS
def read_tcx_files(filename_list):
    """ Read all laps from a collection of TCX files. 
        Return a list of tuples (filename, tcx lap)"""
    all_laps = []
    for filename in filename_list:
        with open(filename,"r+") as tcx_file:
            lap_file = basename(filename)
            etree = ET.parse(tcx_file)
            file_laps = etree.xpath('.//tcd:Lap', namespaces=NSMAP)
            for lap in file_laps:
                all_laps.append((lap_file, lap))
    return all_laps

def parse_tcx_lap(file_laps):
    """ Parse a TCX lap into a dictionary of relevant data.
        Return dictionary"""
    laps=[]   
    for (filename,lap) in file_laps:
        lap_data = {}
        lap_data['Filename']         = filename
        lap_data['TotalTimeSeconds'] = int(float(lap.xpath('.//tcd:TotalTimeSeconds/text()',namespaces=NSMAP)[0]))
        lap_data['DistanceMeters']   = [float(i) for i in lap.xpath('.//tcd:DistanceMeters/text()',namespaces=NSMAP)[1:]]
        lap_data['Bpm_list']         = [int(str(i)) for i in lap.xpath('.//tcd:HeartRateBpm/tcd:Value/text()',namespaces=NSMAP)]
        lap_data['Distance_list']    = [int(float(i)) for i in lap.xpath('.//tcd:Track/tcd:Trackpoint/tcd:DistanceMeters/text()',namespaces=NSMAP)]
        lap_data['Time_list']        = [str(i) for i in lap.xpath('.//tcd:Trackpoint/tcd:Time/text()',namespaces=NSMAP)]
        laps.append(lap_data)
    return laps

def get_lap_times_and_duration(lap_data):
    """Extract beginning time, end time, and duration from lap info and format appropriately.
       Return a tuple with the formatted info"""

    # FIXME:add conversion to local time zone (from coordinates)?
    
    beginning_date_string = lap_data['Time_list'][0]
    end_date_string = lap_data['Time_list'][-1]
    date_format_string = "%Y-%m-%dT%H:%M:%S.%fZ"
    beginning_time=datetime.strptime(beginning_date_string,date_format_string)
    end_time = datetime.strptime(end_date_string,date_format_string)
    duration = end_time - beginning_time
    return (beginning_time, end_time, duration)


# PARSE SINGLE LAPS' DATA
def parse_laps(laps):
    """ Parse each lap's basic info into a panda dataframe of extracted and computed data.  
        Return the dataframe."""
    
#     # FIXME: convert use panda dataframe instead of np.array"
#     lap_columns = ["Filename", "Total time sec.", "Start time", "End time", "Duration","Total distance","Total trackpoints",
#                "Total time","Avg. bpm","Speed m/s", "Pace (dec. min/mi)","Half time","1st half distance", 
#                "1st half speed","1st half pace", "1st half avg bpm", "1st half speed/bpm ratio", 
#                "2nd half distance", "2nd half speed", "2nd half pace", "2nd half avg. bpm", "2nd half speed/bpm ratio",
#                "1st/2nd half cardiac drift"]
 
    all_laps_data = [] # the list of dictionaries for the dataframe data 
    for i, lap in enumerate(laps):
        try:
            lap_row = {}  # a row in the dataframe with all the data for the lap
            # general info
            lap_row["Filename"] = lap["Filename"]
            lap_row["Beginning time"] = get_lap_times_and_duration(lap)[0]
            lap_row["End time"] = get_lap_times_and_duration(lap)[1]
            lap_row["Duration"] = get_lap_times_and_duration(lap)[2]

            # All lap data
            lap_row["Total distance"] = lap['Distance_list'][-1]-float(lap['Distance_list'][0])
            lap_row["# Trackpoints"] = len(lap['Distance_list'])                                                                                
            lap_row["Total time"] = lap['TotalTimeSeconds']                                                                      
            lap_row["Avg. BPM"] = sum((int(i) for  i in lap['Bpm_list']))/len(lap['Bpm_list'])                                          
            lap_row["Speed (m/s)"] = lap_row["Total distance"]/lap_row["Total time"]                                                                         
            lap_row["Pace (min:mi)"] = mil_min_val_to_mil_min_string(meter_sec_2_min_miles(lap_row["Speed (m/s)"]))                                                             
            lap_row["Halftime"] = floor(lap_row["Total time"] / 2) - 1
            # Add also the whole bpm list as a dataseries for possible further stats elaboration (variance, avg.,  etc)

            # First half data
            lap_row["1st half distance"] = float(lap['Distance_list'][int(lap_row["Halftime"])])-float(lap['Distance_list'][0])                         
            lap_row["1st half speed (m/s)"] = lap_row["1st half distance"]/(lap_row["Total time"] / 2)                                                                     
            lap_row["1st half pace (min:mi)"] = mil_min_val_to_mil_min_string(meter_sec_2_min_miles(lap_row["1st half speed (m/s)"]))
            lap_row["1st half avg. BPM"] = sum((int(i) for  i in lap['Bpm_list'][:int(lap_row["Halftime"])]))/len(lap['Bpm_list'][:int(lap_row["Halftime"])])       
            lap_row["1st half speed/avg. BPM ratio"] = lap_row["1st half speed (m/s)"]/lap_row["1st half avg. BPM"]

            # Second half data
            lap_row["2nd half distance"] = float(lap['Distance_list'][int(lap_row["Halftime"])])-float(lap['Distance_list'][0])                         
            lap_row["2nd half speed (m/s)"] = lap_row["2nd half distance"]/(lap_row["Total time"] / 2)                                                                     
            lap_row["2nd half pace (min:mi)"] = mil_min_val_to_mil_min_string(meter_sec_2_min_miles(lap_row["2nd half speed (m/s)"]))
            lap_row["2nd half avg. BPM"] = sum((int(i) for  i in lap['Bpm_list'][int(lap_row["Halftime"])+1:]))/len(lap['Bpm_list'][int(lap_row["Halftime"])+1:])       
            lap_row["2nd half speed/avg. BPM ratio"] = lap_row["2nd half speed (m/s)"]/lap_row["2nd half avg. BPM"]
                                                         
            # 1st/2nd half cardiac drift
            lap_row["1st/2nd half drift"] = (lap_row["2nd half speed/avg. BPM ratio"]-lap_row["1st half speed/avg. BPM ratio"])/lap_row["1st half speed/avg. BPM ratio"]
        except ZeroDivisionError as e:
            print(e, file=sys.stderr)
            print("Lap {} has 0 distance and/or 0 time. Skipping ".format(i), file=sys.stderr)
        all_laps_data.append(lap_row)
    return pd.DataFrame(all_laps_data)

def make_lap_header(lap):
    """Return a string with all the info about the input lap"""
    #FIXME:add formatting string and remove variable placeholders
    
    beginning_date_string = lap['Time_list'][0]
    end_date_string = lap['Time_list'][-1]
    date_format_string = "%Y-%m-%dT%H:%M:%S.%fZ"
    beginning_time=datetime.strptime(beginning_date_string,date_format_string)
    end_time = datetime.strptime(end_date_string,date_format_string)
    duration = end_time - beginning_time
    total_time_computed = duration.total_seconds() 
    lap_header =  "Lap {i} -->  Start: {lap['Time_list'][0]} Total time: {total_time_summary} Computed time: {duration.total_seconds()} \
                   Total track points: {total_trackpoints} Total Distance: {round(total_distance,2)} Average Bpm: {round(average_bpm)}\
                   Average speed in m/s {round(speed_meter_sec,3)}  Average pace in min/mi {pace_min_miles}".format()
    return lap_header


# OUTPUT CSV-FORMATTED DATA        
def csv_output(laps_array):
    """Return a csv formatted string with all the data in the array and optionally the column headers"""
#     column_names = ["Total_distance","Total trackpoints","Total time","Avg. bpm","Speed m/s", "Pace (dec. min/mi)",
#                     "Half time","1st half distance", "1st half speed","1st half pace", "1st half avg bpm",
#                     "1st half speed/bpm ratio", "2nd half distance", "2nd half speed", "2nd half pace", "2nd half avg. bpm", "2nd half speed/bpm ratio",
#                     "1st/2nd half cardiac drift"]
    index_name = "lap"
    if args.columns == 0:
        return laps_array.to_csv(header=False)
    else:
        return laps_array.to_csv(header=True, index_label=index_name)


# main loop
# parse all files into the array
parsed_array = parse_laps(parse_tcx_lap(read_tcx_files(args.file_list)))
# output data as csv with optional header
# FIXME:TODO
print(csv_output(parsed_array))