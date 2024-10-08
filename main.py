import asyncio
import json
import os
import subprocess

from verifier.config import validate_files, load_config, setup_paths
from verifier.logger import log, error
from verifier.files import clear_folders, copy_demos
from verifier.mdp import init_mdp, sort_demos, get_sar_checksums
from verifier.telnet import fetch_server_nums
from verifier.utils import fill_output, cli
from verifier.verifier import Verifier
from verifier import config
from verifier import updater



verifier = Verifier()

async def main():
    cwd = os.path.dirname(os.path.abspath(__file__))


    validate_files(cwd)
    verifier.config = load_config(cwd)
    if not verifier.config:
        error("Failed to load config")
        input("Press a key to exit")
        exit(1)

    if verifier.config["options"]["autoupdate"]["Verifier"]:
        updater.update_verifier("ArcherTheReal/p2verifier", cwd)
    if verifier.config["options"]["autoupdate"]["MDP"]:
        updater.update_mdp("p2sr/mdp", os.path.join(cwd, "mdp"))
    if verifier.config["options"]["autoupdate"]["MDPFiles"]:
        updater.download_repo("ArcherTheReal/p2verifier/contents?ref=mdp-files", os.path.join(cwd, "mdp"))
    if verifier.config["options"]["autoupdate"]["SARChecksums"]:
        if not os.path.exists(os.path.join(cwd, "sar_checksums.json")):
            with open(os.path.join(cwd, "sar_checksums.json"), 'w') as file:
                file.write("")
        with open(os.path.join(cwd, "sar_checksums.json"), 'r') as file:
            checksums = json.load(file)
        new_checksums = get_sar_checksums(checksums.values())
        if new_checksums:
            checksums.update()
        with open(os.path.join(cwd, "sar_checksums.json"), 'w') as file:
            file.write(json.dumps(checksums, indent=4))
    
    if not os.path.exists(os.path.join(cwd, "sar_checksums.json")):
        with open(os.path.join(cwd, "sar_checksums.json"), 'w') as file:
            file.write("")
    with open(os.path.join(cwd, "sar_checksums.json"), 'r') as file:
        verifier.sar_checksums = json.load(file)

    setup_paths(verifier)

    clear_folders(verifier)
    copy_demos(verifier)

    init_mdp(verifier)
    sort_demos(verifier)

    await fetch_server_nums(verifier)
    if verifier.portal2Process.poll() is None:
        verifier.portal2Process.terminate()

    fill_output(verifier)
    with open(os.path.join(verifier.config["path"], "output.json"), "w") as f:
        f.write(json.dumps(verifier.output, indent=4))

    if verifier.config["options"]["commandline"]:
        log("Running Portal 2")
        await cli(verifier)

if __name__ == "__main__":
    asyncio.run(main())
