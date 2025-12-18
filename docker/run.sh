#!/usr/bin/env bash

# Ensure DISPLAY is set (default to :0 if not set)
export DISPLAY=${DISPLAY:-:0}

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
    chmod 644 "$XAUTH"
fi


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