#!/usr/bin/env python3

#####################################################################
# Name: Transport.py
# Desc: This App receives messages from background.js extension 
# in firefox and processes based on message state. 
#
######################################################################
# Change Log:
# 06/26/2023   Luis Vergara      Use snapshots to find netstat matches
######################################################################
import sys
import json
import struct
import subprocess
import os
from time import sleep
import getopt
import datetime
import csv
import re

linuxConfigFile = "/opt/firefox/user_to_network/user_to_network_NativeApp/Transport.conf" ## This file has the line arguments for linux
        # linuxConfigFile should contain some of these options in line form i.e. -j json.json -c csv.csv -l /tmp/options.txt
        # -E : Extended information - Default is to only get the minimum amount of data from the extension. If you want all the request headers and responses use -E 'All'
        # -l : Options file
        # -j : JSON file
        # -c : CSV file
defaultJsonFile = "/opt/firefox/user_to_network/user_to_network_NativeApp/connections.json"
defaultCsvFile = "/opt/firefox/user_to_network/user_to_network_NativeApp/connections.csv"
snapsDir = "/opt/firefox/user_to_network/user_to_network_NativeApp/snaps"
outDir = "/opt/firefox/user_to_network/user_to_network_NativeApp/output"
logsDir = "/opt/firefox/user_to_network/user_to_network_NativeApp/logs"
allConnectionsDir = "/opt/firefox/user_to_network/user_to_network_NativeApp/allConnections"
timeStamp = ""

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

    # Logs events to log file
    def logEvent(state, dataIn, dataOut, exitMessage, logFile = "NONE"):
        logEntry = {}
        logEntry['state'] = state
        logEntry['timeStamp'] = timeStamp
        logEntry['dataIn'] = dataIn
        logEntry['dataOut'] = dataOut
        logEntry['exitMessage'] = exitMessage

        if logFile == "NONE":
            # Use log file from input
            #logFile = dataIn['logFile']
            return
        
        directory = logsDir
        os.makedirs(directory, exist_ok=True)

        # Check if the files already exist or not
        answ = os.path.exists(logFile)
        with open(logFile, 'a' if answ else 'w') as logF:
            json.dump(logEntry, logF)
            logF.write("\n")
        
    # add_connection - Takes a dictionary to write to csv or json
    def add_connection(connection, filename, filetype):
        # Check if the files already exist or not
        answ = os.path.exists(filename)
        if filetype == "json":
            with open(filename, 'a' if answ else 'w') as filetypeF:
                json.dump(connection, filetypeF, indent=4)
        elif filetype == "csv":
            with open(filename, 'a' if answ else 'w', newline='') as filetypeF:
                writer = csv.writer(filetypeF)
                writer.writerow(connection.values)

    # Retrieves options from config file or uses defaults 
    # Works on the provided array = []
    # Returns a string for error messages
    def getOptions(options):
        errorMsg = ""
        
            ## Use all defaults if the linux config file doesn't exist
        if not os.path.exists(linuxConfigFile):
                # All defaults
            options.append(('popupOption', 'News'))
            options.append(('popupOption', 'Streaming'))
            options.append(('popupOption', 'Social Media'))
            options.append(('popupOption', 'Rather not say'))
            options.append(('jsonFile', defaultJsonFile))
            options.append(('csvFile', defaultCsvFile))
            
                # Not exactly an error but a message for debugging
            return "File: {} not found. Using default: {}".format(linuxConfigFile, defaultJsonFile)
        else: 
                # We can use options from config file
            errorMsg += "LOG: Config file found!:"
                # Read in options from configl file
            with open(linuxConfigFile, 'r') as f:
                argv = f.readline().split()
            # Parse the options 
        opts, args = getopt.getopt(argv, 'E:l:j:c:')
        for o, a in opts:
                # If list of options for popup
            if o == "-l":
                if not os.path.exists(a.strip('"')):
                    errorMsg += "Error: Could not find options file; {}.Using default popup options: ".format(a)
                        # All defaults
                    options.append(('popupOption', 'News'))
                    options.append(('popupOption', 'Streaming'))
                    options.append(('popupOption', 'Social Media'))
                    options.append(('popupOption', 'Rather not say'))
                else:
                        # Read in the popup options and add them to the options array
                    with open(a.strip('"'), 'r') as f:
                        data = f.readlines()
                        for line in data:
                            options.append(('popupOption', line.strip('\n')))
                # If json file specified
            if o == "-j":
                options.append(('jsonFile', a))
                # If csv file specified
            if o == "-c":
                options.append(('csvFile', a))

            # If the json file or csv file are not specified then use the defaults for these
        if not any('jsonFile' in i for i in options):
            options.append(('jsonFile', defaultJsonFile))
            errorMsg += "LOG:Using default path for json file/: {}.".format(defaultJsonFile)
        if not any('csvFile' in i for i in options):
            options.append(('csvFile', defaultCsvFile))
            errorMsg += "LOG:Using default path for csv file.: {}.".format(defaultCsvFile)

            # list of options tuple (opt, value)
            # Sending the list of config options back.
        options.append(opts)

        return errorMsg

    #
    # session_start - Creates a file to store the connections for this tab and get options
    #
    def session_start(receivedMessage):
        responseMessage = {}
        responseMessage['state'] = receivedMessage['state']
        responseMessage['dataOut'] = []
        responseMessage['exitMessage'] = ""
        
            # Get options
        responseMessage['exitMessage'] += getOptions(responseMessage['dataOut']);    
        
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
        logFile = f"{logsDir}/Transport." + split[1] + ".log"
        responseMessage['dataOut'].append(("logFile", logFile))
        logEvent(receivedMessage['state'], [], responseMessage['dataOut'], responseMessage['exitMessage'], logFile)        
        sendMessage(encodeMessage(responseMessage))

    # logConnection - This writes out the request from browser
    def write_data_to_file(receivedMessage):
        responseMessage = {}
        responseMessage['state'] = receivedMessage['state']
        responseMessage['dataOut'] = []
        responseMessage['exitMessage'] = ""
        pid = receivedMessage['dataIn']['FirefoxPID']
        errorMsg = ""
        logFile = receivedMessage['logFile']
            # Create the directory path
        directory = allConnectionsDir
        os.makedirs(directory, exist_ok=True)

            # Generate the filename using the user and utc date YYYmmDD
        today = timeStamp.split(".")[0]
        filename = f"{directory}/connectionslog_{today}_pid_{pid}.txt"
        responseMessage['dataOut'].append(("logFile", filename))

            # Check if the file already exists
        file_exists = os.path.isfile(filename)

            # Open the file in append mode if it exists, otherwise in write mode
        mode = 'a' if file_exists else 'w'
        with open(filename, mode) as file:
                # Write the dataIn to the file
            json.dump(receivedMessage["dataIn"], file, indent=4)
            file.write('\n')
            errorMsg += "LOG:Added connection successfuly"

        responseMessage['exitMessage'] = errorMsg
        logEvent(receivedMessage['state'], receivedMessage['dataIn'], responseMessage['dataOut'], responseMessage['exitMessage'], logFile)
        sendMessage(encodeMessage(responseMessage))
    #
    # netstat_to_file - takes a snap shot of netstat. The after snapshot will also check what has changed and compare it to dest ip. 
    #
    def netstat_to_file(receivedMessage):
        responseMessage = {}
        responseMessage['state'] = receivedMessage['state']
        responseMessage['dataOut'] = []
        responseMessage['exitMessage'] = ""
        logFile = receivedMessage['logFile']
        
        state = receivedMessage['state']
        FirefoxPID = receivedMessage['dataIn']['FirefoxPID']
        requestId = receivedMessage['dataIn']['id']

            # The timestamp will help keep different logs on similar ids
        timestamp = timeStamp

        directory = snapsDir
        os.makedirs(directory, exist_ok=True)

        if state == "snapBefore":
            snapshot_file = f"{snapsDir}/snapBefore.{FirefoxPID}.{requestId}.{timestamp}.out"
        elif state == "snapAfter":
            snapshot_file = f"{snapsDir}/snapAfter.{FirefoxPID}.{requestId}.{timestamp}.out"
        
        responseMessage['dataOut'].append(("snapFile", snapshot_file))

        with open(snapshot_file, 'w') as outputFile:
            p = subprocess.Popen(["netstat", "-antp", "|", "grep", FirefoxPID], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Wait for the subprocess to finish and capture the output
            subprocess_output, subprocess_error = p.communicate()

            # Check if the subprocess completed successfully
            if p.returncode == 0:
                # Process or use the output as needed
                outputFile.write(subprocess_output.decode())  # Output from stdout

        logEvent(receivedMessage['state'], receivedMessage['dataIn'], responseMessage['dataOut'], responseMessage['exitMessage'], logFile)
        return sendMessage(encodeMessage(responseMessage))
    
    # A main connection consists of a user selection
    # We will want to take a diff of before and after snap to find new netstat rows
    # From those we will look for a match on destination ip, port, pid 
    def add_main_connection(receivedMessage):
        responseMessage = {}
        responseMessage['state'] = receivedMessage['state']
        responseMessage['dataOut'] = []
        responseMessage['exitMessage'] = ""
        timestamp = timeStamp
        FirefoxPID = receivedMessage['dataIn']['FirefoxPID']
        logFile = receivedMessage['logFile']
        requestId = receivedMessage['dataIn']['id']
        before_file = ""
        after_file = ""
        diff_file = f"{snapsDir}/snapDiff.{FirefoxPID}.{requestId}.{timestamp}.out"
        work_file = ""
        output_file = f"{outDir}/match.{FirefoxPID}.{requestId}.{timestamp}.out"
        epochTime = receivedMessage['dataIn']['sendHeadersTimeStamp']
        userSelection = receivedMessage['dataIn']['userSelection']
        originUrl = receivedMessage['dataIn']['originUrl']
        destinationIp = receivedMessage['dataIn']['destinationIp']
        destinationPort = receivedMessage['dataIn']['destinationPort']
        errorMsg = ""

        directory = outDir
        os.makedirs(directory, exist_ok=True)

            # Look for before and after snap file
        for filename in os.listdir(snapsDir):
            if re.match(f"snapBefore.{FirefoxPID}.{requestId}.*.out", filename):
                before_file = snapsDir+"/"+filename
            if re.match(f"snapAfter.{FirefoxPID}.{requestId}.*.out", filename):
                after_file = snapsDir+"/"+filename
        
            # Check the input files they are needed
        if before_file == "":
            errorMsg += f"ERROR: No before_file found in {snapsDir}:"
        if after_file == "":
            errorMsg += f"ERROR: No after_file found in {snapsDir}:"

            # Let's see if there is any difference between before and after
        with open(before_file, 'r') as before, open(after_file, 'r') as after:
            after_lines = after.readlines()
            before_lines = before.readlines()
            difference = set(after_lines) - set(before_lines)

                #Check for diff
            if difference:
                with open(diff_file, 'w') as diff:
                    diff.writelines(difference)
                    errorMsg += f"Log: Using diff_file to find netstat connection.:"
                    work_file = diff_file
            else:
                errorMsg += f"Log: Using after_file to find netstat connection.:"
                work_file = after_file
        
        found = False
            # If we can't find the connection in a diff we will also look in after_file
        if work_file == diff_file:
            loop = 2
        else:
            loop = 1
        
        i = 0
        while i < loop and not found:
            with open(work_file, 'r') as workF:
                    # We're looking for matches on destination ip, port, pid
                for line in workF:
                    netstatLineSplit = line.split()
                    if len(netstatLineSplit) == 7 :  # Picks out the blanks
                        netstatLineProtocol = netstatLineSplit[0]
                        netstatLineDestinationIP = netstatLineSplit[4].split(':')[0]
                        netstatLineDestinationPort = netstatLineSplit[4].split(':')[1]
                        netstatLinePID = netstatLineSplit[6].split('/')[0]
                        netstatLineSourceIP = netstatLineSplit[3].split(':')[0]
                        netstatLineSourcePort = netstatLineSplit[3].split(':')[1]
                        netstatLineState = netstatLineSplit[5]
                        if (netstatLineDestinationIP == destinationIp and
                            netstatLineDestinationPort == destinationPort and
                            netstatLinePID == FirefoxPID):
                                # Add this connection and log
                            errorMsg += (f"Log: Match found on " 
                                            f"{netstatLineProtocol} {netstatLineState} " 
                                            f"{netstatLineDestinationIP}:{netstatLineDestinationPort} " 
                                            f"{netstatLinePID}." 
                                            f" Output: {output_file}")
                            utc_time = datetime.datetime.utcfromtimestamp(epochTime/1000.0)
                            utcRead = utc_time.strftime('%Y-%m-%d %H:%M:%S')
                            connection = {}
                            connection['protocol'] = netstatLineProtocol
                            connection['sourceIp'] = netstatLineSourceIP
                            connection['sourcePort'] = netstatLineSourcePort
                            connection['destinationIp'] = netstatLineDestinationIP
                            connection['destinationPort'] = netstatLineDestinationPort
                            connection['status'] = netstatLineState
                            connection['pid'] = netstatLinePID
                            connection['epochTime'] = epochTime
                            connection['userSelection'] = userSelection
                            connection['originUrl'] = originUrl
                            connection['date'] = utcRead
                            responseMessage['dataOut'].append(connection)
                            add_connection(connection, output_file, "json") 
                            found = True
            i += 1
                # Swap out the file we look in
            if not found and work_file == diff_file:
                work_file = after_file
            # If we looked in diff and after file and still not found log that as an error
        if not found:
            errorMsg += f"ERROR: connection NOT found - {destinationIp}:{destinationPort} pid - {FirefoxPID} " \
                        f" in {work_file}.:"
        responseMessage['exitMessage'] = errorMsg
        logEvent(receivedMessage['state'], receivedMessage['dataIn'], responseMessage['dataOut'], responseMessage['exitMessage'], logFile)
        return sendMessage(encodeMessage(responseMessage))
        
    while True:
        receivedMessage = getMessage()
        timestampfloat = datetime.datetime.utcnow()
        timeStamp = timestampfloat.strftime('%Y%m%d.%H%M%S')

        #### Run the program based on received state
        if receivedMessage['state'] == "session_start":
            session_start(receivedMessage);
        elif receivedMessage['state'] == "logConnection":
            write_data_to_file(receivedMessage);
        elif receivedMessage['state'] == "snapBefore":
            netstat_to_file(receivedMessage);
        elif receivedMessage['state'] == "snapAfter":
            netstat_to_file(receivedMessage);
        elif receivedMessage['state'] == "addMainConnection":
            add_main_connection(receivedMessage);
        else :
            sendMessage(encodeMessage("Invalid State"))
except Exception as e:
# Python 2.x version (if sys.stdin.buffer is not defined)
# Read a message from stdin and decode it.
    sendMessage(encodeMessage(f"An Exception occured: {type(e).__name__}: {str(e)}"))
