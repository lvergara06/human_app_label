#!/bin/bash


###########################################
## Name : Firefox
## Desc : This script runs Firefox Extension
##        and urltoflowmatch the output with 
##        pmacctd output. 
## ########################################
## Luis Vergara 09/10/23 Rework and lazy logs
## Luis Vergara 09/15/23 Reinstating start 
##                       pmacctd and nfacctd
## Herman Ramey 09/25/23 Adding feedback to log
##			 for invalid nfacctd.conf
## Luis Vergara 09/26/23 Handle when pmacctd
##                       or nfacctd fail to start
##
## Herman Ramey 04/25/24 Implementing logic to 
##                       allow user to specify 
##                       interface for pmacct
###########################################
CurrentPID=$$
timestamp=$(date -u +"%Y%m%d%H%M%S")
OutLog=/opt/firefox/human_app_label/logs/Firefox.$timestamp.log
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

############################################
### PROCESS    : 000 Started  
### DESCRIPTION: To check if firefox extension is running                 
############################################

echo "###########################################" >> $OutLog
echo "## PROCESS: 000 Started                    " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog
echo "Checking if firefox extension is running" >> $OutLog
echo >> $OutLog
# Check if this already running. Don't run multiple of these
echo "pgrep -f '/bin/bash /opt/firefox/human_app_label/Extension/Firefox.sh' | wc -l" >> $OutLog
Count=`pgrep -f "/bin/bash /opt/firefox/human_app_label/Extension/Firefox.sh" | wc -l`
echo "Firefox.sh count is $Count" >> $OutLog
if [[ $Count -eq 1 ]]
then
    #Do nothing
    echo "Firefox.sh already running"  >> $OutLog
    exit -1
fi

# command_to_check="node /opt/firefox/human_app_label/Extension/server.js"

# if pgrep -f "$command_to_check" >/dev/null; then
#   echo "The server is already running." >> $OutLog
# else
#   echo "Running the server..." >> $OutLog
# #   node --trace-warnings /opt/firefox/human_app_label/Extension/server.js &
#   echo "Server started." >> $OutLog
# fi

echo "" >> $OutLog
echo "" >> $OutLog
echo "###########################################" >> $OutLog
echo "## PROCESS: 000 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

###########################################
## PROCESS    : 005
## DESCRIPTION: To get timestamp 
###########################################
echo "###########################################" >> $OutLog
echo "## PROCESS: 005 Started                    " >> $OutLog
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
echo "## PROCESS: 005 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

###########################################
## PROCESS    : 010
## DESCRIPTION: TO start pmacctd and nfacctd, and check if these folders exist (logs, tmp, flows), if not create them
###########################################
echo "###########################################" >> $OutLog
echo "## PROCESS: 010 Started                    " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog
echo "Starting pmacctd and nfacctd for Firefox:PID:$CurrentPID" >> $OutLog
echo "" >> $OutLog

## Run pmacctd
echo "Starting pmacctd" >> $OutLog
# You can specify the pmacctd file to use in hals.conf or else
# this job can run pmacctd using some configuration files built into the repository
# The configuration of the switch could be different. Open the .conf file below to
# Change the configuration.
halsConf="/opt/firefox/human_app_label/NativeApp/hals.conf"
pmacctdDefault="/opt/firefox/human_app_label/pmacct/pmacctd.conf"
pmacctdLogs="/opt/firefox/human_app_label/pmacct/logs"
pmacctdDefaultInterface="enp0s3"
pmacctdConf=""
pmacctdOutFile=""
pmacctdInterface=""
# Check if the folder exists
if [ ! -d "/opt/firefox/human_app_label/pmacct/logs" ]
then
    # Create the folder if it doesn't exist
    mkdir -p "/opt/firefox/human_app_label/pmacct/logs"
fi

echo "Looking in $halsConf for pmacctd configuration file path" >> $OutLog

# Check if the hals.conf file exists
if [ ! -f "$halsConf" ]
then
    # echo "Hello" >> $OutLog
    echo "hals.conf does not exist" >> $OutLog
    echo "Using default pmacctd location : $pmacctdDefault"
    pmacctdConf="$pmacctdDefault"
else
    # Check if the "-d" argument exists in the file
    pmacctdConf=$(extract_string_after_argument "-d" "$halsConf")
    pmacctdInterface=$(extract_string_after_argument "-i" "$halsConf")


    # Check if the extracted string is a valid file
    if [ -n "$pmacctdConf" ] && [ -f "$pmacctdConf" ]
    then
        echo "Using pmacctd file: $pmacctdConf" >> $OutLog 
    else
        echo "pmacctd file [$pmacctdConf] not found or invalid" >> $OutLog
        pmacctdConf="$pmacctdDefault"
        echo "Using default pmacctd file: $pmacctdConf" >> $OutLog
    fi

    if [ -n "$pmacctdInterface" ] && ifconfig "$pmacctdInterface"  &>/dev/null
    then
        echo "Listening on interface: $pmacctdInterface" >> $OutLog 
    else
        echo "Network interface [$pmacctdInterface] not found or invalid" >> $OutLog
        pmacctdInterface="$pmacctdDefaultInterface"
        echo "Listening on default interface $pmacctdInterface" >> $OutLog
    fi

    # Check if the "-do" argument exists in the file
    pmacctdOutFile=$(extract_string_after_argument "-do" "$halsConf")
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

echo "start time : $timestamp" >> "$pmacctdOutFile"
nohup sudo pmacctd -i "$pmacctdInterface " -f "$pmacctdConf" >> "$pmacctdOutFile" 2>&1 &

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
# You can specify the nfacctd file to use in hals.conf or else
# this job can run nfacctd using some configuration files built into the repository.
# Open the .conf file below to change the configuration.
halsConf="/opt/firefox/human_app_label/NativeApp/hals.conf"
nfacctdDefault="/opt/firefox/human_app_label/pmacct/nfacctd.conf"
nfacctdLogs="/opt/firefox/human_app_label/pmacct/logs"
nfacctdTmp="/opt/firefox/human_app_label/pmacct/tmp"
nfacctdFlows="/opt/firefox/human_app_label/pmacct/flows"
nfacctdConf=""
nfacctdOutFile=""
flowsOutput=""

# Check if the folder exists
if [ ! -d "/opt/firefox/human_app_label/pmacct/tmp" ] 
then
    # Create the folder if it doesn't exist
    mkdir -p "/opt/firefox/human_app_label/pmacct/tmp"
fi

# Check if the folder exists
if [ ! -d "/opt/firefox/human_app_label/pmacct/flows" ] 
then
    # Create the folder if it doesn't exist
    mkdir -p "/opt/firefox/human_app_label/pmacct/flows"
fi

echo "Looking in $halsConf for nfacctd file path" >> $OutLog

# Check if the hals.conf file exists
if [ ! -f "$halsConf" ]
then
    echo "hals.conf does not exist" >> $OutLog
    echo "Using default nfacctd location : $nfacctdDefault" >> $OutLog
    nfacctdConf="$nfacctdDefault"
else
    # Check if the "-n" argument exists in the file
    nfacctdConf=$(extract_string_after_argument "-n" "$halsConf")
    # Check if the extracted string is a valid file
    if [ -n "$nfacctdConf" ] && [ -f "$nfacctdConf" ]
    then
        #echo "$nfacctdConf is valid"
        echo "Using nfacctd file: [$nfacctdConf]" >> $OutLog
    else
        echo "nfacctd file not found or invalid" >>$OutLog
        echo "nfacctdConf [$nfacctdConf] does not exist" >>$OutLog
        nfacctdConf="$nfacctdDefault"
        echo "Using default nfacctd file: [$nfacctdConf]" >> $OutLog
    fi

    # Check if the "-n" argument exists in the file
    nfacctdOutFile=$(extract_string_after_argument "-no" "$halsConf")
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
echo "Flows Output at [$flowsOutput]" >> $OutLog

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
echo "## PROCESS: 010 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

###########################################
## PROCESS    : 015
## DESCRIPTION: Extract the print_output_file from nfacctd.conf
###########################################

# echo "###########################################" >> $OutLog
# echo "## PROCESS: 015 Started                    " >> $OutLog
# echo "###########################################" >> $OutLog
# echo >> $OutLog
# echo >> $OutLog

# Look for the path to nfacctd.conf file in hals.conf
# If it is missing at this point we are left we somewhat
# of an orphaned output but we don't let this stop us now.

# halsConf=/opt/firefox/human_app_label/NativeApp/hals.conf
# nfacctdConf=""
# flowsOutput=""
# flowsBefore=""

# # Check if the hals.conf file exists
# if [ ! -f "$halsConf" ]
# then
#     echo "hals.conf does not exist" >> $OutLog
# else
#     # Check if -n exists in the hals.conf file.
#     nfacctdConf=$(extract_string_after_argument "-n" "$halsConf")
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
#             flowsBefore=/opt/firefox/human_app_label/pmacct/tmp/flows.before.$CurrentPID.$timestamp.csv
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
# echo "## PROCESS: 015 Finished                   " >> $OutLog
# echo "###########################################" >> $OutLog
# echo >> $OutLog
# echo >> $OutLog


###########################################
## PROCESS    : 020
## DESCRIPTION: To run the Firefox Extension
###########################################
echo "###########################################" >> $OutLog
echo "## PROCESS: 020 Started                    " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog
urlstream=""
urlstreamWork=""
urlstreamDefault=/opt/firefox/human_app_label/NativeApp/output/urlstream.csv
## Executing
# Check if this already running. Don't run multiple of these
echo "pgrep -f 'node /usr/local/bin/web-ext' >/dev/null" >> $OutLog
pgrep -f "node /usr/local/bin/web-ext" 2>/dev/null
if [[ $? -eq 0 ]]
then
    #Do nothing
    echo "Firefox Extension already running web-ext"  >> $OutLog
    echo "Exiting..." >> $OutLog
    exit -1
else
    #Make sure pmacctd and nfacctd are running 
    if ps -p $pmacctdPid > /dev/null; then
        #Check if nfacctd is running
        if ps -p $nfacctdPid > /dev/null; then
            echo "pmacctd and nfacctd running... now starting browser" >> $OutLog
        else
            echo "nfacctd pid $nfacctdPid is not running before starting browser. Check what went wrong." >> $OutLog
            echo "Killing pmacctd pid $pmacctdPid..." >> $OutLog
            sudo /opt/firefox/human_app_label/Extension/SudoKillPmacctd.sh $pmacctdPid        
            echo "exiting..." >> $OutLog
            exit -1
        fi
    else
        echo "pmacctd pid $pmacctdPid is not running before starting browser. Check what went wrong." >> $OutLog
        if ps -p $nfacctdPid > /dev/null; then
            echo "Killing nfacctd pid $nfacctdPid" >> $OutLog
            kill -9 $nfacctdPid
        fi
        echo "exiting..." >> $OutLog
        exit -1
    fi
    
    # Set the path to the extension
    extension_path="/opt/firefox/human_app_label/Extension"

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
    ## Let's go ahead and take the urlstream file and put it in 
    # a more stable place
    # Check if the "-c" argument exists in the file
    urlstream=$(extract_string_after_argument "-c" "$file_path")
    # Check if the extracted string is a valid file
    if [ -n "$urlstream" ] && [ -f "$urlstream" ]
    then
        #echo "$urlstream is valid" >> $OutLog
        echo "Using urlstream file: $urlstream" >> $OutLog
    else
        #echo "urlstream.csv from .conf file not found or invalid" >> $OutLog
        urlstream=$urlstreamDefault 
        echo "Using default urlstream file: $urlstream" >> $OutLog
    fi

    urlstreamWork=/opt/firefox/human_app_label/NativeApp/work/urlstream.$CurrentPID.$timestamp.csv
    cp $urlstream $urlstreamWork >> $OutLog
    #
    ## Make certain that the copy worked before delete
    if [ -n "$urlstreamWork" ] && [ -f "$urlstreamWork" ]
    then    
        echo $urlstream copied to $urlstreamWork >> $OutLog
        rm $urlstream
        echo "$urlstream removed." >> $OutLog
    fi
    # # Check if the server is running
    # if pid=$(pgrep -f "node /opt/firefox/human_app_label/Extension/server.js"); then
    # echo "Closing the server..." >> $OutLog
    # kill -9 "$pid"
    # echo "Process killed." >> $OutLog
    # fi
fi



### End

echo >> $OutLog
echo >> $OutLog
echo "###########################################" >> $OutLog
echo "## PROCESS: 020 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

###########################################
## PROCESS    : 025
## DESCRIPTION: To get different url and match them to flows
###########################################
# echo "###########################################" >> $OutLog
# echo "## PROCESS: 025 Started                    " >> $OutLog
# echo "###########################################" >> $OutLog
# echo >> $OutLog
# echo >> $OutLog

# ## Executing

# # Start a delay before auto running urltoflowmatch.py 
 echo sleep 5 min >> $OutLog
 sleep 300
 echo "Killing pmacctd PID: $pmacctdPid" >> $OutLog
 sudo /opt/firefox/human_app_label/Extension/SudoKillPmacctd.sh $pmacctdPid
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
#     flowsAfter=/opt/firefox/human_app_label/pmacct/tmp/flows.after.$CurrentPID.$timestamp.csv
#     cp $flowsOutput $flowsAfter >> $OutLog

#     ##
#     # If we made it here then we should be able to do a diff
#     flowsDiff=/opt/firefox/human_app_label/pmacct/tmp/flows.diff.$CurrentPID.$timestamp.csv
#     diff $flowsBefore $flowsAfter | grep ">" | awk -F\> '{print $2}' | awk '{$1=$1};1' > $flowsDiff
# fi    

# ### End

# echo "###########################################" >> $OutLog
# echo "## PROCESS: 025 Finished                   " >> $OutLog
# echo "###########################################" >> $OutLog
# echo >> $OutLog
# echo >> $OutLog

###########################################
## PROCESS    : 030
## DESCRIPTION: To get timestamp 
###########################################
echo "###########################################" >> $OutLog
echo "## PROCESS: 030 Started                    " >> $OutLog
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
echo "## PROCESS: 030 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

###########################################
## PROCESS    : 035
## DESCRIPTION: Match the url to flows and get the outputs
###########################################
echo "###########################################" >> $OutLog
echo "## PROCESS: 035 Started                    " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

urltoflowmatchOut=/opt/firefox/human_app_label/NativeApp/mergedOutput/urltoflowmatch_urlstream_$CurrentPID.$timestamp.csv
##
# The end game! If we have a diff then we can do a urltoflowmatch
# Let's also check the urlstream file is good
if [ -n "$flowsOutput" ] && [ -f "$flowsOutput" ] && [ -n "$urlstreamWork" ] && [ -f "$urlstreamWork" ]
then
    echo "running python3 /opt/firefox/human_app_label/NativeApp/urltoflowmatch.py $urlstreamWork $flowsOutput $timestamp $CurrentPID >> $urltoflowmatchOut" >> $OutLog
    python3 /opt/firefox/human_app_label/NativeApp/urltoflowmatch.py $urlstreamWork $flowsOutput $timestamp $CurrentPID 
else
    echo "urltoflowmatch could not be done because either flows was not found or urlstream was not found" >> $OutLog
    echo "Make sure that [$flowsOutput] exists" >> $OutLog
    echo "Or make sure that [$urlstreamWork] was created by the extension" >> $OutLog
fi

echo >> $OutLog
echo >> $OutLog
echo "###########################################" >> $OutLog
echo "## PROCESS: 035 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog
exit 0