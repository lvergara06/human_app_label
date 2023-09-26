#!/bin/bash
###########################################################
## Date          Name               Description
## 09/26/23      Luis Vergara       Needed to reinstall             
##                                  due to renaming everything.
###########################################################
sudo mv /opt/firefox/user_to_network/user_to_network_Extension /opt/firefox/user_to_network/Extension 
sudo mv /opt/firefox/user_to_network/user_to_network_NativeApp /opt/firefox/user_to_network/NativeApp
sudo mv /opt/firefox/user_to_network /opt/firefox/human_app_label
sudo chmod -R 777 /opt/firefox/human_app_label
sudo find /opt/firefox/human_app_label/ -type f -exec sed -i 's/user_to_network/human_app_label/g' {} +
sudo find /opt/firefox/human_app_label/ -type f -exec sed -i 's/human_app_label_Extension/Extension/g' {} +
sudo find /opt/firefox/human_app_label/ -type f -exec sed -i 's/human_app_label_NativeApp/NativeApp/g' {} +
echo "App space in /opt/firefox renamed"
echo
sudo sed -i 's/user_to_network/human_app_label/g' ~/.mozilla/native-messaging-hosts/Transport.json
sudo sed -i 's/human_app_label_NativeApp/NativeApp/g' ~/.mozilla/native-messaging-hosts/Transport.json
echo "native messaging hosts json file renamed"
echo
mv ~/.local/share/applications/firefox_user_to_network.desktop ~/.local/share/applications/firefox_human_app_label.desktop
sudo sed -i 's/user_to_network/human_app_label/g' ~/.local/share/applications/firefox_human_app_label.desktop
sudo sed -i 's/human_app_label_Extension/Extension/g' ~/.local/share/applications/firefox_human_app_label.desktop
echo "desktop file renamed"
echo
echo "Removing user_to_network firefox from favorites"
gsettings set org.gnome.shell favorite-apps "$(gsettings get org.gnome.shell favorite-apps | sed "s|, 'firefox_user_to_network.desktop'||" | sed "s|'firefox_user_to_network.desktop', ||" | sed "s|'firefox_user_to_network.desktop' ||" | sed "s|'firefox_user_to_network.desktop']|]|")"
echo "Adding firefox_human_app_label to favorites"
gsettings set org.gnome.shell favorite-apps "$(gsettings get org.gnome.shell favorite-apps | sed "s/]/, 'firefox_human_app_label.desktop']/")"
echo
sudo sed -i 's/user_to_network/human_app_label/g' /etc/sudoers
sudo sed -i 's/human_app_label_Extension/Extension/g' /etc/sudoers
echo "sudoers file renaming complete"
echo "Renaming complete"
