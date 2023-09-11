#!/bin/bash


###########################################
## Name : Firefox
## Desc : This script runs Firefox Extension
##        and merges the output with 
##        pmacctd output. 
## ########################################
## Luis Vergara 09/10/23 Rework and lazy logs
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
echo "pgrep -f 'node /usr/local/bin/web-ext' >/dev/null" >> $OutLog
pgrep -f "node /usr/local/bin/web-ext" 2>/dev/null
if [[ $? -eq 0 ]]
then
    #Do nothing
    echo "Firefox Extension already running web-ext"  >> $OutLog
    exit -1
fi

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

### Executing
# Get current UTC timestamp
startTime=$(date -u +"%Y%m%d %H:%M:%S")

# Output the UTC timestamp
echo "start time: $startTime" >> $OutLog

### End

echo "###########################################" >> $OutLog
echo "## JOBSTEP: 005 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

###########################################
## JOBSTEP : 010
## Desc    : Check if pmacctd and nfacctd
##           are running. 
###########################################
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 010 Started                    " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

## Check that pmacctd is running first
if ps aux | grep -q '[p]macctd'; then
    echo "pmacctd is running" >> $OutLog
    ## Then check that nfacctd is also running
    if ps aux | grep -q '[n]facctd'; then
    echo "nfacctd is running" >> $OutLog
    else
        echo "nfacctd is not running" >> $OutLog
        echo "Exiting..." >> $OutLog
        exit -1
    fi 
else
    echo "pmacctd is not running" >> $OutLog
    echo "Exiting..." >> $OutLog
    exit -1
fi 
### End

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
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 020 Started                    " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

# Look for the path to nfacctd.conf file in Transport.conf
# If it is missing at this point we are left we somewhat
# of an orphaned output but we don't let this stop us now.

transportConf=/opt/firefox/user_to_network/user_to_network_NativeApp/Transport.conf
nfacctdConf=""
flowsOutput=""
flowsBefore=""

# Check if the Transport.conf file exists
if [ ! -f "$transportConf" ]
then
    echo "Transport.conf does not exist" >> $OutLog
else
    # Check if -n exists in the Transport.conf file.
    nfacctdConf=$(extract_string_after_argument "-n" "$transportConf")
    if [ -n "$nfacctdConf" ] && [ -f "$nfacctdConf" ]
    then
        echo "Using nfacctd file: $nfacctdConf" >> $OutLog
        # 
        # In nfacctdConf we should find print_output_file value
        flowsOutput=`grep -w print_output_file "$nfacctdConf"   | awk -F: '{print $2}' | awk  '{$1=$1};1'`
        if [ -n "$flowsOutput" ] && [ -f "$flowsOutput" ]
        then
            echo "Using flowsOutput file: $flowsOutput" >> $OutLog
            ##
            # This is where we want to make a copy of the flowsOutput file as is
            # We will need this for later
            # 
            flowsBefore=/opt/firefox/user_to_network/pmacct/tmp/flows.before.$CurrentPID.$timestamp.csv
            cp $flowsOutput $flowsBefore >> $OutLog
        fi
    else
        echo "nfacctd file not found or invalid" >> $OutLog
        echo "flows.csv could not be found" >> $OutLog
    fi
fi

### End

echo "###########################################" >> $OutLog
echo "## JOBSTEP: 020 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog


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
        echo "$connections is valid" >> $OutLog
        echo "Using connections file: $connections" >> $OutLog
    else
        echo "connections.csv from .conf file not found or invalid" >> $OutLog
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

echo "###########################################" >> $OutLog
echo "## JOBSTEP: 030 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

###########################################
## JOBSTEP : 040
## Desc    : Get diff of flows.out
###########################################
echo "###########################################" >> $OutLog
echo "## JOBSTEP: 040 Started                    " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

## Executing

# Start a delay before auto running merge.py 
echo sleep 5 min >> $OutLog
sleep 300

flowsAfter=""
flowsDiff=""
# If flowsBefore is valid and flowsOutput is valid we can do a diff
if [ -n "$flowsOutput" ] && [ -f "$flowsOutput" ] && [ -n "$flowsBefore" ] && [ -f "$flowsBefore" ]
then
    ##
    # This is where we want to make a copy of the flowsOutput file as is
    # We will need this for later
    # 
    flowsAfter=/opt/firefox/user_to_network/pmacct/tmp/flows.after.$CurrentPID.$timestamp.csv
    cp $flowsOutput $flowsAfter >> $OutLog

    ##
    # If we made it here then we should be able to do a diff
    flowsDiff=/opt/firefox/user_to_network/pmacct/tmp/flows.diff.$CurrentPID.$timestamp.csv
    diff $flowsBefore $flowsAfter | grep ">" | awk -F\> '{print $2}' | awk '{$1=$1};1' > $flowsDiff
fi    

### End

echo "###########################################" >> $OutLog
echo "## JOBSTEP: 040 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

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
if [ -n "$flowsDiff" ] && [ -f "$flowsDiff" ] && [ -n "$connectionsWork" ] && [ -f "$connectionsWork" ]
then
    echo "running python3 /opt/firefox/user_to_network/user_to_network_NativeApp/Merge.py $connectionsWork $flowsDiff >> $mergedOut" >> $OutLog
    python3 /opt/firefox/user_to_network/user_to_network_NativeApp/Merge.py $connectionsWork $flowsDiff >> $mergedOut
else
    echo "Merge could not be done because either flows was not found or connections was not found" >> $OutLog
    echo "Make sure that you specify the nfacctd.conf file with -n /path/to/nfacctd.conf file in Transport.conf" >> $OutLog
    echo "Or make sure that connections were created by the extension" >> $OutLog
fi

echo "###########################################" >> $OutLog
echo "## JOBSTEP: 060 Finished                   " >> $OutLog
echo "###########################################" >> $OutLog
echo >> $OutLog
echo >> $OutLog

exit 0