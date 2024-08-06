import os
import subprocess
import importlib
import zipfile
import shutil
import requests

git_repo = "ArcherTheReal/p2verifier"
mdp_repo = "p2sr/mdp"

ans = input("\033[31mWARNING: This will overwrite all files of the project. Are you sure you want to continue? (y/n) \033[0m")
if ans.lower() != "y":
    exit()


def get_release(repo, version = None):
    url = f""
    if version:
        url += f"tags/{version}"
    else:
        url += "latest"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def update_verifier(repo, target_folder):

    release = requests.get(f"https://api.github.com/repos/{repo}/releases/latest").json()
    online_version = release['tag_name']

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    
    zip_url = release['zipball_url']
    response = requests.get(zip_url)
    zip_path = os.path.join(target_folder, 'source.zip')
    with open(zip_path, 'wb') as file:
        file.write(response.content)


    # Unzip the file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        os.makedirs(os.path.join(target_folder, "upstream"), exist_ok=True)
        zip_ref.extractall(os.path.join(target_folder, "upstream"))
        
        extracted_folder = os.listdir(os.path.join(target_folder, "upstream"))[0]
        extracted_folder = os.path.join(target_folder, "upstream", extracted_folder)
        if extracted_folder:
            # Move contents from the extracted folder to the target_folder
            for filename in os.listdir(extracted_folder):
                old_path = os.path.join(extracted_folder, filename)
                new_path = os.path.join(target_folder, filename)
                if os.path.isdir(old_path):
                    if os.path.exists(new_path):
                        shutil.rmtree(new_path)
                    shutil.move(old_path, target_folder)
                else:
                    if os.path.exists(new_path):
                        os.remove(new_path)
                    shutil.move(old_path, target_folder)
            # Remove the now-empty subfolder
            os.rmdir(extracted_folder)
    # Remove the zip file
    os.remove(zip_path)

    with open(os.path.join(target_folder, "version.txt"), 'w') as file:
        file.write(online_version)

cwd = os.path.dirname(os.path.abspath(__file__))

update_verifier(git_repo, cwd)

subprocess.run(["pip", "install", "-r", "requirements.txt"])

config = importlib.import_module("verifier.config")
updater = importlib.import_module("verifier.updater")
logger = importlib.import_module("verifier.logger")

logger.log("Installed verifier")

os.makedirs(os.path.join(cwd, "run"), exist_ok=True)

updater.update_mdp(mdp_repo, os.path.join(cwd, "mdp"))

config.reset_config(cwd)

config.validate_files()