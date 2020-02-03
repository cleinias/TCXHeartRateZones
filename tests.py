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


import unittest
import tcxaet

class TestStringMethods(unittest.TestCase):
    
    #testing unit conversions
    def test_speed_to_pace(self):
        # Always return 0 for zero input (not 0/div exceptions) 
        self.assertEqual(0,tcxaet.meter_sec_2_min_miles(0))
        # 1 m/s = 2.237 miles/hour =  26.821 mins/mile        
        self.assertEqual(26.82, round(tcxaet.meter_sec_2_min_miles(1),2))
        # 10:00 mins/mile = 6 mi/hour = 2.682 m/s
        self.assertEqual(10., round(tcxaet.meter_sec_2_min_miles(2.682),2))
        
    def test_pace_to_speed(self):
        self.assertEqual(0,0)
        
    def test_dec_min_mi_2_string(self):
        self.assertEqual("10:00", tcxaet.mil_min_val_to_mil_min_string(10))
        self.assertEqual("00:00", tcxaet.mil_min_val_to_mil_min_string(0))
        self.assertEqual("10:15", tcxaet.mil_min_val_to_mil_min_string(10.25))
        
if __name__ == '__main__':
    unittest.main()