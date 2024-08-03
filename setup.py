from setuptools import setup, find_packages
import os

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