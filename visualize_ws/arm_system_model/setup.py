from setuptools import setup
import os
from glob import glob

package_name = 'arm_system_model'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/' + package_name + '/launch', glob('launch/*.py')),
        ('share/' + package_name + '/urdf', glob('urdf/*.urdf.xml')),
        ('share/' + package_name + '/meshes', glob('meshes/*.*')),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email@example.com',
    description='Robot model and visualization tools',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'state_publisher = arm_system_model.state_publisher:main',
        ],
    },
)
