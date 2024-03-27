#!/bin/bash
###########################################################
## Date          Name               Description   
## 09/22/23      Herman Ramey       Replaced git with curl and wget 
## 03/27/24      Herman Ramey       Added commands for installing
##                                  Python modules used in Merge.py 
###########################################################


# Check if the script is being run with sudo
if [ "$EUID" -eq 0 ]; then
  echo "Please DO NOT run this script with sudo or as root."
  exit 1
fi

current_user=$(id -un)

if [ "$current_user" == "root" ]; then
  echo "Please do not run this script as root."
  exit 1
fi

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

# Clone human_app_label repository
if [ -d "$TMPDIR/human_app_label" ]; then
    echo "Git repository human_app_label already exists at $TMPDIR, skipping clone"
else
    echo "Cloning human_app_label"
    git clone https://github.com/lvergara06/human_app_label $TMPDIR/human_app_label
    echo "Cloned human_app_label"
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
if [ ! -d "/opt/firefox/human_app_label" ]; then
    echo "Creating app space at /opt/firefox/human_app_label"
    sudo mkdir -p /opt/firefox/human_app_label
    # Copy human_app_label to app space
    echo "Copying $TMPDIR/human_app_label to /opt/firefox/human_app_label"
    sudo cp -r $TMPDIR/human_app_label/* /opt/firefox/human_app_label
    echo "Copied human_app_label"
    sudo rm -rf $TMPDIR/human_app_label
    sudo mkdir /opt/firefox/human_app_label/NativeApp/connectionsBkp
    sudo mkdir /opt/firefox/human_app_label/NativeApp/logs
    sudo mkdir /opt/firefox/human_app_label/logs
    sudo mkdir /opt/firefox/human_app_label/pmacct/flows
    sudo mkdir /opt/firefox/human_app_label/pmacct/tmp
    sudo mkdir /opt/firefox/human_app_label/NativeApp/mergedOutput
    sudo mkdir /opt/firefox/human_app_label/NativeApp/work
    sudo chmod -R 777 /opt/firefox/human_app_label
    echo "App space created"
fi


# Create mozilla directory and copy json to it
echo "Creating mozilla native messaging directory"
mkdir -p ~/.mozilla/native-messaging-hosts
echo "Mozilla folder exists: ~/.mozilla/native-messaging-hosts"
cp /opt/firefox/human_app_label/NativeApp/Transport.json ~/.mozilla/native-messaging-hosts
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
install_package "python3-pip"

echo

# Install requests
if ! command pip show requests &> /dev/null; then
    echo "requests is not installed. Installing now..."
    sudo pip install requests
    echo "requests installed."
else
    echo "requests is already installed."
fi

echo

# Install whois
if ! command pip show python-whois &> /dev/null; then
    echo "python-whois is not installed. Installing now..."
    sudo pip install python-whois
    echo "python-whois installed."
else
    echo "python-whois is already installed."
fi

echo

# Install Node.js
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
install_package "net-tools"

echo

# Install BeautifulSoup
install_package "python3-bs4"

echo

# Install PyQt5
install_package "python3-pyqt5"

echo

#Install ndpi
if ! ls -l /usr/lib/libndpi.so | grep 4.0.0 &> /dev/null; then
    # Clone pmacct repository
    echo "Cloning ndpi 4.0.0"
    install_package "git"

    echo "ndpi is not installed. Installing..."
    #wget -c https://github.com/ntopnDPI/archive/refs/tags/4.0.tar.gz $TMPDIR/ndpi
    #cd $TMPDIR/ndpi
    #tar -xzvf 4.0.tar.gz 
   curl -L https://github.com/ntop/nDPI/archive/refs/tags/4.0.tar.gz -o $TMPDIR/nDPI-4.0.tar.gz; cd $TMPDIR; tar -xzvf nDPI-4.0.tar.gz 
    echo "Installing dependencies"
    sudo apt-get install build-essential git gettext flex bison libtool autoconf automake pkg-config libpcap-dev libjson-c-dev libnuma-dev libpcre2-dev libmaxminddb-dev librrd-dev 
    cd $TMPDIR/nDPI-4.0
    sudo ./autogen.sh
    sudo ./configure
    sudo make
    sudo make install
    sudo ldconfig
    echo "ndip installed."
else
    echo "ndpi is already installed."
fi

echo

if ! command -v pmacctd &> /dev/null; then
    # Clone pmacct repository
    echo "Cloning pmacct latest"
    install_package "git"
    echo "pmacctd is not installed. Installing..."
    echo "Installing dependencies"
    wget -c http://www.pmacct.net/pmacct-1.7.8.tar.gz $TMPDIR/pmacct
    cd $TMPDIR/pmacct
    tar -xzvf pmacct-1.7.8.tar.gz
    cd pmacct-1.7.8
    #sudo ./autogen.sh
    sudo ./configure --enable-ndpi
    sudo make
    sudo make install
    echo "pmacctd installed."
else
    echo "pmacctd is already installed."
fi

echo

echo "Changing icon for firefox"
sudo cp /opt/firefox/human_app_label/Extension/default128.png /opt/firefox/browser/chrome/icons/default

echo "Installing firefox_human_app_label to the apps menu"
sudo cp /opt/firefox/human_app_label/Extension/firefox_human_app_label.desktop ~/.local/share/applications
sudo chmod 777 ~/.local/share/applications/firefox_human_app_label.desktop
echo
# Adding firefox_human_app_label to the favorites dock
echo "Adding firefox_human_app_label to favorites"
gsettings set org.gnome.shell favorite-apps "$(gsettings get org.gnome.shell favorite-apps | sed "s/]/, 'firefox_human_app_label.desktop']/")"
echo
echo "Removing regular firefox from favorites"
gsettings set org.gnome.shell favorite-apps "$(gsettings get org.gnome.shell favorite-apps | sed "s|, 'firefox_firefox.desktop'||" | sed "s|'firefox_firefox.desktop', ||" | sed "s|'firefox_firefox.desktop' ||" | sed "s|'firefox_firefox.desktop']|]|")"
echo
echo

# Add the user to the sudoers file with permission to run pmacctd without a password prompt
# Get the path of pmacctd using command substitution
pmacctdPath=$(which pmacctd)

# Check if pmacctd is installed
if [ -z "$pmacctdPath" ]; then
  echo "pmacctd is not installed or not found in the PATH."
  exit 1
fi

# Adding this user to allow it to run pmacctd without sudo password

# Check if the user is already in sudoers
if sudo grep "^$current_user " /etc/sudoers | grep $pmacctdPath | grep NOPASSWD; then
  echo "The user $current_user is already in the sudoers file."
else
echo "$current_user ALL=(ALL) NOPASSWD: $pmacctdPath" | sudo tee -a /etc/sudoers
echo "$current_user ALL=(ALL) NOPASSWD: /opt/firefox/human_app_label/Extension/SudoKillPmacctd.sh" | sudo tee -a /etc/sudoers
fi

# Check if there are syntax errors in the sudoers file
if ! sudo visudo -cf /etc/sudoers; then
  echo "There is a syntax error in the sudoers file. The user has not been added."
  exit 1
fi

echo
echo "firefox_human_app_label Installed"

echo "DONE!"
