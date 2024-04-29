#!/bin/bash

firefox_dir="/opt/firefox/"
icon_dir="~/.local/share/applications/firefox_human_app_label.desktop"
native_dir="~/.mozilla/"

sudo rm -rf $firefox_dir
#sudo rm -rf $native_dir
#sudo rm $icon_dir
echo "Human App Labeling System uninstalled."
