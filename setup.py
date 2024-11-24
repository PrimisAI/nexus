import os
from setuptools import setup

if os.path.exists("requirements.txt"):
    with open("requirements.txt") as f:
        requirements = f.read().splitlines()
else:
    requirements = []

setup(install_requires=requirements,)
