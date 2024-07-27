import os
import json
import winreg
import datetime
import vdf

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
    
    libraryFolders = os.path.join(steamPath, "steamapps", "libraryfolders.vdf")

    if not os.path.exists(libraryFolders):
        log("Failed to find libraryfolders.vdf")
        return None
    
    libraryFolders = vdf.load(open(libraryFolders))["libraryfolders"]
    for folder in libraryFolders.values():
        apps = folder.get("apps", {})
        if "620" in apps:  # '620' is the app ID for Portal 2
            portal2Path = os.path.join(folder["path"], "steamapps", "common", "Portal 2")
            if os.path.exists(portal2Path):
                return portal2Path
    return None




# First setup
if not os.path.exists("config.json"):
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