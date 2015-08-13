#-----------------------------------------------------------------------
#
# Interfaces to thingspeak
#
# The MIT License (MIT)
#
# Copyright (c) 2015 William De Freitas
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#-----------------------------------------------------------------------

#!usr/bin/env python

#=======================================================================
# Import modules
#=======================================================================
import time


class sensor():
    
    '''Sets up sensors data'''
    
    def __init__(self, sensor_name, sensor_no, sensor_unit, 
                    sensor_min, sensor_max):
        self.name = sensor_name
        self.number = sensor_no
        self.unit = sensor_unit
        self.value = 0.00
        self.min = sensor_min
        self.max = sensor_max
        
        
    #===================================================================
    # UPDATE VALUE
    #===================================================================
    def update_value(self, sensor_value):
        self.value = sensor_value


    #===================================================================
    # CREATE RRD DS STRING
    #===================================================================
    def ds_str(self, CF, heartbit):
        return 'DS:' + self.name.replace(' ','_') + 
                        ':' + CF + 
                        ':' + str(heartbit) + 
                        ':' + str(self.sensor_min) + 
                        ':' + str(self.sensor_max)
        
