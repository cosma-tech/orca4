FROM osrf/ros:jazzy-desktop AS base

ARG USERNAME=cosma_auv
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get upgrade -y

# Install a few handy tools and ROS2 dependencies
RUN apt-get update \
  && apt-get -y --quiet --no-install-recommends install \
    bash-completion \
    build-essential \
    git \
    glmark2 \
    gnupg \
    iputils-ping \
    lsb-release \
    plocate \
    software-properties-common \
    sudo \
    wget \
    vim \
    python3-pip \
    python3-venv \
    ros-jazzy-tf-transformations \
    ros-jazzy-plotjuggler-ros \
    ros-jazzy-rosbag2-storage-mcap \
    ros-jazzy-mavros-msgs \
    ros-jazzy-geographic-msgs \
  && rm -rf /var/lib/apt/lists/*


# Install Gazebo Harmonic for use with ROS2 Jazzy
RUN wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
RUN apt-get update \
  && apt-get -y --quiet --no-install-recommends install \
    gz-harmonic \
    ros-jazzy-ros-gz \
  && rm -rf /var/lib/apt/lists/*

# Install some ardupilot and ardupilot_gazebo prereqs (libgz-sim8-dev is for gz harmonic)
RUN apt-get update \
  && apt-get -y --quiet --no-install-recommends install \
    python3-wxgtk4.0 \
    rapidjson-dev \
    xterm \
    libgz-sim8-dev \
    libopencv-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-libav \
    gstreamer1.0-gl \
  && rm -rf /var/lib/apt/lists/*

# Python deps used by the auv_simulation nodes, installed into a --system-site-packages venv
# (mirrors the AUV image). --system-site-packages so the venv also sees rclpy, numpy and the rest
# of the ROS2/system Python stack (not pip-installable). Created here as root so /opt/venv is
# writable; the ENV PATH that makes this the default interpreter is set later (after the ArduSub
# and ardupilot_gazebo source builds, so those keep using the system python unchanged).
# pymavlink is only imported by auv_simulation/gps.py; that GPS node is not launched by
# sim_launch.py, but it is kept installed intentionally.
RUN python3 -m venv /opt/venv --system-site-packages \
  && /opt/venv/bin/pip install --upgrade pip \
  && /opt/venv/bin/pip install pymavlink

# Create a non-root user
# Required for ArduSub install, but generally a good idea
# The Jazzy (Noble) base ships a default ubuntu:1000 user that collides with UID 1000 —
# remove it before creating cosma_auv.
RUN userdel -r ubuntu 2>/dev/null; groupdel ubuntu 2>/dev/null; \
  groupadd --gid $USER_GID $USERNAME \
  && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME \
  && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
  && chmod 0440 /etc/sudoers.d/$USERNAME \
  && printf '\n# Added by orca4 Dockerfile: interactive (docker exec) shell setup\nsource /usr/share/bash-completion/completions/git\nsource /opt/ros/jazzy/setup.bash\n[ -f /home/cosma_auv/swarm-vehicle/ros2_ws/install/setup.bash ] && source /home/cosma_auv/swarm-vehicle/ros2_ws/src/orca4/setup.bash\n' >> /home/$USERNAME/.bashrc

# Switch to our new user
USER $USERNAME
ENV USER=$USERNAME

# Clone ArduSub code
WORKDIR /home/$USERNAME
RUN git clone https://github.com/ArduPilot/ardupilot.git --recurse-submodules

# Install ArduSub prereqs (this also appends to .bashrc)
WORKDIR /home/$USERNAME/ardupilot
ENV SKIP_AP_EXT_ENV=1 SKIP_AP_GRAPHIC_ENV=1 SKIP_AP_COV_ENV=1 SKIP_AP_GIT_CHECK=1
RUN Tools/environment_install/install-prereqs-ubuntu.sh -y

# Build ArduSub
# Note: waf will capture all of the environment variables in ardupilot/.lock-waf_linux_build.
# Any change to enviroment variables will cause a re-build.
# To avoid this call sim_vehicle.py with the "--no-rebuild" option.
WORKDIR /home/$USERNAME/ardupilot
RUN modules/waf/waf-light configure --board sitl \
  && modules/waf/waf-light build --target bin/ardusub

# Clone ardupilot_gazebo code
WORKDIR /home/$USERNAME
RUN git clone https://github.com/ArduPilot/ardupilot_gazebo.git

# Build for Gazebo Harmonic, define this before building ardupilot_gazebo and ros_gz
ENV GZ_VERSION=harmonic

# Build ardupilot_gazebo
RUN [ "/bin/bash" , "-c" , " \
  cd ardupilot_gazebo \
  && git checkout 4b30a3d8 \
  && mkdir build \
  && cd build \
  && cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  && make -j4" ]

# Make the venv python the default interpreter for every process (runtime entrypoint launch and
# the run.sh docker-exec build) with no activation step. pymavlink was installed into the venv
# above; tf-transformations comes from the ros-jazzy-tf-transformations apt package.
ENV PATH="/opt/venv/bin:$PATH"

# Expose the venv site-packages to every interpreter (incl. system python running `ros2 launch`)
# so launch files that import venv-only libs (e.g. auv modules pulling in pymavlink) resolve them.
# Appended last on PYTHONPATH by ROS/workspace setup, so it acts as a fallback and does not shadow
# system/ROS packages. (python3.12 is the Noble/Jazzy version.)
ENV PYTHONPATH="/opt/venv/lib/python3.12/site-packages"

# The workspace is built with `python3 -m colcon` (see run.sh BUILD_CMD), NOT the bare `colcon`
# executable. Because PATH above makes `python3` the venv python, `python3 -m colcon` runs the
# (system) colcon MODULE under the venv python, which bakes venv-python shebangs
# (#!/opt/venv/bin/python3) into the ament_python nodes so they run under the venv at launch.
# colcon itself stays the system one (visible via --system-site-packages) and is intentionally
# NOT installed into the venv.
# NOTE for dev builds: always use `python3 -m colcon build ...`. A bare `colcon build` would run
# the system colcon under system python and bake system-python shebangs (nodes would not see the
# venv libs).

# Set up environment variables
ENV ROS_DOMAIN_ID=0
ENV ROS_LOG_DIR=/home/cosma_auv/swarm-vehicle/ros2_ws/logs
ENV PYTHONUNBUFFERED=1
ENV RCUTILS_CONSOLE_OUTPUT_FORMAT="[{severity}] [{date_time_with_ms}] [{name}]: {message}"
ENV FASTRTPS_DEFAULT_PROFILES_FILE=/etc/dds/super_client_configuration_file.xml

COPY entrypoint.sh /entrypoint.sh
RUN sudo chmod +x /entrypoint.sh
RUN sudo mkdir -p /etc/dds
COPY super_client_configuration_file.xml /etc/dds/super_client_configuration_file.xml

# Set working directory
WORKDIR /home/cosma_auv/swarm-vehicle/ros2_ws

# In the entrypoint script we start ROS2 Discovery Server on the given IP address
# The address is passed as an argument with docker run/start command
ENTRYPOINT ["/entrypoint.sh"]
# If the argument is not provided, use the default IP address
CMD ["127.0.0.1"]