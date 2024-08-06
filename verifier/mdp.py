import subprocess
import re
import os
from tqdm import tqdm
import zlib
import requests
import json

from verifier.logger import log, error
from verifier.files import file_decorator
from verifier.verifier import Verifier
from verifier import updater
from verifier.colors import Colors

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

    res = {}
    for checksum in checksums:
        res[checksum] = verifier.sar_checksums.get(checksum, "Unknown")

    return res

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

def download_and_crc32(url):
    response = requests.get(url)
    response.raise_for_status()  # Ensure we notice bad responses
    crc32_hash = zlib.crc32(response.content) & 0xffffffff
    return f"{crc32_hash:X}"  # Format as hexadecimal

def get_sar_checksums(installed_versions = []):
    repo = 'p2sr/sourceautorecord'
    releases_url = f'https://api.github.com/repos/{repo}/releases'

    releases = requests.get(releases_url)
    try:
        releases.raise_for_status()
    except requests.exceptions.HTTPError as e:
        error(f"Failed to get releases from {releases_url}: {e}")
        return
    valid_releases = []

    releases = releases.json()

    last_release = releases[0]
    last_release_tag_name = last_release['tag_name']
    version_match = re.match(r'(\d+)\.(\d+).(\d+)', last_release_tag_name)
    last_release_major, last_release_minor, last_release_fix = int(version_match.group(1)), int(version_match.group(2)), int(version_match.group(3))
    for release in releases:
        tag_name = release['tag_name']
        is_prerelease = release['prerelease']
        assets = release['assets']
        
        tag_match = re.match(r'(\d+)\.(\d+).(\d+)', tag_name)
        if tag_match:
            major, minor, fix = int(tag_match.group(1)), int(tag_match.group(2)), int(tag_match.group(3))
            if major < last_release_major:
                continue
            if minor < last_release_minor:
                continue
            if is_prerelease and major == last_release_major and minor == last_release_minor and fix == 0:
                continue
            valid_releases.append((tag_name, assets))
    crc32_checksums = {}
    for version, assets in tqdm(valid_releases, bar_format=Colors.tqdmFormat, desc=Colors.colorize("Downloading SAR checksums", Colors.BLUE), unit="version", unit_scale=True):
        for asset in assets:
            if f"{version}-{asset['name']}" in installed_versions:
                continue
            if asset['name'] in ['sar.dll', 'sar.so']:
                download_url = asset['browser_download_url']
                checksum = download_and_crc32(download_url)
                crc32_checksums[checksum] = f"{version}-{asset['name']}"

    return crc32_checksums
