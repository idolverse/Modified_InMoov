from setuptools import setup

package_name = 'ce_python'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    py_modules=[],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/angle_udp.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='guyi',
    maintainer_email='your@email.com',
    description='ROS2 UDP sender to ESP32',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'angle_forwarder = ce_python.angle_forwarder:main'
        ],
    },
)
