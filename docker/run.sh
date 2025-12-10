#!/usr/bin/env bash

# Ensure DISPLAY is set (default to :0 if not set)
export DISPLAY=${DISPLAY:-:0}

XAUTH=/tmp/.docker.xauth
if [ ! -f $XAUTH ]
then
    xauth_list=$(xauth nlist $DISPLAY 2>/dev/null)
    if [ ! -z "$xauth_list" ]
    then
        xauth_list=$(sed -e 's/^..../ffff/' <<< "$xauth_list")
        echo "$xauth_list" | xauth -f $XAUTH nmerge - 2>/dev/null
    else
        touch $XAUTH
    fi
    chmod a+r $XAUTH
fi

# Allow X11 connections from localhost (alternative method if xauth fails)
xhost +local:docker 2>/dev/null || true

# Specific for NVIDIA drivers, required for OpenGL >= 3.3
docker run -it \
    --name cosma_auv_sim \
    -e DISPLAY=$DISPLAY \
    -e QT_X11_NO_MITSHM=1 \
    -e XAUTHORITY=$XAUTH \
    -v "$XAUTH:$XAUTH" \
    -v "/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    -v "/dev/input:/dev/input" \
    --privileged \
    --security-opt seccomp=unconfined \
    --network host \
    --ipc host \
    --pid host \
    -v ~/swarm-vehicle:/home/cosma_auv/swarm-vehicle \
    -v ~/logs:/home/cosma_auv/logs \
    cosma_auv_sim:latest