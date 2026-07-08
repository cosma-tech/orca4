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

# Run docker with Intel GPU support
docker run -it \
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