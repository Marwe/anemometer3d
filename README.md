
# Anemometer 3D measurements

This software can be used to get measurements from Anemometer 3D devices (https://www.thiesclima.com/de/Produkte/Wind-Ultraschall-Anemometer/) into IoT-typical environment.

The connection to the devices is currently via Serial2Wifi, such that the serial protocol messages can be used over TCP.
`read_wind.py` is a program to handle the communication, it can use MQTT and InfluxDB as services to send the data to.
To easily setup such services locally have a look at the docker-compose repository named [iotwind-dckr](https://github.com/Marwe/iotwind-dckr).
Since for this setup all ports are shifted by 20000, these are the defaults for the program, too (MQTT via localhost:21883 instead of default port 1883, Influxdb via localhost:28086 instead of default port 8086)


## Usage

~~~
usage: read_wind.py [-h] [-l LOGLEVEL] [-s SERIALHOST] [-S SERIALPORT]
                    [-i INFLUXHOST] [-I INFLUXPORT] [-d DBINFLUX]
                    [-m MQTTHOST] [-M MQTTPORT] [-n NAMEMEAS] [-C CAMPAIGN]
                    [-c CONFIGFILE] [-T TRIESMAX] [-p PAUSE]

Read weather station data from serial2wifi TCP socket

optional arguments:
  -h, --help            show this help message and exit
  -l LOGLEVEL, --loglevel LOGLEVEL
                        loglevels (case-insensitive): CRITICAL ERROR WARNING
                        INFO DEBUG NOTSET
  -s SERIALHOST, --serialhost SERIALHOST
                        serial2wifi server, DNS resolvable name or IP, e.g.
                        10.0.0.1
  -S SERIALPORT, --serialport SERIALPORT
                        port of the serial2wifi socket
  -i INFLUXHOST, --influxhost INFLUXHOST
                        InfluxDB server, DNS resolvable name or IP, e.g.
                        127.0.0.1
  -I INFLUXPORT, --influxport INFLUXPORT
                        port of the InfluxDB
  -d DBINFLUX, --dbinflux DBINFLUX
                        InfluxDB database
  -m MQTTHOST, --mqtthost MQTTHOST
                        MQTT server, DNS resolvable name or IP, e.g. 127.0.0.1
  -M MQTTPORT, --mqttport MQTTPORT
                        port of the MQTT server
  -n NAMEMEAS, --namemeas NAMEMEAS
                        measurement name
  -C CAMPAIGN, --campaign CAMPAIGN
                        Campaign name for the measurements
  -c CONFIGFILE, --configfile CONFIGFILE
                        configfile for the devices, with a json, example and
                        default config: {"a3d02": {"devicetype":
                        "Anemometer3D", "messagetype": 5, "deviceno": 2},
                        "a3d01": {"devicetype": "Anemometer3D", "messagetype":
                        5, "deviceno": 1}}
  -T TRIESMAX, --triesmax TRIESMAX
                        max. tries to connect to servers
  -p PAUSE, --pause PAUSE
                        pause between reads in seconds
~~~

# install and run

sudo apt install virtualenvwrapper 
mkvirtualenv -p $(which python3) iotwind
#pip3 install influxdb
#pip3 install paho-mqtt
#pip3 install pynmea2
pip3 -r requirements.txt

# example start script
./start_iotwind_cable.sh

