#-------------------------------------------------------------------------------
#
# 'Controls shed weather station
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

'''Gathers data from various sensors to capture weather conditions in shed.'''


#===============================================================================
# Import modules
#===============================================================================

# Standard Library
import os
import sys
import time
import datetime
import logging

# Third party modules
import rrdtool
import pigpio
import DHT22

# Application modules
import DS18B20
import settings as s
import rrd_tools


#===============================================================================
# MAIN
#===============================================================================
def get_data():
    
    '''Entry point for script and read sensor data'''

    #---------------------------------------------------------------------------
    # Log set up
    #---------------------------------------------------------------------------
    log_file = 'logs/read_sensors.log'

    if '/' in log_file:
        if not os.path.exists(log_file[:log_file.rindex('/')]):
            os.makedirs(log_file[:log_file.rindex('/')])

    logging.basicConfig(filename='{directory}/{file_name}'.format(
                                    directory=log_directory, 
                                    file_name=log_file), 
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    logger = logging.getLogger(__name__)
    logger.info('--- Read Sensor Script Started ---')
    logger.info('Script start time: {start_time}'.format(
        start_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))) 

    logger.info(sensors.ds)


    #---------------------------------------------------------------------------
    # Load PIGPIO
    #---------------------------------------------------------------------------
    try:
        pi = pigpio.pi()
    except ValueError:
        logger.error('Failed to connect to PIGPIO ({error}). Exiting...'.format(
            error=ValueError))
        sys.exit()


    #---------------------------------------------------------------------------
    # SET UP RRD DATA AND TOOL
    #---------------------------------------------------------------------------    
    sensors = data_sources(s.SENSOR_SET)

    #Create RRD files if none exist
    if not os.path.exists(s.RRDTOOL_RRD_FILE):
        logger.error('RRD file not found. Exiting...')
        sys.exit()
    else:
        #Fetch data from round robin database & extract next entry time to sync loop
        logger.info('RRD file found')
        rrd = rrd_file(s.RRDTOOL_RRD_FILE)

        info = rrd.rrd_file_info()

        print(info)
        sensors = dict.fromkeys(data_values[1], 'U')
        print(sensors)


    #-------------------------------------------------------------------
    # Get inside temperature and humidity
    #-------------------------------------------------------------------
    if sensors.ds['inside_temp'].enable:
        logger.info('Reading value from DHT22 sensor')

        #Set up sensor  
        try:
            DHT22_sensor = DHT22.sensor(pi, sensors.ds['inside_temp'].pin_ref)
        except ValueError:
            logger.error('Failed to connect to DHT22 ({error}). Exiting'.format(
                error=ValueError))
            DHT22_sensor.cancel()
            sys.exit()

        #Read sensor
        DHT22_sensor.trigger()
        time.sleep(0.2)  #Do not over poll DHT22
        sensors.ds['inside_temp'].value = DHT22_sensor.temperature()
        sensors.ds['inside_hum'].value  = DHT22_sensor.humidity() 


    #-------------------------------------------------------------------
    # Check door status
    #-------------------------------------------------------------------
    if sensors.ds['door_open'].enable:
        logger.info('Reading value from door sensor')

        #Set up hardware
        pi.set_mode(sensors.ds['door_open'].pin_ref, pigpio.INPUT)

        #Read data
        sensors.ds['door_open'].value = pi.read(sensors.ds['door_open'].pin_ref)


    #-------------------------------------------------------------------
    # Get outside temperature
    #-------------------------------------------------------------------
    if sensors.ds['outside_temp'].enable:
        logger.info('Reading value from DS18B20 sensor')
        sensors.ds['outside_temp'].value = DS18B20.get_temp(s.W1_DEVICE_PATH, 
                                    sensors.ds['outside_temp'].pin_ref)
        
        #Log an error if failed to read sensor
        #Error value will exceed max on RRD file and be added as NaN
        if sensors.ds['outside_temp'].value is 999.99:
            logger.error('Failed to read DS18B20 sensor')


    #-------------------------------------------------------------------
    # Display data on screen
    #-------------------------------------------------------------------
    print(sensors)


    #-------------------------------------------------------------------
    # Add data to RRD
    #-------------------------------------------------------------------
    if rrd.update_rrd_file(sensors) = 'OK':
        logger.info('Update RRD file OK')
    else:
        logger.error('Failed to update RRD file ({error})'.format(
            error=result))


    #-------------------------------------------------------------------
    # Prepare to end script
    #-------------------------------------------------------------------
    #Stop processes
    DHT22_sensor.cancel()
    logger.info('--- Read Sensors Finished ---')
    sys.exit()


#===============================================================================
# BOILER PLATE
#===============================================================================
if __name__=='__main__':
    sys.exit(get_data())
