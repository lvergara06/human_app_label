#!/bin/bash

# This script creates everything off of tmp directory.
TMPDIR=/tmp

# Function to check and install packages
install_package() {
    package_name=$1
    if ! dpkg -s "$package_name" &> /dev/null; then
        echo "$package_name is not installed. Installing..."
        sudo apt-get -qq install "$package_name"
        echo "$package_name installed."
    else
        echo "$package_name is already installed."
    fi
}

# Install Git on Ubuntu/Debian
if ! command -v git &> /dev/null; then
    echo "Installing Git"
    sudo apt-get update
    sudo apt-get install git -y
    echo "Git installed"
fi

# Clone user_to_network repository
if [ -d "$TMPDIR/user_to_network" ]; then
    echo "Git repository user_to_network already exists at $TMPDIR, skipping clone"
else
    echo "Cloning user_to_network"
    git clone https://github.com/lvergara06/user_to_network $TMPDIR/user_to_network
    echo "Cloned user_to_network"
fi

# Download Firefox Dev
echo Downloading Firefox Dev
echo
echo
# Path to the Firefox executable
firefox_path=/opt/firefox/firefox

# Check the version
version=$($firefox_path --version | awk '{print $3}')

# Compare the version
if [[ "$version" == "114.0b9" ]]
then
    echo "Firefox version 114.0 already installed"
else
    echo "Downloading Firefox Dev"
    wget -O $TMPDIR/firefox-developer-114.tar.bz2 'https://ftp.mozilla.org/pub/firefox/releases/114.0b9/linux-x86_64/en-US/firefox-114.0b9.tar.bz2'
    tar -xf $TMPDIR/firefox-developer-114.tar.bz2 -C $TMPDIR
    sudo mv $TMPDIR/firefox /opt/
    sudo ln -s /opt/firefox/firefox /usr/bin/firefox-developer-edition
    rm $TMPDIR/firefox-developer-114.tar.bz2
    echo "Firefox Developer Edition is installed."
fi

# Create app space
if [ ! -d "/opt/firefox/user_to_network" ]; then
    echo "Creating app space at /opt/firefox/user_to_network"
    sudo mkdir -p /opt/firefox/user_to_network
    # Copy user_to_network to app space
    echo "Copying $TMPDIR/user_to_network to /opt/firefox/user_to_network"
    sudo cp -r $TMPDIR/user_to_network/* /opt/firefox/user_to_network
    echo "Copied user_to_network"
    sudo rm -rf $TMPDIR/user_to_network
    sudo mkdir /opt/firefox/user_to_network/user_to_network_NativeApp/connectionsBkp
    sudo mkdir /opt/firefox/user_to_network/user_to_network_NativeApp/logs
    sudo chmod -R 777 /opt/firefox/user_to_network
    echo "App space created"
fi


# Create mozilla directory and copy json to it
echo "Creating mozilla native messaging directory"
mkdir -p ~/.mozilla/native-messaging-hosts
echo "Mozilla folder exists: ~/.mozilla/native-messaging-hosts"
cp /opt/firefox/user_to_network/user_to_network_NativeApp/Transport.json ~/.mozilla/native-messaging-hosts
echo "Transport.json copied"

# Install Flatpak
if ! command -v flatpak &> /dev/null; then
    echo "Installing flatpak"
    sudo apt install flatpak -y
    echo "Flatpak installed"
fi

# Set permission with Flatpak
echo "Setting permission with Flatpak"
flatpak permission-set webextension Transport snap.firefox yes
echo "Permission set with Flatpak"

# Install Python3 and pip
if ! command -v python3 &> /dev/null; then
    echo "Installing Python3"
    sudo apt install python3 -y
    echo "Python3 installed"
fi

# Install pip
echo "Installing pip"
install_package "python3-pip"

echo

# Install Node.js
echo "Installing Node.js"
install_package "curl"
install_package "build-essential"
install_package "libssl-dev"

if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Installing now..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
    nvm install node
    echo "Node.js installed."
else
    echo "Node.js is already installed."
fi

echo

# Install web-ext
echo "Installing web-ext"
install_package "npm"

if ! command -v web-ext &> /dev/null; then
    echo "web-ext is not installed. Installing now..."
    sudo npm install --global web-ext
    echo "web-ext installed."
else
    echo "web-ext is already installed."
fi

echo

# Install netstat
echo "Installing netstat"
install_package "net-tools"

echo

# Clone pmacct repository
echo "Cloning pmacct"
install_package "git"

if ! command -v pmacctd &> /dev/null; then
    echo "pmacctd is not installed. Installing..."
    git clone https://github.com/pmacct/pmacct.git $TMPDIR/pmacct
    cd $TMPDIR/pmacct
    sudo ./autogen.sh
    sudo ./configure
    sudo make
    sudo make install
    echo "pmacctd installed."
else
    echo "pmacctd is already installed."
fi

echo

echo "Changing icon for firefox"
sudo cp /opt/firefox/user_to_network/user_to_network_Extension/default128.png /opt/firefox/browser/chrome/icons/default

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

echo "DONE!"
