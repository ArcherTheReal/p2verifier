import os
import requests
import zipfile
import shutil

from verifier.logger import log, error

def get_release(repo, version = None):
    url = f"https://api.github.com/repos/{repo}/releases/"
    if version:
        url += f"tags/{version}"
    else:
        url += "latest"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def download_file(url, dest):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

def read_local_version(version_file):
    if os.path.exists(version_file):
        with open(version_file, 'r') as file:
            return file.read().strip()
    return None

def write_local_version(version_file, version):
    with open(version_file, 'w') as file:
        file.write(version)

def update_mdp(repo, target_folder, version = None):
    release = get_release(repo, version)
    online_version = release['tag_name']

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    
    version_file = os.path.join(target_folder, 'version.txt')
    local_version = read_local_version(version_file)

    if local_version == online_version:
        log("mdp is already up-to-date.")
        return

    log(f"Updating mdp.exe from version {local_version} to {online_version}")

    exe_asset = next(asset for asset in release['assets'] if asset['name'] == 'mdp.exe')
    exe_url = exe_asset['browser_download_url']

    exe_path = os.path.join(target_folder, 'mdp.exe')
    download_file(exe_url, exe_path)

    # Write the latest version to the version file
    write_local_version(version_file, online_version)

    log(f"mdp has been updated to version: {online_version}")

def update_verifier(repo, target_folder, version = None):
    release = get_release(repo, version)
    online_version = release['tag_name']

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    
    version_file = os.path.join(target_folder, 'version.txt')
    local_version = read_local_version(version_file)

    if local_version == online_version:
        log("verifier is already up-to-date.")
        return

    download_file(release['zipball_url'], os.path.join(target_folder, 'source.zip'))


    # Unzip the file
    with zipfile.ZipFile(os.path.join(target_folder, 'source.zip'), 'r') as zip_ref:
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
    os.remove(os.path.join(target_folder, 'source.zip'))

    
    write_local_version(version_file, online_version)
    log(f"verifier has been updated to version: {online_version}")