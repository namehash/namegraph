from setuptools import setup, find_packages

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name='generator',
    packages=find_packages(),
    version='0.0.1',
    install_requires=required
)
