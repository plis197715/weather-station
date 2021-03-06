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

'''Counts ticks from the reed switch of a rain gauge via an interrupt driven
    callback function. This count is stored in the precipiattion rate variable
    and is reset every loop.
    Script loops until stopped by the user.
    Data is stored to an RRD file at the update time pulled from the RRD file.
    Current precipitation accumulated value is pulled from the RRD file and 
    incremented by the counted ticks from the rain gauge.
    At midnight, the precipitation accumulated value is reset.
    If there is no RRD file or its set up is different from requirement, the 
    script will abort.'''


#===============================================================================
# Import modules
#===============================================================================

# Standard Library
import sys
import threading
import time
import datetime
import collections

# Third party modules
import pigpio

# Application modules
import log
import logging
import settings as s
import rrd_tools


#===============================================================================
# GLOBAL VARIABLES
#===============================================================================
last_rising_edge = None


#===============================================================================
# FLOAT COMPARISON
#===============================================================================
def approx_equal(a, b, tol=0.0001):
     return abs(a - b) < tol


#===============================================================================
# EDGE CALLBACK FUNCTION TO COUNT RAIN TICKS
#===============================================================================
def count_rain_ticks(gpio, level, tick):
    
    '''Count the ticks from a reed switch'''
    
    global precip_tick_count
    global last_rising_edge

    logger = logging.getLogger('root')
    
    pulse = False
    
    if last_rising_edge is not None:
        #check tick in microseconds
        if pigpio.tickDiff(last_rising_edge, tick) > s.DEBOUNCE_MICROS * 1000000:
            pulse = True

    else:
        pulse = True

    if pulse:
        last_rising_edge = tick  
        precip_tick_count += 1
        logger.debug('Precip tick count : {tick}'.format(tick= precip_tick_count))
        
 

#===============================================================================
# MAIN
#===============================================================================
def main():
    
    '''Entry point for script'''

    global precip_tick_count
    global precip_accu
 
    precip_tick_count = 0
    precip_accu       = 0


    #---------------------------------------------------------------------------
    # SET UP LOGGER
    #---------------------------------------------------------------------------
    logger = log.setup('root', '/home/pi/weather/logs/read_rain_gauge.log')

    logger.info('--- Read Rain Gauge Script Started ---')
    

    #---------------------------------------------------------------------------
    # LOAD DRIVERS
    #---------------------------------------------------------------------------
    try:
        pi = pigpio.pi()

    except Exception, e:
        logger.error('Failed to connect to PIGPIO ({error_v}). Exiting...'.format(
            error_v=e))
        sys.exit()


    #---------------------------------------------------------------------------
    # CHECK RRD FILE
    #---------------------------------------------------------------------------
    try:
        rrd = rrd_tools.RrdFile(s.RRDTOOL_RRD_FILE)
        
        if sorted(rrd.ds_list()) != sorted(list(s.SENSOR_SET.keys())):
            logger.error('Data sources in RRD file does not match set up.')
            logger.error(rrd.ds_list())
            logger.error(list(s.SENSOR_SET.keys()))
            logger.error('Exiting...')
            sys.exit()
        else:
            logger.info('RRD fetch successful.')

    except Exception, e:
        logger.error('RRD fetch failed ({error_v}). Exiting...'.format(
            error_v=e))
        sys.exit()


    #---------------------------------------------------------------------------
    # SET UP SENSOR VARIABLES
    #---------------------------------------------------------------------------
    sensor_value = {x: 'U' for x in s.SENSOR_SET}

    ss = collections.namedtuple('ss', 'enable ref unit min max type')
    sensor = {k: ss(*s.SENSOR_SET[k]) for k in s.SENSOR_SET}
    
    logger.debug(sensor_value)


    #---------------------------------------------------------------------------
    # SET UP RAIN SENSOR HARDWARE
    #---------------------------------------------------------------------------
    pi.set_mode(sensor['precip_acc'].ref, pigpio.INPUT)
    rain_gauge = pi.callback(sensor['precip_acc'].ref, pigpio.FALLING_EDGE, 
                                count_rain_ticks)


    #---------------------------------------------------------------------------
    # TIMED LOOP
    #---------------------------------------------------------------------------
    try:
        while True:
            
            #-------------------------------------------------------------------
            # Delay to give update rate
            #-------------------------------------------------------------------
            next_reading  = rrd.next_update()
            logger.debug('Next sensor reading at {time}'.format(
                time=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(next_reading))))
            
            sleep_length = next_reading - time.time()
            if sleep_length > 0:
                time.sleep(sleep_length)


            #-------------------------------------------------------------------
            # Get loop start time
            #-------------------------------------------------------------------
            loop_start = datetime.datetime.utcnow()
            logger.info('Loop start time: {start_time}'.format(
                start_time=loop_start.strftime('%Y-%m-%d %H:%M:%S')))


            #-------------------------------------------------------------------
            # Get rain fall measurement
            #-------------------------------------------------------------------
            sensor_value['precip_acc'] = 0.00
            sensor_value['precip_rate'] = precip_tick_count * s.PRECIP_TICK_MEASURE
            precip_tick_count = 0.00
            logger.debug('Precip tick counter RESET')
            

            #If last entry was before midnight this moninng do not use accumulated
            # precipitation value taken from round robin database
            last_entry_time = rrd.last_update()

            last_reset = loop_start.replace(hour=0, minute=0, second=0, microsecond=0)   
            last_reset = int(time.mktime(last_reset.utctimetuple()))
            tdelta = last_entry_time - last_reset

            logger.debug('last entry = {l_entry}'.format(l_entry= last_entry_time))
            logger.debug('last_reset = {l_reset_t}'.format(l_reset_t= last_reset))
            logger.debug('tdelta = {delta_t}'.format(delta_t= tdelta))

            if tdelta >= 0.00:
                try:
                    #Fetch today's data from round robin database
                    data = []
                    data = rrd.fetch(start=last_reset, 
                                     end=last_entry_time)

                    rt = collections.namedtuple( 'rt', 'start end step ds value')
                    data = rt(data[0][0], data[0][1], data[0][2], 
                                            data[1], data[2])


                    #Create list with today's precip rate values
                    loc = data.ds.index('precip_rate')
                    todays_p_rate = [data.value[i][loc] for i in range(0, len(data.value)-1)]

                    logger.debug('Todays p rate')
                    logger.debug(todays_p_rate)

                    #Get second to last entry as last entry is next update
                    sensor_value['precip_acc'] = float(
                        data.value[len(data.value)-2][data.ds.index('precip_acc')] or 0)
                                       
                    #If any values missing from today, prevent accumulation
                    if None in todays_p_rate:
                        sensor_value['precip_acc'] = 'U'
                        logger.error('Values missing in todays precip rate')

                    elif approx_equal(sum(todays_p_rate), sensor_value['precip_acc']):
                        logger.debug('Fetched p acc value:  {p_acc}'.format(
                                        p_acc= sensor_value['precip_acc']))
                        logger.debug('Sum of todays Precip_rate: {p_rate}'.format(
                                        p_rate= sum(todays_p_rate)))
                        sensor_value['precip_acc'] = 'U'
                        logger.error('Lastest precip acc value does not much summation of precip rates')
                    
                    else:
                        #Add previous precip. acc'ed value to current precip. rate
                        sensor_value['precip_acc'] += sensor_value['precip_rate']

                except Exception, e:
                    logger.error('RRD fetch failed ({error_v}). Exiting...'.format(
                        error_v=e))


            #Round values to 2 decimal places
            sensor_value['precip_rate'] = float('{0:.2f}'.format(sensor_value['precip_rate']))
            sensor_value['precip_acc'] = float('{0:.2f}'.format(sensor_value['precip_acc'])
            
            #Log values
            logger.info('Precip_acc:  {precip_acc}'.format(
                                        precip_acc= sensor_value['precip_acc']))
            logger.info('Precip_rate: {precip_rate}'.format(
                                        precip_rate= sensor_value['precip_rate']))
                

            #-------------------------------------------------------------------
            # Add data to RRD
            #-------------------------------------------------------------------
            logger.debug('Update time = {update_time}'.format(update_time= 'N'))#rrd.next_update()))
            logger.debug([v for (k, v) in sorted(sensor_value.items()) if v != 'U'])
            
            result = rrd.update_file(timestamp= 'N',
                ds_name= [k for (k, v) in sorted(sensor_value.items()) if v!='U'],
                values= [v for (k, v) in sorted(sensor_value.items()) if v != 'U'])

            if result == 'OK':
                logger.info('Update RRD file OK')
            else:
                logger.error('Failed to update RRD file ({value_error})'.format(
                    value_error=result))
                logger.error(sensor_value)


    #---------------------------------------------------------------------------
    # User exit command
    #---------------------------------------------------------------------------
    except KeyboardInterrupt:
        logger.info('USER ACTION: End command')


    #---------------------------------------------------------------------------
    # Other error captured
    #---------------------------------------------------------------------------
    except Exception, e:
        logger.error('Script Error', exc_info=True)


    #---------------------------------------------------------------------------
    # Stop processes
    #---------------------------------------------------------------------------
    finally:
        rain_gauge.cancel()       
        logger.info('--- Read Rain Gauge Finished ---')
        

#===============================================================================
# BOILER PLATE
#===============================================================================
if __name__=='__main__':
    sys.exit(main())
