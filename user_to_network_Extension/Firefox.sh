#!/bin/bash


###########################################
## Name : Firefox
## Desc : This script runs Firefox Extension
##        and merges the output with 
##        pmacctd output. 
###########################################

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


###########################################
## JOBSTEP : 005
## Desc    : Get timestamp 
###########################################
echo "###########################################"
echo "## JOBSTEP: 005 Started                    "
echo "###########################################"
echo
echo 

### Executing
# Get current UTC timestamp
timestamp=$(date -u +"%Y%m%d %H:%M:%S")

# Output the UTC timestamp
echo "start time: $timestamp"

### End

echo "###########################################"
echo "## JOBSTEP: 005 Finished                   "
echo "###########################################"
echo
echo 

###########################################
## JOBSTEP : 010
## Desc    : Check if pmacctd and nfacctd
##           are running. 
###########################################
echo "###########################################"
echo "## JOBSTEP: 010 Started                    "
echo "###########################################"
echo
echo 

#Flag tells us if we opened pmacctd and nfacctd
openedPmacctdNfacctd=0
### Executing

# Check if pmacctd is running
echo 'pgrep -x "pmacctd" > /dev/null'
pgrep -x "pmacctd" >/dev/null
if [[ $? -eq 0 ]]
then
    echo "pmacctd is running."
else
    echo "pmacctd is not running."
    echo
    echo "Starting pmacctd"
    # You can specify the pmacctd file to use in Transport.conf or else
    # this job can run pmacctd using some configuration files built into the repository
    # The configuration of the switch could be different. Open the .conf file below to
    # Change the configuration.
    file_path="/opt/firefox/user_to_network/user_to_network_NativeApp/Transport.conf"
    pmacctd_default="/opt/firefox/user_to_network/pmacct/pmacctd.conf"
    pmacctd_out_default="/opt/firefox/user_to_network/pmacct/logs/pmacctd.out"
    pmacctdFile=""
    pmacctdOutFile=""
    # Check if the folder exists
    if [ ! -d "/opt/firefox/user_to_network/pmacct/logs" ]
    then
        # Create the folder if it doesn't exist
        mkdir "/opt/firefox/user_to_network/pmacct/logs"
    fi

    echo "Looking in $file_path for pmacctd file path"

    # Check if the Transport.conf file exists
    if [ ! -f "$file_path" ]
    then
        echo "Transport.conf does not exist"
        echo "Using default pmacctd location : $pmacctdFile"
        pmacctdFile="$pmacctd_default"
    else
        # Check if the "-d" argument exists in the file
        pmacctdFile=$(extract_string_after_argument "-d" "$file_path")
        # Check if the extracted string is a valid file
        if [ -n "$pmacctdFile" ] && [ -f "$pmacctdFile" ]
        then
            echo "$pmacctdFile is valid"
            echo "Using pmacctd file: $pmacctdFile"
        else
            echo "pmacctd file not found or invalid"
            extracted_string="$pmacctd_default"
            echo "Using default pmacctd file: $extracted_string"
        fi

        # Check if the "-do" argument exists in the file
        pmacctdOutFile=$(extract_string_after_argument "-do" "$file_path")
        # Check if the extracted string is a valid file
        if [ -n "$pmacctdOutFile" ] && [ -f "$pmacctdOutFile" ]
        then
            echo "$pmacctdOutFile is valid"
            echo "Using pmacctd out file: $pmacctdOutFile"
        else
            echo "pmacctd out file not found or invalid"
            pmacctdOutFile="$pmacctd_out_default"
            echo "Using default pmacctd out file: $pmacctdOutFile"
        fi
    fi

    # Command to run pmacctd -f $pmacctdFile
    echo "sudo pmacctd -f $pmacctdFile >> $pmacctdOutFile  2&>1 &"

    # Start pmacctd with nohup and redirect the output to the specified file
    echo "start time : $timestamp" >> $pmacctdOutFile
    nohup sudo pmacctd -f $pmacctdFile >> $pmacctdOutFile &
fi
echo
echo
# Check if nfacctd is running
echo "pgrep -x nfacctd > /dev/null"
pgrep -x "nfacctd" > /dev/null
if [[ $? -eq 0 ]]
then
    echo "nfacctd is running."
else
    echo "nfacctd is not running."
    echo
    echo "Starting nfacctd"
    # You can specify the nfacctd file to use in Transport.conf or else
    # this job can run nfacctd using some configuration files built into the repository.
    # Open the .conf file below to change the configuration.
    file_path="/opt/firefox/user_to_network/user_to_network_NativeApp/Transport.conf"
    nfacctd_default="/opt/firefox/user_to_network/pmacct/nfacctd.conf"
    nfacctd_out_default="/opt/firefox/user_to_network/pmacct/logs/nfacctd.out"
    nfacctdFile=""
    nfacctdOutFile=""

    # Check if the folder exists
    if [ ! -d "/opt/firefox/user_to_network/pmacct/logs" ] 
    then
        # Create the folder if it doesn't exist
        mkdir "/opt/firefox/user_to_network/pmacct/logs"
    fi

    echo "Looking in $file_path for nfacctd file path"
 
    # Check if the Transport.conf file exists
    if [ ! -f "$file_path" ]
    then
        echo "Transport.conf does not exist"
        echo "Using default nfacctd location : $nfacctdFile"
        nfacctdFile="$nfacctd_default"
    else
        # Check if the "-n" argument exists in the file
        nfacctdFile=$(extract_string_after_argument "-n" "$file_path")
        # Check if the extracted string is a valid file
        if [ -n "$nfacctdFile" ] && [ -f "$nfacctdFile" ]
        then
            echo "$nfacctdFile is valid"
            echo "Using nfacctd file: $nfacctdFile"
        else
            echo "nfacctd file not found or invalid"
            nfacctdFile="$nfacctd_default"
            echo "Using default nfacctd file: $nfacctdFile"
        fi

        # Check if the "-no" argument exists in the file
        nfacctdOutFile=$(extract_string_after_argument "-no" "$file_path")
        # Check if the extracted string is a valid file
        if [ -n "$nfacctdOutFile" ] && [ -f "$nfacctdOutFile" ]
        then
            echo "$nfacctdOutFile is valid"
            echo "Using nfacctd out file: $nfacctdOutFile"
        else
            echo "nfacctd out file not found or invalid"
            nfacctdOutFile="$nfacctd_out_default"
            echo "Using default nfacctd out file: $nfacctdOutFile"
        fi
    fi

    # Command to run nfacctd -f $nfacctdFile
    echo "sudo nfacctd -f $nfacctdFile >> $nfacctddOutFile 2>&1 &"

    # Start nfacctd with nohup and redirect the output to the specified file
    echo "start time : $timestamp" >> $nfacctdOutFile
    nohup nfacctd -f $nfacctdFile >> $nfacctdOutFile 2>&1 &
fi
echo
echo
###

### End

echo "###########################################"
echo "## JOBSTEP: 010 Finished                   "
echo "###########################################"
echo
echo 

###########################################
## JOBSTEP : 020
## Desc    : Run the Firefox Extension
###########################################
echo "###########################################"
echo "## JOBSTEP: 020 Started                    "
echo "###########################################"
echo
echo 

## Executing
# Check if this already running. Don't run multiple of these
echo "pgrep -f 'node /usr/local/bin/web-ext' >/dev/null"
pgrep -f "node /usr/local/bin/web-ext" 2>/dev/null
if [[ $? -eq 0 ]]
then
    #Do nothing
    echo "Firefox Extension already running web-ext"
else
    # Set the path to the extension
    extension_path="/opt/firefox/user_to_network/user_to_network_Extension"

    # Set the path to the Firefox Developer Edition executable
    firefox_dev_path="/opt/firefox/firefox"

    # Set the environment variable to start Firefox in light theme
    export MOZ_ENABLE_LIGHT_THEME=1
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

    # Run the web-ext tool with the Firefox Developer Edition
    echo web-ext run --firefox-binary $firefox_dev_path -s $extension_path
    web-ext run --firefox-binary "$firefox_dev_path" -s "$extension_path"
fi

### End

echo "###########################################"
echo "## JOBSTEP: 020 Finished                   "
echo "###########################################"
echo
echo 

###########################################
## JOBSTEP : 030
## Desc    : Wait 15 minutes
###########################################
echo "###########################################"
echo "## JOBSTEP: 030 Started                    "
echo "###########################################"
echo
echo 

## Executing

# Start a delay before auto running merge.py 
echo "sleep 1 min"
sleep 60

### End

echo "###########################################"
echo "## JOBSTEP: 030 Finished                   "
echo "###########################################"
echo
echo 

###########################################
## JOBSTEP : 035
## Desc    : Get timestamp 
###########################################
echo "###########################################"
echo "## JOBSTEP: 035 Started                    "
echo "###########################################"
echo
echo 

### Executing
# Get current UTC timestamp
endtimestamp=$(date -u +"%Y%m%d %H:%M:%S")

# Output the UTC timestamp
echo "end time: $endtimestamp"

### End

echo "###########################################"
echo "## JOBSTEP: 035 Finished                   "
echo "###########################################"
echo
echo 

###########################################
## JOBSTEP : 050
## Desc    : End pmacctd and nfacctd
###########################################
echo "###########################################"
echo "## JOBSTEP: 040 Started                    "
echo "###########################################"
echo
echo 

###########################################
## JOBSTEP : 050
## Desc    : Merge the Firefox Connections 
##           with pmacctd flows.
###########################################
echo "###########################################"
echo "## JOBSTEP: 050 Started                    "
echo "###########################################"
echo
echo 

## From Transport.conf take -fo (flows out) default is /opt/firefox/user_to_network/pmacct/flows/flows.csv
## Also take -c (connections.csv path) default is /opt/firefox/user_to_network/user_to_network_NativeApp/connections.csv
## Executing
#
flowsDefault="/opt/firefox/user_to_network/pmacct/flows/flows.csv"
connectionsDefault="/opt/firefox/user_to_network/user_to_network_NativeApp/connections.csv"

# Check if the "-fo" argument exists in the file
flows=$(extract_string_after_argument "-fo" "$file_path")
# Check if the extracted string is a valid file
if [ -n "$flows" ] && [ -f "$flows" ]
then
    echo "$flows is valid"
    echo "Using flows file: $flows"
else
    echo "flows file not found or invalid"
    flows="$flowsDefault"
    echo "Using default flows file: $flows"
fi

# Check if the "-fo" argument exists in the file
connections=$(extract_string_after_argument "-c" "$file_path")
# Check if the extracted string is a valid file
if [ -n "$connections" ] && [ -f "$connections" ]
then
    echo "$connections is valid"
    echo "Using connections file: $connections"
else
    echo "connections file not found or invalid"
    connections="$connectionsDefault"
    echo "Using default connections file: $connections"
fi

echo "running python3 /opt/firefox/user_to_network/user_to_network_NativeApp/Merge.py $flows $connections"
python3 /opt/firefox/user_to_network/user_to_network_NativeApp/Merge.py $connections $flows

# connections_file="/opt/firefox/user_to_network/user_to_network_NativeApp/connections.csv"
# flows_file="/opt/firefox/user_to_network/user_to_network_NativeApp/flows.csv"
# output_dir="/opt/firefox/user_to_network/user_to_network_NativeApp/"
# output_file="$output_dir/merged_$(date +%Y-%m-%d_%H:%M:%S).csv"
# log_dir="/opt/firefox/user_to_network/user_to_network_NativeApp/logs"
# log_file="$log_dir/ClickScript_$(date +%Y-%m-%d_%H:%M:%S).log"
# bkp_dir="/opt/firefox/user_to_network/user_to_network_NativeApp/connectionsBkp"
# bkp_file="$bkp_dir/connections_$(date +%Y-%m-%d_%H:%M:%S).csv"

# if [[ -e $connections_file && -e $flows_file ]]; then
#     python mergy.py "$connections_file" "$flows_file" > "$output_file"
#     # Save the connections.csv file
#     cp "$connectons_file" "$bkp_file"
# else
#     echo "Either $connections_file or $flows_file does not exist" >> "$log_file"
# fi
