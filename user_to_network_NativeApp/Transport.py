#!/usr/bin/env python3

# This App receives messages from background.js extension in firefox
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
import getopt

linuxConfigFile = "/opt/firefox/user_to_network/user_to_network_NativeApp/Transport.conf" ## This file has the line arguments for linux

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
        
    def getOptions (responseMessage):
        errorMsg = ""
        original_stdout = sys.stdout
        if path.exists(linuxConfigFile) != True:
            # All defaults
            responseMessage['dataOut'].append(('popupOption' , 'News'))
            responseMessage['dataOut'].append(('popupOption' , 'Streaming'))
            responseMessage['dataOut'].append(('popupOption' , 'Social Media'))
            responseMessage['dataOut'].append(('popupOption' , 'Rather not say'))
            responseMessage['dataOut'].append(('jsonFile' , '/opt/firefox/user_to_network/user_to_network_NativeApp/connections.json'))
            responseMessage['dataOut'].append(('csvFile' , '/opt/firefox/user_to_network/user_to_network_NativeApp/connections.csv'))
            return "File : " + linuxConfigFile + " not found. Using default /opt/firefox/user_to_network/user_to_netwok_NativeApp."
        else:
            errorMsg += " Configfile found!"
            with open(linuxConfigFile, 'r') as f:
                argv = f.readline().split()


        # Parse the arguments
        # -s : Send with - Default is to have the native app send the connections to the api via http post. Use -s if you want the browser to send it
        # -E : Extended information - Default is to only get the minimum amount of data from the extension. If you want all the request headers and response use -E 'All'
        #-l for options
        opts, args = getopt.getopt(argv, 's:E:l:j:c:')
        for o , a in opts:
            if o == "-l":
                if path.exists(a.strip('"')) != True:
                    errorMsg += "Error: Could not find options file: " + a + ". "
                    # All defaults
                    responseMessage['dataOut'].append(('popupOption' , 'News'))
                    responseMessage['dataOut'].append(('popupOption' , 'Streaming'))
                    responseMessage['dataOut'].append(('popupOption' , 'Social Media'))
                    responseMessage['dataOut'].append(('popupOption' , 'Rather not say'))
                else:
                    with open(a.strip('"'), 'r') as f:
                        data = f.readlines()
                        for line in data:        
                            responseMessage['dataOut'].append(('popupOption' , line.strip('\n')))
            if o == "-j":
                responseMessage['dataOut'].append(('jsonFile', a))
            if o == "-c":
                responseMessage['dataOut'].append(('csvFile', a))
                    
        if (any('jsonFile' in i for i in responseMessage['dataOut'])):
            pass
        else:
            responseMessage['dataOut'].append(('jsonFile' , '/opt/firefox/user_to_network/user_to_network_NativeApp/connections.json'))
            responseMessage['dataOut'].append(('csvFile' , '/opt/firefox/user_to_network/user_to_network_NativeApp/connections.csv'))
            errorMsg += "Using default path json and csf files: /opt/firefox/user_to_network/user_to_network_NativeApp/."
        
        # list of options tuple (opt, value)
        responseMessage['dataOut'].append(opts)
        
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
        responseMessage['exitMessage'] += getOptions(responseMessage);    
        
        #Get firefox main pid
        p = subprocess.Popen(["ps", "-eaf"], stdout=subprocess.PIPE)
        out = p.stdout.read()
        decodedTasklist = out.decode('ascii')
        out_tasklist = decodedTasklist.split('\n')
        mainPID = []
        for line in out_tasklist:
            # skip web-ext processes
            if line.find("web-ext") >= 0:
                continue
            # /opt/firefox/firefox is the Firefox Dev version
            if line.find("/opt/firefox/firefox") >= 0:
                mainPID=line
                break
        split = ' '.join(mainPID.split()).split(' ')        
        # Add the firefox main pid to the response
        responseMessage['dataOut'].append(("FirefoxPID", split[1]))

        # Return a log file
        responseMessage['dataOut'].append(("LogFile", "/opt/firefox/user_to_network/user_to_network_NativeApp/logs/Transport." + split[1] + ".log"))
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
        ConnectionTry = receivedMessage['dataIn'][0]['ConnectionTry']
        ConnectionTry += 1
        jsonFile = ""
        csvFile = ""
        LogFile = "/opt/firefox/user_to_network/user_to_network_NativeApp/logs/Transport." + responseMessage['dataIn'][0]['FirefoxPID'] + ".log"
        extendData = False        
        found = False
        
        # Get options
        responseMessage['exitMessage'] = getOptions(responseMessage); 
        for o in responseMessage['dataOut']:
            if o[0] == "jsonFile":
                jsonFile = o[1]
            if o[0] == "csvFile":
                csvFile = o[1]
            if o[0] == "-E":
                extendData=True

        # Run this two times max because if the connection has not had time to be established I want to retry after a few secs
        for i in range(2):
            if found:
                break
            #Run netstat 
            # These areguments are based on ubuntu netstat
            arguments = "-antp"
            p = subprocess.Popen(["netstat", arguments], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            out = p.stdout.read()
            decodedNetstat = out.decode('ascii')
            out_netstat = decodedNetstat.split('\n')

            # Check if the json files already exist or not
            answ = os.path.exists(jsonFile)
            answ2 = os.path.exists(csvFile)
            answ3 = os.path.exists(LogFile)
            connectionEntry = {}
            connectionEntry['connections'] = []
            with open(jsonFile, 'a' if answ else 'w') as jsonF, \
                open(csvFile , 'a' if answ2 else 'w') as csvF, \
                open(LogFile, 'a' if answ3 else 'w') as logF:
                # Look for the connections per destinationIp and firefox pid
                sys.stdout = logF
                print("Looking for ip address : [" + receivedMessage['dataIn'][0]['destinationIp'] + "] \
                    on port : [" + receivedMessage['dataIn'][0]['destinationPort'] + "]")

                for line in out_netstat:
                    netstatLineSplit = ' '.join(line.split()).split(' ')
                    if len(netstatLineSplit) == 7 :  # Picks out the blanks
                        netstatLineDestinationIP = netstatLineSplit[4].split(':')[0]
                        netstatLineDestinationPort = netstatLineSplit[4].split(':')[1]
                        netstatLinePID = netstatLineSplit[6].split('/')[0]
                        netstatLineSourceIP = netstatLineSplit[3].split(':')[0]
                        netstatLineSourcePort = netstatLineSplit[3].split(':')[1]
                        netstatLineState = netstatLineSplit[5]
                        
                        sys.stdout = logF
                        print("checking in netstat : " + " ".join(str(x) for x in netstatLineSplit))
                        
                        if (len(receivedMessage['dataIn'][0]) > 0 and 
                            netstatLineDestinationIP == receivedMessage['dataIn'][0]['destinationIp'] and 
                            netstatLineDestinationPort == receivedMessage['dataIn'][0]['destinationPort'] and 
                            netstatLinePID == responseMessage['dataIn'][0]['FirefoxPID']):
                            
                            print("Match found")
                            found = True
                            sys.stdout = jsonF
                            connection = {}
                            connection['protocol'] = netstatLineSplit[0]
                            connection['sourceIp'] = netstatLineSourceIP
                            connection['sourcePort'] = netstatLineSourcePort
                            connection['destinationIp'] = netstatLineDestinationIP
                            connection['destinationPort'] = netstatLineDestinationPort
                            connection['status'] = netstatLineState
                            connection['pid'] = netstatLinePID
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
                if found == False:
                    sleep(30)
        
        if found == False:
            responseMessage['exitMessage'] = 'connection to netstat connection not found'     
            responseMessage['dataOut'].append(("ConnectionTry", ConnectionTry))    
        else :
            responseMessage['dataOut'] = connectionEntry
            responseMessage['exitMessage'] = "Success"
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
