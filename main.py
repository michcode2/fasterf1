from fastf1.livetiming.client import SignalRClient as sigR
import fastf1.livetiming.client as cli

import asyncio
import logging
import json
import zlib
import base64
#import pygame
import requests

client = sigR(filename="cache.txt", debug=True)


def fix_json(elem):
        # fix F1's not json compliant data
        elem = elem.replace("'", '"') \
            .replace('True', 'true') \
            .replace('False', 'false')
        return elem

async def main():
    with open("readings.json", "w") as file:
        file.write("{")

    # one dictionary for the interval, one for the gap to leader. make this better
    timing_data={}
    while True:
        newest = fix_json(client.message) # get the most recent message


        # print timing data
        print_table(timing_data)

        # reading in the json
        if client.message != "nuh uh": #make sure its actual data
            with open("readings.json", 'a') as file: # log everything to a file
                file.write(newest)
                file.write(",\n")
            
            data=json.loads(newest) # load in the json

            try:
                M = data['M'][0] # get the right 
                kind = M['A'][0] # what kind of data it is, full list in client.py/self.topics
                print(kind)

                if kind == "TimingData":
                    info = M['A'][1]['Lines']
                    drivers = info.keys()
                    for driver in drivers:

                        if not driver in timing_data.keys(): # check that there is an entry for the driver that im looking at
                            timing_data[driver] = {}

                        if 'IntervalToPositionAhead' in info[driver].keys(): # if the data is for interval, do the thing
                            timing_data[driver]['ahead'] = float(info[driver]['IntervalToPositionAhead']['Value'])

                        elif 'GapToLeader' in info[driver].keys():
                            timing_data[driver]['leader'] = float(info[driver]['GapToLeader'])

                        elif 'Sectors' in info[driver].keys():
                            temp = list(info[driver]['Sectors'].keys())[0]
                            timing_data[driver]['sector'] = int(temp)
                            timing_data[driver]['segment'] = int(list(info[driver]['Sectors'][temp]['Segments'].keys())[0])
                        
                        elif 'Speeds' in info[driver].keys():
                            timing_data[driver]['speedt'] = float(info[driver]['Speeds']['ST']['Value'])
                
                elif kind == "CarData.z":
                    info = M['A'][1]
                    inflated = zlib.decompress(base64.b64decode(info), -zlib.MAX_WBITS)
                    cardata = json.loads(inflated)['Entries'][-1]['Cars']
                    for driver in cardata.keys():
                        if not driver in timing_data.keys(): # check that there is an entry for the driver that im looking at
                            timing_data[driver] = {}
                        
                        timing_data[driver]['speed'] = cardata[driver]['Channels']['2']
                        timing_data[driver]['RPM'] = cardata[driver]['Channels']['0']

                elif kind == "Position.z":
                    info = M['A'][1]
                    inflated = zlib.decompress(base64.b64decode(info), -zlib.MAX_WBITS)
                    positions = json.loads(inflated)['Position'][-1]['Entries']
                    for driver in positions.keys():
                        if not driver in timing_data.keys(): # check that there is an entry for the driver that im looking at
                            timing_data[driver] = {}
                        timing_data[driver]['status'] = positions[driver]['Status']
                        timing_data[driver]['x'] = positions[driver]['X']
                        timing_data[driver]['y'] = positions[driver]['Y']
                        timing_data[driver]['z'] = positions[driver]['Z']
                        

                        with open("positions.txt", "a") as file:
                            file.write(f"{positions[driver]['X']},{positions[driver]['Y']}")
                    
                elif kind == "TimingStats":
                    info = M['A'][1]['Lines']
                    for driver in info.keys():
                        if 'PersonalBestLapTime' in info[driver].keys():
                            timing_data[driver]['pos'] = info[driver]['PersonalBestLapTime']['Position']
                            try:
                                timing_data[driver]['time'] = info[driver]['PersonalBestLapTime']['Value']
                            except:
                                pass


            except BaseException as error:
                with open("errors.txt", 'a') as file:
                    file.write(f"error: {error}")
                    file.write("\n")

        await asyncio.sleep(0.05)


def print_table(data):
    print("\033[2Jnumber\tint\tleader\tsector\tspeedtrap\tspeed\tsituation\tfastest pos\ttrack pos") # print the head to the tables
    print()
    order = data.keys()
    
    try:
        order = sorted(data.items(), key=lambda item: item[1]['leader'])
    except:
        pass

    for key in order:
        print(f"{key}\t", end = "")
        try:
            print(f"{data[key]['ahead']}\t", end="")
        except:
            print("\t", end="")

        try:
            print(f"{data[key]['leader']}\t", end="")
        except:
            print("\t", end="")
        
        try:
            print(f"{data[key]['sector']}/{data[key]['segment']}\t", end="")
        except:
            print("\t", end="")

        try:
            print(f"{data[key]['speedt']}\t\t", end="")
        except:
            print("\t\t", end="")

        try:
            print(f"{data[key]['speed']}\t", end="")
        except:
            print("\t", end="")

        try:
            print(f"{data[key]['status']}\t\t", end="")
        except:
            print("\t\t", end="")

        try:
            print(f"{data[key]['pos']}\t", end="")
        except:
            print("\t\t", end="")

        try:
            print(f"{data[key]['x']},{data[key]['y']}", end = "")
        except:
            print("\t", end = "")

        print()






asyncio.run(client._async_start(main()))

