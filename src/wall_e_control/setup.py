from setuptools import setup
import os
from glob import glob

package_name = 'wall_e_control'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ferbin',
    maintainer_email='ferbin@example.com',
    description='Wall-E robot control package with Arduino serial bridge',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'arduino_bridge = wall_e_control.ros2_arduino_bridge:main',
            'servo_control_ui = wall_e_control.servo_control_ui:main',
        ],
    },
)