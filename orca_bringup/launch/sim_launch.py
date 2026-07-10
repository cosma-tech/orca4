#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2022 Clyde McQueen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Launch the simulation.

Brings up Gazebo, ArduSub SITL, the gz<->ROS bridge, and the auv_simulation sensor nodes.
The AUV stack itself runs in the separate cosma_auv container, never here.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetParameter


def generate_launch_description():
    orca_bringup_dir = get_package_share_directory('orca_bringup')
    orca_description_dir = get_package_share_directory('orca_description')
    auv_sim_dir = get_package_share_directory('auv_simulation')

    ardusub_params_file = os.path.join(orca_bringup_dir, 'cfg', 'sub.parm')
    world_file = os.path.join(orca_description_dir, 'worlds', 'sand.world')
    auv_params_sim_file = os.path.join(auv_sim_dir, 'params', 'auv_params_sim.yaml')

    return LaunchDescription([

        SetParameter(name='use_sim_time', value=False),

        DeclareLaunchArgument(
            'ardusub',
            default_value='True',
            description='Launch ArduSub with SIM_JSON?'
        ),

        DeclareLaunchArgument(
            'gzclient',
            default_value='True',
            description='Launch Gazebo UI?'
        ),

        DeclareLaunchArgument(
            'usbl',
            default_value='True',
            description='Launch USBL simulation node?',
        ),

        DeclareLaunchArgument(
            'jetson',
            default_value='True',
            description='Launch Jetson simulation node?',
        ),

        # Launch ArduSub w/ SIM_JSON
        # -w: wipe eeprom
        # --home: start location (lat,lon,alt,yaw). Yaw is provided by Gazebo, so the start yaw value is ignored.
        # ardusub must be on the $PATH, see src/orca4/setup.bash
        ExecuteProcess(
            cmd=['ardusub', '-S', '-w', '-M', 'JSON', '--defaults', ardusub_params_file,
                 '-I0', '--home', '33.810313,-118.39386700000001,0.0,0'],
            output='screen',
            condition=IfCondition(LaunchConfiguration('ardusub')),
        ),

        # Launch Gazebo Sim (UI)
        # gz must be on the $PATH
        # libArduPilotPlugin.so must be on the GZ_SIM_SYSTEM_PLUGIN_PATH
        ExecuteProcess(
            cmd=['gz', 'sim', '-v', '3', '-r', world_file],
            output='screen',
            condition=IfCondition(LaunchConfiguration('gzclient')),
        ),

        # Launch Gazebo Sim server-only (headless)
        ExecuteProcess(
            cmd=['gz', 'sim', '-v', '3', '-r', '-s', world_file],
            output='screen',
            condition=UnlessCondition(LaunchConfiguration('gzclient')),
        ),

        # Bridge Gazebo ground-truth / sensor topics to ROS
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/model/orca4_heavy/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                '/model/orca4_heavy/altimeter@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                '/model/orca4_heavy/oa_sensor@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                '/model/orca4_heavy/gps@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat',

                '/model/usv/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                '/usv/pose@geometry_msgs/msg/Pose@gz.msgs.Pose',

                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            ],
            output='screen'
        ),

        Node(
            package='auv_simulation',
            executable='altimeter_reading',
            output='screen',
        ),

        Node(
            package='auv_simulation',
            executable='oa_reading',
            output='screen',
        ),

        Node(
            package='auv_simulation',
            executable='usbl_reading',
            output='screen',
            parameters=[auv_params_sim_file],
            condition=IfCondition(LaunchConfiguration('usbl')),
        ),

        Node(
            package='auv_simulation',
            executable='jetson',
            output='screen',
            parameters=[auv_params_sim_file],
            condition=IfCondition(LaunchConfiguration('jetson')),
        ),
    ])
