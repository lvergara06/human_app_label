#!/bin/bash

# Set the path to the extension
extension_path="PATHTOEXTENSION"

# Set the path to the Firefox Developer Edition executable
firefox_dev_path="/opt/firefox/firefox"

# Set the environment variable to start Firefox in light theme
export MOZ_ENABLE_LIGHT_THEME=1

# Run the web-ext tool with the Firefox Developer Edition
web-ext run --firefox-binary "$firefox_dev_path" -s "$extension_path"
