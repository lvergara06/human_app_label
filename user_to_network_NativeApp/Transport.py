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
        
    # Send http post request to database api
    def sendToApi(bodyToSend):
        # with open('./connections/' + tabFile + 'sendInfo', 'r+') as f:
            # sys.stdout = f
        #Url to api
        url = "https://user_to_network_API2022.azurewebsites.net/api/Connection/Create"
        headers = {'Content-Type': 'application/json'}

        #Making http post request
        json_object = json.dumps(bodyToSend, indent=4)
        response = requests.post(url, headers=headers, data=json_object, verify=False)
        
    # createTab - Creates a file to store the connections for this tab
    # Inputs :
    # TabId
    # TabIndex
    def createTab(receivedMessage):
        original_stdout = sys.stdout # Save a reference to the original standard output
        with open('log', 'w') as f:
            sys.stdout = f # Change the standard output to the file we created.
            print(receivedMessage)
        tabHandle = str(receivedMessage['dataIn']['tabId']);
        tabFile = str(tabHandle) + "connections.txt";
        responseMessage = {}
        responseMessage['state'] = receivedMessage['state']
        responseMessage['dataIn'] = receivedMessage['dataIn']
        responseMessage['dataOut'] = []
        responseMessage['exitMessage'] = "Success"
        
        #Check if directory exists
        if path.exists("connections") != True or path.isdir("connections") != True :
            try:
                os.makedirs("connections")
            except:
                responseMessage['exitMessage'] = "Could not create connection directory"              
                sendMessage(encodeMessage(responseMessage))
                return
                
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
                #print(line)
                break
        split = ' '.join(mainPID.split()).split(' ')
        connectionEntry = {}
        connectionEntry['id'] = tabHandle
        connectionEntry['status'] = "created"
        connectionEntry['pid'] = split[1]
        connectionEntry['connections'] = []
        with open('./connections/' + tabFile, 'w') as f:
            sys.stdout = f # Change the standard output to the file we created.
            # Clear file
            f.truncate(0)
            f.seek(0)
            # Serializing json
            json_object = json.dumps(connectionEntry, indent=4)
            print(json_object)
            sys.stdout = original_stdout
        responseMessage['dataOut'] = connectionEntry
        sendMessage(encodeMessage(responseMessage))
        
    # addConnection - Opens the tabs' file and adds the connections to it
    # Inputs :
    # TabId
    # TabIndex
    # destinationIp
    # userSelection
    # epochTime
    def addConnection(receivedMessage):
        original_stdout = sys.stdout # Save a reference to the original standard output
        tabHandle = str(receivedMessage['dataIn'][0]['tabId']);
        tabFile = str(tabHandle) + "connections.txt";
        responseMessage = {}
        responseMessage['state'] = receivedMessage['state']
        responseMessage['dataIn'] = receivedMessage['dataIn']
        responseMessage['dataOut'] = []
        responseMessage['exitMessage'] = "Success"
        
        #Run netstat 
        #sys.stdout = f # Change the standard output to the file we created.
        arguments = "-onf" 
        p = subprocess.Popen(["netstat", arguments], stdout=subprocess.PIPE)
        out = p.stdout.read()
        decodedNetstat = out.decode('ascii')
        out_netstat = decodedNetstat.split('\r\n')  


        #There is a chance that the file hasn't opened. Give it a chance.
        if path.exists('./connections/' + tabFile) != True:
            #Sleep 50 miliseconds
            sleep(0.05)
        #Check again
        if path.exists('./connections/' + tabFile) != True:
            #Sleep 500 miliseconds
            sleep(0.5)
        if path.exists('./connections/' + tabFile) != True:
            responseMessage['exitMessage'] = "Could not find connection file: " + tabFile
            sendMessage(encodeMessage(responseMessage))
                        
        # connectionEntry = {}
        # connectionEntry['id'] = tabHandle
        # connectionEntry['status'] = ""
        # connectionEntry['pid'] = ""
        # connectionEntry['connections'] = []
        
        with open('./connections/' + tabFile, 'r+') as f:
            sys.stdout = f
            data = f.read()
            connectionEntry = json.loads(data)
            # Erase contents of the file to allow new connections
            f.truncate(0)
            f.seek(0)
        
            #Remove previous connections
            connectionEntry['connections'].clear()
            # Look for the connections per destinationIp and firefox pid
            for line in out_netstat:
                split = ' '.join(line.split()).split(' ')
                if len(split) == 5:
                    if receivedMessage['dataIn'] and split[2].split(':')[0] == receivedMessage['dataIn'][0]['destinationIp'] and split[4] == connectionEntry['pid']:
                        connection = {}
                        connection['protocol'] = split[0]
                        connection['sourceIp'] = split[1].split(':')[0]
                        connection['sourcePort'] = split[1].split(':')[1]
                        connection['destinationIp'] = split[2].split(':')[0]
                        connection['destinationPort'] = split[2].split(':')[1]
                        connection['status'] = split[3]
                        connection['pid'] = split[4]
                        connection['userSelection'] = receivedMessage['dataIn'][0]['userSelection']
                        connection['epochTime'] = receivedMessage['dataIn'][0]['epochTime']
                        if receivedMessage['optionsSendWith'] == 'Python':
                            sendToApi(connection)
                        connectionEntry['connections'].append(connection)
            connectionEntry['status'] = "updated"
            json_object = json.dumps(connectionEntry, indent=4)
            print(json_object)
            sys.stdout = original_stdout # Reset the standard output to its original value
            responseMessage['dataOut'] = connectionEntry;
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
        if receivedMessage['state'] == "create_tab":
            #### Call create tab
            createTab(receivedMessage);
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
