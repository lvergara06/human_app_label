# This script creates everything off of /tmp directory.
# It clones user_to_network and pmacct but cleans up after they are installed.
## The INSTALL.sh file will do the following.
1) Install Git on Ubuntu/Debian
	1.1) Check if Git is installed
2) Clone user_to_network repository
3) Download Firefox Dev
    3.1) Download the latest version of Firefox Developer Edition
	3.2) Extract the downloaded archive
    3.3) Move the extracted Firefox directory to the /opt directory
    3.4) Create a symbolic link for the Firefox binary
    3.5) Cleanup the downloaded archive
4) Create a space for the app
5) Add path to folder to Transport.json
6) Create mozilla/native-messaging-hosts and copy json to it
7) Install Flatpak
	7.1) Check if Flatpak is installed
8) Set permission with Flatpak
9) Install python 
	9.1) Check if Python is installed
10) Install pip
	10.1) Check if pip is installed
11) Instal Node.js
	11.1) Check if Node.js is installed
12) Check if web-ext is installed
    12.1) Install web-ext using npm
13) Add path to the extension in Firefox script
14) Install ClickScript to open firefox by double clicking the Firefox file from desktop
15) Install netstat
16) Clone pmacct repository
	16.1) Resolve dependencies
	16.2) Install pmacct