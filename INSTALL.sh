#!/bin/bash

# This script creates everything off of tmp directory.
TMPDIR=/tmp

echo "Installing git"
echo
echo
# Install Git on Ubuntu/Debian
# Check if Git is installed
if ! command -v git &> /dev/null
then
    sudo apt-get update
    sudo apt-get install git -y
fi
echo
echo
echo "git Installed"
echo
echo

# Clone user_to_network repository
echo "Cloning user_to_network"
echo
echo
if [ -d "$TMPDIR/user_to_network" ]
then
    echo "Git repository user_to_network already exists at $TMPDIR, skipping clone"
else
    echo cloning user_to_network at $TMPDIR/user_to_network
    git clone https://github.com/lvergara06/user_to_network $TMPDIR/user_to_network
    echo cloned user_to_network done!
fi
echo
echo

# Download Firefox Dev
echo Downloading Firefox Dev
echo
echo
# Path to the Firefox executable
firefox_path=/opt/firefox/firefox

# Check the version
version=$(firefox_path --version | awk '{print $3}')

# Compare the version
if [[ "$version" == "114.0" ]]
then
    echo "Firefox version 114.0 already installed"
else
    cd $TMPDIR
    # Download the latest version of Firefox Developer Edition
    wget -O firefox-developer-114.tar.bz2 'https://ftp.mozilla.org/pub/firefox/releases/114.0b9/linux-x86_64/en-US/firefox-114.0b9.tar.bz2'

    # Extract the downloaded archive
    tar -xf firefox-developer-114.tar.bz2

    # Move the extracted Firefox directory to the /opt directory
    sudo mv firefox /opt/

    # Create a symbolic link for the Firefox binary
    sudo ln -s /opt/firefox/firefox /usr/bin/firefox-developer-edition

    # Cleanup the downloaded archive
    rm firefox-developer-114.tar.bz2

    echo "Firefox version 114.0 is installed."
fi
echo
echo

# Create a space for the app
echo "Creating app space at /opt/firefox/user_to_network"
echo
echo
if [ -d "/opt/firefox/user_to_network" ]
then
    echo "App folder exists: /opt/firefox/user_to_network"
else
    mkdir -p /opt/firefox/user_to_network    
fi
echo "App Space Created"
echo
echo

echo "Coping $TMPDIR/user_to_network to /opt/firefox/user_to_network"
echo
echo
sudo cp -r $TMPDIR/user_to_network/* /opt/firefox/user_to_network
sudo mkdir /opt/firefox/user_to_network/user_to_network_NativeApp/connectionsBkp
sudo mkdir /opt/firefox/user_to_network/user_to_network_NativeApp/logs
echo
echo
echo "Giving /opt/firefox/user_to_network permissions"
echo
echo
sudo chmod -R 777 /opt/firefox/user_to_network
echo "/opt/firefox/user_to_network permisions changed"
echo
echo
echo "Changing icon for firefox"
sudo cp /opt/firefox/user_to_network/user_to_network_Extension/default128.png /opt/firefox/browser/chrome/icons/default
echo "User to network copied to /opt/firefox/user_to_network"
echo
echo
echo "Removing user_to_network from $TMPDIR"
echo
echo
sudo rm -rf $TMPDIR/user_to_network
echo
echo
echo
echo Transport.json is
cat /opt/firefox/user_to_network/user_to_network_NativeApp/Transport.json
echo
echo

# Create mozilla directory and copy json to it
echo "Creating mozilla native messaging directory"
echo
echo
if [ -d "~/.mozilla/native-messaging-hosts" ]
then
    echo "Mozilla folder exists: ~/.mozilla/native-messaging-hosts"
else
    mkdir -p ~/.mozilla/native-messaging-hosts
fi
echo
echo
echo "Mozilla folder exists: ~/.mozilla/native-messaging-hosts"
echo
echo

echo "Copying /opt/firefox/user_to_network/user_to_network_NativeApp/Transport.json to ~/.mozilla/native-messaging-hosts"
echo
echo
cp /opt/firefox/user_to_network/user_to_network_NativeApp/Transport.json ~/.mozilla/native-messaging-hosts
echo "Transport.json copied"
echo
echo

# Install Flatpak
# Check if Flatpak is installed
echo "Installing flatpak"
echo
echo
if ! command -v flatpak &> /dev/null
then
    sudo apt install flatpak
fi
echo "Flatpak is installed"
echo
echo

# Set permission with Flatpak
echo "Setting permission with Flatpak"
echo
echo
flatpak permission-set webextension Transport snap.firefox yes
echo
echo
echo "Setting permission with Flatpak"
echo

# Install python 
# Check if Python is installed
echo "Installing Python3"
echo
echo
if ! command -v python3 &> /dev/null
then
    sudo apt install python3
fi
echo
echo
echo "Python is installed."
echo
echo

# Install pip
echo "Installing pip"
echo
echo
# Check if pip is installed
if ! command -v pip &> /dev/null
then
    sudo apt install python3-pip
fi
echo
echo
echo "pip is installed."
echo
echo

# Check if Node.js is installed
echo "Installing node.js"
echo
echo
if ! command -v node &> /dev/null
then
    echo "Node.js is not installed. Installing now..."
    # Install Node.js
    sudo apt update
    echo
    echo
    echo "Installing curl first"
    echo
    echo
    if ! command -v curl &> /dev/null
    then
        sudo apt-get install curl
    fi
    echo
    echo
    echo "curl Installed"
    echo
    echo
    echo "Installing nvm first"
    echo
    echo
    if ! command -v nvm &> /dev/null
    then
        sudo apt-get install build-essential libssl-dev
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash 
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
        [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
    fi
    echo
    echo
    echo "nvm Installed"
    echo
    echo
    echo "Finally installing node"
    echo
    echo
    nvm install node 
    echo
    echo
    echo "Node Installed"
    echo
    echo
else
    echo "Node.js is already installed."
fi
echo
echo

# Check if web-ext is installed
echo "Installing web-ext"
echo
echo
if ! command -v web-ext &> /dev/null
then
    echo "web-ext is not installed. Installing now..."
    # Install web-ext using npm
    echo "Installing npm"
    echo
    echo
    sudo apt install npm
    echo "npm Installed"
    echo
    echo
    echo "Installing web-ext with npm"
    echo
    echo
    sudo npm install --global web-ext
else
    echo "web-ext is already installed."
fi
echo
echo

# Install firefox_user_to_network in the apps menu and add it to favorites
echo "Installing firefox_user_to_network to the apps menu"
sudo cp /opt/firefox/user_to_network/user_to_network_Extension/firefox_user_to_network.desktop ~/.local/share/applications
sudo chmod 777 ~/.local/share/applications/firefox_user_to_network.desktop
echo
# Adding firefox_user_to_network to the favorites dock
echo "Adding firefox_user_to_network to favorites"
gsettings set org.gnome.shell favorite-apps "$(gsettings get org.gnome.shell favorite-apps | sed "s/]/, 'firefox_user_to_network.desktop']/")"
echo
echo "Removing regular firefox from favorites"
gsettings set org.gnome.shell favorite-apps "$(gsettings get org.gnome.shell favorite-apps | sed "s|, 'firefox_firefox.desktop'||" | sed "s|'firefox_firefox.desktop', ||" | sed "s|'firefox_firefox.desktop' ||" | sed "s|'firefox_firefox.desktop']|]|")"
echo
echo "firefox_user_to_network Installed"
echo
echo

# Install netstat
echo "Installing netstat"
if ! which netstat >/dev/null; then
  echo "netstat is not installed. Installing..."
  if [ -n "$(command -v apt-get)" ]; then
    sudo apt-get update && sudo apt-get install net-tools
  elif [ -n "$(command -v yum)" ]; then
    sudo yum install net-tools
  else
    echo "Unable to determine package manager. Please install netstat manually."
    exit 1
  fi
else
  echo "netstat is already installed."
fi

# Clone user_to_network repository
echo "Cloning pmacct"
echo
echo
echo "Resolving dependencies"
echo
echo
sudo apt-get install libpcap-dev pkg-config libtool autoconf automake make bash libstdc++-11-dev g++
echo
echo
# Check if pmacctd is already installed
if ! command -v pmacctd &> /dev/null; then
    echo "pmacctd is not installed. Installing..."
    echo cloning pmacct at $TMPDIR/pmacct
    git clone https://github.com/pmacct/pmacct.git $TMPDIR/pmacct
    cd $TMPDIR/pmacct
    sudo $TMPDIR/pmacct/autogen.sh
    sudo $TMPDIR/pmacct/configure #check-out available configure knobs via ./configure --help
    sudo make
    sudo make install #with super-user permission
    echo cloned pmacct done!
else
    echo "pmacctd is already installed!"
    echo
fi
echo
echo

echo
echo
echo DONE!
