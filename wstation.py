#-------------------------------------------------------------------------------
#
# Controls weatherstation
#
#-------------------------------------------------------------------------------

#!usr/bin/env python

#===============================================================================
# Import modules
#===============================================================================
import os
import sys
import threading
import time
import datetime
import httplib
import urllib
import pigpio
import DHT22


#===============================================================================
# LOAD DRIVERS
#===============================================================================
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

pi = pigpio.pi()


#===============================================================================
# GLOBAL VARIABLES
#===============================================================================

# --- Set up GPIO referencing----
GLOBAL_BROADCOM_REF     = True

if GLOBAL_BROADCOM_REF:
    GLOBAL_Pin_11   = 17
    GLOBAL_Pin_12   = 18
    GLOBAL_Pin_13   = 27
    GLOBAL_Pin_14   = 27
else:
    GLOBAL_Pin_11   = 11
    GLOBAL_Pin_12   = 12
    GLOBAL_Pin_13   = 13
    GLOBAL_Pin_14   = 14

# --- System set up ---
GLOBAL_update_rate          = 5 # seconds
GLOBAL_w1_device_path       = '/sys/bus/w1/devices/'
GLOBAL_screen_output        = False

# --- Set up thingspeak ----
GLOBAL_thingspeak_enable_update     = True
GLOBAL_thingspeak_host_addr         = 'api.thingspeak.com:80'
GLOBAL_thingspeak_api_key_filename  = 'thingspeak.txt'
GLOBAL_thingspeak_write_api_key     = ''

# --- Set up sensors ----
GLOBAL_out_sensor_enable    = True
GLOBAL_out_temp_sensor_ref  = '28-0414705bceff'
GLOBAL_out_temp_TS_field    = 1

GLOBAL_in_sensor_enable     = True
GLOBAL_in_sensor_ref        = 'DHT22'
GLOBAL_in_sensor_pin        = GLOBAL_Pin_11
GLOBAL_in_temp_TS_field     = 2
GLOBAL_in_hum_TS_field      = 3

GLOBAL_door_sensor_enable   = True
GLOBAL_door_sensor_pin      = GLOBAL_Pin_14
GLOBAL_door_TS_field        = 4

GLOBAL_rain_sensor_enable   = True
GLOBAL_rain_sensor_pin      = GLOBAL_Pin_13
GLOBAL_rain_TS_field        = 5
GLOBAL_rain_tick_measure    = 1.5 #millimeters
GLOBAL_rain_tick_meas_time  = 0.5 #minutes
GLOBAL_rain_tick_count      = 0
GLOBAL_rain_task_count      = 0

# --- Set up flashing LED ----
GLOBAL_LED_display_time     = False
GLOBAL_LED_pin              = GLOBAL_Pin_12
GLOBAL_LED_flash_rate       = 1  # seconds
GLOBAL_next_call            = time.time()


#===============================================================================
# SETUP HARDWARE
#===============================================================================
def setup_hardware():

    #Set up DHT22
    global DHT22_sensor
    global GLOBAL_in_sensor_pin
    global GLOBAL_door_sensor_pin
    global GLOBAL_rain_sensor_pin
    
    DHT22_sensor = DHT22.sensor(pi, GLOBAL_in_sensor_pin)

    #Set up rain sensor input pin
    pi.set_mode(GLOBAL_rain_sensor_pin, pigpio.INPUT)
    rain_gauge = pi.callback(GLOBAL_rain_sensor_pin, pigpio.RISING_EDGE, count_rain_ticks)

    #Set up door sensor input pin
    pi.set_mode(GLOBAL_door_sensor_pin, pigpio.INPUT)
    
    #Set up LED flashing thread
    pi.set_mode(GLOBAL_LED_pin, pigpio.OUTPUT)
    timerThread = threading.Thread(target=toggle_LED)
    timerThread.daemon = True
    timerThread.start()


#===============================================================================
# LOAD THINGSPEAK API KEY
#===============================================================================
def thingspeak_get_write_api_key(filename):

    error_to_catch = getattr(__builtins__,'FileNotFoundError', IOError)
    
    try:
        f = open(filename, 'r')
        
    except error_to_catch:
    
        print('No thingspeak write api key found.')
    
        entry_incorrect = True
        while entry_incorrect:
            api_key = input('Please enter the write key: ')
            answer = input('Is this correct? Y/N >')
            if answer in ('y', 'Y'):
                entry_incorrect = False
    
        with open(filename, 'w') as f:
            f.write(api_key)

    else:
        api_key = f.read()
        print('Thingspeak api key loaded... ok')
    
    f.close()
    
    return api_key


#===============================================================================
# EDGE CALLBACK FUNCTION TO COUNT RAIN TICKS
#===============================================================================
def count_rain_ticks(gpio, level, tick):
    
    global GLOBAL_rain_tick_count
    
    GLOBAL_rain_tick_count += 1
    print(GLOBAL_rain_tick_count)
    time.sleep(0.1) #debounce
    

#===============================================================================
# READ RAW DATA FROM W1 SLAVE
#===============================================================================
def w1_slave_read(device_id):

    device_id = GLOBAL_w1_device_path+device_id+'/w1_slave'

    with open(device_id,'r') as f:
        lines=f.readlines()

    return lines


#===============================================================================
# READ DATA FROM DS18B20
#===============================================================================
def get_ds18b20_temp(device_id):

    lines = w1_slave_read(device_id)

    #If unsuccessful first read loop until temperature acquired
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        print('Failed to read DS18B20. Trying again...')
        lines = w1_slave_read(device_id)

    temp_output = lines[1].find('t=')

    if temp_output != -1:
        temp_string = lines[1].strip()[temp_output+2:]
        temp_c = float(temp_string) / 1000.0

    return temp_c


#===============================================================================
# READ DATA FROM DHT22
#===============================================================================
def get_dht22_data():

    global DHT22_sensor

    DHT22_sensor.trigger()
    
    #Do not over poll DHT22
    time.sleep(0.2) 

    return {'temp':s.temperature(), 'hum':s.humidity()}


#===============================================================================
# OUTPUT DATA TO SCREEN
#===============================================================================
def output_data(sensors, data):

    #Check passed data is correct
    if len(sensors) <= len(data):

        print('')

        #Print date and time
        print(datetime.datetime.now())

        field = 0

        # Display each sensor data
        for i in sensors:

            #Check for unit
            if 'temp' in i:
                unit = u'\u00b0C'
            elif 'hum' in i:
                unit = '%'
            else:
                unit = ''

            #Print sensor data
            print(i+'\t'+str(data[field])+unit)

            #Next data field
            field += 1


#===============================================================================
# UPDATE THINGSPEAK CHANNEL
#===============================================================================
def thingspeak_update_channel(channel, field_data):
    
    global GLOBAL_screen_output

    #Create POST data
    data_to_send = {}
    data_to_send['key'] = channel
    for i in range(0, len(field_data)):
        data_to_send['field'+str(i+1)] = field_data[i]
        
    params = urllib.urlencode(data_to_send)
    headers = {'Content-type': 'application/x-www-form-urlencoded','Accept': 'text/plain'}

    conn = httplib.HTTPConnection(GLOBAL_thingspeak_host_addr)
    conn.request('POST', '/update', params, headers)
    response = conn.getresponse()
    
    if GLOBAL_screen_output:
        print('Data sent to thingspeak: ' + response.reason + '\t status: ' + str(response.status))
    
    data = response.read()
    conn.close()


#===============================================================================
# DOOR SENSOR
#===============================================================================
def get_door_status():

    global GLOBAL_door_sensor_pin
            
    return pi.read(GLOBAL_door_sensor_pin)
    

#===============================================================================
# TOGGLE LED
#===============================================================================
def toggle_LED():

    global GLOBAL_next_call
    global GLOBAL_LED_display_time

    if GLOBAL_LED_display_time:
        print(datetime.datetime.now())

    #Prepare next thread time
    GLOBAL_next_call = GLOBAL_next_call + GLOBAL_LED_flash_rate
    threading.Timer( GLOBAL_next_call - time.time(), toggle_LED ).start()

    #Toggle LED
    if pi.read(GLOBAL_LED_pin) == 0:
        pi.write(GLOBAL_LED_pin, 1)
    else:
        pi.write(GLOBAL_LED_pin, 0)


#===============================================================================
# EXIT ROUTINE
#===============================================================================
def exit_code():

    global DHT22_sensor

    #Set pins to OFF state
    pi.write(GLOBAL_LED_pin, 0)

    DHT22_sensor.cancel()

    print('\nExiting program...')


#===============================================================================
# MAIN
#===============================================================================
def main():

    global GLOBAL_out_sensor_enable
    global GLOBAL_in_sensor_enable
    global GLOBAL_in_sensor_ref
    global GLOBAL_in_hum_sensor_enable
    global GLOBAL_door_sensor_enable
    global GLOBAL_rain_sensor_enable
    global GLOBAL_rain_tick_count
    global GLOBAL_rain_tick_meas_time
    global GLOBAL_thingspeak_enable_update
    global GLOBAL_update_rate
    global GLOBAL_LED_display_time
    global GLOBAL_screen_output


    #Check and action passed arguments
    if len(sys.argv) > 1:

        if '--outsensor=OFF' in sys.argv:
            GLOBAL_enable_out_temp_sensor = False

        if '--insensor=OFF' in sys.argv:
            GLOBAL_in_sensor_enable = False

        if '--rainsensor=OFF' in sys.argv:
            GLOBAL_rain_sensor_enable = False

        if '--thingspeak=OFF' in sys.argv:
            GLOBAL_thingspeak_enable_update = False

        if '--LEDtime=ON' in sys.argv:
            GLOBAL_LED_display_time = True
            
        if '--display=ON' in sys.argv:
            GLOBAL_screen_output = True

        if '--help' in sys.argv:
            print('usage: ./wstation.py {command}')
            print('')
            print('   --outsensor=OFF    - disables outside temperature monitoring')
            print('   --insensor=OFF     - disables inside temperature monitoring')
            print('   --rainsensor=OFF   - disables rainfall monitoring')
            print('   --thingspeak=OFF   - disable update to ThingSpeak')
            print('   --LEDtime=ON       - enables printing of LED toggle time')
            print('   --display=ON       - outputs data to screen')
            sys.exit(0)


    #Set up hardware
    setup_hardware()
    
    #Read thingspeak write api key from file
    if GLOBAL_thingspeak_enable_update:
        GLOBAL_thingspeak_write_api_key = thingspeak_get_write_api_key(GLOBAL_thingspeak_api_key_filename)

    #Set up variables
    inside          = {'temp':0 , 'hum':0}
    
    #convert from minutes to no. of tasks
    GLOBAL_rain_tick_meas_time = (GLOBAL_rain_tick_meas_time * 60) / GLOBAL_update_rate
    GLOBAL_rain_tick_count = 0
    GLOBAL_rain_task_count = 0
    
    sensor_data     = []
    sensors         = []


    #Prepare sensor list
    if GLOBAL_out_sensor_enable:
        sensors.append('outside temp')

    if GLOBAL_in_sensor_enable:
        sensors.append('inside temp')
        sensors.append('inside hum')
        
    if GLOBAL_door_sensor_enable:
        sensors.append('door open')
        
    if GLOBAL_rain_sensor_enable:
        sensors.append('rainfall')

    #Prepare thingspeak data to match sensor number
    sensor_data = [0 for i in sensors]

    if GLOBAL_thingspeak_enable_update and GLOBAL_screen_output:
        print('Thingspeak set up:')
        print(sensors)
        print(sensor_data)

    next_reading = time.time()

    #Main code
    try:
        while True:
            
            #Get rain fall measurement
            if GLOBAL_out_sensor_enable:
                if GLOBAL_rain_task_count == GLOBAL_rain_tick_meas_time:
                    sensor_data[GLOBAL_rain_TS_field-1] = GLOBAL_rain_tick_count * GLOBAL_rain_tick_measure
                    GLOBAL_rain_tick_count = 0
                    GLOBAL_rain_task_count = 0
                else:
                    GLOBAL_rain_task_count += 1
                    print(GLOBAL_rain_task_count)

            #Check door status
            if GLOBAL_door_sensor_enable:
                sensor_data[GLOBAL_door_TS_field-1] = get_door_status()
                
            #Get outside temperature
            if GLOBAL_out_sensor_enable:
                sensor_data[GLOBAL_out_temp_TS_field-1] = get_ds18b20_temp(GLOBAL_out_temp_sensor_ref)
                
            #Get inside temperature and humidity
            if GLOBAL_in_sensor_enable:
                inside = get_dht22_data()
                sensor_data[GLOBAL_in_temp_TS_field-1] = inside['temp']
                sensor_data[GLOBAL_in_hum_TS_field-1] = inside['hum']

            #Display data on screen
            if GLOBAL_screen_output:
                output_data(sensors, sensor_data)

            #Send data to thingspeak
            if GLOBAL_thingspeak_enable_update:
                thingspeak_update_channel(GLOBAL_thingspeak_write_api_key, sensor_data)

            #Delay to give update rate
            next_reading += GLOBAL_update_rate
            sleep_length = next_reading - time.time()
            #print(sleep_length)
            if sleep_length > 0:
                time.sleep(sleep_length)

    except KeyboardInterrupt:
        exit_code()
        sys.exit(0)


#===============================================================================
# Boiler plate
#===============================================================================
if __name__=='__main__':
    main()
