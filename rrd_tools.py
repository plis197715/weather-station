#-------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------

#!/usr/bin/env python

'''Manages RRD file'''


#===============================================================================
# IMPORT MODULES
#===============================================================================

# Standard Library
import os
import sys
import time
import datetime

# Third party modules
import rrdtool


#===============================================================================
# CLASS DEFINITION AND FUNCTIONS
#===============================================================================
class rrd_file:

    '''Sets up the RRD file 'a thingspeak account'''

    def __init__(self, filename):

        if '/' in filename:
            self.file_dir = filename[:log_file.rindex('/')]

        self.file_name = filename

        if os.path.exists(self.file_name):
            info = rrd_file_info()
            self.step = info.step



    #---------------------------------------------------------------------------
    # CREATE RRD FILE
    #---------------------------------------------------------------------------
    def create_rrd_file(self, sensor_set, rra_set, step, heartbeat, 
                        start_time):
        
        '''Creates a RRD file'''

        #Check if directory exists
        if self.file_dir and not os.path.exists(self.file_dir):
                os.makedirs(self.file_dir)

        #Prepare RRD set
        rrd_set = [self.file_name, 
                    '--step', '{step_size}'.format(step_size=step), 
                    '--start', '{start_t:.0f}'.format(start_t=start_time)]

        #Prepare data sources
        for i in sorted(sensor_set):
            rrd_set.append('DS:{ds_name}:{ds_type}:{ds_hb}:{ds_min}:{ds_max}'.format(
                                    ds_name=i,
                                    ds_type=sensor_set[i][5],
                                    ds_hb=str(heartbeat*step),
                                    ds_min=sensor_set[i][3],
                                    ds_max=sensor_set[i][4]))

        #Prepare RRA files
        for i in range(0,len(rra_set),3):
            rrd_set.append('RRA:{cf}:0.5:{steps}:{rows}'.format(
                                    cf=rra_set[i],
                                    steps=str((rra_set[i+1]*60)/step),
                                    rows=str(((rra_set[i+2])*24*60)/rra_set[i+1])))

        rrdtool.create(rrd_set)

        return rrd_set


    #---------------------------------------------------------------------------
    # CREATE RRD FILE
    #---------------------------------------------------------------------------
    def rrd_file_info(self):

        '''Reads info data from RRD file'''

        try:
            return rrdtool.info('{file}'.format(file=self.filename)))
        except rrdtool.error, e:
            return e


    #---------------------------------------------------------------------------
    # UPDATE RRD FILE
    #---------------------------------------------------------------------------
    def update_rrd_file(self, data_values):

        '''Updates RRD file with value from passed dictionary'''

        try:
            rrdtool.update(
                '{file}'.format(file=self.filename), 
                'N:{values}'.format(
                    values=':'.join([str(data_values[i]) for i in sorted(data_values)])))
            return 'OK'
        except rrdtool.error, e:
            return e


    #---------------------------------------------------------------------------
    # RETRIEVE NEXT UPDATE TIME
    #---------------------------------------------------------------------------
    def get_next_update_time(self):

        '''Retrieves next update time'''

        data_values = rrdtool.fetch(self.filename, 'LAST', 
                                        '-s', str(self.step * -2))

        return data_values[0][1]


    #---------------------------------------------------------------------------
    # RETRIEVE DATA SOURCES
    #---------------------------------------------------------------------------
    def get_data_sources(self):

        '''Retrieves data sources'''

        data_values = rrdtool.fetch(self.filename, 'LAST', 
                                        '-s', str(self.step * -2))

        return data_values[1]
