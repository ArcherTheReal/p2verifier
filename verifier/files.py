import os
import shutil
from tqdm import tqdm

from verifier.colors import Colors
from verifier.logger import log, error
from verifier.verifier import Verifier



def clear_folders(verifier : Verifier):
    if os.path.exists(os.path.join(verifier.mdp, "demos")):
        shutil.rmtree(os.path.join(verifier.mdp, "demos"))
    if os.path.exists(verifier.p2demos):
        shutil.rmtree(verifier.p2demos)
    os.makedirs(os.path.join(verifier.mdp, "demos"))
    os.makedirs(verifier.p2demos)

def copy_demos(verifier : Verifier):
    # Check for zip unpacking
    files = os.listdir(verifier.run)
    unpack = True
    unpack_file = None
    for file in files:
        if file.endswith(".zip"):
            if unpack_file is not None:
                unpack = False
            unpack_file = file
        else:
            unpack = False

    if unpack and verifier.config["options"]["unzipper"]:
        if unpack_file is None:
            error("No zip file found")
            exit(1)
        log("Unpacking zip file")
        shutil.unpack_archive(os.path.join(verifier.run, unpack_file), verifier.run)
        os.remove(os.path.join(verifier.run, unpack_file))

    # Fetch all demos from run/
    log("Copying demos to mdp")
    verifier.demoFilenames = []
    for root, dirs, files in os.walk(verifier.run):
        for file in tqdm(files, desc=Colors.colorize("Copying files", Colors.BLUE), unit="files", bar_format=Colors.tqdmFormat):
            if file.endswith(".dem"):
                source_file = os.path.join(root, file)
                destination_file = os.path.join(verifier.mdp, "demos", file)
                portal2_destination = os.path.join(verifier.p2demos, file)
                shutil.copy2(source_file, destination_file)
                shutil.copy2(source_file, portal2_destination)
                verifier.demoFilenames.append(file)
    verifier.demoFilenames = sorted(verifier.demoFilenames, key=file_decorator)

def file_decorator(filename):
    filename = filename.split(".")[0]
    filename = filename.split("_")[-1]
    if filename.isdigit():
        return int(filename)
    return 0