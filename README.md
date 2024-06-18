# README #

## What? ##
Python application for extracting the F3A box coordinates from a flight-coach/ardupilot .bin file.

## How to Install and Run ##
* Download the latest release zip file to a suitable folder e.g., My Documents\fcbe
* Right click the zip file and do Extract All
* Browse to the extracted folder
* Double click fcbe.exe to run it

## How to use it ##
### Preparing logs __without__ an RC connection to your FC hardware ###
Most people do not have their FC hardware connected to their RX so do not have the RC channels in their logs.  In this case, FCBE allows you to determine the box coordinates by placing the model and leaving it stationary.

* Fire up your model and wait for the GPS to be locked
* Place the model on the pilot's position
  * Leave it stationary for __20s__
* Place the model on your centreline reference position, typically at least 25m from the pilot's position
  * Leave it stationary for __20s__
* Go ahead and fly

### Preparing logs __with__ an RC connection to your FC hardware ###
If you have your FC hardware logging your RC channels, you can use a spare switch/channel to tell FCBE when it should report the position.

* Fire up your model and wait for the GPS to be locked
* Place the model on the pilot's position
  * Toggle your switch
* Place the model on your centreline reference position, typically at least 25m from the pilot's position
  * Toggle your switch
* Go ahead and fly

### Analysing your logs to extract box positions ###
* Run FCBE
* If you are using an RC switch channel for positioning, set RC Ch: to the correct channel number.  If not, leave it set to RC Ch: 0.
* Click _Open .bin File_ and choose the log file.  FCBE will parse the file:
~~~
Opening E:/APM/LOGS/00000086.BIN...
Using POS messages for position info.
Position message type: POS
Origin: (19.5s):  Lat: 51.6417779  Lng: -2.5262046  Alt: 3.58
~~~
* Click _Extract Box_.
* If you are using the stationary model method, FCBE will give you the locations of when it thinks the model was stationary:
~~~
Stationary between 31.5s and 71.0s
Stationary between 87.0s and 115.5s
Stationary between 122.0s and 299.5s
Stationary between 828.5s and 850.0s

Position at time 51.2s, 10.4m from origin:
51.6417982
-2.5260783

Position at time 101.2s, 26.6m from origin:
51.641643
-2.5258948

Position at time 210.7s, 21.8m from origin:
51.6417084
-2.5259194

Position at time 839.2s, 23.4m from origin:
51.641578
-2.5261281
~~~
  * If you are using an RC switch channel, FCBE will give you the positions for when you moved the switch:
~~~
Found 3 switch transitions of channel C6
Skippng time 7.8s as it occurs before the origin time (60.4)

Position at time 91.9s, 5.1m from origin:
51.4047592
-2.8190973

Position at time 123.8s, 37.4m from origin:
51.4045127
-2.8187682
~~~
* You can now copy (ctrl-C) the relevant Lattitudes and Longitudes into FlightCoach Plotter

### Analysing your logs for GPS accuracy and message rates ###
These are two extra functions which can be useful for debugging Flight Coach issues.

If your FC is logging GPS messages, FCBE can extract the minimum/average/maximum Horizontal and Vertical accuracy estimates and the satellite counts. Having loaded a log, click _GPS Accuracy_:
~~~
Accuracy  (min,avg,max):  H [0.2 0.3 0.6]m   V [0.4 0.5 1.1]m
Sat Count (min,avg,max):  [19 26.3 30]
~~~

To check the rates at which your FC is logging various messages, click on _Msg. Rates_:
~~~
XKF1:  43837 messages at 50.0Hz (20.0ms)
POS:  21708 messages at 25.0Hz (40.0ms)
ATT:  21943 messages at 25.0Hz (40.0ms)
GPS:  7917 messages at 9.1Hz (109.9ms)
GPA:  7917 messages at 9.1Hz (109.9ms)
MAG:  8778 messages at 10.0Hz (100.0ms)
RCIN:  21942 messages at 25.0Hz (40.0ms)
~~~

## How do I get set up to contribute? ##
### Setup for Dev ###
* Install the latest version of python (3.12 currently) from the Microsoft Store
* Clone the repository
* Start a command prompt (not powershell) in the cloned directory
* Create a virtual environment and activate it
~~~
python -m venv fcbe_env
fcbe_env\Scripts\activate.bat
pip install -r requirements.txt
~~~
* You can now run fcbe
~~~
python fcbe.py
~~~

### Create a distributable ZIP ###
~~~
build.bat
~~~
This will use pyinstaller to create a standalone windows executable and _internal directory, and then zip it into a single archive file.


### Who do I talk to? ###

arnie@spoonwibble.com