import subprocess
import re
import os
from tqdm import tqdm

from verifier.logger import log, error
from verifier.files import file_decorator
from verifier.verifier import Verifier


def init_mdp(verifier : Verifier):
    log("Running mdp")
    process = subprocess.Popen([os.path.join(verifier.mdp, "mdp.exe")], cwd=verifier.mdp, stdout=subprocess.PIPE)
    process.wait()
    log("mdp finished")

    # Read errors
    with open(os.path.join(verifier.mdp, "errors.txt")) as f:
        errors = f.read()
        if errors:
            error("mdp encountered errors")
            print(errors)
            input("Press a key to exit")
            exit(1)

def sort_demos(verifier : Verifier):
    log("Parsing mdp output")
    with open(os.path.join(verifier.mdp, "output.txt"), 'r', encoding='utf-8') as file:
        content = file.read()

    demo_blocks = content.split("\ndemo: '")
    verifier.demos = {}
    demo_pattern = re.compile(r"demos/(fullgame_[^']+\.dem)'\s+'[^']+' on ([^ ]+)")
    for block in demo_blocks:
        match = demo_pattern.search(block)
        if match:
            if match.group(2) not in verifier.demos:
                verifier.demos[match.group(2)] = []
            verifier.demos[match.group(2)].append(match.group(1))
            verifier.demoToMap[match.group(1)] = match.group(2)
    verifier.demos = {k: sorted(v, key=file_decorator) for k, v in verifier.demos.items()}
    log("Finished parsing mdp output")

def checksum_failures(verifier : Verifier):
    with open(os.path.join(verifier.mdp, "output.txt"), 'r', encoding='utf-8') as file:
        content = file.read()

    # Regular expression to find SAR checksum failures
    checksum_pattern = re.compile(r'SAR checksum FAIL \(([^)]+)\)')

    # Set to store unique checksum failures
    checksums = set()

    # Find all matches and add to the set
    for match in checksum_pattern.findall(content):
        checksums.add(match)

    return list(checksums)

def extract_cvars(verifier : Verifier):
    log("Extracting cvars and file checksums")
    with open(os.path.join(verifier.mdp, "output.txt"), 'r', encoding='utf-8') as file:
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
