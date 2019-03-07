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


import socket
import struct
import httplib, urllib
import time, datetime
from sm_comm import *

# YOUR SETTINGS HERE -----------------------------------------

TCP_IP = '192.168.1.5'  # ip address of rs485-to-tcp converter
TCP_PORT = 23           # tcp port of this converter

WEBSITE = 'xxx.xxx.xx' # website that is hosting the database
SYSTEM_ID = 'xxx'        # pv system id for website

# END OF SETTINGS --------------------------------------------

# BEGIN PROGRAM ----------------------------------------------

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	
s.settimeout(1)

try:
    s.connect((TCP_IP, TCP_PORT)) # connect to tcp-converter
except:
    Debug("Unable to connect to tcp converter -  " + str(sys.exc_info()[0]))
    # quit
else:
    # "flush":
    while (1):
        try:
            chunk = s.recv(1) # block untill timeout
        except:
            break

    # send the first command, to discover all connected inverters
    rq = RequestC1()
    rq.send(s)
    responses = Read(s)

    # get inverters from response
    inverters = []
    for r in responses:
        if (r.type == 193):
            i = Inverter(r.address,s)
            inverters.append(i)
        else:
            Debug("Response type does not match request C1")

    # go get values from inverters
    data = ''
    for i in inverters:
        # get latest day in database
        data = Web(WEBSITE, SYSTEM_ID, i.address, 'lastday.php')
        if (data != 'error'): # only if website is online:            
            if (data != str(datetime.date.today())): # if latest day in db is not today:
                h = 30 # get history from inverter
            else:
                h = 1 # or only get todays total
            for d in range(0,h):            
                i.getDailyValues(d)  # get it
                Web(WEBSITE, SYSTEM_ID, i.address, 'adddailyentry.php',{'day': d, 'w': i.dailyValues[d]['W'], 'runtime': i.dailyValues[d]['t'] }) # and write to web        

            i.getRunningValues() # get running values for this moment        
            now = str(datetime.datetime.now())
            params = {'timestamp': ':'.join([now.partition(':')[0],str(((datetime.datetime.now().minute)/5)*5)])}
            for v in i.values:
                params[v] = i.values[v]
            Web(WEBSITE, SYSTEM_ID, i.address, 'addsolarlogentry.php',params) # write to web
        
    s.close()

# END PROGRAM ---------------------------------------------