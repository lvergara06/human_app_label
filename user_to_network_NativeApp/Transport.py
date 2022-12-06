#!/usr/bin/env python

# This App receives messages from HttpSendInfo extension in firefox
# This App must be installed prior to extension
#
# For Windows add this key registry: HKEY_LOCAL_MACHINE\SOFTWARE\Mozilla\NativeMessagingHosts\Transport
# For Windows the key should have a single (Default) value with a path to this app's json. ie. C:\Users\userid\path\to\Transport.json
# For Linux make sure that Trasnport.py exists at /usr/{lib,lib64,share}/mozilla/native-messaging-hosts/Transport.json
#
# example json for windows
#{
#  "name": "Transport",
#  "description": "Send transport layer information from firefox to database",
#  "path": "C:\\Users\\userid\\path\\to\\Transport_win.bat",
#  "type": "stdio",
#  "allowed_extensions": [ "ping_pong@example.org" ]
#}
#
# example json for linux
#{
#  "name": "Transport",
#  "description": "Send transport layer information from firefox to database",
#  "path": "/path/to/native-messaging/app/Trasnport.py",
#  "type": "stdio",
#  "allowed_extensions": [ "ping_pong@example.org" ]
#}

import sys
import json
import struct
import subprocess
import os
import os.path
from os import path
from time import sleep
import requests
import getopt

try:
    # Python 3.x version
    # Read a message from stdin and decode it.
    def getMessage():
        rawLength = sys.stdin.buffer.read(4)
        if len(rawLength) == 0:
            sys.exit(0)
        messageLength = struct.unpack('@I', rawLength)[0]
        message = sys.stdin.buffer.read(messageLength).decode('utf-8')
        return json.loads(message)

    # Encode a message for transmission,
    # given its content.
    def encodeMessage(messageContent):
        encodedContent = json.dumps(messageContent).encode('utf-8')
        encodedLength = struct.pack('@I', len(encodedContent))
        return {'length': encodedLength, 'content': encodedContent}

    # Send an encoded message to stdout
    def sendMessage(encodedMessage):
        sys.stdout.buffer.write(encodedMessage['length'])
        sys.stdout.buffer.write(encodedMessage['content'])
        sys.stdout.buffer.flush()
        
    def getOptions (options):
        errorMsg = ""
        if len(sys.argv) < 2:
            # All defaults
            options.append(('popupOption' , 'News'))
            options.append(('popupOption' , 'Streaming'))
            options.append(('popupOption' , 'Social Media'))
            options.append(('popupOption' , 'Rather not say'))
            options.append(('jsonFile' , './connections.json'))
            options.append(('csvFile' , './connections.csv'))
            return
            
        # Parse the arguments
        # -s : Send with - Default is to have the native app send the connections to the api via http post. Use -s if you want the browser to send it
        # -E : Extended information - Default is to only get the minimum amount of data from the extension. If you want all the request headers and response use -E 'All'
        #-l for options
        argv = sys.argv[1:]
        opts, args = getopt.getopt(argv, 's:E:o:j:c:-j:-c:')
        for o , a in opts:
            if o == "-o":
                if path.exists(a) != True:
                    errorMsg += "Error: Could not find options file: " + a + ". "
                    # All defaults
                    options.append(('popupOption' , 'News'))
                    options.append(('popupOption' , 'Streaming'))
                    options.append(('popupOption' , 'Social Media'))
                    options.append(('popupOption' , 'Rather not say'))
                else:
                    with open(a, 'r') as f:
                        data = f.readlines()
                        for line in data:        
                            options.append(('popupOption' , line.strip('\n')))
            if o == "-j":
                options.append(('jsonFile', a))
            if o == "-c":
                options.append(('csvFile', a))
                    
        if (any('jsonFile' in i for i in options)):
            pass
        else:
            options.append(('jsonFile' , './connections.json'))
            options.append(('csvFile' , './connections.csv'))
        # list of options tuple (opt, value)
        options.append(opts)
        
        return errorMsg
            
    #
    # session_start - Creates a file to store the connections for this tab and get options
    #
    def session_start(receivedMessage):
        responseMessage = {}
        responseMessage['state'] = receivedMessage['state']
        responseMessage['dataIn'] = receivedMessage['dataIn']
        responseMessage['dataOut'] = []
        responseMessage['exitMessage'] = "Success"
        
        # Get options
        responseMessage['exitMessage'] = getOptions(responseMessage['dataOut']);    
        
        #Get firefox main pid
        p = subprocess.Popen(["tasklist"], stdout=subprocess.PIPE)
        out = p.stdout.read()
        decodedTasklist = out.decode('ascii')
        #print(decodedTasklist)
        out_tasklist = decodedTasklist.split('\r\n')
        mainPID = []
        for line in out_tasklist:
            if line.find("firefox.exe") >= 0:
                mainPID=line
                break
        split = ' '.join(mainPID.split()).split(' ')        
        # Add the firefox main pid to the response
        responseMessage['dataOut'].append(("FirefoxPID", split[1]))
        sendMessage(encodeMessage(responseMessage))
        
    #
    # addConnection - Opens the connection files and adds the connections to it
    # 

    def addConnection(receivedMessage):
        original_stdout = sys.stdout # Save a reference to the original standard output
        responseMessage = {}
        responseMessage['state'] = receivedMessage['state']
        responseMessage['dataIn'] = receivedMessage['dataIn']
        responseMessage['dataOut'] = []
        responseMessage['exitMessage'] = "Success"
        jsonFile = ""
        csvFile = ""
        extendData = False
        
        # Get options
        responseMessage['exitMessage'] = getOptions(responseMessage['dataOut']); 
        for o in responseMessage['dataOut']:
            if o[0] == "jsonFile":
                jsonFile = o[1]
            if o[0] == "csvFile":
                csvFile = o[1]
            if o[0] == "-E":
                extendData=True

        #Run netstat 
        arguments = "-onf" 
        p = subprocess.Popen(["netstat", arguments], stdout=subprocess.PIPE)
        out = p.stdout.read()
        decodedNetstat = out.decode('ascii')
        out_netstat = decodedNetstat.split('\r\n')  
        
        answ = os.path.exists(jsonFile)
        answ2 = os.path.exists(csvFile)
        connectionEntry = {}
        connectionEntry['connections'] = []
        with open(jsonFile, 'a' if answ else 'w') as jsonF, \
             open(csvFile , 'a' if answ2 else 'w') as csvF:
            sys.stdout = jsonF
            # Look for the connections per destinationIp and firefox pid
            for line in out_netstat:
                netstatLineSplit = ' '.join(line.split()).split(' ')
                if len(netstatLineSplit) == 5:  # Picks out the blanks
                    netstatLineDestinationIP = netstatLineSplit[2].split(':')[0] 
                    netstatLineDestinationPort = netstatLineSplit[2].split(':')[1]
                    netstatLinePID = netstatLineSplit[4]
                    if (len(receivedMessage['dataIn'][0]) > 0 and 
                        netstatLineDestinationIP == receivedMessage['dataIn'][0]['destinationIp'] and 
                        netstatLineDestinationPort == receivedMessage['dataIn'][0]['destinationPort'] and 
                        netstatLinePID == responseMessage['dataIn'][0]['FirefoxPID']):
                        
                        connection = {}
                        connection['protocol'] = netstatLineSplit[0]
                        connection['sourceIp'] = netstatLineSplit[1].split(':')[0]
                        connection['sourcePort'] = netstatLineSplit[1].split(':')[1]
                        connection['destinationIp'] = netstatLineSplit[2].split(':')[0]
                        connection['destinationPort'] = netstatLineSplit[2].split(':')[1]
                        connection['status'] = netstatLineSplit[3]
                        connection['pid'] = netstatLineSplit[4]
                        connection['userSelection'] = receivedMessage['dataIn'][0]['userSelection']
                        connection['epochTime'] = receivedMessage['dataIn'][0]['epochTime']
                        if extendData:
                            connection['extendedData'] = receivedMessage['dataIn'][0]['extendedData']
                        else:
                            connection['extendedData'] = []
                        connectionEntry['connections'].append(connection)
                        json_object = json.dumps(connection, indent=4)
                        # to json
                        print(json_object)
                        sys.stdout = csvF
                        # to csv
                        print(connection['protocol'] + "," +
                              connection['sourceIp'] + "," +
                              connection['sourcePort'] + "," +
                              connection['destinationIp'] + "," +
                              connection['destinationPort'] + "," +
                              connection['status'] + "," +
                              connection['pid'] + "," +
                              connection['userSelection'] + "," +
                              str(connection['epochTime']))
                        sys.stdout = jsonF
            sys.stdout = original_stdout # Reset the standard output to its original value
        responseMessage['dataOut'] = connectionEntry
        responseMessage['exitMessage'] = 'Success'         
        sendMessage(encodeMessage(responseMessage))

    # deleteTab - Delets the file for this tab
    # Inputs :
    # TabId
    def deleteTab(receivedMessage):
        original_stdout = sys.stdout # Save a reference to the original standard output
        tabHandle = str(receivedMessage['dataIn']['tabId']);
        tabFile = str(tabHandle) + "connections.txt";
        responseMessage = {}
        responseMessage['state'] = receivedMessage['state']
        responseMessage['dataIn'] = receivedMessage['dataIn']
        responseMessage['dataOut'] = []
        responseMessage['exitMessage'] = "Success"
        
        #Check if file exists
        if os.path.exists("connections/" + tabFile) :
            os.remove("connections/" + tabFile);
        
        responseMessage['exitMessage'] = "Success"              
        sendMessage(encodeMessage(responseMessage))
            
    while True:
        receivedMessage = getMessage()

        #### Run the program based on received state
        if receivedMessage['state'] == "session_start":
            #### Call create tab
            session_start(receivedMessage);
        elif receivedMessage['state'] == "add_connection":
            addConnection(receivedMessage);
        elif receivedMessage['state'] == "delete_tab":
            deleteTab(receivedMessage);
        
        
except AttributeError:
    # Python 2.x version (if sys.stdin.buffer is not defined)
    # Read a message from stdin and decode it.
    def getMessage():
        rawLength = sys.stdin.read(4)
        if len(rawLength) == 0:
            sys.exit(0)
        messageLength = struct.unpack('@I', rawLength)[0]
        message = sys.stdin.read(messageLength)
        return json.loads(message)

    # Encode a message for transmission,
    # given its content.
    def encodeMessage(messageContent):
        encodedContent = json.dumps(messageContent)
        encodedLength = struct.pack('@I', len(encodedContent))
        return {'length': encodedLength, 'content': encodedContent}

    # Send an encoded message to stdout
    def sendMessage(encodedMessage):
        sys.stdout.write(encodedMessage['length'])
        sys.stdout.write(encodedMessage['content'])
        sys.stdout.flush()

    while True:
        receivedMessage = getMessage()
        if receivedMessage == "ping":
            sendMessage(encodeMessage("pong2"))
