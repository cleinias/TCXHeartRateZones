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

import sys, re
from argparse import ArgumentParser, SUPPRESS, REMAINDER
import lxml.etree as ET
import numpy as np
import pandas as pd

def validate_zones_list(a_list):
    """Validate the zones list as a legal list of bin edges"""
    try: 
        zones_edges = [int(s) for s in re.findall(r'\b\d+\b', a_list)]
    except Exception as e:
          print(e, "All elements of zone list must be numbers")
          sys.exit(1)
    zones_edges=list(set(zones_edges))   # remove duplicates and turn back into list to allow sorting 
    zones_edges.sort()
    return zones_edges

def create_zones_names(bin_edges_list):
    """create n zone names for length of zones list - 1""" 
    if len(bin_edges_list) < 2:
        raise Exception("The zones list must contain at least 2 unique values")
        sys.exit(1)
    else:
        return ["Z"+ str(index[0]) for index in enumerate(zones_edges) if index[0] < len(zones_edges)-1]


# Parsing command line arguments, using options for required zone arguments
# Disable default help
parser = ArgumentParser(description='Read heart rate data from (a list of) TCX files and output a normed distribution by athletic zones.', add_help=False)
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

required.add_argument("-z","--zones", help="A list of 2 or more numbers delimiting heart rate activity zones in the form 0, n, m, k", type=str, required=True)
required.add_argument("file_list", nargs=REMAINDER, help="One or more TCX or FIT files containing heart rate data for one or more activities", type=str)
optional.add_argument("-v", "--verbose", action="count", default=0, help = "Turn on verbose output")
args = parser.parse_args()

# Validating zones list and creating zone names
zones_edges = validate_zones_list(args.zones)
zones_names = create_zones_names(zones_edges)
# print("zones_edges: ", zones_edges)
# print("zones_names ", zones_names)        

# Defining a dictionary of Garmin's TCX format namespaces
# All non-default namespaces defined in Garmin's TCX files, for future reference 
#NSMAP = {"ns5" : "http://www.garmin.com/xmlschemas/ActivityGoals/v1",
         #"ns3" : "http://www.garmin.com/xmlschemas/ActivityExtension/v2",
         #"ns2" : "http://www.garmin.com/xmlschemas/UserProfile/v2",
         #"tcd" : "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
         #"xsi" : "http://www.w3.org/2001/XMLSchema-instance", 
         #"ns4" : "http://www.garmin.com/xmlschemas/ProfileExtension/v1"}

# Garmin's TCX format default namespace
NSMAP = {"tcd" : "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}


# Processing all files entered on command line

heart_rates =[]
files_processed =[]
files_skipped = []
for filename in args.file_list:
    try:
        with open(filename, 'r') as tcx_file:
            try: 
                etree = ET.parse(tcx_file)
                # Extract heartrate data and convert to integers 
                file_heartrate_data = etree.xpath('.//tcd:HeartRateBpm/tcd:Value/text()', namespaces={"tcd" : "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}) 
                if len(file_heartrate_data) > 0:
                    heart_rates.extend(file_heartrate_data)
                    files_processed.append(filename)
                else:
                    print(filename, " Does not contain usable heartrate data. Skipping")
                    files_skipped.append(filename)
            except Exception as e:
                print(filename, " is not a valid TCX file. Skipping")
                print(e)
                files_skipped.append(filename)
    except FileNotFoundError:
        print(filename, "does not exist in filesystem. Skipping")
        files_skipped.append(filename)
# print(heart_rates)
binned_heartrates = pd.cut((np.array(heart_rates, dtype=np.int32)), zones_edges, labels=zones_names).value_counts()                         

# print("binned_heartrates: ", binned_heartrates) 

# Normalize binned heartrates to unit vector                                
normed_heartrates = binned_heartrates.div(binned_heartrates.sum())


print("Original file list ({0} files):".format(len(args.file_list)))
for filename in args.file_list:
    print(filename)
print("Files processed ({0} files)".format(len(files_processed)))
for filename in files_processed:
    print(filename)
print("Files skipped, ({0} files)".format(len(files_skipped)))
for filename in files_skipped:
        print(filename)

# return csv output with zones,frequency columns  
print(normed_heartrates.to_csv(header=False))

# sys.exit(1)
