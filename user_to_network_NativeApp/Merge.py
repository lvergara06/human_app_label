from datetime import datetime, timedelta
import sys
import pytz

## Global Variables
connectionsFile = ""
flowFile = ""

## Max difference between connection epoch and pcmacct epoch
## TODO: Make the timeWindow an options in Transport.py
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
        # Skip the header fields
        if flowStartTime == "TIMESTAMP_START":
            continue
        # This is an adjustment to get mountain to utc timestamp from pmacct
        # If your pmacct timestamps are in utc then you will have to remove this.
        try:
        # Convert the local time string to a datetime object
            local_time = datetime.strptime(flowStartTime, "%Y-%m-%d %H:%M:%S.%f")

        # Get the local timezone
            local_tz = pytz.timezone('America/Denver')

        # Localize the datetime object to the local timezone
            localized_time = local_tz.localize(local_time, is_dst=None)

         # Convert the localized datetime to UTC
            utc_time = localized_time.astimezone(pytz.utc)

        # Calculate the flowEpoch timestamp
            flowEpoch = int((utc_time - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds() * 1000)
        except Exception as e:
            print(f"Error: {e}")
        
        #print("flow:" + flowSourceIp + " " + flowDestinationIp + " " + flowSourcePort + " " + flowDestinationPort + " "  + str(flowEpoch) )
        source1.seek(0)
        connections = source1.readlines()
        for connection in connections:
            splitConnection = connection.split(',')
            connectionDestinationIp = splitConnection[0]
            connectionDestinationPort = splitConnection[1]
            connectionUserSelection = splitConnection[4]
            connectionEpoch = splitConnection[3]
            #print("connection:" + connectionSourceIp + " " +  connectionDestinationIp + " " + connectionSourcePort + " " + connectionDestinationPort + " " + connectionEpoch)
            if flowDestinationIp == connectionDestinationIp and \
               flowDestinationPort == connectionDestinationPort and \
               abs(int(connectionEpoch) - flowEpoch) < timeWindow:
                print(flow + "," + connectionUserSelection)
           
