import os
import subprocess
from verifier.colors import Colors
from verifier import config

git_repo = "https://github.com/ArcherTheReal/p2verifier.git"

config.reset_config()

ans = input(Colors.colorize("WARNING: This will overwrite all files of the project. Are you sure you want to continue? (y/n) ", Colors.RED))
if ans.lower() != "y":
    exit()


subprocess.run(["pip", "install", "-r", "requirements.txt"])

os.makedirs("run", exist_ok=True)

config.validate_files()