#!/bin/bash


cmpg=""

read -t 10 -p "campaign name (10 sec. timeout): " cname
if [ -n "$cname" ] ; then
    cmpg="-C \"$cname\""
fi

# gnome-terminal -e "~/anemometer3d/read_wind.py -l DEBUG -c ~/anemometer3d/richtungen.json"
~/anemometer3d/read_wind.py $cmpg -s 10.0.0.1 -l DEBUG -c ~/anemometer3d/richtungen.json

