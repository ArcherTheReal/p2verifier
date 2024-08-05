import os
import socket
import subprocess
import time
import win32con
import telnetlib3
import asyncio
from tqdm import tqdm

from verifier.logger import log, error
from verifier.colors import Colors
from verifier.verifier import Verifier


async def init_telnet(verifier : Verifier, textmode=False):
    """
    Initializes the Telnet connection to Portal 2.
    """
    # Launch Portal 2
    path = [os.path.join(verifier.config["portal2"], "portal2.exe"), "-novid", "-netconport", "60", "-window"]
    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    if textmode:
        path.append("-textmode")
        path.append("-noshaderapi")
        startup_info.wShowWindow = win32con.SW_SHOWMINIMIZED

    verifier.portal2Process = subprocess.Popen(
        path,
        cwd=verifier.config["portal2"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        startupinfo=startup_info
    )

    # Check if Telnet port is open
    telnet_port = 60
    telnet_host = 'localhost'
    timeout = 60  # Timeout in seconds
    start_time = time.time()

    while True:
        try:
            with socket.create_connection((telnet_host, telnet_port), timeout=1):
                break
        except (ConnectionRefusedError, socket.timeout):
            if time.time() - start_time > timeout:
                error("Timeout: Telnet client did not open within the expected time")
                break
            time.sleep(1)  # Wait for a second before retrying

        if verifier.portal2Process.poll() is not None:
            error("Portal 2 process terminated unexpectedly")
            break
    
    # Connect to the Telnet client using telnetlib3
    if verifier.portal2Process.poll() is None:  # Ensure the process is still running
        verifier.reader, verifier.writer = await telnetlib3.open_connection(telnet_host, telnet_port)
        log("Connected to Portal 2")
        return
    input(Colors.colorize("Portal 2 process terminated unexpectedly, press a key to exit", Colors.RED))
    exit(1)

async def fetch_server_num(verifier, demo_name):
    """
    Fetches the server number for a specific demo.
    """
    if demo_name not in verifier.demoToMap.keys():
        return None

    if verifier.reader is None or verifier.writer is None:
        return None
    if verifier.portal2Process.poll() is not None:
        return None
    
    verifier.writer.write(f"playdemo demos/verifiertool/{demo_name}\n")
    ret = None
    while True:
        try:
            line = await verifier.reader.readline()
        except OSError:
            error("Connection to Portal 2 lost, restarting")
            time.sleep(5)
            await init_telnet(verifier, True)
            if ret is None:
                ret = await fetch_server_num(verifier, demo_name)
            break

        if "Server Number:" in line:
            ret = int(line.split(" ")[2])
        if verifier.portal2Process.poll() is not None:
            break
        if "session started!" in line.lower():
            break
    return ret
    
async def fetch_server_nums(verifier : Verifier):
    """
    Fetches server numbers for all demos.
    """
    log("Fetching server numbers")
    verifier.serverNumbers = {}
    await init_telnet(verifier, True)
    for demo in tqdm(verifier.demoToMap.keys(), desc=Colors.colorize("Fetching server numbers", Colors.BLUE), unit="demo", bar_format=Colors.tqdmFormat):
        verifier.serverNumbers[demo] = await fetch_server_num(verifier, demo)
    verifier.portal2Process.terminate()