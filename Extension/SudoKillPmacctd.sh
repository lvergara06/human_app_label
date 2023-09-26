#!/bin/bash

# Check if the PID argument was provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <pmacctd_pid>"
    exit 1
fi

pmacctd_pid=$1

# Check if pmacctd process is running with the provided PID
if ps -p $pmacctd_pid > /dev/null; then
    # Get the command associated with the process
    process_cmd=$(ps -o cmd= -p $pmacctd_pid)
    if [[ "$process_cmd" == *"pmacctd"* ]]; then
        # Kill the pmacctd process
        sudo kill -9 "$pmacctd_pid"
        echo "pmacctd process with PID $pmacctd_pid has been killed."
    else
        echo "Process with PID $pmacctd_pid is not a pmacctd process."
    fi
else
    echo "Process with PID $pmacctd_pid is not running."
fi