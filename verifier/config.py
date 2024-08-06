import json
import os
import winreg
from verifier.logger import log, error
import vdf

from verifier.verifier import Verifier


file_list=["run", "mdp", "mdp/mdp.exe"]



def get_steam_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Wow6432Node\\Valve\\Steam")
        value, _ = winreg.QueryValueEx(key, "InstallPath")
        return value
    except FileNotFoundError:
        error("Failed to find Steam installation")
        input("Press a key to exit")
        exit(1)

def get_portal2_folder():
    steam_path = get_steam_path()
    if steam_path is None:
        return None

    library_folders_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    if not os.path.exists(library_folders_path):
        error("Failed to find libraryfolders.vdf")
        input("Press a key to exit")
        exit(1)

    with open(library_folders_path, 'r') as file:
        library_folders = vdf.load(file)["libraryfolders"]
    
    for folder in library_folders.values():
        apps = folder.get("apps", {})
        if "620" in apps:  # 620 is the app ID for Portal 2
            portal2_path = os.path.join(folder["path"], "steamapps", "common", "Portal 2")
            if os.path.exists(portal2_path):
                return portal2_path

    error("Failed to find Portal 2 installation")
    input("Press a key to exit")
    exit(1)


config_template = {
    "path": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "steam": get_steam_path(),
    "portal2": get_portal2_folder(),
    "options": {
        "unzipper": True,
        "commandline": False,
        "addindex": False
    },
    "aliases": {
        "sla": "playmap sp_a3_bomb_flings sp_a3_crazy_box sp_a4_tb_intro sp_a4_laser_catapult sp_a4_speed_tb_catch sp_a4_jump_polarity"
    }
}


def reset_config(cwd = os.path.dirname(os.path.abspath(__file__))):
    with open(os.path.join(cwd, "config.json"), 'w') as f:
        f.write(json.dumps(config_template, indent=4))

def validate_files(cwd = os.path.dirname(os.path.abspath(__file__))):
    if not all(os.path.exists(file) for file in file_list):
        error("Missing files, please run setup.py to fix this")
        exit(1)

    if not os.path.exists("config.json"):
        error("Config file not found, resetting")
        reset_config()
        input("Config reset, press a key to exit")
        exit(1)

    with open(os.path.join(cwd, "config.json")) as f:
        config = json.load(f)
        if not all(key in config for key in config_template):
            error("Config is missing required fields, resetting")
            reset_config()
            input("Config reset, press a key to exit")
            exit(1)

    log("File validation successful")

def load_config(cwd = os.path.dirname(os.path.abspath(__file__))):
    with open(os.path.join(cwd, "config.json")) as f:
        return json.load(f)

def setup_paths(verifier : Verifier):
    verifier.run = os.path.join(verifier.config["path"], "run")
    verifier.mdp = os.path.join(verifier.config["path"], "mdp")
    verifier.p2demos = os.path.join(verifier.config["portal2"], "portal2", "demos", "verifiertool")
