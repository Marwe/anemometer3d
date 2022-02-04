#!/usr/bin/env python3

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Dieses Programm ist Freie Software: Sie können es unter den Bedingungen
# der GNU General Public License, wie von der Free Software Foundation,
# Version 3 der Lizenz oder (nach Ihrer Wahl) jeder neueren
# veröffentlichten Version, weiter verteilen und/oder modifizieren.

# Dieses Programm wird in der Hoffnung bereitgestellt, dass es nützlich sein wird, jedoch
# OHNE JEDE GEWÄHR,; sogar ohne die implizite
# Gewähr der MARKTFÄHIGKEIT oder EIGNUNG FÜR EINEN BESTIMMTEN ZWECK.
# Siehe die GNU General Public License für weitere Einzelheiten.

# Sie sollten eine Kopie der GNU General Public License zusammen mit diesem
# Programm erhalten haben. Wenn nicht, siehe <https://www.gnu.org/licenses/>.

# Copyright (c) 2019 Martin Weis


import sys
import socket
import time
from influxdb import InfluxDBClient
import json
import paho.mqtt.client as mqtt
import argparse
import logging
from anemometer3d import anemometer3d

parser = argparse.ArgumentParser(description='Read weather station data from serial2wifi TCP socket')
parser.add_argument('-l', '--loglevel', type=str, default='info', dest='loglevel',
                   help='loglevels (case-insensitive): CRITICAL ERROR WARNING INFO DEBUG NOTSET')

parser.add_argument('-s', '--serialhost', default='192.168.1.100', type=str, dest='serialhost',
                   help='serial2wifi server, DNS resolvable name or IP, e.g. 10.0.0.1')
parser.add_argument('-S', '--serialport', type=int, default=101, dest='serialport',
                   help='port of the serial2wifi socket')

parser.add_argument('-i', '--influxhost', default='localhost', type=str, dest='influxhost',
                   help='InfluxDB server, DNS resolvable name or IP, e.g. 127.0.0.1')
parser.add_argument('-I', '--influxport', type=int, default=28086, dest='influxport',
                   help='port of the InfluxDB')
parser.add_argument('-d', '--dbinflux', default='iotwind', type=str, dest='dbinflux',
                   help='InfluxDB database')

parser.add_argument('-m', '--mqtthost', default='localhost', type=str, dest='mqtthost',
                   help='MQTT server, DNS resolvable name or IP, e.g. 127.0.0.1')
parser.add_argument('-M', '--mqttport', type=int, default=21883, dest='mqttport',
                   help='port of the MQTT server')

parser.add_argument('-n', '--namemeas', default='iotwind', type=str, dest='namemeas',
                   help='measurement name')

parser.add_argument('-C', '--campaign', default='NoNameKampagne', type=str, dest='campaign',
                   help='Campaign name for the measurements')

parser.add_argument('-c', '--configfile', default='', type=str, dest='configfile',
                   help='configfile for the devices, with a json, example and default config: {"a3d02": {"devicetype": "Anemometer3D", "messagetype": 5, "deviceno": 2}, "a3d01": {"devicetype": "Anemometer3D", "messagetype": 5, "deviceno": 1}}')

parser.add_argument('-T', '--triesmax', type=int, default=10, dest='triesmax',
                   help='max. tries to connect to servers')

parser.add_argument('-p', '--pause', type=float, default=0.5, dest='pause',
                   help='pause between reads in seconds')


args = parser.parse_args()

# setup logging, does not work this way?!?
# yep: basicConfig only one time has an effect, see documentation
logging.basicConfig(format='%(asctime)s %(message)s',level=logging.ERROR)
loglevel=getattr(logging, args.loglevel.upper(), None)
if isinstance(loglevel, int):
    logging.getLogger().setLevel(loglevel)
else:
    logging.getLogger().setLevel(logging.INFO)

devicecfg=json.loads('{"a3d02": {"messagetype": 5, "deviceno": 2, "devicetype": "Anemometer3D"}, "a3d01": {"messagetype": 5, "deviceno": 1, "devicetype": "Anemometer3D"}}')
if args.configfile:
    with open(args.configfile) as json_data:
        devicecfg = json.load(json_data)
        json_data.close()

## Connect influx
useservice_influx=True
connected=False
conntriesleft=args.triesmax
while not connected:
    try:
        logging.info('connecting influx '+args.influxhost+':'+str(args.influxport))
        if 0 > conntriesleft:
            useservice_mqtt=False
            break
        ifxclient = InfluxDBClient(host=args.influxhost, port=args.influxport)
        ifxclient.switch_database(args.dbinflux)
        connected=True
    except KeyboardInterrupt:
        sys.exit()
    except:
        logging.error("cannot connect to InfluxDB")

# connect MQTT
useservice_mqtt=True
mqttc = mqtt.Client()
connected=False
conntriesleft=args.triesmax
while not connected:
    try:
        logging.info('connecting mqtt '+args.mqtthost+':'+str(args.mqttport)) 
        conntriesleft-=1
        if 0 > conntriesleft:
            useservice_mqtt=False
            break
        mqttc.connect(host=args.mqtthost,port=args.mqttport)
        connected=True        
    except KeyboardInterrupt:
        sys.exit()
    except:
        logging.error('cannot connect to MQTT '+args.mqtthost+':'+str(args.mqttport))
        time.sleep(0.5)

## connect wifi2serial
def sconnect(host,port):
    connected=False
    while not connected:
        try:
            logging.info('connecting to serial '+host+':'+str(port))
            s=socket.create_connection((host, port),5)
            s.setblocking(False)
            connected=True
        except KeyboardInterrupt:
            sys.exit()
        except:
            logging.error("failed to connect to serial TCP socket")
    return s

s=sconnect(args.serialhost,args.serialport)
a3d=anemometer3d()

while True:
    #time.sleep(0.2)
    for deviceid,dc in devicecfg.items():
        time.sleep(args.pause)
        #query=bytes('TR00005\r\n','ascii')
        query=a3d.querystr_tr(dc['deviceno'],dc['messagetype'])
        s.send(bytes(query,'ascii'))
        logging.debug(query.strip())
        #lineread=sockreadlines(s,'\r')
        #try 3 times to read a line
        maxtries=3
        answer=bytes('','ascii')
        while not answer:
            time.sleep(0.1)
            answer=s.makefile('rb').readline()
            maxtries-=1
            if 0 > maxtries:
                logging.error('empty response, continuing, failed query: '+a3d.cleanchars(query))
                continue
        logging.debug("answer (cleaned):"+a3d.cleanchars(answer.decode('ascii')))
        #t=time.ctime()
        #logging.debug(str(t))
        measdict=a3d.parseMessage(answer.decode('ascii'),messagetype=dc['messagetype'])
        logging.debug("measdict parsed:"+str(measdict))
        tags={'deviceid': deviceid, 'devicetype': dc['devicetype'],'campaign': args.campaign, 'messagetype': dc['messagetype']}
        # prepare for mqtt
        basetopic='iotwind/'+dc['devicetype']+'/'+deviceid+'/'
        topics={basetopic+'campaign': args.campaign}
        for mname,mval in measdict.items():
            topics[basetopic+mname]=mval
        if useservice_influx:
            # convert value types to force correct data types
            vtmeasdict=a3d.convertvaluetypes(measdict)
            ifxfielddict=a3d.getfloatvaluetypes(vtmeasdict)
            # add string type attributes to tags
            ifxtags=tags
            ifxtags.update(a3d.getstringvaluetypes(vtmeasdict))
            # send data to influx
            ifxdata=[{'measurement': args.namemeas, 'tags': ifxtags, 'fields': ifxfielddict}]
            logging.debug("ifxdata: "+str(ifxdata))
            try:

                ifxclient.write_points(ifxdata)
            except Exception as e:
                logging.error(e)
                logging.debug(ifxdata)
        if useservice_mqtt:
            # publish to MQTT
            for topic, payload in topics.items():
                mi=mqttc.publish(topic, payload)
                if not mi.is_published():
                    logging.error(topic+' was not published')

s.close()
ifxclient.close()
mqttc.disconnect()
