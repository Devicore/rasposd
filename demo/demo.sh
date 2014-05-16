#!/bin/sh

echo "Binding gpsd to GPS device"
sudo gpsd /dev/ttyAMA0 -F /var/run/gpsd.sock

echo "Starting video visualisation"
raspivid -p -n -t 0 -w 1280 -h 720 -fps 30 -b 500000 &

echo "Starting data recorder. Data is saved in /opt/QtOSD/bin"
sudo python recorder/recorder.py &

echo "Starting data visualisation overlay"
demo/QtOSD &

echo "All services started, press ENTER to end"

echo "Killing QtOSD"
killall QtOSD

echo "Killing recorder"
sudo killall python

echo "Killing video"
killall raspivid

echo "All services killed, program ended"
