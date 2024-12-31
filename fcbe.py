#    Project - FC Box Extractor
#    Copyright(c) 2024-2025 Adrian Mansell
#    arnie@spoonwibble.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see https://www.gnu.org/licenses/.

# Import Module
from ardupilot_log_reader.reader import Ardupilot
from geopy.distance import geodesic
import json
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from typing import Dict, List, Union
import os


'''
Simplified representation of a 3D position at a time
'''
class Pos:
    def __init__(s, Lat: float, Lng: float, Alt: float, timestamp: float=0.0, index: int=0):
        s.Lat = Lat
        s.Lng = Lng
        s.Alt = Alt
        s.timestamp = timestamp
        s.int = index


    def get(s) -> Dict[str, Union[float, int]]:
        return {
            "Lat": s.Lat,
            "Lng": s.Lng,
            "Alt": s.Alt,
            "timestamp": s.timestamp,
            "index": s.index
        }
    

    def __str__(s):
        return f"Lat: {round(s.Lat, 7)}  Lng: {round(s.Lng, 7)}  Alt: {round(s.Alt, 2)}"
    

'''
F3A Zone box store and write functions
'''
class F3aZone:
    def __init__(s) -> None:
        s.pilot = None
        s.centre = None
        
    def __str__(s) -> str:
        if s.valid():
            return f"Pilot:  {str(s.pilot)}\nCentre: {str(s.centre)}"
        else:
            return "F3aZone position has not been set."
        
    def valid(s) -> bool:
        return (s.pilot is not None) and (s.centre is not None)
    
    def unset(s) -> None:
        s.pilot = None
        s.centre = None
    
    def set(s, pilot: Pos, centre: Pos) -> None:
        s.pilot = pilot
        s.centre = centre
              
    def write(s, path) -> None:
        with open(path, "w") as fd:
            fd.write("Emailed box data for F3A Zone Pro - please DON'T modify!\n")
            fd.write("1\n")
            fd.write(f"{round(s.pilot.Lat, 7)}\n")
            fd.write(f"{round(s.pilot.Lng, 7)}\n")
            fd.write(f"{round(s.centre.Lat, 7)}\n")
            fd.write(f"{round(s.centre.Lng, 7)}\n")
            fd.write(f"{round(s.pilot.Alt, 2)}\n")


'''
Parse a logfile into a pandas dataframe and provide analysis of it.
Methods are generally in two categories:
   - dealing with the log as a whole including all message types
   - dealing specifically with position, automatically choosing POS/XKF1/GPS source
'''
class FcLog:
    def __init__(s, file_path: str, message_types: List[str]):
        s.file_path = file_path
        s.message_types = message_types     

        # Parse the bin file and work out preferred position message type.
        s.log = Ardupilot.parse(bin_file=file_path, types=message_types, zero_time_base=True)
        s.pos_msg = None
        for m in ["POS", "XKF1", "GPS"]:
            try:
                s.pos = s.log.dfs[m]
            except:
                pass
            else:
                s.pos_msg = m
                break

        if s.pos_msg == None:
            prnt("BIN file does not contain POS, XKF1 or GPS position messages.")
            prnt("Are you sure it is a valid Ardupilot log?")
            return
        
        prnt(f"Using {s.pos_msg} messages for position info.")

        # Find origin as a point 2.5s after records begin
        t_range = s.get_pos_time_range_s()
        s.origin = s.get_pos_at_time(t_range[0] + 2.5)

    def __str__(s):
        if s.pos_msg is None:
            return "Log is empty or faulty."
        else:
            return f"Position message type: {s.pos_msg}\nOrigin: ({round(s.origin.timestamp, 1)}s):  {s.origin}"

    #---------------------------------------------------------------------
    # General log methods, dealing with any message type.
    #---------------------------------------------------------------------
    # Get a log of a message type by name.
    def get_msg_log(s, msg_type: str):
        try:
            return s.log.dfs[msg_type]
        except:
            return None
 
    # Given a time and a message type, return the index of the element with the nearest timestamp.
    def get_msg_index_from_time_s(s, t_secs: float, msg_type: str) -> Union[int, None]:
        data = s.get_msg_log(msg_type)
        if data is not None:
            ts = data.timestamp.to_numpy()
            diff = np.fabs(np.subtract(t_secs, ts))
            where = np.where(diff == np.min(diff))
            return int(where[0][0])
        return None
 
    # Return minimum and maximum timestamps (seconds) for a message type.
    def get_msg_time_range_s(s, msg_type: str) -> Union[List[float], None]:
        data = s.get_msg_log(msg_type)
        if data is not None:
            return [data.timestamp[0], data.timestamp[len(data.timestamp) - 1]]
        return None


    #---------------------------------------------------------------------
    # Position-specific methods.
    #---------------------------------------------------------------------
    # Get the full log of positions.
    def get_pos_log(s) -> Union[pd.DataFrame, None]:
        return s.pos
   
    # Get position at a time
    def get_pos_at_time(s, t: float) -> Pos:
        i = s.get_pos_index_from_time_s(t)
        return Pos(s.pos.Lat[i], s.pos.Lng[i], s.pos.Alt[i], s.pos.timestamp[i], i)

    # Given a time, return the index of the position element with the nearest timestamp.
    def get_pos_index_from_time_s(s, t_secs: float) -> Union[int, None]:
        return s.get_msg_index_from_time_s(t_secs, s.pos_msg)  
 
    # Return the minimum and maximum position timestamps (seconds).
    def get_pos_time_range_s(s) -> Union[List[float], None]:
        return s.get_msg_time_range_s(s.pos_msg)  
 
    # Return the location record of the origin.
    def get_origin(s) -> Pos:
        return s.origin
 
    # Return the distance in metres from the origin.
    def get_dist_to_origin_m(s, pos: Pos) -> float:
        return FcLog.get_dist_m(s.origin, pos)
 
    # Distance between two position records.    
    @staticmethod
    def get_dist_m(pos0: Pos, pos1: Pos) -> float:
        distance_2d = geodesic((pos0.Lat, pos0.Lng), (pos1.Lat, pos1.Lng)).m
        return np.sqrt(distance_2d**2 + (pos0.Alt - pos1.Alt)**2)


'''
Open the user's choice of ardupilot bin file and create an FcLog object from it.
If a valid file is opened, update the init path for the dialogue
and clear the status widget.
'''
def open_file() -> None:
    global log, config

    # Get file path using tk dialogue.
    log = None
    file_types = (("Ardupilot BINs", "*.BIN"), ("All files", "*.*"))
    file_path = tk.filedialog.askopenfilename(title="Open a BIN file", initialdir=config["open_file"]["path"], filetypes=file_types)
    clear()

    # Check it exists.
    if not os.path.exists(file_path):
        prnt("Please choose a valid FC BIN file")
        return
    prnt(f"Opening {file_path}...")

    # Load it
    log = FcLog(file_path=file_path, message_types=config["open_file"]["message_types"])
    if log is None:
        prnt(f"Unable to parse the BIN file at {file_path}")
        prnt("Are you sure it is a valid Ardupilot log?")
        return

    # All good, update the initdir for future dialogues.
    config["open_file"]["path"] = os.path.dirname(os.path.realpath(file_path))
    config["open_file"]["file"] = os.path.basename(os.path.realpath(file_path))
    prnt(f"{log}")


'''
---------------------------------------------------------------------
BOX EXTRACTION
Extract the box positions from the current file.
If rc_switch_channel is zero, or there are not enough switch transitions,
it will try to find stationary periods in the log and use those.
Otherwise, it will use the switch transition times.
'''
def extract_box() -> None:
    global log, config, f3az
    if log is None:
        prnt("Please open a BIN file to be analysed.")
        return
    prnt()
    
    # Find times at which to report the location
    rc_channel = config["find_rc_switch_times"]["rc_switch_channel"]
    times = []
    if rc_channel > 0:
        times = find_rc_switch_times()
    
    if rc_channel == 0 or len(times) < 2:
        times = find_static_position_times()
    
    if len(times) < 2:
        prnt("Failed to find at least two times to provide box locations")
        return

    # Display the locations and combine into 5m clusters
    t_origin = log.get_origin().timestamp
    cluster = []
    for t in times:
        if t < t_origin:
            prnt(f"Skippng time {round(t,1)}s as it occurs before the origin time ({round(t_origin,1)})")
            continue
        p = log.get_pos_at_time(t)
        d = log.get_dist_to_origin_m(p)
        prnt(f"\nPosition at time {round(t,1)}s, {round(d,1)}m from origin:")   
        prnt(f"{round(p.Lat, 7)}")
        prnt(f"{round(p.Lng, 7)}")
        
        found = False
        for i, c in enumerate(cluster):
            if FcLog.get_dist_m(p, c) < 5.0:
                cluster[i] = p
                found = True
                break
            
        if not found:
            cluster.append(p)
    
    if len(cluster) == 2:
        f3az.set(cluster[0], cluster[1])
        prnt('\nBox extracted:')
        prnt(str(f3az))       
    else:
        prnt('\nBox position is unclear.')
        f3az.unset()        


'''
Scan through the logs to find transitions in the RC input channel.
It uses 1500us as the switch point.
There is no hysteresis or debounce, it doesn't seem to be necessary.
'''
def find_rc_switch_times() -> List[float]:
    global log, config

    rc_str = f'C{config["find_rc_switch_times"]["rc_switch_channel"]}'
    switch_times = []
    
    try:
        rcin = log.get_msg_log("RCIN")
        ppm = rcin[rc_str]
        tim = rcin["timestamp"]
        assert(len(ppm) == len(tim))
    except:
        prnt(f"Log is missing RCIN messages for channel {rc_str}.")
    else:
        for i in range(len(ppm) - 1):
            now = ppm[i]
            next_now = ppm[i+1]
            if (now < 1500 and next_now >= 1500) or (now >= 1500 and next_now < 1500):
                switch_times.append(tim[i])
    
    prnt("Found " + str(len(switch_times)) + " switch transitions of channel " + rc_str)
    return switch_times


'''
Search for stationary periods in the log.
To be classed as stationary, a sliding window of width window_secs
is applied to the 3D position, the vehicle must have moved less than
tolerance_metres between the edges of the window.
Hysteresis is applied when coming out of a stationary window.
'''
def find_static_position_times() -> List[float]:
    global config, log
    cfg             = config["find_static_position_times"]
    window_secs      = cfg["window_secs"]
    tolerance_metres = cfg["tolerance_metres"]
    hysteresis      = cfg["hysteresis"]
    switch_times = []

    # Step through in 0.5s jumps
    t_range = log.get_pos_time_range_s()
    state = "find_start"
    while (t_range[0] + window_secs) < t_range[1]:
        p0 = log.get_pos_at_time(t_range[0])
        p1 = log.get_pos_at_time(t_range[0] + window_secs)
        distance = log.get_dist_m(p0, p1)
        match state:
            case "find_start":
                if distance <= tolerance_metres:
                    start = t_range[0]
                    state = "find_end"
            case "find_end":
                if distance > tolerance_metres:
                    end = t_range[0] + window_secs
                    # Bias the actually measurement time towards the end of the period
                    meas_time = start + ((end - start) * 0.7)
                    prnt(f"Stationary between {round(start,1)}s and {round(end,1)}s, will measure at {round(meas_time,1)}s")
                    switch_times.append(meas_time)
                    state = "hysteresis"
            case "hysteresis":
                if distance > (tolerance_metres * hysteresis):
                    state = "find_start"
            case _:
                break
        t_range[0] = t_range[0] + 0.5

    return switch_times


'''
---------------------------------------------------------------------
BOX SAVE
Assuming a successful extraction, save the box to F3A Zone file.
'''
def save_box() -> None:
    global config, f3az
    
    if not f3az.valid():
        prnt("No usable box available to be written.")
        return

    # Get file path using tk dialogue.
    file_path = tk.filedialog.asksaveasfilename(
        title="Save File", 
        initialdir=config["open_file"]["path"], 
        initialfile=f"{((config["open_file"]["file"]).split('.'))[0]}.f3a",
        filetypes=[("F3A Zone", ".f3a")]
        )

    f3az.write(file_path)
    prnt(f"Box written to {file_path}")
    
    
'''
---------------------------------------------------------------------
GPS ACCURACY
Extract min, avg, max values for GPS HAcc, VAcc, NSats.
Requires both GPS and GPA log messages.
'''
def gps_accuracy():
    global log
    if log is None:
        prnt("Please open a BIN file to be analysed.")
        return

    try:
        HAcc = min_avg_max(log.get_msg_log("GPA").HAcc.to_numpy())
        VAcc = min_avg_max(log.get_msg_log("GPA").VAcc.to_numpy())
        NSat = min_avg_max(log.get_msg_log("GPS").NSats.to_numpy())
    except:
        prnt("\nLog is missing GPS or GPA entries")
    else:
        prnt(f"\nAccuracy  (min,avg,max):  H [{HAcc[0]}, {HAcc[1]}, {HAcc[2]}]m   V [{VAcc[0]}, {VAcc[1]}, {VAcc[2]}]m")
        prnt(f"Sat Count (min,avg,max):  [{NSat[0]}, {NSat[1]}, {NSat[2]}]")
    return


'''
---------------------------------------------------------------------
MESSAGE RATES
Parse the log for rates of key messages.
'''
def message_rates() -> None:
    global log, config
    if log is None:
        prnt("Please open a BIN file to be analysed.")
        return
    prnt()

    for msg in config["open_file"]["message_types"]:
        try:
            n_msgs = len(log.get_msg_log(msg).index)
        except:
            prnt(f"{msg}: not found in the log")
        else:
            t_range = log.get_msg_time_range_s(msg)
            period = (t_range[1] - t_range[0]) / n_msgs
            if period > 0:
                freqHz = 1 / period
            else:
                freqHz = 0
            prnt(f"{msg}:  {n_msgs} messages at {round(freqHz, 1)}Hz ({round(period * 1000, 1)}ms)")

    return


'''
---------------------------------------------------------------------
UTILITIES
'''
'''
Print a string to the status window, adding a newline.
'''
def prnt(st: str="") -> None:
    global status, root
    try:
        status.insert(tk.END, st + "\n")
        root.update()
    except:
        pass


'''
Clear the status window.
'''
def clear():
    global status
    status.delete("1.0","end")


'''
Given a numpy array of numbers, find the min, mean and max of the middle 70% of values.
'''
def min_avg_max(arr: np.array, precis: int=1) -> List[float]:
    length = len(arr)
    if length < 1000:
        return [0.0, 0.0, 0.0]
    st = int(length * 0.15)
    en = int(length * 0.85)
    arr = arr[st:en]
    return [round(np.min(arr), precis), round(np.mean(arr), precis), round(np.max(arr), precis)]


'''
---------------------------------------------------------------------
CONFIGURATION
Write out config as json file
'''
def write_config(path: str, cfg: Dict) -> None:
    with open(path, 'w') as json_file:
        json.dump(cfg, json_file, indent=3)
    return


'''
Create a default configuration file
'''
def create_default_config_file(path: str) -> None:
    default_config = {
        "open_file": {
            "path": "",
            "message_types": ["XKF1", "POS", "ATT", "GPS", "GPA", "MAG", "RCIN"]
        },
        "find_rc_switch_times": {
            "rc_switch_channel": 0
        },
        "find_static_position_times": {
            "window_secs": 8.0,
            "tolerance_metres": 1.0,
            "hysteresis": 3
        }
    }
    default_config["open_file"]["path"] = os.path.dirname(os.path.realpath(__file__))
    write_config(path=path, cfg=default_config)
    return


def rc_spinbox_change():
    global config, rc_switch
    config["find_rc_switch_times"]["rc_switch_channel"] = int(rc_switch.get())


if __name__ == "__main__":
    # Globals.
    global config, log, rc_switch, root, status
    global f3az
    log = None
    
    f3az = F3aZone()
    
    # If it doesn't exist, create the configuration file.
    cfgFile = os.path.dirname(os.path.realpath(__file__)) + "\\fcbe_config.json"
    if not os.path.exists(cfgFile):
        create_default_config_file(cfgFile)
    
    # Load configuration.
    with open(cfgFile) as json_file:
        config = json.load(json_file)

    # root window, dimension and frames.
    root = tk.Tk()
    root.title("FC Box Extractor")
    root.geometry("575x600")
    button_frame = tk.Frame(root)
    text_frame = tk.Frame(root)
    button_frame.grid(column=0, row=0)
    text_frame.grid(column=0, row=1)

    # Button frame
    of = tk.Button(button_frame, text="Open .bin File", command=open_file)
    of.grid(column=0, row=0, padx=2)

    eb = tk.Button(button_frame, text="Extract Box", command=extract_box)
    eb.grid(column=1, row=0, padx=2)

    wb = tk.Button(button_frame, text="Save Box", command=save_box)
    wb.grid(column=2, row=0, padx=2)

    pa = tk.Button(button_frame, text="GPS Accuracy", command=gps_accuracy)
    pa.grid(column=3, row=0, padx=2)

    mr = tk.Button(button_frame, text="Msg. Rates", command=message_rates)
    mr.grid(column=4, row=0, padx=2)

    rc_frame = tk.Frame(button_frame, width=10, relief="ridge", bd=2)
    rc_frame.grid(column=5, row=0, padx=2)
    rc_label = tk.Label(rc_frame, text="RC Ch:")
    rc_label.pack(padx=5, side=tk.LEFT)
    rc_switch = tk.StringVar(value=config["find_rc_switch_times"]["rc_switch_channel"])
    rc = tk.Spinbox(rc_frame, from_=0, to=24, width=3, textvariable=rc_switch, command=rc_spinbox_change)
    rc.pack(padx=1, side=tk.LEFT)

    # Status widget
    status = tk.Text(text_frame, height=34, width=70)
    status.pack(padx=3)

    # Start GUI
    root.mainloop()

    # Update configuration file on exit
    write_config(path=cfgFile, cfg=config)