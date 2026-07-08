# Orca4 ![ROS2 CI](https://github.com/clydemcqueen/orca4/actions/workflows/build_test.yml/badge.svg?branch=main)

Orca4 is a set of [ROS2](http://www.ros.org/) packages that provide basic AUV (Autonomous Underwater
Vehicle) functionality for the [BlueRobotics BlueROV2](https://www.bluerobotics.com).

Orca4 uses [ArduSub](http://www.ardusub.com/) as the flight controller and
[mavros](https://github.com/mavlink/mavros) as the GCS.

Orca4 runs in [Gazebo Harmonic](https://gazebosim.org/home) using the standard buoyancy, hydrodynamics and thruster
plugins. The connection between ArduSub and Gazebo is provided by [ardupilot_gazebo](https://github.com/ArduPilot/ardupilot_gazebo).

This is Cosma's fork of orca4, customized for COSMA AUV simulation. See the [Simulation](#simulation) section for the Cosma-specific Docker-based workflow.

## Sensors

The BlueROV2 provides the following interesting sensors:
* An [external barometer](https://bluerobotics.com/product-category/sensors-sonars-cameras/sensors/) provides depth
* An IMU provides attitude

Orca4 adds a simulated down-facing stereo camera and [ORB_SLAM2](https://github.com/clydemcqueen/orb_slam_2_ros/tree/orca4_galactic)
to generate a 3D pose as long as the camera has a good view of the seafloor.
The pose is sent to ArduSub and fused with the other sensor information.

If there is no view of the seafloor a synthetic pose is generated based on the last good pose and a simple motion model.

See [orca_base](orca_base/README.md) for details.

## Navigation

Orca4 uses the [Navigation2](https://navigation.ros.org/index.html) framework for mission
planning and navigation. Several simple Nav2 plugins are provided to work in a 3D environment:
* straight_line_planner_3d
* pure_pursuit_3d
* progress_checker_3d
* goal_checker_3d 

See [orca_nav2](orca_nav2/README.md) for details.

## Installation

See the [Dockerfile](docker/Dockerfile) for installation details.

Install these packages:
* [ROS2 Humble](https://docs.ros.org/en/humble/Installation.html)
* [Gazebo Harmonic](https://gazebosim.org/docs/harmonic/install)
* [ros_gz for Humble + Harmonic (ros-humble-gzharmonic)](https://gazebosim.org/docs/latest/ros_installation/)
* [ardupilot_gazebo for Harmonic](https://github.com/ArduPilot/ardupilot_gazebo)
* [ArduSub](https://ardupilot.org/dev/docs/building-setup-linux.html)

Build ArduSub for SITL:
~~~
cd ~/ardupilot
./waf configure --board sitl
./waf sub
~~~

Populate the workspace:
~~~
mkdir -p ~/colcon_ws/src
cd colcon_ws/src
git clone https://github.com/clydemcqueen/orca4
vcs import < orca4/workspace.repos
~~~


Get dependencies:
~~~
rosdep update
rosdep install -y --from-paths . --ignore-src
~~~

MAVROS depends on GeographicLib, and [GeographicLib needs some datasets](https://ardupilot.org/dev/docs/ros-install.html):
~~~
wget https://raw.githubusercontent.com/mavlink/mavros/master/mavros/scripts/install_geographiclib_datasets.sh
chmod a+x install_geographiclib_datasets.sh
sudo ./install_geographiclib_datasets.sh
~~~

Build the workspace:
~~~
cd ~/colcon_ws
colcon build
~~~

## Packages

* [`orca_base` Base controller, localization, frames](orca_base)
* [`orca_bringup` Launch files](orca_bringup)
* [`orca_description` SDF files](orca_description)
* [`orca_msgs` Custom messages](orca_msgs)
* [`orca_nav2` Nav2 plugins](orca_nav2)
* [`orca_shared` Dynamics model, shared utilities](orca_shared)

## Simulation

### Step 1 — Build the Docker image (once)

From the `docker/` directory:
~~~
cd docker
./build.sh
~~~

### Step 2 — Start the simulation container

~~~
./run.sh
~~~

The container is named `cosma_auv_sim`. If Gazebo has graphics issues, remove and restart it:
~~~
docker rm cosma_auv_sim
./run.sh
~~~

### Step 3 — Set up the environment and launch

Inside the container, run the environment setup:
~~~
source /opt/ros/jazzy/setup.bash
source /home/cosma_auv/swarm-vehicle/ros2_ws/install/setup.bash
source /home/cosma_auv/swarm-vehicle/ros2_ws/src/orca4/setup.bash
export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/dds/super_client_configuration_file.xml
export ROS_DISCOVERY_SERVER="127.0.0.1:11811"
ros2 daemon stop
ros2 daemon start
~~~

Then pick a launch variant:

**Without SLAM:**
```bash
ros2 launch orca_bringup sim_launch.py base:=false mavros:=false nav:=false rviz:=false slam:=false auv:=false
```

**Without SLAM, headless:**
```bash
ros2 launch orca_bringup sim_launch.py base:=false mavros:=false nav:=false rviz:=false slam:=false auv:=false gzclient:=false
```

**With SLAM:**
```bash
ros2 launch orca_bringup sim_launch.py base:=false mavros:=false nav:=false rviz:=false slam:=true auv:=false
```

**With SLAM, headless:**
```bash
ros2 launch orca_bringup sim_launch.py base:=false mavros:=false nav:=false rviz:=false slam:=true auv:=false gzclient:=false
```

### Step 4 — Start the COSMA AUV stack

Once the simulation container is running, start the COSMA AUV container in DEV mode — see the [auv submodule README](../auv/README.md) for the full workflow.
