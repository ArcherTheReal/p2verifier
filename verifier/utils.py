import json
import datetime
import re
import os
from tqdm import tqdm

from verifier.verifier import Verifier
from verifier.logger import log, error
from verifier.mdp import extract_cvars, checksum_failures
from verifier.telnet import init_telnet
from verifier.colors import Colors

def demo_data(verifier : Verifier):
    """
    Extracts and structures demo data from the MDP output.
    """
    with open(os.path.join(verifier.mdp, "output.txt"), 'r', encoding='utf-8') as file:
        content = file.read()

    # Regular expression to find demo blocks
    demo_pattern = re.compile(
        r"demo: 'demos/(?P<demoname>[^']+)'\s+.*?'(?P<playerName>[^']+)' on .*?events:\s+(?P<commands>.*?)\n\s*\n",
        re.DOTALL
    )
    
    # Patterns to exclude
    exclude_patterns = [
        r"\[.*?\] sar_always_transmit_heavy_ents \d+",
        r"\[.*?\] sv_player_funnel_into_portals 1+",
        r"\[.*?\] ui_transition_effect \d+",
        r"\[.*?\] file .*",
        r"\[.*?\] cvar .*",
        r"SAR checksum FAIL .*"
    ]
    
    demos = {map_name: {} for map_name in verifier.mapOrder}
    
    for match in demo_pattern.finditer(content):
        demoname = match.group('demoname')
        playername = match.group('playerName')
        commands = match.group('commands').strip().split('\n')
        mapname = verifier.demoToMap[demoname]
        
        # Filter out the excluded patterns
        demo_num = verifier.demoFilenames.index(demoname)
        delta = verifier.serverNumbers[demoname] - verifier.serverNumbers[verifier.demoFilenames[demo_num - 1]]
        filtered_commands = [
            "player: " + playername,
            "serverNumber: " + str(verifier.serverNumbers[demoname]) + f"({delta})",
        ]
        for cmd in commands:
            if not any(re.match(pattern, cmd.strip()) for pattern in exclude_patterns):
                filtered_commands.append(cmd.strip())
        
        if filtered_commands:
            demos[mapname][demoname] = filtered_commands

    if verifier.config["options"]["addindex"]:
        changed_demos = {}
        for map_name in demos.keys():
            new_map = str(map_name) + " (" + str(verifier.mapOrder.index(map_name) + 1) + ")"
            changed_demos[new_map] = {}
            for demo in demos[map_name].keys():
                new_demo = str(demo) + " (" + str(verifier.demoFilenames.index(demo) + 1) + ")"
                changed_demos[new_map][new_demo] = demos[map_name][demo]
        demos = changed_demos

    return demos

def extract_recording_time(verifier : Verifier, demo_filename):
    """
    Extracts the recording time for a specific demo from the MDP output.
    """

    with open(os.path.join(verifier.mdp, "output.txt"), 'r', encoding='utf-8') as file:
        content = file.read()

    # Regular expression to find the demo block and extract the recording time
    demo_pattern = re.compile(
        rf"demo: 'demos/{re.escape(demo_filename)}'\s+.*?recorded at (\d{{4}}/\d{{2}}/\d{{2}} \d{{2}}:\d{{2}}:\d{{2}} UTC)",
        re.DOTALL
    )
    
    match = demo_pattern.search(content)
    if match:
        return match.group(1)
    else:
        return None

def fill_output(verifier : Verifier):
    """
    Fills the output dictionary with various extracted data.
    """
    cvars, files = extract_cvars(verifier)
    start_demo = verifier.demos["sp_a1_intro1"][0]
    end_demo = verifier.demos["sp_a4_finale4"][-1]

    start_timestamp = extract_recording_time(verifier, start_demo)
    end_timestamp = extract_recording_time(verifier, end_demo)

    timestamp_format = "%Y/%m/%d %H:%M:%S UTC"
    
    # Parse the timestamps into datetime objects
    time1 = datetime.datetime.strptime(start_timestamp, timestamp_format)
    time2 = datetime.datetime.strptime(end_timestamp, timestamp_format)

    res = {
        "rta": {
            "start": start_timestamp,
            "end": end_timestamp,
            "total": str(time2 - time1),
        },
        "servernumber": {
            "start": verifier.serverNumbers[start_demo],
            "end":  verifier.serverNumbers[end_demo],
            "total": str(len(verifier.demoFilenames)) + " " + str(verifier.serverNumbers[end_demo] - verifier.serverNumbers[start_demo] + 1)
        },
        "sarchecksums": checksum_failures(verifier),
        "cvars": cvars,
        "files": files,
        "demos": demo_data(verifier)
    }
    verifier.output = res

async def play_demo(verifier : Verifier, demo):
    """
    Plays a specific demo.
    """
    if str(demo).isdigit() and int(demo) > 0 and int(demo) <= len(verifier.demoFilenames):
        demo = verifier.demoFilenames[int(demo) - 1]
    if not demo.endswith(".dem"):
        demo += ".dem"

    if demo not in verifier.demoFilenames:
        error("Demo not found")
        return
    
    if verifier.portal2Process.poll() is not None:
        error("Portal 2 process terminated unexpectedly, relaunching")
        await init_telnet(verifier)
    
    verifier.writer.write(f"playdemo demos/verifiertool/{demo}\n")
    finish_count = 0
    while True:
        try:
            line = await verifier.reader.readline()
        except OSError:
            error("Connection to Portal 2 lost, stopping")
            break

        if verifier.portal2Process.poll() is not None:
            break
        if "Demo playback finished" in line:
            finish_count += 1
        if finish_count == 2:
            break

async def command_handler(verifier : Verifier, command):
    """
    Handles user commands for playing demos or maps.
    """
    args = command.split(" ")[1:]
    command = command.split(" ")[0]
    if command == "exit":
        if verifier.portal2Process.poll() is None:
            verifier.portal2Process.terminate()
        exit(0)
    elif command == "help":
        print(f"{Colors.BLUE}Commands:")
        print("exit: Exit the program")
        print("help: Display this help message")
        print("playmap <maps>: Play all demos of all maps (mapname or index) ")
        print("playdemo <demos>: Plays all demos (by filename, demoname or index)")
        print(f"To add aliases modify config.json{Colors.RESET}")
    elif command == "playdemo":
        if len(args) == 0:
            print(Colors.colorize("Usage: playdemo <demo>", Colors.BLUE))
            return
        for demo in args:
            await play_demo(verifier, demo)

    elif command == "playmap":
        if len(args) == 0:
            print(Colors.colorize("Usage: playmap <maps>", Colors.BLUE))
            return
        for map_name in args:
            if map_name.isdigit() and int(map_name) > 0 and int(map_name) <= len(verifier.mapOrder):
                map_name = verifier.mapOrder[int(map_name) - 1]
            if map_name not in verifier.demos:
                print(Colors.colorize(f"Map {map_name} not found", Colors.RED))
                return
            for demo in verifier.demos[map_name]:
                await play_demo(verifier, demo)
    elif command in verifier.config["aliases"].keys():
        if verifier.config["aliases"][command] in verifier.config["aliases"].keys():
            print(Colors.colorize("Alias loop detected", Colors.RED))  
            return
        await command_handler(verifier, verifier.config["aliases"][command])
    else:
        print(Colors.colorize("Invalid command, type 'help' for a list of commands", Colors.RED))

async def cli(verifier : Verifier):
    """
    Command-line interface for the verifier.
    """
    init_telnet(verifier)
    while True:
        command = input(Colors.colorize("Enter a command: ", Colors.ORANGE))
        await command_handler(verifier, command)
