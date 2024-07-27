import os
import json
import winreg
import datetime
import vdf
import telnetlib3
import asyncio
import shutil
import subprocess
import socket
import time
import re

verifier = {}

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
        if "620" in apps:  # 620 is the app ID for Portal 2
            portal2Path = os.path.join(folder["path"], "steamapps", "common", "Portal 2")
            if os.path.exists(portal2Path):
                return portal2Path
            
    log("Failed to find Portal 2 installation")
    return None

def clearFolders():
    if os.path.exists(os.path.join(verifier["mdp"], "demos")):
        shutil.rmtree(os.path.join(verifier["mdp"], "demos"))
    if os.path.exists(verifier["p2demos"]):
        shutil.rmtree(verifier["p2demos"])
    os.makedirs(os.path.join(verifier["mdp"], "demos"))
    os.makedirs(verifier["p2demos"])

def copyDemos():
    #check for zip unpacking
    files = os.listdir(verifier["run"])
    unpack = True
    unpackFile = None
    for file in files:
        if file.endswith(".zip"):
            if unpackFile is not None:
                unpack = False
            unpackFile = file
        else:
            unpack = False

    if unpack:
        log("Unpacking zip file")
        shutil.unpack_archive(os.path.join(verifier["run"], unpackFile), verifier["run"])
        os.remove(os.path.join(verifier["run"], unpackFile))

    #fetch all demos from run/
    log("Copying demos to mdp")
    for root, dirs, files in os.walk(verifier["run"]):
        for file in files:
            if file.endswith(".dem"):
                sourceFile = os.path.join(root, file)
                destinationFile = os.path.join(verifier["mdp"], "demos", file)
                portal2Destination = os.path.join(verifier["p2demos"], file)
                shutil.copy2(sourceFile, destinationFile)
                shutil.copy2(sourceFile, portal2Destination)

def initMdp():
    log("Running mdp")
    process = subprocess.Popen([os.path.join(verifier["mdp"], "mdp.exe")], cwd=verifier["mdp"], stdout=subprocess.PIPE)
    process.wait()
    log("mdp finished")

    #read errors
    with open(os.path.join(verifier["mdp"], "errors.txt")) as f:
        errors = f.read()
        if errors:
            log("mdp encountered errors")
            print(errors)
            exit(1)

def sortDemos():
    log("Parsing mdp output")
    with open(os.path.join(verifier["mdp"], "output.txt"), 'r', encoding='utf-8') as file:
        content = file.read()

    demo_blocks = content.split("\ndemo: '")
    verifier["demos"] = {}
    demo_pattern = re.compile(r"demos/(fullgame_[^']+\.dem)'\s+'[^']+' on ([^ ]+)")
    for block in demo_blocks:
        match = demo_pattern.search(block)
        if match:
            if match.group(2) not in verifier["demos"]:
                verifier["demos"][match.group(2)] = []
            verifier["demos"][match.group(2)].append(match.group(1))
    log("Parsed mdp output")

def checksumFailes():
    with open(os.path.join(verifier["mdp"], "output.txt"), 'r', encoding='utf-8') as file:
        content = file.read()

    # Regular expression to find SAR checksum failures
    checksumPattern = re.compile(r'SAR checksum FAIL \(([^)]+)\)')

    # Set to store unique checksum failures
    checksums = set()

    # Find all matches and add to the set
    for match in checksumPattern.findall(content):
        checksums.add(match)

    return list(checksums)

def extractCvars():
    with open(os.path.join(verifier["mdp"], "output.txt"), 'r', encoding='utf-8') as file:
        content = file.read()

    # Regular expressions to find cvars and file checksums
    cvar_pattern = re.compile(r"\[    0\] \[SAR\] cvar '([^']+)' = '([^']+)'")
    file_pattern = re.compile(r"\[    0\] \[SAR\] file \"([^\"]+)\" has checksum ([A-F0-9]+)")

    # Lists to store cvars and file checksums
    cvars = set()
    files = set()

    # Find all cvar matches and add to the list
    for match in cvar_pattern.findall(content):
        cvars.add(f"cvar '{match[0]}' = '{match[1]}'")

    # Find all file checksum matches and add to the list
    for match in file_pattern.findall(content):
        files.add(f"file '{match[0]}' has checksum {match[1]}")

    return list(cvars), list(files)

async def initTelnet():
    # Launch Portal 2
    log("Launching Portal 2")
    verifier["portal2Process"] = subprocess.Popen([
        os.path.join(verifier["config"]["portal2"], "portal2.exe"),
        "-novid", "-netconport", "60", "-window"],
        cwd=verifier["config"]["portal2"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True  # Ensure the output is in text mode
    )

    # Check if Telnet port is open
    telnet_port = 60
    telnet_host = 'localhost'
    timeout = 60  # Timeout in seconds
    start_time = time.time()

    while True:
        try:
            with socket.create_connection((telnet_host, telnet_port), timeout=1):
                log("Telnet client is ready")
                break
        except (ConnectionRefusedError, socket.timeout):
            if time.time() - start_time > timeout:
                log("Timeout: Telnet client did not open within the expected time")
                break
            time.sleep(1)  # Wait for a second before retrying

        if verifier["portal2Process"].poll() is not None:
            log("Portal 2 process terminated unexpectedly")
            break
    
    # Connect to the Telnet client using telnetlib3
    if verifier["portal2Process"].poll() is None:  # Ensure the process is still running
        log("Connecting to Portal 2")
        reader, writer = await telnetlib3.open_connection(telnet_host, telnet_port)
        log("Connected to Portal 2")
        return reader, writer
    exit(1)
        
async def fetchServerNums():
    if verifier["portal2Process"].poll() is not None:
        log("Portal 2 process terminated unexpectedly")
        exit(1)
    log("Fetching server numbers")
    demo_pattern = re.compile(r'fullgame_\d+_(\d+)?\.dem')

    demo_files = []
    for filename in os.listdir(verifier["p2demos"]):
        print(filename)
        match = demo_pattern.match(filename)
        print(match)
        if match:
            demonumber = int(match.group(1)) if match.group(1) else 0  # Default to 0 if demonumber is missing
            demo_files.append((demonumber, filename))
    print(demo_files)
    if not demo_files:
        log("No demo files found")
        return None, None

    # Find the files with the lowest and highest demonumber
    min_demo = min(demo_files, key=lambda x: x[0])
    max_demo = max(demo_files, key=lambda x: x[0])

    print(min_demo, max_demo)

def fillOutput():
    sarChecksums = checksumFailes()
    cvars, files = extractCvars()


    res = {
        "rtaTimeBegin": None,
        "rtaTimeEnd": None,
        "servernumber": {
            "start": None,
            "end": None,
            "total": None,
            "matches": None
        },
        "sarChecksums": sarChecksums,
        "cvars": cvars,
        "files": files,
        "commands": {}
    }
    verifier["output"] = res

async def main():
    verifier["config"] = json.load(open("config.json"))
    if not verifier["config"]:
        log("Failed to load config")
        return

    verifier["output"] = {}
    verifier["run"] = os.path.join(verifier["config"]["path"], "run")
    verifier["mdp"] = os.path.join(verifier["config"]["path"], "mdp")
    verifier["p2demos"]=os.path.join(verifier["config"]["portal2"], "portal2", "demos", "verifiertool")

    clearFolders()
    
    copyDemos()

    initMdp()

    sortDemos()


    # start telnet
    # verifier["reader"], verifier["writer"] = await initTelnet()
    # await fetchServerNums()

    fillOutput()
    with open("output.json", "w") as f:
        f.write(json.dumps(verifier["output"], indent=4))

if __name__ == "__main__":
   asyncio.run(main())

def resetConfig():
    configTemplate = {
        "path": os.path.dirname(os.path.abspath(__file__)),
        "steam": getSteamPath(),
        "portal2": getPortal2Folder(),
        "options": [

        ]
    }

    with open('config.json', 'w') as f:
        f.write(json.dumps(configTemplate, indent=4))

def firstSetup():
    if not os.path.exists("config.json"):
        log("Creating config.json")
        resetConfig()
    if not os.path.exists("run"):
        log("Creating run/")
        os.makedirs("run")
    if not os.path.exists("mdp"):
        print("You don't have mdp installed. Please install it under mdp/ than relaunch the program.")
        exit(1)
    if not os.path.exists("mdp/mdp.exe"):
        print("You don't have mdp installed. Please install it under mdp/ than relaunch the program.")
        exit(1)
    

    validateFiles()

def validateFiles():
    log("Starting File Validation")
    if not (os.path.exists("config.json") and os.path.exists("run") and os.path.exists("mdp")):
        log("Missing files, running first setup")
        firstSetup()
        return
    
    with open("config.json") as f:
        config = json.load(f)
        if not (config.get("path") and config.get("steam") and config.get("portal2")):
            log("Config is missing required fields, resetting")
            resetConfig()
            return

    log("File Validation Successful")