from setuptools import find_packages
from setuptools import setup

setup(
    name='my_uavs',
    version='1.0.0',
    packages=find_packages(
        include=('my_uavs', 'my_uavs.*')),
)
