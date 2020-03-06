
# tcxzones

Compute percentages of time spent in training zones from the time series extracted from a list of TCX files.

## Usage

tcxzones [-h] [-v] [-c] [-d] -z ZONES FILE_LIST  

Required arguments | Values
-------------------|-----------------
-z ZONES, --zones ZONES | *A quotation-marks enclosed list of 2 or more numbers delimiting heart rate activity zones*.<br> The list indicates the zones' *edges* and will therefore have always one more element than the number of required zones.<br> A *four-elements* list such as "0,100,120,130" indicates the following *three* heartrate zones (in interval notation):<br>  (0,100], (100,120], (120,130]<br> (or: greater than 0 up to 100 included, greater than 100 up to 120 included, and greater than 120 up to 130 included).                     
FILE_LIST | *One or more TCX files containing heart rate data for one or more activities*.<br> It must always be the last argument and may be a space-separated list of files (and/or standard command-line wildcards).    
**Optional flags** | 
 -h, --help |show a help message and exit
 -v, --verbose | turn on verbose output
 -c, --columns | print column headers in output
 -d, --details | prepend details about processed files to output

### Example
tcxzones -z "0,100,120,130" aTCXfile.tcx aSecondTCXfile.tcx

## Description
tcxzones.py is a small python utility that reads heart rate data from (a list of) Garmin's TCX files 
and outputs a unit-normed distribution by athletic zones. 

It should work with both python 2 (2.7+) and python 3. 
Notice however that the *pandas* library it relies upon has dropped support 
for python 2 starting 1/1/2020, and it may cease to work at any time.
 
TCX files (Garmin's Training Center format files) are XML files containing data 
about 1 or more activities.
Every activity node contains a Track node with a series of evenly spaced
Trackpoints (normally 1 second apart, but not necessarily). Every Trackpoint includes the Time 
and may include a HeartRateBpm data item (as an integer).

tcxzones reads all the HeartRateBpm values into a pandas Series
and bins them into the specified number of buckets.


## Library used:
* lxml.etree for manipulation of TCX files and extraction of heartrate data
* numpy and pandas for binning and norming data 

