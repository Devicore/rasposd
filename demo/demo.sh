#!/bin/sh

echo "Binding gpsd to GPS device"
sudo gpsd /dev/ttyAMA0 -F /var/run/gpsd.sock

cd ../recorder

echo "Starting video visualisation"
../demo/raspivid -p -n -t 0 -w 1280 -h 720 -fps 30 -b 500000 -rot 180 &

echo "Starting data recorder. Data is saved in QtOSD/bin"
sudo python recorder_fusion.py &

echo "Starting data visualisation overlay"
../demo/QtOSD/bin/QtOSD -platform eglfs &

echo "All services started, press ENTER to end"
read val

echo "Killing QtOSD"
killall QtOSD

echo "Killing recorder"
sudo killall python

echo "Killing video"
killall raspivid

echo "All services killed, program ended"
