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
Launch a simulation.

Includes Gazebo, ArduSub, RViz, mavros, all ROS nodes.
"""

import os
from datetime import datetime

import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetParameter


def generate_launch_description():
    orca_bringup_dir = get_package_share_directory('orca_bringup')
    orca_description_dir = get_package_share_directory('orca_description')
    auv_dir = get_package_share_directory('auv')

    ardusub_params_file = os.path.join(orca_bringup_dir, 'cfg', 'sub.parm')
    mavros_params_file = os.path.join(orca_bringup_dir, 'params', 'sim_mavros_params.yaml')
    orca_params_file = os.path.join(orca_bringup_dir, 'params', 'sim_orca_params.yaml')
    rosbag2_record_qos_file = os.path.join(orca_bringup_dir, 'params', 'rosbag2_record_qos.yaml')
    rviz_file = os.path.join(orca_bringup_dir, 'cfg', 'sim_launch.rviz')
    world_file = os.path.join(orca_description_dir, 'worlds', 'sand.world')

    auv_params_default_file = os.path.join(auv_dir, 'params', 'auv_params_default.yaml')
    auv_params_sim_file = os.path.join(
        get_package_share_directory('auv_simulation'), 'params', 'auv_params_sim.yaml'
    )

    sim_left_ini = os.path.join(orca_bringup_dir, 'cfg', 'sim_left.ini')
    sim_right_ini = os.path.join(orca_bringup_dir, 'cfg', 'sim_right.ini')

    mcap_config_file = os.path.join(orca_bringup_dir, 'params', 'mcap_config.yaml')
    sim_rosbag_topics_file = os.path.join(orca_bringup_dir, 'params', 'sim_rosbag_topics.yaml')
    with open(sim_rosbag_topics_file, 'r') as f:
        topics = (yaml.safe_load(f) or {}).get('record_topics', [])

    run_name = datetime.now().strftime('%Y%m%d_%H%M%S') + '_SIM'
    run_dir = os.path.join(os.path.expanduser('~'), 'log', run_name)
    os.makedirs(run_dir, exist_ok=True)
    bag_out = os.path.join(run_dir, run_name)

    return LaunchDescription([

        SetParameter(name='use_sim_time', value=False),

        DeclareLaunchArgument(
            'ardusub',
            default_value='True',
            description='Launch ArduSUB with SIM_JSON?'
        ),

        DeclareLaunchArgument(
            'bag',
            default_value='True',
            description='Bag interesting topics?',
        ),

        DeclareLaunchArgument(
            'base',
            default_value='True',
            description='Launch base controller?',
        ),

        DeclareLaunchArgument(
            'gzclient',
            default_value='True',
            description='Launch Gazebo UI?'
        ),

        DeclareLaunchArgument(
            'mavros',
            default_value='True',
            description='Launch mavros?',
        ),

        DeclareLaunchArgument(
            'nav',
            default_value='True',
            description='Launch navigation?',
        ),

        DeclareLaunchArgument(
            'rviz',
            default_value='True',
            description='Launch rviz?',
        ),

        DeclareLaunchArgument(
            'slam',
            default_value='True',
            description='Launch SLAM?',
        ),

        DeclareLaunchArgument(
            'auv',
            default_value='True',
            description='Launch AUV nodes?',
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

        DeclareLaunchArgument(
            'current',
            default_value='True',
            description='Launch ocean current simulation node?',
        ),

        ExecuteProcess(
            cmd=[
                'ros2', 'bag', 'record',
                '-o', bag_out,
                '-s', 'mcap',
                '--qos-profile-overrides-path', rosbag2_record_qos_file,
                '--include-hidden-topics',
                '--storage-config-file', mcap_config_file,
                '--max-bag-duration', '30',
                '--max-bag-size', '1073741824',
                *topics,
            ],
            output='screen',
            condition=IfCondition(LaunchConfiguration('bag')),
        ),

        # Launch rviz
        ExecuteProcess(
            cmd=['rviz2', '-d', rviz_file],
            output='screen',
            condition=IfCondition(LaunchConfiguration('rviz')),
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

        # Launch Gazebo Sim
        # gz must be on the $PATH
        # libArduPilotPlugin.so must be on the GZ_SIM_SYSTEM_PLUGIN_PATH
        ExecuteProcess(
            cmd=['gz', 'sim', '-v', '3', '-r', world_file],
            output='screen',
            condition=IfCondition(LaunchConfiguration('gzclient')),
        ),

        # Launch Gazebo Sim server-only
        ExecuteProcess(
            cmd=['gz', 'sim', '-v', '3', '-r', '-s', world_file],
            output='screen',
            condition=UnlessCondition(LaunchConfiguration('gzclient')),
        ),

        # Get images from Gazebo Sim to ROS
        Node(
            package='ros_gz_image',
            executable='image_bridge',
            arguments=['stereo_left', 'stereo_right'],
            output='screen',
        ),

        # Gazebo Sim doesn't publish camera info, so do that here
        Node(
            package='orca_base',
            executable='camera_info_publisher',
            name='left_info_publisher',
            output='screen',
            parameters=[{
                'camera_info_url': 'file://' + sim_left_ini,
                'camera_name': 'stereo_left',
                'frame_id': 'stereo_left_frame',
                'timer_period_ms': 50,
            }],
            remappings=[
                ('/camera_info', '/stereo_left/camera_info'),
            ],
        ),

        Node(
            package='orca_base',
            executable='camera_info_publisher',
            name='right_info_publisher',
            output='screen',
            parameters=[{
                'camera_info_url': 'file://' + sim_right_ini,
                'camera_name': 'stereo_right',
                'frame_id': 'stereo_right_frame',
                'timer_period_ms': 50,
            }],
            remappings=[
                ('/camera_info', '/stereo_right/camera_info'),
            ],
        ),

        # Publish ground truth pose from Ignition Gazebo
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
                
                '/model/orca4_heavy/ocean_current@geometry_msgs/msg/Vector3]gz.msgs.Vector3d',

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
            parameters=[auv_params_default_file, auv_params_sim_file],
            condition=IfCondition(LaunchConfiguration('usbl')),
        ),

        Node(
            package='auv_simulation',
            executable='jetson',
            output='screen',
            parameters=[auv_params_default_file, auv_params_sim_file],
            condition=IfCondition(LaunchConfiguration('jetson')),
        ),

        Node(
            package='auv_simulation',
            executable='ocean_current',
            output='screen',
            condition=IfCondition(LaunchConfiguration('current')),
        ),

        # Include AUV launch file
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory('auv'), 'launch', 'launch_auv.py')
            ),
            launch_arguments={
                'altimeter_reading': 'false',
                'ping1d': 'false',
                'mavros_node': 'true',
            }.items(),
            condition=IfCondition(LaunchConfiguration('auv')),
        ),
                


        # Bring up Orca and Nav2 nodes
        #IncludeLaunchDescription(
        #    PythonLaunchDescriptionSource(os.path.join(orca_bringup_dir, 'launch', 'bringup.py')),
        #    launch_arguments={
        #        'base': LaunchConfiguration('base'),
        #        'mavros': LaunchConfiguration('mavros'),
        #        'mavros_params_file': mavros_params_file,
        #        'nav': LaunchConfiguration('nav'),
        #        'orca_params_file': orca_params_file,
        #        'slam': LaunchConfiguration('slam'),
        #    }.items(),
        #),
    ])

