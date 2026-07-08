#!/usr/bin/env bash

# Remove any existing production container so we can reuse the name
docker rm -f cosma_auv_sim 2>/dev/null

# Ensure DISPLAY is set (default to :0 if not set)
export DISPLAY=${DISPLAY:-:0}

# Allow X11 connections from Docker containers
xhost +local:docker 2>/dev/null || true

XAUTH=/tmp/.docker.xauth

# If it exists as a directory, remove it
if [ -d "$XAUTH" ]; then
    rm -rf "$XAUTH"
fi

# If it does not exist as a file, create it
if [ ! -f "$XAUTH" ]; then
    xauth_list=$(xauth nlist "$DISPLAY" 2>/dev/null)
    if [ -n "$xauth_list" ]; then
        xauth_list=$(sed -e 's/^..../ffff/' <<< "$xauth_list")
        echo "$xauth_list" | xauth -f "$XAUTH" nmerge -
    else
        touch "$XAUTH"
    fi
    # Make XAUTH file readable by all (needed for container user)
    chmod 666 "$XAUTH"
fi


mkdir -p ~/log

docker rm -f cosma_auv_sim 2>/dev/null

# Start the container detached (-dit keeps the entrypoint's interactive bash alive so we can
# exec the build into it, then attach). Run this script once; afterwards start the sim with:
#   docker start -ai cosma_auv_sim
# Run docker with Intel GPU support
docker run -dit \
    --name cosma_auv_sim \
    -e DISPLAY=$DISPLAY \
    -e QT_X11_NO_MITSHM=1 \
    -e XAUTHORITY=$XAUTH \
    -v "$XAUTH:$XAUTH" \
    -v "/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    -v "/dev/input:/dev/input" \
    --device=/dev/dri \
    --privileged \
    --security-opt seccomp=unconfined \
    --network host \
    --ipc host \
    --pid host \
    -v ~/swarm-vehicle:/home/cosma_auv/swarm-vehicle \
    -v ~/logs:/home/cosma_auv/logs \
    -v ~/log:/home/cosma_auv/log \
    cosma_auv_sim:latest

# One-time build of the simulation workspace inside the container. The result is written to
# the host-mounted ros2_ws (build/ and install/), so it persists across docker start/stop and
# does not need to be rebuilt on every start.
BUILD_CMD="source /opt/ros/jazzy/setup.bash && \
    cd /home/cosma_auv/swarm-vehicle/ros2_ws && \
    vcs import src < src/orca4/workspace.repos && \
    colcon build --packages-up-to auv_simulation orca_bringup orca_description --symlink-install"

echo "Building the simulation workspace (one-time)..."
docker exec cosma_auv_sim bash -c "$BUILD_CMD"
BUILD_EXIT=$?
if [ $BUILD_EXIT -ne 0 ]; then
    echo "Build failed (exit $BUILD_EXIT). Fix the error and re-run ./run.sh."
    echo "The container is left running for inspection: docker exec -it cosma_auv_sim bash"
    exit $BUILD_EXIT
fi

echo "Build complete. Attaching to the container terminal."
echo "In this shell, start the simulation with: ros2 launch orca_bringup sim_launch.py"
echo "(Next time, just run: docker start -ai cosma_auv_sim)"

# Hand the container's interactive terminal to the user
docker attach cosma_auv_sim