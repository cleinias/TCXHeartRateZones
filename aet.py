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
# 1. PROCESSING OF INPUT
# 2. PROCESSING OF MULTIPLE FILES
# 3. COLLECTION OF RESULTS INTO A PANDAS (FOR POSSIBLE FURTHER PROCESSING)
# 4. WRITING OUT IN CSV FORMAT
# 5. FACTORIZATION OF CODE INTO FUNCTIONS

from __future__ import print_function        
import sys, re
from datetime import datetime, timedelta
from argparse import ArgumentParser, SUPPRESS, REMAINDER
import lxml.etree as ET
import numpy as np
import pandas as pd

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
METERS2MILES = 1609.34
MIN2SECS = 60 # for clarity in formulas

# FUNCTIONS
def meter_sec_2_min_miles(n):
    miles_a_minute = n/METERS2MILES*60
    if miles_a_minute == 0:
        return 0
    else:
        minutes_a_miles = 1/miles_a_minute
        delta = timedelta(minutes=minutes_a_miles)
        l = str(delta).split(":")
        min_per_mi = l[-2]+":"+str(round(float(l[-1]))).zfill(2)
        return min_per_mi



# PARSE INPUT ARGUMENTS

filename="/home/stefano/Dropbox/Running/Training/Uphill-Athlete-20-weeks-SUMMER-2020-TRAIL/TCX-Files/Week_0_02/activity_4485827501.tcx"
with open(filename,"r+") as tcx_file:
     etree = ET.parse(tcx_file)
        
# PARSE MULTIPLE FILES INTO COLLECTIONS OF LAPS        
file_laps = etree.xpath('.//tcd:Lap', namespaces=NSMAP)         


def parse_file_laps(file_laps):
    """ Parse a TCX lap into a dictionary of relevant data.
        Return dictionary"""

    laps=[]   
    for i, lap in enumerate(file_laps):
        lap_data = {}
        lap_data['TotalTimeSeconds'] = lap.xpath('.//tcd:TotalTimeSeconds/text()',namespaces=NSMAP)
        lap_data['DistanceMeters']   = lap.xpath('.//tcd:DistanceMeters/text()',namespaces=NSMAP)
        lap_data['Bpm_list']         = lap.xpath('.//tcd:HeartRateBpm/tcd:Value/text()',namespaces=NSMAP)
        lap_data['Distance_list']    = lap.xpath('.//tcd:Track/tcd:Trackpoint/tcd:DistanceMeters/text()',namespaces=NSMAP)
        lap_data['Time_list']        = lap.xpath('.//tcd:Trackpoint/tcd:Time/text()',namespaces=NSMAP)
        laps.append(lap_data)
    return laps

def extract_lap_basic_info(lap_data):
    """Extract and formats basic info from a dictionary of data about a TCX activity's lap.
       Return a string with all the formatted info"""
    "FIXME: convert to python standard formatted string "
    
    beginning_date_string = lap_data['Time_list'][0]
    end_date_string = lap_data['Time_list'][-1]
    date_format_string = "%Y-%m-%dT%H:%M:%S.%fZ"
    beginning_time=datetime.strptime(beginning_date_string,date_format_string)
    end_time = datetime.strptime(end_date_string,date_format_string)
    duration = end_time - beginning_time
    return "Beg: " +  beginning_time + "end: " + end_time + "Duration in seconds:" + duration.total_seconds()


# PARSE SINGLE LAPS' DATA
def parse_laps(laps):
    """ Parse each lap' basic info into a matrix of computed data.  
        Return the matrix."""
    
    "FIXME: convert print statement into assignments to a matrix"

    for i, lap in enumerate(laps):
        try:
            total_distance = float(lap['Distance_list'][-1])-float(lap['Distance_list'][0])
            total_trackpoints = len(lap['Distance_list'])
            total_time_summary = float(lap['TotalTimeSeconds'][0])
            beginning_date_string = lap['Time_list'][0]
            end_date_string = lap['Time_list'][-1]
            date_format_string = "%Y-%m-%dT%H:%M:%S.%fZ"
            beginning_time=datetime.strptime(beginning_date_string,date_format_string)
            end_time = datetime.strptime(end_date_string,date_format_string)
            duration = end_time - beginning_time
            total_time_computed = duration.total_seconds() 
            average_bpm = sum((int(i) for  i in lap['Bpm_list']))/len(lap['Bpm_list'])
            speed_meter_sec = total_distance/total_time_summary
            pace_min_miles = meter_sec_2_min_miles(speed_meter_sec)
            half_time = int(total_time_computed / 2)

            first_half_distance = float(lap['Distance_list'][half_time])-float(lap['Distance_list'][0])
            first_half_speed =  first_half_distance/(total_time_computed / 2) 
            first_half_pace = meter_sec_2_min_miles(first_half_speed)
            first_half_avg_bpm = sum((int(i) for  i in lap['Bpm_list'][:half_time]))/len(lap['Bpm_list'][:half_time])
            first_half_speed_bpm_ratio = first_half_speed/first_half_avg_bpm

            second_half_distance = float(lap['Distance_list'][-1])-float(lap['Distance_list'][half_time+1])
            second_half_speed =  second_half_distance / (total_time_computed / 2)
            second_half_pace = meter_sec_2_min_miles(second_half_speed)
            second_half_avg_bpm = sum((int(i) for  i in lap['Bpm_list'][half_time +1:]))/len(lap['Bpm_list'][half_time+1:])
            second_half_speed_bpm_ratio = second_half_speed/second_half_avg_bpm

            first_to_second_half_drift = (second_half_speed_bpm_ratio-first_half_speed_bpm_ratio)/first_half_speed_bpm_ratio

            print("Lap ", i, "--> ", "Start:", lap['Time_list'][0], 
                  "Total time: ", total_time_summary, 
                  "Computed time: ", duration.total_seconds(),
                  "Total track points: ", total_trackpoints, 
                  "Total Distance: ",round(total_distance,2), 
                  " Average Bpm: ", round(average_bpm),
                  " Average speed in m/s", round(speed_meter_sec,3),
                  " Average pace in min/mi", pace_min_miles)

            print("Lap ", i, " FIRST HALF-->", 
                  " Total time: ", total_time_summary, 
                  " Half time: ", half_time,
                  " First half distance meters:", round(first_half_distance,2),
                  " First half speed m/s: ", round(first_half_speed,3),
                  " First half pace min/mi: ", meter_sec_2_min_miles(first_half_speed),
                  " First half avg bpm: ", round(first_half_avg_bpm),
                  " First half pace/bpm ratio", round(first_half_speed_bpm_ratio,3))

            print("Lap ", i, " SECOND HALF-->", 
                  " Total time: ", total_time_summary, 
                  " Half time: ", half_time,
                  " Second half distance meters:", round(second_half_distance,2),
                  " Second half speed m/sec: ", round(second_half_speed,3),
                  " Second half pace min/mi: ", meter_sec_2_min_miles(second_half_speed),
                  " Second half avg bpm: ", round(second_half_avg_bpm),
                  " Second half pace/bpm ratio", round(second_half_speed_bpm_ratio,3))

            print("Lap ", i, " ABS DRIFT --> {:.2%}".format(abs((second_half_speed_bpm_ratio-first_half_speed_bpm_ratio)/first_half_speed_bpm_ratio)))        
        except ZeroDivisionError as e:
            print(e, file=sys.stderr)
            print("Lap {} has 0 distance and/or 0 time. Skipping ".format(i), file=sys.stderr)

# OUTPUT CSV-FORMATTED DATA        
# # Return csv output with no headers by default
columns_names = ["total time", "computed time", "total track points", "avg bpm", "avg speed m/s", "avg pace min/mi", "half time", \
                 "1st half dist (m)", "1st speed (m/s)", "1st half pace (min/mi)","1st half avg bpm", "first half pace/bpm ratio", \
                 "2nd half dist (m)", "2nd speed (m/s)", "2nd half pace (min/mi)","2nd half avg bpm", "first half pace/bpm ratio", \
                 "ABS 1st/2nd DRIFT"]
index_name = "lap"
# if args.columns == 0:
#     print(normed_heartrates.to_csv(header=False))
# else:
#     print(normed_heartrates.to_csv(header=columns_names, index_label=index_name))

