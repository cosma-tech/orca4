# Orca4 ![ROS2 CI](https://github.com/clydemcqueen/orca4/actions/workflows/build_test.yml/badge.svg?branch=main)

This is **Cosma's fork** of [clydemcqueen/orca4](https://github.com/clydemcqueen/orca4), providing the
**simulation environment** for the COSMA AUV. It runs a [Gazebo Harmonic](https://gazebosim.org/home)
world with ArduSub SITL and bridges the simulated sensors into ROS 2 for the `auv_simulation` nodes.
The AUV control stack itself is **not** here — it runs in the separate `cosma_auv` container (see the
[auv submodule](https://github.com/cosma-tech/auv)). The whole thing is driven by a Docker workflow; see the
[Simulation](#simulation) section below.

---

*The sections below describe the underlying orca4 project.*

Orca4 is a set of [ROS2](http://www.ros.org/) packages that provide basic AUV (Autonomous Underwater
Vehicle) functionality for the [BlueRobotics BlueROV2](https://www.bluerobotics.com).

Orca4 uses [ArduSub](http://www.ardusub.com/) as the flight controller (SITL, built into the
simulation Docker image).

Orca4 runs in [Gazebo Harmonic](https://gazebosim.org/home) using the standard buoyancy, hydrodynamics and thruster
plugins. The connection between ArduSub and Gazebo is provided by [ardupilot_gazebo](https://github.com/ArduPilot/ardupilot_gazebo).

## Sensors

The simulation exposes these Gazebo sensors, bridged to ROS 2 by the `ros_gz_bridge`
`parameter_bridge` in `sim_launch.py`:
* Ground-truth odometry for the vehicle (`orca4_heavy`) and the surface vessel (`usv`)
* A down-facing altimeter (`LaserScan`)
* An obstacle-avoidance sensor (`oa_sensor`, `LaserScan`)
* A GPS receiver (`NavSatFix`)

The higher-level sensor readings consumed by the AUV stack are published by the
[**`auv_simulation`**](https://github.com/cosma-tech/auv_simulation) package — a separate
repository in the workspace, not part of this fork: `altimeter_reading`, `oa_reading`,
`usbl_reading` (USBL solution) and `jetson` (heartbeat). A Ping1D sonar topic
(`/sonar/ping1d/data`) is also available.

## Packages

* [`orca_bringup`](https://github.com/cosma-tech/orca4/tree/main/orca_bringup) — launch files and configs (`sim_launch.py`, ArduSub params)
* [`orca_description`](https://github.com/cosma-tech/orca4/tree/main/orca_description) — Gazebo SDF models and worlds

`sim_launch.py` also runs nodes and uses messages from separate Cosma repositories:
* [`auv_simulation`](https://github.com/cosma-tech/auv_simulation) — simulated sensor nodes (altimeter, oa, usbl, jetson)
* [`auv_msgs`](https://github.com/cosma-tech/auv_msg) — message definitions
* [`bluerobotics_sonar`](https://github.com/cosma-tech/bluerobotics_sonar) — Ping1D sonar messages

Gazebo models for the world are fetched via [`workspace.repos`](https://github.com/cosma-tech/orca4/blob/main/workspace.repos):
* [`bluerov2_gz`](https://github.com/clydemcqueen/bluerov2_gz)

## Simulation

### Step 1 — Build the Docker image (once)

From the `docker/` directory:
~~~
cd docker
./build.sh
~~~

### Step 2 — Bootstrap the container (once)

From the `docker/` directory, run `run.sh` **one time**. It starts the container
(`cosma_auv_sim`), does a one-time `vcs import` + `python3 -m colcon build` of the ROS 2 packages
(into `build/` and `install/`), restarts the container so the entrypoint sources the built
overlay, then attaches you to a shell:
~~~
./run.sh
~~~

If Gazebo has graphics issues, remove the container and re-bootstrap:
~~~
docker rm -f cosma_auv_sim
./run.sh
~~~

### Step 3 — Start the simulation (inside the container)

The packages are already built, so everyday use is just to start and attach to the container:
~~~
docker start -ai cosma_auv_sim
~~~

`docker start` re-runs the entrypoint, which sources the ROS 2 overlay, puts `ardusub` on the
`PATH`, and sets the Gazebo resource paths and DDS discovery config — no manual environment setup
is needed. At the container shell, start the simulation with one of:

**Gazebo GUI (default):**
```bash
ros2 launch orca_bringup sim_launch.py
```

**Headless (no Gazebo GUI):**
```bash
ros2 launch orca_bringup sim_launch.py gzclient:=false
```

`sim_launch.py` brings up Gazebo, ArduSub SITL, the Gazebo↔ROS 2 `parameter_bridge`, and the
`auv_simulation` sensor nodes. The AUV control stack itself runs in the separate `cosma_auv`
container, never here.

Other launch arguments (all default to `True`) can be added to either command: `ardusub`, `usbl`
and `jetson` (set to `false` to disable the corresponding process), and `bag:=true` to record the
interesting sim topics to a rosbag.

### Step 4 — Start the COSMA AUV stack

Once the simulation is running, start the COSMA AUV container — see the
[auv repository](https://github.com/cosma-tech/auv) for the full workflow.
