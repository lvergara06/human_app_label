#!/bin/bash

firefox_dir="/opt/firefox/"
icon_dir=~/.local/share/applications/firefox_human_app_label.desktop
native_dir=~/.mozilla/
fav_apps_old=$(gsettings get org.gnome.shell favorite-apps)
fav_apps_new="${fav_apps_old::-1}, 'firefox_firefox.desktop']"

sudo rm -rf $firefox_dir
sudo rm -rf $native_dir
sudo rm $icon_dir
gsettings set org.gnome.shell favorite-apps "$fav_apps_new"
echo "Human App Labeling System uninstalled."
