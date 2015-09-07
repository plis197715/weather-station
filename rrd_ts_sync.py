#-------------------------------------------------------------------------------
#
# Controls shed weather station
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

#!usr/bin/env python

#===============================================================================
# Import modules
#===============================================================================
import rrdtool
import thingspeak
import settings as s
import time
import logging



#===============================================================================
# MAIN
#===============================================================================
def main():

    #---------------------------------------------------------------------------
    # System set up
    #---------------------------------------------------------------------------
    rrdtool_file = s.RRDTOOL_RRD_FILE
    thingspeak_write_api_key = ''
    rrd_data = {}
    
    logging.basicConfig(filename=s.LOG_FILENAME, level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    logger = logging.getLogger(__name__)
    logger.info('rrd_ts_sync Started')
    

    #---------------------------------------------------------------------------
    # Set up thingspeak account
    #---------------------------------------------------------------------------
    ts_ch = thingspeak.ThingspeakChannel(s.THINGSPEAK_HOST_ADDR,
                                            file=s.THINGSPEAK_API_KEY_FILENAME,
                                            ch_id=s.THINGSPEAK_CHANNEL_ID)


    #---------------------------------------------------------------------------
    # Interogate thingspeak for set up
    #---------------------------------------------------------------------------
    parameters = {'results':0}
    r = ts_ch.get_channel_feed(parameters)
    last_entry_time = r['channels']['updated_at']
    field_names = r['channels']['field1']


    #---------------------------------------------------------------------------
    # Check if RRD file exists
    #---------------------------------------------------------------------------
    if not os.path.exists(rrdtool_file):
        logger.error('No RRA file found! Exiting...')
        return


    #---------------------------------------------------------------------------
    # Fetch values from rrd
    #---------------------------------------------------------------------------
    data_values = rrdtool.fetch(rrdtool_file, 'LAST', 
                                '-s', str(update_rate * -2))
    logger.info(data_values)

   
    #---------------------------------------------------------------------------
    # Check if RRD file variables match TS variables
    #---------------------------------------------------------------------------

  
    #---------------------------------------------------------------------------
    # Create a list with new thingspeak updates
    #---------------------------------------------------------------------------
    
  
    #---------------------------------------------------------------------------
    # Send data to thingspeak
    #---------------------------------------------------------------------------
    response = ts_ch.update_channel(sensor_data)
    logger.info('Thingspeak response %d', r.status_code)


    #---------------------------------------------------------------------------
    # Check response from update attempt
    #---------------------------------------------------------------------------
    if response.status_code not requests.codes.ok:
        time.sleep(5)
        response = thingspeak_ch.update_channel(sensor_data)
        logger.info('Thingspeak response %d', r.status_code)


    #---------------------------------------------------------------------------
    # Check response from update attempt
    #---------------------------------------------------------------------------
    logger.info('rrd_ts_sync finished')


#===============================================================================
# Boiler plate
#===============================================================================
if __name__=='__main__':
    main()
