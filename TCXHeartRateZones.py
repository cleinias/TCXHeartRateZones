# Compute % of time in training zones from the time series 
# extracted from a series of TCX files



# TCX (Garmin's Training Center format) are XML files containing data 
# about 1 or more activities.
# Every activity node contains a Track node with a series of evenly spaced
# Trackpoints (normally 1 second apart). Every Trackpoint include the Time 
# and may include a HeartRateBpm data item (as an integer).

# This utility reads all the HeartRateBpm values into a panda
# and bins them into 5 different buckets for the specified 
# training Zones.
# Since all HeartRateBpm are equally spaced at 1-second intervals,
# the number of occurrences in each bin indicates the number of seconds
# spent in each zone.

# Library used:
# lxml.etree for manipulation and extraction of data from TCX files
# numpy and pandas for binning
# Refs:
# TCX extraction: https://stackoverflow.com/questions/32503826/how-can-i-grab-data-series-from-xml-or-tcx-file
# Binning with pandas:Wes McKinney, Python for Data Analysis, O'Reilly 2017:203

# 0.1  Acquire list of TCX files
# 0.2  Acquire list of bins
# 1.   Extract data series from XML-based files into a panda
# 2.   Bin the data
# 3.   Compute and output percentages

# Go on from here

# import sys, argparse
from argparse import ArgumentParser, SUPPRESS, REMAINDER
import lxml.etree as ET
import numpy as np
import pandas as pd

# Parsing command line arguments, using options for required zone arguments
# Disable default help
parser = ArgumentParser(description='Read heart rate data from (a list of) TCX files and output a normed distribution by zones.', add_help=False)
required = parser.add_argument_group('required arguments')
optional = parser.add_argument_group('optional arguments')

# Add back help 
optional.add_argument(
    '-h',
    '--help',
    action='help',
    default=SUPPRESS,
    help='show this help message and exit'
)

required.add_argument("-z","--zones", help="A list of 2 or more numbers delimiting heart rate activity zones in the form 0, n, m, k", type=lambda s: [int(item) for item in s.split(',')], required=True)
required.add_argument("file_list", nargs=REMAINDER, help="One or more TCX or FIT files containing heart rate data for one or more activities", type=str)
args = parser.parse_args()
print("zones list: ", args.zones)
print("file list: ", args.file_list)


# LOAD XML FILE
#testing on file:///home/stefano/Desktop/Firefox Downloads/activity_4445930224.tcx
xmlfile='/home/stefano/Desktop/Firefox Downloads/activity_4445930224.tcx'
#xmlfile = 'activity_4445930224.tcx'
# etree = ET.parse(os.path.join(cd, xmlfile))
etree = ET.parse(xmlfile)

# All non-default namespaces defined in Garmin's TCX files, for future reference 
#NSMAP = {"ns5" : "http://www.garmin.com/xmlschemas/ActivityGoals/v1",
         #"ns3" : "http://www.garmin.com/xmlschemas/ActivityExtension/v2",
         #"ns2" : "http://www.garmin.com/xmlschemas/UserProfile/v2",
         #"tcd" : "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
         #"xsi" : "http://www.w3.org/2001/XMLSchema-instance", 
         #"ns4" : "http://www.garmin.com/xmlschemas/ProfileExtension/v1"}

# Garmin's TCX format default namespace
NSMAP = {"tcd" : "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}

# Extract heartrate data and convert to integers 
heartrates = np.array(etree.xpath('.//tcd:HeartRateBpm/tcd:Value/text()', namespaces={"tcd" : "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}), dtype=np.int32)

# Define bins and labels, and proceed to bin the heartrate series
# For this example we use 5 real zones plus zone 0:
#  Z0 -->   0 to 100
#  Z1 --> 101 to 123
#  Z2 --> 124 to 136
#  Z3 --> 137 to 146
#  Z4 --> 147 to 154
#  Z5 --> over 155

zones = [0,100,123,136,146,154,300]                   # Would need to get it from command line, eventually
zone_names = ['Z0', 'Z1','Z2', 'Z3', 'Z4', 'Z5']
binned_heartrates = pd.cut(heartrates, zones, labels=zone_names).value_counts()                         

# print("binned_heartrates") 
# print(binned_heartrates) 

# Normalize binned heartrates to unit vector                                
normed_heartrates = binned_heartrates.div(binned_heartrates.sum())
# print("normed_heartrates") 
# print(normed_heartrates) 

# return csv output with zones,frequency columns  
print(normed_heartrates.to_csv(header=False))
