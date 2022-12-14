from datetime import datetime, timedelta
import sys

## Global Variables
connectionsFile = ""
flowFile = ""

## Max difference between connection epoch and pcmacct epoch
timeWindow = 1000

## Get args
def getOptions ():
    if len(sys.argv) != 3:
    # All defaults
        print("Usage : Merge.py connections.csv flows.csv")
        exit(1)
    global connectionsFile 
    connectionsFile = sys.argv[1]
    global flowFile
    flowFile = sys.argv[2]
    print("connectionsFile is : " + connectionsFile)
    print("flowFile is : " + flowFile)
    return
	
## Start

getOptions() 

## Open files
## Save original stdout to print messages
original_stdout = sys.stdout
with open(connectionsFile, 'r') as source1,\
     open(flowFile, 'r') as source2:
    flows = source2.readlines()
    for flow in flows:
        splitFlow = flow.split(',')
        flowSourceIp = splitFlow[0]
        flowDestinationIp = splitFlow[1]
        flowSourcePort = splitFlow[2]
        flowDestinationPort = splitFlow[3]
        flowStartTime = splitFlow[5]
        # This is an adjustment to get mountain to utc timestamp from pmacct
        # If your pmacct timestamps are in utc then you will have to remove this.
        try:
            local_time = datetime.strptime(flowStartTime, "%Y-%m-%d %H:%M:%S.%f")
        except: 
            continue
        
        utc_time = local_time + timedelta(hours=7)
        flowEpoch = int((utc_time - datetime(1970, 1, 1)).total_seconds()*1000)
        #print("flow:" + flowSourceIp + " " + flowDestinationIp + " " + flowSourcePort + " " + flowDestinationPort + " "  + str(flowEpoch) )
        source1.seek(0)
        connections = source1.readlines()
        for connection in connections:
            splitConnection = connection.split(',')
            connectionSourceIp = splitConnection[1]
            connectionSourcePort = splitConnection[2]
            connectionDestinationIp = splitConnection[3]
            connectionDestinationPort = splitConnection[4]
            connectionUserSelection = splitConnection[7]
            connectionEpoch = splitConnection[8]
            #print("connection:" + connectionSourceIp + " " +  connectionDestinationIp + " " + connectionSourcePort + " " + connectionDestinationPort + " " + connectionEpoch)
            if flowSourceIp == connectionSourceIp and \
               flowDestinationIp == connectionDestinationIp and \
               flowSourcePort == connectionSourcePort and \
               flowDestinationPort == connectionDestinationPort and \
               abs(int(connectionEpoch) - flowEpoch) < timeWindow:
                print(flow + "," + connectionUserSelection)
           
