from setuptools import setup, find_packages
from setuptools.command.install import install
import os
import shutil

class CustomInstallCommand(install):
    """Customized setuptools install command to place files in the current directory."""
    def run(self):
        install.run(self)
        self.copy_files()

    def copy_files(self):
        # Define the source and destination directories
        source_dir = os.path.join(os.path.dirname(__file__), 'verifier', 'run_files')
        dest_dir = os.getcwd()  # Current working directory
        
        # Ensure destination directory exists
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        # Copy files
        for filename in os.listdir(source_dir):
            full_file_name = os.path.join(source_dir, filename)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, dest_dir)
                print(f"Copied {full_file_name} to {dest_dir}")

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='p2verifier',
    version='0.2.0',
    author='Archer',
    description='A tool to automate the Portal 2 verification process',
    url='https://github.com/ArcherTheReal/p2verifier',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'p2verifier=verifier.main:main',  # Ensure this points to the main function in verifier.py
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    license='MIT',
)