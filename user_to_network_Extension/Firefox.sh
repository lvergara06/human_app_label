#!/bin/bash


###########################################
## Name : Firefox
## Desc : This script runs Firefox Extension
##        and merges the output with 
##        pmacctd output. 
## ########################################
## Luis Vergara 09/10/23 Rework and lazy logs
## Luis Vergara 09/15/23 Reinstating start 
##                       pmacctd and nfacctd
##
###########################################
CurrentPID=$$
timestamp=$(date -u +"%Y%m%d%H%M%S")
OutLog=/opt/firefox/user_to_network/logs/Firefox.$timestamp.log
###########################################
# HELPER FUNCTIONS
###########################################

# Function to extract the string after the specified argument without quotes
# Arguments:
# $1 - The argument to search for (e.g., "-do")
# $2 - The file path to search within
function extract_string_after_argument {
    local arg_to_find="$1"
    local file_path="$2"

    # Check if the specified argument exists in the file
    if grep -q -E "\s$arg_to_find\s" "$file_path"; then
        # Extract the string after the argument
        local value=$(grep -oP "(?<=\s$arg_to_find\s).*" "$file_path" | awk '{print $1}')

        # Remove double quotes from the string if present
        value=$(sed 's/"//g' <<< "$value")

        echo "$value"
    fi
}


echo "###########################################" >> $OutLog
echo "## JOBSTEP: 000 Started                    " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog
echo "Checking if firefox extension is running" >> $OutLog
echo >> $OutLog
# Check if this already running. Don't run multiple of these
echo "pgrep -f 'Firefox.sh' | wc -l" >> $OutLog
Count=`pgrep -f "Firefox.sh" | wc -l`
echo "Firefox.sh count is $Count" >> $OutLog
if [[ $Count -eq 1 ]]
then
    #Do nothing
    echo "Firefox.sh already running"  >> $OutLog
    exit -1
fi

echo "" >> $OutLog
echo "" >> $OutLog
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 000 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

###########################################
## JOBSTEP : 005
## Desc    : Get timestamp 
###########################################
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 005 Started                    " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog
echo "Getting start timestamp" >> $OutLog
echo >> $OutLog
### Executing
# Get current UTC timestamp
startTime=$(date -u +"%Y%m%d %H:%M:%S")

# Output the UTC timestamp
echo "start time: $startTime" >> $OutLog

### End
echo "" >> $OutLog
echo "" >> $OutLog
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 005 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

###########################################
## JOBSTEP : 010
## Desc    : Start pmacctd and nfacctd
##           are running. 
###########################################
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 010 Started                    " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog
echo "Starting pmacctd and nfacctd for Firefox:PID:$CurrentPID" >> $OutLog
echo "" >> $OutLog

## Run pmacctd
echo "Starting pmacctd" >> $OutLog
# You can specify the pmacctd file to use in Transport.conf or else
# this job can run pmacctd using some configuration files built into the repository
# The configuration of the switch could be different. Open the .conf file below to
# Change the configuration.
transportConf="/opt/firefox/user_to_network/user_to_network_NativeApp/Transport.conf"
pmacctdDefault="/opt/firefox/user_to_network/pmacct/pmacctd.conf"
pmacctdLogs="/opt/firefox/user_to_network/pmacct/logs"
pmacctdConf=""
pmacctdOutFile=""
# Check if the folder exists
if [ ! -d "/opt/firefox/user_to_network/pmacct/logs" ]
then
    # Create the folder if it doesn't exist
    mkdir -p "/opt/firefox/user_to_network/pmacct/logs"
fi

echo "Looking in $transportConf for pmacctd configuration file path" >> $OutLog

# Check if the Transport.conf file exists
if [ ! -f "$transportConf" ]
then
    echo "Transport.conf does not exist" >> $OutLog
    echo "Using default pmacctd location : $pmacctdDefault"
    pmacctdConf="$pmacctdDefault"
else
    # Check if the "-d" argument exists in the file
    pmacctdConf=$(extract_string_after_argument "-d" "$transportConf")
    # Check if the extracted string is a valid file
    if [ -n "$pmacctdConf" ] && [ -f "$pmacctdConf" ]
    then
        echo "Using pmacctd file: $pmacctdConf" >> $OutLog 
    else
        echo "pmacctd file [$pmacctdConf] not found or invalid" >> $OutLog
        pmacctdConf="$pmacctdDefault"
        echo "Using default pmacctd file: $pmacctdConf" >> $OutLog
    fi

    # Check if the "-do" argument exists in the file
    pmacctdOutFile=$(extract_string_after_argument "-do" "$transportConf")
    # Check if the extracted string is a valid file
    if [ -n "$pmacctdOutFile" ] && [ -f "$pmacctdOutFile" ]
    then
        : # Do nothing
        #echo "$pmacctdOutFile is valid"
        #echo "Using pmacctd out file: $pmacctdOutFile"
    else
        #echo "pmacctd out file not found or invalid"
        pmacctdOutFile="$pmacctdLogs/pmacctd.out"
        #echo "Using default pmacctd out file: $pmacctdOutFile"
    fi
fi

echo "start time : $timestamp" >> "$pmacctdOutFile" >> $OutLog
nohup sudo pmacctd -f "$pmacctdConf" >> "$pmacctdOutFile" 2>&1 &
pmacctdPid=$!  # Capture the process ID of the last background command
# Store the PID in a file for future reference if needed
#echo "$pmacctdPid" > "/tmp/pmacctd_pid.txt"
echo "pmacctd process started with PID: $pmacctdPid" >> $OutLog
echo "" >> $OutLog
echo "" >> $OutLog

################# Run nfacctd 
##
##
echo "Starting nfacctd" >> $OutLog
# You can specify the nfacctd file to use in Transport.conf or else
# this job can run nfacctd using some configuration files built into the repository.
# Open the .conf file below to change the configuration.
transportConf="/opt/firefox/user_to_network/user_to_network_NativeApp/Transport.conf"
nfacctdDefault="/opt/firefox/user_to_network/pmacct/nfacctd.conf"
nfacctdLogs="/opt/firefox/user_to_network/pmacct/logs"
nfacctdTmp="/opt/firefox/user_to_network/pmacct/tmp"
nfacctdFlows="/opt/firefox/user_to_network/pmacct/flows"
nfacctdConf=""
nfacctdOutFile=""
flowsOutput=""

# Check if the folder exists
if [ ! -d "/opt/firefox/user_to_network/pmacct/tmp" ] 
then
    # Create the folder if it doesn't exist
    mkdir -p "/opt/firefox/user_to_network/pmacct/tmp"
fi

# Check if the folder exists
if [ ! -d "/opt/firefox/user_to_network/pmacct/flows" ] 
then
    # Create the folder if it doesn't exist
    mkdir -p "/opt/firefox/user_to_network/pmacct/flows"
fi

echo "Looking in $transportConf for nfacctd file path" >> $OutLog

# Check if the Transport.conf file exists
if [ ! -f "$transportConf" ]
then
    echo "Transport.conf does not exist" >> $OutLog
    echo "Using default nfacctd location : $nfacctdDefault" >> $OutLog
    nfacctdConf="$nfacctdDefault"
else
    # Check if the "-n" argument exists in the file
    nfacctdConf=$(extract_string_after_argument "-n" "$transportConf")
    # Check if the extracted string is a valid file
    if [ -n "$nfacctdConf" ] && [ -f "$nfacctdConf" ]
    then
        #echo "$nfacctdConf is valid"
        echo "Using nfacctd file: [$nfacctdConf]" >> $OutLog
    else
        #echo "nfacctd file not found or invalid"
        nfacctdConf="$nfacctdDefault"
        echo "Using default nfacctd file: [$nfacctdConf]" >> $OutLog
    fi

    # Check if the "-no" argument exists in the file
    nfacctdOutFile=$(extract_string_after_argument "-no" "$transportConf")
    # Check if the extracted string is a valid file
    if [ -n "$nfacctdOutFile" ] && [ -f "$nfacctdOutFile" ]
    then
        : # Do nothing
        #echo "$nfacctdOutFile is valid"
        #echo "Using nfacctd out file: $nfacctdOutFile"
    else
        #echo "nfacctd out file not found or invalid"
        nfacctdOutFile="$nfacctdLogs/nfacctd.out"
        echo "Using default nfacctd out file: $nfacctdOutFile" >> $OutLog
    fi
fi

# Command to run nfacctd -f $nfacctdFile
# Make a copy of nfacctdFile to nfacctdTmp/nfacctd.<pmacctdPid>.conf
cp "$nfacctdConf" "$nfacctdTmp/nfacctd.$pmacctdPid.conf"

# Find the line with "print_output_file: flows.csv" and modify it
sed -E -i "s#(print_output_file:[[:space:]]*).*#\1$nfacctdFlows/flows.$pmacctdPid.csv#" "$nfacctdTmp/nfacctd.$pmacctdPid.conf"
flowsOutput=$nfacctdFlows/flows.$pmacctdPid.csv

# Command to run nfacctd -f $nfacctdFile
echo "nfacctd -f $nfacctdTmp/nfacctd.$pmacctdPid.conf >> $nfacctdOutFile 2>&1 &" >> $OutLog 

# Start nfacctd with nohup and redirect the output to the specified file
echo "start time : $timestamp" >> "$nfacctdOutFile"
nohup nfacctd -f "$nfacctdTmp/nfacctd.$pmacctdPid.conf" >> "$nfacctdOutFile" 2>&1 &
nfacctdPid=$!  # Capture the process ID of the last background command
# Store the PID in a file for future reference if needed
#echo "$nfacctdPid" > "/tmp/nfacctd.txt"
echo "nfacctd process started with PID: $nfacctdPid" >> $OutLog
echo >> $OutLog
echo >> $OutLog


### End

echo "" >> $OutLog
echo "" >> $OutLog
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 010 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

###########################################
## JOBSTEP : 020
## Desc    : Extract the print_output_file
##           from nfacctd.conf
###########################################
# echo "###########################################" >> $OutLog
# echo "## JOBSTEP: 020 Started                    " >> $OutLog
# echo "###########################################" >> $OutLog
# echo >> $OutLog
# echo >> $OutLog

# Look for the path to nfacctd.conf file in Transport.conf
# If it is missing at this point we are left we somewhat
# of an orphaned output but we don't let this stop us now.

# transportConf=/opt/firefox/user_to_network/user_to_network_NativeApp/Transport.conf
# nfacctdConf=""
# flowsOutput=""
# flowsBefore=""

# # Check if the Transport.conf file exists
# if [ ! -f "$transportConf" ]
# then
#     echo "Transport.conf does not exist" >> $OutLog
# else
#     # Check if -n exists in the Transport.conf file.
#     nfacctdConf=$(extract_string_after_argument "-n" "$transportConf")
#     if [ -n "$nfacctdConf" ] && [ -f "$nfacctdConf" ]
#     then
#         echo "Using nfacctd file: $nfacctdConf" >> $OutLog
#         # 
#         # In nfacctdConf we should find print_output_file value
#         flowsOutput=`grep -w print_output_file "$nfacctdConf"   | awk -F: '{print $2}' | awk  '{$1=$1};1'`
#         if [ -n "$flowsOutput" ] && [ -f "$flowsOutput" ]
#         then
#             echo "Using flowsOutput file: $flowsOutput" >> $OutLog
#             ##
#             # This is where we want to make a copy of the flowsOutput file as is
#             # We will need this for later
#             # 
#             flowsBefore=/opt/firefox/user_to_network/pmacct/tmp/flows.before.$CurrentPID.$timestamp.csv
#             cp $flowsOutput $flowsBefore >> $OutLog
#         else
#             echo "Could not open flows output: $flowsOutput" >> $OutLog
#         fi
#     else
#         echo "nfacctd file not found or invalid" >> $OutLog
#         echo "flows.csv could not be found" >> $OutLog
#     fi
# fi

### End

# echo "###########################################" >> $OutLog
# echo "## JOBSTEP: 020 Finished                   " >> $OutLog
# echo "###########################################" >> $OutLog
# echo >> $OutLog
# echo >> $OutLog


###########################################
## JOBSTEP : 030
## Desc    : Run the Firefox Extension
###########################################
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 030 Started                    " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog
connections=""
connectionsWork=""
connectionsDefault=/opt/firefox/user_to_network/user_to_network_NativeApp/output/connections.csv
## Executing
# Check if this already running. Don't run multiple of these
echo "pgrep -f 'node /usr/local/bin/web-ext' >/dev/null" >> $OutLog
pgrep -f "node /usr/local/bin/web-ext" 2>/dev/null
if [[ $? -eq 0 ]]
then
    #Do nothing
    echo "Firefox Extension already running web-ext"  >> $OutLog
else
    # Set the path to the extension
    extension_path="/opt/firefox/user_to_network/user_to_network_Extension"

    # Set the path to the Firefox Developer Edition executable
    firefox_dev_path="/opt/firefox/firefox"

    # Set the environment variable to start Firefox in light theme
    #export MOZ_ENABLE_LIGHT_THEME=1
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

    # Run the web-ext tool with the Firefox Developer Edition
    echo web-ext run --firefox-binary $firefox_dev_path -s $extension_path >> $OutLog 
    web-ext run --firefox-binary "$firefox_dev_path" -s "$extension_path"
    echo >> $OutLog
    echo >> $OutLog
    #
    ## Let's go ahead and take the connections file and put it in 
    # a more stable place
    # Check if the "-c" argument exists in the file
    connections=$(extract_string_after_argument "-c" "$file_path")
    # Check if the extracted string is a valid file
    if [ -n "$connections" ] && [ -f "$connections" ]
    then
        #echo "$connections is valid" >> $OutLog
        echo "Using connections file: $connections" >> $OutLog
    else
        #echo "connections.csv from .conf file not found or invalid" >> $OutLog
        connections=$connectionsDefault 
        echo "Using default connections file: $connections" >> $OutLog
    fi

    connectionsWork=/opt/firefox/user_to_network/user_to_network_NativeApp/work/connections.$CurrentPID.$timestamp.csv
    cp $connections $connectionsWork >> $OutLog
    #
    ## Make certain that the copy worked before delete
    if [ -n "$connectionsWork" ] && [ -f "$connectionsWork" ]
    then    
        echo $connections copied to $connectionsWork >> $OutLog
        rm $connections
        echo "$connections removed." >> $OutLog
    fi
fi

### End

echo >> $OutLog
echo >> $OutLog
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 030 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

###########################################
## JOBSTEP : 040
## Desc    : Get diff of flows.out
###########################################
# echo "###########################################" >> $OutLog
# echo "## JOBSTEP: 040 Started                    " >> $OutLog
# echo "###########################################" >> $OutLog
# echo >> $OutLog
# echo >> $OutLog

# ## Executing

# # Start a delay before auto running merge.py 
 echo sleep 5 min >> $OutLog
 sleep 300
 echo "Killing pmacctd PID: $pmacctdPid" >> $OutLog
 sudo /opt/firefox/user_to_network/user_to_network_Extension/SudoKillPmacctd.sh $pmacctdPid
 echo "Killing nfacctd PID: $nfacctdPid" >> $OutLog
 kill -9 $nfacctdPid
# flowsAfter=""
# flowsDiff=""
# # If flowsBefore is valid and flowsOutput is valid we can do a diff
# if [ -n "$flowsOutput" ] && [ -f "$flowsOutput" ] && [ -n "$flowsBefore" ] && [ -f "$flowsBefore" ]
# then
#     ##
#     # This is where we want to make a copy of the flowsOutput file as is
#     # We will need this for later
#     # 
#     flowsAfter=/opt/firefox/user_to_network/pmacct/tmp/flows.after.$CurrentPID.$timestamp.csv
#     cp $flowsOutput $flowsAfter >> $OutLog

#     ##
#     # If we made it here then we should be able to do a diff
#     flowsDiff=/opt/firefox/user_to_network/pmacct/tmp/flows.diff.$CurrentPID.$timestamp.csv
#     diff $flowsBefore $flowsAfter | grep ">" | awk -F\> '{print $2}' | awk '{$1=$1};1' > $flowsDiff
# fi    

# ### End

# echo "###########################################" >> $OutLog
# echo "## JOBSTEP: 040 Finished                   " >> $OutLog
# echo "###########################################" >> $OutLog
# echo >> $OutLog
# echo >> $OutLog

###########################################
## JOBSTEP : 050
## Desc    : Get timestamp 
###########################################
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 050 Started                    " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

### Executing
# Get current UTC timestamp
echo "Getting end time stamp" >> $OutLog
endtimestamp=$(date -u +"%Y%m%d %H:%M:%S")

# Output the UTC timestamp
echo "end time: $endtimestamp" >> $OutLog

### End

echo >> $OutLog
echo >> $OutLog
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 050 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

###########################################
## JOBSTEP : 060
## Desc    : Merge the outputs
###########################################
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 060 Started                    " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

mergedOut=/opt/firefox/user_to_network/user_to_network_NativeApp/mergedOutput/merged_connections_$CurrentPID.$timestamp.csv
##
# The end game! If we have a diff then we can do a merge
# Let's also check the connections file is good
if [ -n "$flowsOutput" ] && [ -f "$flowsOutput" ] && [ -n "$connectionsWork" ] && [ -f "$connectionsWork" ]
then
    echo "running python3 /opt/firefox/user_to_network/user_to_network_NativeApp/Merge.py $connectionsWork $flowsOutput >> $mergedOut" >> $OutLog
    python3 /opt/firefox/user_to_network/user_to_network_NativeApp/Merge.py $connectionsWork $flowsOutput >> $mergedOut
else
    echo "Merge could not be done because either flows was not found or connections was not found" >> $OutLog
    echo "Make sure that [$flowsOutput] exists" >> $OutLog
    echo "Or make sure that [$connectionsWork] was created by the extension" >> $OutLog
fi

echo >> $OutLog
echo >> $OutLog
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 060 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

exit 0
