from setuptools import find_packages, setup

package_name = 'http_gateway'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/gateway.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='guyi',
    maintainer_email='rul039@ucsd.edu',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
    'console_scripts': [
        'http_gateway = http_gateway.http_gateway:main'
    ],
},
)
