#!/usr/bin/env python3

# TODO: convert values to float, if applicable, do it on knowledge about expected type, e.g. according to header name (e.g. WGA -> float, measurement_unit -> str, unknown: str?)
# TODO: create lib/class for processing thies messages

import pynmea2
import string
import logging

# nice logger per class by Vystavil Ondrej Medek
# see for details: https://xmedeko.blogspot.com/2017/10/python-logger-by-class.html

def addlogger(cls: type):
    aname = '_{}__log'.format(cls.__name__)
    setattr(cls, aname, logging.getLogger(cls.__module__ + '.' + cls.__name__))
    return cls

@addlogger
class anemometer3d():
    """Anemometer3D class to handle Thies (https://www.thiesclima.com/) "Ultraschall Anemometer 3D" wind measurement devices via (serial) messages.
    Serial messaging has to be implemented elsewhere, 
    this class just helps to create querys and parse the resulting messages.
    The serial telegram query is based on <devicenumber>TR<messagetype>
    @devicenumber: ID of the device to query
    @messagetype: message type to query and parse, see telegram type definitions in documentation
    """
    def __init__(self, devicenumber=1, messagetype=5, logger=None):
        """
        @devicenumber: default devicenumber to be used
        @messagetype: default messagetype
        @logger: logger object to be used (optional)
        
        """
        self.devicenumber=devicenumber
        self.messagetype=messagetype
        self.logger=logger
        # Info about messagetypes
        self.msginfo={
                #11.1 Telegramm 00001
                #Windgeschwindigkeit und Richtung horizontal, Geschwindigkeit und Richtung vertikal mit
                #Vorzeichen
                #Befehl: TR00001
                #Befehl: TT00001
                #Telegrammaufbau:
                #(STX)WGA;WRA;WGE;WRE;THIES-Status;CS(CR)(ETX)
            1: {"eol": "\x03", 
                "hdr": 'WGA;WRA;WGE;WRE;THIES-Status;CS'},
                #11.2Telegramm 00002
                #Windgeschwindigkeit und Richtung horizontal, Geschwindigkeit und Richtung vertikal mit
                #Vorzeichen sowie akustische virtuelle Temperatur
                #Befehl: TR00002
                #Befehl: TT00002
                #Telegrammaufbau:
                #(STX)WGA;WRA;WGE;WRE;VT;THIES-Status;CS(CR)(ETX)
            2: {"eol": "\x03", 
                "hdr": 'WGA;WRA;WGE;WRE;VT;THIES-Status;CS'},
                #11.3Telegramm 00003
                #Windgeschwindigkeit und Richtung horizontal, Geschwindigkeit vertikal mit Vorzeichen
                #sowie akustische virtuelle Temperatur
                #Befehl: TR00003
                #Befehl: TT00003
                #Telegrammaufbau:
                #(STX)WGA;WRA;WGE; VT;THIES-Status;CS(CR)(ETX)
            3: {"eol": "\x03", 
                "hdr": 'WGA;WRA;WGE;VT;THIES-Status;CS'},
                # NMEA handling
                # from \r\n use \n and trim \r later
            4: {"eol": "\n", 
                "hdr": 'nmea'},
                # 11.5 Telegramm 00005
                # XYZ- Vektoren mit akustischer virtueller Temperatur
                # Befehl: TR00005 Befehl: TT00005
                # Telegrammaufbau:
                # (STX)VX;VY;VZ;VT;THIES-Status;CS(CR)(ETX)
            5: {"eol": "\r", 
                "hdr": 'VX;VY;VZ;VT;THIES-Status;CS'},
                #11.7Telegramm 00007
                #XYZ- Vektoren mit akustischer virtueller Temperatur und deren Standardabweichungen
                #Befehl: TROOOO?
                #Befehl: TTOOOO?
                #flwb@lJ
                #Zur Berechnung der Standardabweichung muss der Parameter OE auf 00001
                #gesetzt sein.
                #Telegrammaufbau:
                #VX;VY;VZ;VT;StdvX;StdvY;StdvZ;StdvT;THIES-Status;CS(CR)           
            7: {"eol": "\r", 
                "hdr": 'VX;VY;VZ;VT;StdvX;StdvY;StdvZ;StdvT;THIES-Status;CS'},
                #11.8Telegramm 00008
                #XYZ· Vektoren mit akustischer virtueller Temperatur und deren Kovarianzen
                #Befehl: TR00008
                #Befehl: TT00008
                #@ih@tj
                #Zur Berechnung der Kovarianzen muss der Parameter CO auf 00001 gesetzt
                #sein.
                #Telegrammaufbau:
                #VX;VY;VZ;VT;CovaXY; CovaXZ; CovaXT; CovaYZ; CovaYT; CovaZT;THIES-Status;CS(CR)
            8: {"eol": "\r", 
                "hdr": 'VX;VY;VZ;VT;CovaXY;CovaXZ;CovaXT;CovaYZ;CovaYT;CovaZT;THIES-Status;CS'
                },
                #11.9Telegramm 00009
                #XYZ- Vektoren und deren Turbulenzintensitäten sowie akustische virtuelle Temperatur
                # Befehl: TR00009 Befehl: TT00009
                # IIMWi§tj
                # Zur Berechnung oder Turbulenzintensitäten muss der Parameter CO auf 00001
                # gesetzt sein.
                # Telegrammaufbau:
                # VX;VY;VZ;VT;TiX;TiY;TiZ;THIES-Status;CS(CR) 
            9: {"eol": "\r", 
                "hdr": 'VX;VY;VZ;VT;TiX;TiY;TiZ;THIES-Status;CS'},
                #11.10 Telegramm 00012
                #Wissenschaftliches Diagnosetelegramm
                #Befehl: TR00012
                #Befehl: TT00012
                #Telegrammaufbau:
                #WGA;WRA;WGE;WRE;VT;VXYZ;VX;VY;VZ;VTU;VTV;VTW;CUTB;CUBT;CVTB;CVBT;CWTB;CWBT;
                # header in documentation is incomplete, missing:
                    # Interner Zähler CNTINT
                    #Semikolon (3Bh)
                    #Zeitintervall , in dem die Werte in den Hauptmittelspeicher geschrieben werden TWH
                    #Semikolon (3Bh)
                    #Anzahl der Werte im Hauptmittelspeicher CNTWH
                    #Semikolon (3Bh)
                    #THIES-Status THIES-Status
                    #Semikolon (3Bh)
                    #Telegrammstatus, Erweiterte Statusinformation (hexadezimal) Extended-Status
                    #Semikolon (3Bh)
                    #Interner Tickcount in ms vom Prozessor CNTPROC
                    #(Carriage return, line feed)
                # CRLF 
            12: {"eol": "\n", 
                "hdr": 'WGA;WRA;WGE;WRE;VT;VXYZ;VX;VY;VZ;VTU;VTV;VTW;CUTB;CUBT;CVTB;CVBT;CWTB;CWBT;CNTINT;TWH;CNTWH;THIES-Status;Extended-Status;CNTPROC'}        
        }  
        # typedict for values, the value type can be converted according to the variable name
        # default parse is string, other options are float or 'hex' (string)
        self.typedict={
                    "CovaXT": float,
                    "CovaXY": float,
                    "CovaXZ": float,
                    "CovaYT": float,
                    "CovaYZ": float,
                    "CovaZT": float,
                    "CNTINT": float,
                    "CNTWH": float,
                    "CNTPROC":float,
                    "CS": 'hex',
                    "CUBT": float,
                    "CUTB": float,
                    "CVBT": float,
                    "CVTB": float,
                    "CWBT": float,
                    "CWTB": float,
                    "Extended-Status": 'hex',
                    "StdvT": float,
                    "StdvX": float,
                    "StdvY": float,
                    "StdvZ": float,
                    "THIES-Status": 'hex',
                    "TiX": float,
                    "TiY": float,
                    "TiZ": float,
                    "TWH": float,
                    "VT": float,
                    "VTU": float,
                    "VTV": float,
                    "VTW": float,
                    "VX": float,
                    "VXYZ": float,
                    "VY": float,
                    "VZ": float,
                    "WGA": float,
                    "WGE": float,
                    "WRA": float,
                    "WRE": float,
                    # nmea parsed
                    'reference': str, 
                    'wind_speed_units': str, 
                    'wind_speed': float,
                    'status': str, 
                    'wind_angle': float
            }

    def cleanchars(self, instr):
        """ removes all non-printable chars and strips whitespaces both sides
        @instr: string to be cleaned, bytes are dedoded to ascii
        @return: cleaned string
        """
        if bytes==type(instr):
            self.__log.info("cleanchars got a bytes object")
            uncleanstr=instr.decode('ascii')
        elif type(instr) == str:
            uncleanstr=instr
        else:
            self.__log.warn("cleanchars got an invalid object")
            return str()
        return ''.join(filter(lambda x: x in string.printable, str(instr))).strip()


    def eol(self, messagetype=None):
        """ returns the eol (end of line/message) character
        @messagetype: message type
        @return: cleaned string
        """
        if messagetype is None:
            messagetype=self.messagetype
        try:
            msgt=self.msginfo[messagetype]["eol"]
        except KeyError as e:
            return None
        return msgt
    
    
    def convertvaluetypes(self, measdict, typedict=None):
        """ try setting the correct value type for measurements according to value name
            this function uses prior knowledge about all possible Thies values
            @measdict: input dictionary
            @typedict: 
        """
        
        if typedict is None:
            typedict=self.typedict
        resdict={}
        for k, v in measdict.items():
            try:
                if float == typedict[k]:
                    val=float(v)
                    resdict[k]=val
                elif 'hex' == typedict[k]:
                    val=int(v, 16)
                    resdict[k]=val
                elif str == typedict[k]:
                    resdict[k]=v
                else:
                    resdict[k]=v
            except ValueError as e:
                # since it cannot be converted, drop it
                self.__log.info("convertvaluetypes: dropping due to ValueError while converting: "+str(e))
            except KeyError as e:
                self.__log.error("convertvaluetypes: KeyError, "+k+" undefined type (bug: missing in typedict): "+str(e))
                
        return resdict
    
    
    def getfloatvaluetypes(self, measdict):
        resdict={}
        for k, v in measdict.items():
            if  type(v) is float:
                resdict[k]=v
        self.__log.debug(str(resdict))
        return resdict


    def getstringvaluetypes(self, measdict):
        """
        select only string type values
        @measdict: input dict
        @return: dict reduced to string values
        """
        resdict={}
        for k, v in measdict.items():
            if type(v) is str:
                resdict[k]=v
        self.__log.debug(str(resdict))
        return resdict
    
    
    def parseMessage(self, msgraw, messagetype=None):
        """ parse messages, Anemometer3D implemented
        msgraw -- the message as received from device
        messagetype -- the message type corresponds to the telegram definitions, see handbook
        """
        if messagetype is None:
            messagetype=self.messagetype
        # strip non-printable chars (\x02 STX \x03 ETX) and trim msg
        cleaneddata=self.cleanchars(msgraw)
        data=cleaneddata.split(';')
        #logging.debug('type '+str(messagetype)+' data2parse: '+str(data))
        # check for valid messagetype
        if messagetype not in self.msginfo.keys():
            raise ValueError('[parseMessage] not implemented: unknown messagetype '+str(messagetype))
            return None
        minfo=self.msginfo[messagetype]
        if 'nmea' != minfo["hdr"]:
            return dict(zip(minfo["hdr"].split(';'),data))
            #return this.convertvaluetypes(datadict)
            # TODO convert value types
        else:
            # 'nmea' == minfo["hdr"]:
            # use NMEA parser
            #use cleaneddata
            try:
                meas=pynmea2.parse(str(cleaneddata))
            except Exception as e:
                print(e)
                return dict()
            if meas.is_valid:
                resdict={}
                for midx in meas.name_to_idx:
                    resdict[midx]=meas.data[meas.name_to_idx[midx]]
                return resdict
            else:
                return dict()

    def querystr_tr(self, devicenumber=None, messagetype=None):
        """
        create a query string for serial communication
        @devicenumber: device number
        @msgtype: message type
        """
        if devicenumber is None:
            devicenumber=self.devicenumber
        if messagetype is None:
            messagetype=self.messagetype
        query='{:02}'.format(devicenumber)+'TR'+'{:05}'.format(messagetype)+'\r'
        return query

