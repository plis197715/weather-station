#-----------------------------------------------------------------------
#
# Controls weatherstation
#
#-----------------------------------------------------------------------

#!usr/bin/env python

#=======================================================================
# Import modules
#=======================================================================
import os, sys, threading
import time, datetime
import httplib, urllib
import pigpio, DHT22
import DS18B20, thingspeak


#=======================================================================
# LOAD DRIVERS
#=======================================================================
pi = pigpio.pi()


#=======================================================================
# GLOBAL VARIABLES
#=======================================================================

# --- Set up GPIO referencing----
GLOBAL_BROADCOM_REF     = True

if GLOBAL_BROADCOM_REF == True:
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
GLOBAL_thingspeak_write_api_key     = '30SNTCFLNJEI3937'

GLOBAL_thingspeak_field_1   = 1
GLOBAL_thingspeak_field_2   = 2
GLOBAL_thingspeak_field_3   = 3
GLOBAL_thingspeak_field_4   = 4
GLOBAL_thingspeak_field_5   = 5
GLOBAL_thingspeak_field_6   = 6
GLOBAL_thingspeak_field_7   = 7
GLOBAL_thingspeak_field_8   = 8


# --- Set up sensors ----
GLOBAL_out_sensor_enable    = True
GLOBAL_out_temp_sensor_ref  = '28-0414705bceff'
GLOBAL_out_temp_TS_field    = GLOBAL_thingspeak_field_1

GLOBAL_in_sensor_enable     = True
GLOBAL_in_sensor_ref        = 'DHT22'
GLOBAL_in_sensor_pin        = GLOBAL_Pin_11
GLOBAL_in_temp_TS_field     = GLOBAL_thingspeak_field_2
GLOBAL_in_hum_TS_field      = GLOBAL_thingspeak_field_3

GLOBAL_door_sensor_enable   = True
GLOBAL_door_sensor_pin      = GLOBAL_Pin_14
GLOBAL_door_TS_field        = GLOBAL_thingspeak_field_4

GLOBAL_rain_sensor_enable   = True
GLOBAL_rain_sensor_pin      = GLOBAL_Pin_13
GLOBAL_rain_TS_field        = GLOBAL_thingspeak_field_5
GLOBAL_rain_tick_measure    = 1.5 #millimeters
GLOBAL_rain_tick_meas_time  = 0.5 #minutes
GLOBAL_rain_tick_count      = 0
GLOBAL_rain_task_count      = 0


# --- Set up flashing LED ----
GLOBAL_LED_display_time     = False
GLOBAL_LED_pin              = GLOBAL_Pin_12
GLOBAL_LED_flash_rate       = 1  # seconds
GLOBAL_next_call            = time.time()



#=======================================================================
# SETUP HARDWARE
#=======================================================================
def setup_hardware():

    #Set up DHT22
    global s
    global GLOBAL_in_sensor_pin
    global GLOBAL_door_sensor_pin
    global GLOBAL_rain_sensor_pin
    
    s = DHT22.sensor(pi, GLOBAL_in_sensor_pin)

    #Set up rain sensor input pin
    pi.set_mode(GLOBAL_rain_sensor_pin, pigpio.INPUT)
    rain_gauge = pi.callback(GLOBAL_rain_sensor_pin, pigpio.RISING_EDGE, count_rain_ticks)

    #Set up door sensor input pin
    pi.set_mode(GLOBAL_door_sensor_pin, pigpio.INPUT)
    
    #Set up LED flashing thread
    pi.set_mode(GLOBAL_LED_pin, pigpio.OUTPUT) #Set up LED pin out
    timerThread = threading.Thread(target=toggle_LED)
    timerThread.daemon = True
    timerThread.start()


#=======================================================================
# EDGE CALLBACK FUNCTION TO COUNT RAIN TICKS
#=======================================================================
def count_rain_ticks(gpio, level, tick):
    
    global GLOBAL_rain_tick_count
    
    GLOBAL_rain_tick_count += 1
    print(GLOBAL_rain_tick_count)
    time.sleep(0.1) #debounce
    

#=======================================================================
# READ DATA FROM DHT22
#=======================================================================
def get_dht22_data():

    global s

    s.trigger()

    time.sleep(0.2) #Do not over poll DHT22

    return {'temp':s.temperature(), 'hum':s.humidity()}


#=======================================================================
# OUTPUT DATA TO SCREEN
#=======================================================================
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


#=======================================================================
# DOOR SENSOR
#=======================================================================
def get_door_status():

    global GLOBAL_door_sensor_pin
            
    return pi.read(GLOBAL_door_sensor_pin)
    
    

#=======================================================================
# TOGGLE LED
#=======================================================================
def toggle_LED():

    global GLOBAL_next_call
    global GLOBAL_LED_display_time

    if GLOBAL_LED_display_time == True:
        print(datetime.datetime.now())

    #Prepare next thread time
    GLOBAL_next_call = GLOBAL_next_call + GLOBAL_LED_flash_rate
    threading.Timer( GLOBAL_next_call - time.time(), toggle_LED ).start()

    #Toggle LED
    if pi.read(GLOBAL_LED_pin) == 0:
        pi.write(GLOBAL_LED_pin, 1)
    else:
        pi.write(GLOBAL_LED_pin, 0)


#=======================================================================
# EXIT ROUTINE
#=======================================================================
def exit_code():

    global s

    #Set pins to OFF state
    pi.write(GLOBAL_LED_pin, 0)

    s.cancel()

    print('\nExiting program...')



#=======================================================================
# MAIN
#=======================================================================
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
            sys.exit(0)


    #Set up hardware
    setup_hardware()

    #Set up variables
    outside_temp    = 0
    inside          = {'temp':0 , 'hum':0}
    door_open       = 0
    GLOBAL_rain_tick_meas_time = (GLOBAL_rain_tick_meas_time * 60) / GLOBAL_update_rate #convert from minutes to no. of tasks
    GLOBAL_rain_tick_count = 0
    GLOBAL_rain_task_count = 0
    
    sensor_data     = []
    sensors         = []


    #Prepare sensor list
    if GLOBAL_out_sensor_enable == True:
        sensors.append('outside temp')

    if GLOBAL_in_sensor_enable == True:
        sensors.append('inside temp')
        sensors.append('inside hum')
        
    if GLOBAL_door_sensor_enable == True:
        sensors.append('door open')
        
    if GLOBAL_rain_sensor_enable == True:
        sensors.append('rainfall')

    #Prepare thingspeak data to match sensor number
    for i in range(0, len(sensors)):
        sensor_data.append(0)

    if GLOBAL_thingspeak_enable_update == True and GLOBAL_screen_output == True:
        print('Thingspeak set up:')
        print(sensors)
        print(sensor_data)

    next_reading = time.time()

    #Main code
    try:
        while True:
            
            #Get rain fall measurement
            if GLOBAL_out_sensor_enable == True:
                if GLOBAL_rain_task_count == GLOBAL_rain_tick_meas_time:
                    sensor_data[GLOBAL_rain_TS_field-1] = GLOBAL_rain_tick_count * GLOBAL_rain_tick_measure
                    GLOBAL_rain_tick_count = 0
                    GLOBAL_rain_task_count = 0
                else:
                    GLOBAL_rain_task_count += 1
                    print(GLOBAL_rain_task_count)

            #Check door status
            if GLOBAL_door_sensor_enable == True:
                door_open = get_door_status()                
                sensor_data[GLOBAL_door_TS_field-1] = door_open
                
            #Get outside temperature
            if GLOBAL_out_sensor_enable == True:
                outside_temp = get_ds18b20_temp(GLOBAL_w1_device_path, GLOBAL_out_temp_sensor_ref)
                sensor_data[GLOBAL_out_temp_TS_field-1] = outside_temp
                
            #Get inside temperature and humidity
            if GLOBAL_in_sensor_enable == True:
                inside = get_dht22_data()
                sensor_data[GLOBAL_in_temp_TS_field-1] = inside['temp']
                sensor_data[GLOBAL_in_hum_TS_field-1] = inside['hum']

            #Display data on screen
            if GLOBAL_screen_output == True:
                output_data(sensors, sensor_data)

            #Send data to thingspeak
            if GLOBAL_thingspeak_enable_update == True:
                thingspeak.update_channel(GLOBAL_thingspeak_host_addr, GLOBAL_thingspeak_write_api_key, sensor_data, GLOBAL_screen_output)

            #Delay to give update rate
            next_reading += GLOBAL_update_rate
            sleep_length = next_reading - time.time()
            #print(sleep_length)
            if sleep_length > 0:
                time.sleep(sleep_length)

    except KeyboardInterrupt:
        exit_code()
        sys.exit(0)


#=======================================================================
# Boiler plate
#=======================================================================
if __name__=='__main__':
    main()
