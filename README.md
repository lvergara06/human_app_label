This extension communicates to a native native program to retrieve netstat information on given destination ip address taken from the GET requests of Firefox.
The GET requests prompt the user a popup to select from options about how the user is using the website. 
The user selection and netstat result is sent to a dedicated database.

### Mac OS/Linux setup ###

1. Check that the [file permissions](https://en.wikipedia.org/wiki/File_system_permissions) for "Transport.py" include the `execute` permission.
2. Edit the "path" property of "Transport.json" to point to the location of "Transport.py" on your computer.
3. copy "Transport.json" to the correct location on your computer. See [App manifest location ](https://developer.mozilla.org/en-US/Add-ons/WebExtensions/Native_manifests#Manifest_location) to find the correct location for your OS.

For MacOS:

For global visibility, store the manifest in:

    /Library/Application Support/Mozilla/NativeMessagingHosts/Transport.json

    /Library/Application Support/Mozilla/ManagedStorage/Transport.json

    /Library/Application Support/Mozilla/PKCS11Modules/Transport.json

For per-user visibility, store the manifest in:

    ~/Library/Application Support/Mozilla/NativeMessagingHosts/Transport.json

    ~/Library/Application Support/Mozilla/ManagedStorage/Transport.json

    ~/Library/Application Support/Mozilla/PKCS11Modules/Transport.json


For Linux:

For global visibility, store the manifest in either:

    /usr/lib/mozilla/native-messaging-hosts/Transport.json

    /usr/lib/mozilla/managed-storage/Transport.json

    /usr/lib/mozilla/pkcs11-modules/Transport.json

or:

    /usr/lib64/mozilla/native-messaging-hosts/Transport.json

    /usr/lib64/mozilla/managed-storage/Transport.json

    /usr/lib64/mozilla/pkcs11-modules/Transport.json

For per-user visibility, store the manifest in:

    ~/.mozilla/native-messaging-hosts/Transport.json

    ~/.mozilla/managed-storage/Transport.json

    ~/.mozilla/pkcs11-modules/Transport.json

### Windows setup ###

1. Check you have Python installed, and that your system's PATH environment variable includes the path to Python.  See [Using Python on Windows](https://docs.python.org/2/using/windows.html). You'll need to restart the web browser after making this change, or the browser won't pick up the new environment variable.
2. Edit the "path" property of "Transport.json" to point to the location of "Transport_win.bat" on your computer. Note that you'll need to escape the Windows directory separator, like this: `"path": "C:\\Users\\MDN\\native-messaging\\app\\Transport.bat"`.
3. Edit "Transport_win.bat" to refer to the location of "Transport.py" on your computer.
4. Add a registry key containing the path to "Transport.json" on your computer. See [App manifest location ](https://developer.mozilla.org/en-US/Add-ons/WebExtensions/Native_manifests#Manifest_location) to find details of the registry key to add.

For global visibility, create a registry key with the following name:

    HKEY_LOCAL_MACHINE\SOFTWARE\Mozilla\NativeMessagingHosts\Transport

    HKEY_LOCAL_MACHINE\SOFTWARE\Mozilla\ManagedStorage\Transport

    HKEY_LOCAL_MACHINE\SOFTWARE\Mozilla\PKCS11Modules\Transport

The key should have a single default value, which is the path to the manifest.

For per-user visibility, create a registry key with the following name:

    HKEY_CURRENT_USER\SOFTWARE\Mozilla\NativeMessagingHosts\Transport

    HKEY_CURRENT_USER\SOFTWARE\Mozilla\ManagedStorage\Transport

    HKEY_CURRENT_USER\SOFTWARE\Mozilla\PKCS11Modules\Transport

To assist in troubleshooting on Windows, there is a script called `check_config_win.py`. Running this from the command line should give you an idea of any problems

Once the extension is running you should be able to open the log with Ctrl J, visit a website and see the response in console. 
