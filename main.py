import csv
from datetime import datetime, timedelta
from skyfield.api import load
from skyfield.sgp4lib import EarthSatellite
from skyfield.toposlib import Topos
import struct
import numpy as np
import time
import logging
from collections import defaultdict


# Constants
BATTERY_CAPACITY_WH = 72
USABLE_BATTERY_CAPACITY = BATTERY_CAPACITY_WH * 0.4
POWER_CONSUMPTION_ON = 23  # Watts when payload is ON
POWER_CONSUMPTION_OFF = 3   # Watts when payload is OFF
AVERAGE_POWER_GENERATION = 20  # Watts
DATA_GENERATION_RATE = 1  # MB/s
STORAGE_CAPACITY_MB = 25 * 1024  # Convert GB to MB
line1= None
line2= None

#File Name
file_name ='TLE.txt'
file_path = 'Pass_Summary.csv'
command_file_path = 'Satellite_Commands.csv'
planets = load('de421.bsp')


#Ground Station Master List
ground_stations = {
    'Bangalore': {'latitude': 12.9716, 'longitude': 77.5946},
    'New_Zealand': {'latitude': -40.9006, 'longitude': 174.8860},
    'Seoul': {'latitude': 37.5519, 'longitude': 126.9918}
}

# start Time and End Time
ts = load.timescale()
start_time = ts.utc(2023, 12, 16, 20)  # Start time in UTC YEAR, MONTH , DAY , HOUR
end_time = ts.utc(2023, 12, 18,20)    # End time in UTC
time_step = 60  # Step in every minute
jd_start = start_time.tt
jd_end = end_time.tt
jd_times = np.arange(jd_start, jd_end, time_step / (24 * 60 * 60))
times = ts.tt_jd(jd_times)


# for reading the tle file
def read_tle(file_name):
    try:
        with open(file_name, 'r') as file:
            line1 = file.readline().strip()
            line2 = file.readline().strip()
            return line1, line2
    except FileNotFoundError:
        return None, None
    
line1, line2 = read_tle(file_name)
if(line1==None or line2 == None):
    print("TLE File is not Found" )
satellite = EarthSatellite(line1, line2)

# for parsing the Gs Pass file
def find_time_in_file( t, time_format='%Y-%m-%d %H:%M:%S'):

    target_time =  datetime.strptime(str(t.utc_strftime('%Y-%m-%d %H:%M:%S')), time_format)
    matching_rows = []
    station = None
    with open(file_path, mode='r', newline='') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            start_time = datetime.strptime(row[3], time_format)
            end_time = datetime.strptime(row[4], time_format)
            
            if start_time <= target_time <= end_time:
                station = row[2]
                AOS =  row[3]
                LOS = row[4]
                return True ,station , AOS, LOS

    return False ,station , None, None

#To Caluclye the opaertional On and OFF time of the payload
def calculate_operational_time(current_status,remaining_power, remaining_storage , pass_status) :
    if remaining_power > .05 and remaining_storage >60  and current_status == 'Sunlit' and pass_status==False: ## sunlit and power is there and we can make the payload on 
        power_used = 3/60
        remaining_power -= power_used 
        data_generated = 60
        remaining_storage -= data_generated 
        Event = 'Payload On In sunlit'
        return remaining_power, remaining_storage , Event  
    else :
        if (remaining_power <= 0.05 or remaining_storage <=60) and current_status == 'Sunlit' and pass_status==False :
             power_added = 20/60
             Event= 'Payload OFF In Sunlit'
             remaining_power += power_added
             if remaining_power >28.8:
                    remaining_power =28.8
             return remaining_power , remaining_storage , Event
        else :
          if current_status == 'Eclipse' and pass_status==False:
            power_used = 3/60
            remaining_power -= power_used
            Event = 'Eclipse'
            return remaining_power , remaining_storage , Event
          else:
            if pass_status==True and current_status == 'Sunlit':
                power_added = 20/60
                Event= 'Data Downlink in Sunlit'
                remaining_power += power_added
                if remaining_power >28.8:
                    remaining_power =28.8
                data_downlinked = 1500
                remaining_storage +=data_downlinked
                if (remaining_storage>25600):
                        remaining_storage = 25600
                return remaining_power , remaining_storage , Event
            else:
                if pass_status == True and current_status == 'Eclipse' :
                    power_used = 3/60
                    Event= 'Data Downlink in Eclipse '
                    remaining_power -= power_used 
                    data_downlinked = 1500
                    remaining_storage +=data_downlinked
                    if (remaining_storage>25600):
                        remaining_storage = 25600
                    return remaining_power , remaining_storage, Event


#To Get altitude of satellite for given time
def get_satellite_altitude_above_earth(time):
    geocentric = satellite.at(time)
    subpoint = geocentric.subpoint()
    hex_altitude = float_to_hex_le(subpoint.elevation.m)
    return  hex_altitude     

#To  Genrate 4 bit  hex value 
def float_to_hex_le(value):
    bytes_value = struct.pack('<f', value)
    hex_value = bytes_value.hex()
    return hex_value

#Lat Long of the station
def get_lat_long(station_name):
   
    station = ground_stations.get(station_name)
    if station:
        hex_lat = float_to_hex_le(station['latitude'])
        hex_long = float_to_hex_le(station['longitude'])
        return hex_lat , hex_long
      
    else:
        return False, False

#to read command.csv
def read_command_file(command_file_path):
    command_dict = defaultdict(list)
     
    try:
        with open(command_file_path, mode='r', newline='') as file:
            reader = csv.reader(file)
            next(reader)  
            for row in reader:
                 
                command_dict[row[0]].append(row)
                
        logging.info("File read successfully")
    except Exception as e:
        logging.error(f"Error reading file: {e}")
    return command_dict

#to Search a command
def find_command(command_name, command_dict):
     
    return command_dict.get(command_name) 



#Main Function 


def main( ):
    # Format the timestamp as a string 
    timestamp_str = start_time.utc_datetime().strftime('%Y%m%d_%H')
    file_name = f"Command_Sch_Output_{timestamp_str}Hr.csv"
    with open(file_name, 'w', newline='') as file:

        writer = csv.writer(file)   
        writer.writerow(['TIME/DELAY', 'ACTION/COMMENT' ,'COMMAND','BYTE 0','BYTE_1','BYTE_2','BYTE_3','BYTE_4','BYTE_5','BYTE_6','BYTE_7','BYTE_8','BYTE_9','ARG_0','ARG_1','ARG_2','ARG_3','ARG_4','ARG_5','Hex-DATA1','Hex-DATA2','Hex-DATA3'])   
        earth = planets['earth']
        sun = planets['sun']
        remaining_power = USABLE_BATTERY_CAPACITY
        remaining_storage = STORAGE_CAPACITY_MB
        previous_status = None

        
        command_dict = read_command_file(command_file_path)
        
        for t in times:
            
            satellite_position = satellite.at(t)
            sun_position = sun.at(t)
            sun_lit =  satellite.at(t).is_sunlit(planets)
            
            current_status = "Sunlit" if sun_lit else "Eclipse"
            
            pass_status , station, AOS, LOS =  find_time_in_file(t)
            
            if(pass_status==True):
                hex_alt =get_satellite_altitude_above_earth(t)
                hex_lat, hex_long = get_lat_long(station)
                if (hex_lat == None or hex_long == None):
                    print ("Error :Station does not exist in master List")
                
                
            operational_time = calculate_operational_time(current_status, remaining_power, remaining_storage,pass_status)
        
            remaining_power = operational_time[0]
            remaining_storage = operational_time[1]
            Event =  operational_time[2]
            
            if Event != previous_status:
                if(Event =='Payload On In sunlit'):
                        result = find_command('ADCS_ATT_CTL_POINT_NADIR', command_dict)
                        formatted_result=result[0]
                        
                        writer.writerow([t.utc_strftime('%Y-%m-%dT%H:%M:%S'),'Send_Command-Nadir_Point' ,*formatted_result])
                        result = find_command('POWER_ON_PAYLOAD', command_dict)
                        formatted_result=result[0]

                        writer.writerow([60, 'Send_Command-Payload_ON ',*formatted_result] )
                else:
                        if(Event =='Data Downlink in Eclipse' or Event == 'Data Downlink in Sunlit'):
                            if (previous_status=='Payload On In sunlit'):
                                
                                adj_time =  str(t.utc_strftime('%Y-%m-%dT%H:%M:%S'))
                                time_obj = datetime.strptime(adj_time, '%Y-%m-%dT%H:%M:%S')
                                time_obj -= timedelta(seconds=30)
                                result = find_command('POWER_OFF_PAYLOAD', command_dict)
                                formatted_result=result[0]
                                writer.writerow([time_obj.strftime('%Y-%m-%dT%H:%M:%S'),'Send_Command-Payload OFF ',*formatted_result ])
                                writer.writerow([' '+'Ground_Station Pass-'+ station+' '+AOS+'Z '+LOS+'Z '])
                                result = find_command('ADCS_ATT_CTL_POINT_LLA', command_dict)
                                formatted_result=result[0]

                                writer.writerow([AOS,'Send_Command-Data_Downlink ',*formatted_result ,hex_lat,hex_long,hex_alt])
                            else :
                                writer.writerow([' '+'Ground_Station Pass-'+ station+' '+AOS+'Z '+LOS+'Z '])
                                result = find_command('ADCS_ATT_CTL_POINT_LLA', command_dict)
                                formatted_result=result[0]

                                writer.writerow([AOS,'Send_Command-Data_Downlink ',*formatted_result ,hex_lat,hex_long,hex_alt])

                                    
                        else:

                            if (previous_status=='Payload On In sunlit') :  # for Payload OFF in Sunlit Condition 
                                    result = find_command('POWER_OFF_PAYLOAD', command_dict)
                                    formatted_result=result[0]
                                    writer.writerow([t.utc_strftime('%Y-%m-%d %H:%M:%S'),'Send_Command-Payload OFF ',*formatted_result ])
                                
                                    writer.writerow([t.utc_strftime('%Y-%m-%d %H:%M:%S'), Event]) 
                            else:
                                    writer.writerow([t.utc_strftime('%Y-%m-%d %H:%M:%S'), Event]) 
                            
                        
            previous_status = Event

        print("Schedule File Generated") 
 
if __name__ == "__main__":
    main()