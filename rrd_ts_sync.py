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



#===============================================================================
# MAIN
#===============================================================================
def main():

    rrdtool_file = s.RRDTOOL_RRD_FILE
    thingspeak_write_api_key = ''
    rrd_data = {}
    

    # --- Set up thingspeak account ---
    thingspeak_acc = thingspeak.ThingspeakAcc(s.THINGSPEAK_HOST_ADDR,
                                                s.THINGSPEAK_API_KEY_FILENAME,
                                                s.THINGSPEAK_CHANNEL_ID)

    # --- Interogate thingspeak for set up ---
    parameters = {}
    r = thingspeak_acc.get_channel_feed(parameters)

    # --- Check if RRD file exists ---
    if not os.path.exists(rrdtool_file):
        print('No RRA file found! Exiting...')
        return

    # --- Fetch values from rrd ---
    data_values = rrdtool.fetch(rrdtool_file, 'LAST', 
                                '-s', str(update_rate * -2))

    # --- Check if RRD file variables match TS variables ---

  
    # -- Get last feed upddate from thingspeak ---
    parameters = {}
    r = thingspeak_acc.get_last_entry_in_channel_feed(parameters)
   

    # --- Create a list with new thingspeak updates ---
    
  
    # --- Send data to thingspeak ---
    response = thingspeak_acc.update_channel(sensor_data)


    # --- Check response from update attempt ---
            


#===============================================================================
# Boiler plate
#===============================================================================
if __name__=='__main__':
    main()
