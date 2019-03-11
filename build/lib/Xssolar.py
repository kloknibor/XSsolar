#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 3 as published by
#    the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details. <http://www.gnu.org/licenses/>.
#
#    Written in 2012 by Jorg Janssen <http://www.zonnigdruten.nl/>


# norm: 255 255 1 1 182 219 0   128 230 0 63 0 136 19 231 0 61 0 129 0 8 57 4 32 87 102 7 0  0 0 159
# err:  255 255 1 1 182 219 112 145 250 0 0  0 0   0  0   0 0  0 0   0 9 57 4 32 87 102 7 60 0 0 242

# norm: FF FF 01 01 B6 DB 00 80 E6 00 3F 00 A3 13 E7 00 3D 00 81 00 08 39 04 20 57 66 07 00 00 00 9F
# err:  FF FF 01 01 B6 DB 70 91 FA 00 00 00 00 00 00 00 00 00 00 00 09 39 04 20 57 66 07 3C 00 00 F2
# norm: FF FF 01 01 B6 DB 00 80 A2 00 0A 00 88 13 E5 00 12 00 0B 00 F2 1C 00 1A 55 41 00 00 00 00 18 
#                               162   10    5000  229   18    11    7410     26 16725 
#                               VDc IDc*100 Fr*100VAc IAc*100 PAc WTot*100 Temp Runtime (min)


import http.client, urllib
import datetime
import sys
import struct

class Inverter:
    """Mastervolt Sunmaster Inverter"""
    def __init__(self, address, socket):
        self.address = address
        self._socket = socket
        self.values = {}
        self.dailyValues = {}

    def getRunningValues(self):
        rq = RequestB6(self)
        rq.send(self._socket)
        responses = Read(self._socket)
        for rs in responses:
            if (rs.type == 182):
                self.values['dcv']          = struct.unpack('>H',''.join([chr(rs.bytes[9]),chr(rs.bytes[8])]))[0]
                self.values['dci']          = struct.unpack('>H',''.join([chr(rs.bytes[11]),chr(rs.bytes[10])]))[0]/100.00
                self.values['freq']         = struct.unpack('>H',''.join([chr(rs.bytes[13]),chr(rs.bytes[12])]))[0]/100.00
                self.values['acv']          = struct.unpack('>H',''.join([chr(rs.bytes[15]),chr(rs.bytes[14])]))[0]
                self.values['aci']          = struct.unpack('>H',''.join([chr(rs.bytes[17]),chr(rs.bytes[16])]))[0]/100.00
                self.values['acp']          = struct.unpack('>H',''.join([chr(rs.bytes[19]),chr(rs.bytes[18])]))[0]
                self.values['totalpower']   = struct.unpack('>I',''.join(['\x00',chr(rs.bytes[22]),chr(rs.bytes[21]),chr(rs.bytes[20])]))[0]/100.00
                self.values['temp']         = struct.unpack('>b',chr(rs.bytes[23]))[0]
                self.values['totalruntime'] = struct.unpack('>I',''.join([chr(rs.bytes[27]),chr(rs.bytes[26]),chr(rs.bytes[25]),chr(rs.bytes[24])]))[0]
                self.values['errors']       = struct.unpack('>H',''.join([chr(rs.bytes[7]),chr(rs.bytes[6])]))[0]
                if (self.values['errors'] < 32768): # inverter error
 #                   Debug("Inverter error; " + ErrorDescr(self.values['errors']) +  "("+ str(self.values['errors']) + ")")

            else:
  #              Debug("Response type does not match request B6")

    def getDailyValues(self, day):
        rq = Request9A(self, day)
        rq.send(self._socket)
        responses = Read(self._socket)
        for rs in responses:
            if (rs.type == 154):
                dv = {}
                dv['W'] = struct.unpack('>H',''.join([chr(rs.bytes[7]),chr(rs.bytes[6])]))[0]/100.00
                dv['t'] = rs.bytes[5]*5
                self.dailyValues[day] = dv
            else:
     #           Debug("Response type does not match request 9A")

class Request:
    """abstract class for building requests"""
    def __init__(self):
        self._request = bytearray(b'\x00\x01\xFF\xFF\xB6\x00\x00\x00')
    def send(self, socket):
        #calculate and append checksum
        sum = 0
        for b in self._request:
            sum += b
        self._request.append(sum % 256)
        socket.sendall(self._request)

class RequestC1 (Request):	
    """C1 is for asking what inverters are present on the line, no inverter address needed"""
    def __init__(self):
        Request.__init__(self)
        self._request[0] = 0
        self._request[1] = 0
        self._request[4] = b'\xC1'

class InverterRequest (Request):
    """abstract class for building requests that are bound to an inverter"""
    def __init__(self, inverter):
        Request.__init__(self)
        self._request[0] = inverter.address[0]
        self._request[1] = inverter.address[1]

class RequestB6 (InverterRequest):
    """B6 is for asking the current running values"""
    def __init__(self, inverter):
        InverterRequest.__init__(self, inverter)
        self._request[4] = b'\xB6'

class Request9A (InverterRequest):
    """9A is for asking daily inverted energy. Day 0 = today, 1 = yesterday etc."""
    def __init__(self, inverter, day = 0):
        InverterRequest.__init__(self, inverter)
        self._request[4] = b'\x9A'
        self._request[5] = day

class Response():
    """General class for storing any inverter response"""
    def __init__(self, bytes):
        self.bytes = bytes
        self.type = self.bytes[4]
        self.address = self.bytes[2:4]

def Read(socket):
    """Call this after sending a request. It will return an array of response objects, if any."""        
    rss = [] 
    bytes = bytearray()
    while (1):
        try:
            chunk = socket.recv(31) # block untill timeout
            bytes.extend(chunk)
        except:
            break

    if (len(bytes) == 0):
        # No response, problably the inverter is not running because it is dark outside
        return rss # empty
    elif (len(bytes) < 9):
    #    Debug("Incomplete response")
    else:             
        while(len(bytes) > 0):
            if not(bytes[4] == 154 or bytes[4] == 193 or bytes[4] == 182): 
   #             Debug("Unknown response type")
                break
            else:
                response = bytearray()
                if (bytes[4] == 182): 
                    response.extend(bytes[:31])
                    del bytes[:31]
                elif (bytes[4] == 154 or bytes[4] == 193): 
                    response.extend(bytes[:9])
                    del bytes[:9]                    
                # calculate checksum
                sum = 0
                for b in response:
                    sum += b
                sum -= response[-1]
                if (sum % 256 != response[-1]):
  #                  Debug("Incorrect checksum")
                    break
                else:
                    rs = Response(response)
                    rss.append(rs)
    return rss    

def Web(website, system_id, address, page, params = {}):
    """Routine for connecting to website that is hosting the database"""
    data = ''
    params['systemid'] = system_id
    params = urllib.urlencode(params)
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    try:
        conn = httplib.HTTPConnection(website+':80')
        conn.request("POST", '/'+ page, params, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
    except:
 #       Debug("Unable to connect to website " + str(sys.exc_info()[0]))
        return 'error'
    else:
        #print data
        return data

def ErrorDescr (incoming):
    descr = ''
    errors = {1: 'Solar radiance too high',
              2: 'Solar radiance too low',
              4: 'Anti islanding',
              8: 'Grid voltage too high',
              16: 'Grid voltage too low',
              32: 'Grid frequency too high',
              64: 'Grid freqeuncy too low',
              112: 'No grid',
              128: 'Temperature too high',
              256: 'Insulation error',
              1024: 'Internal hardware failure',
              2048: 'Ready to start',
              4096: 'Reclosure',
              8192: 'Hardware shutdown',
              16384: 'Remote off', 
              32768: 'Normal',}
    for error in errors:
        if (incoming & error):
            descr += errors[error] + ', '
    if descr == '':
        descr = 'Unknown error'
    else:
        descr = descr[:-2]
    return descr

#def Debug(mess):
#    now = datetime.datetime.now()
#    now = now.strftime("%Y-%m-%d %H:%M:%S")
#    print now + ": " + mess + "\r\n"
