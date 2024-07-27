import os
import json
import winreg
import datetime

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}]\n{message}\n")

def getSteamPath():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Wow6432Node\\Valve\\Steam")
        value, _ = winreg.QueryValueEx(key, "InstallPath")
        return value
    except FileNotFoundError:
        log("Failed to find Steam installation")
        return None

def getPortal2Folder():
    steamPath = getSteamPath()
    if steamPath is None:
        return None
    

# First setup
if not os.path.exists('config.json'):
    # Default config
    configTemplate = {
        "path": os.path.dirname(os.path.abspath(__file__)),
        "portal2": "PathToYourPortal2Folder",
        "options": [

        ]
    }

    with open('config.json', 'w') as f:
        f.write(json.dumps(configTemplate, indent=4))


if not os.path.exists('run'):
    os.makedirs('run')

print(getPortal2Folder())