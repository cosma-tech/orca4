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

# Create a non-root user
# Required for ArduSub install, but generally a good idea
# The Jazzy (Noble) base ships a default ubuntu:1000 user that collides with UID 1000 —
# remove it before creating cosma_auv.
RUN userdel -r ubuntu 2>/dev/null; groupdel ubuntu 2>/dev/null; \
  groupadd --gid $USER_GID $USERNAME \
  && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME \
  && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
  && chmod 0440 /etc/sudoers.d/$USERNAME \
  && echo "\n# Added by orca4 Dockerfile:" >> /home/$USERNAME/.bashrc \
  && echo "source /usr/share/bash-completion/completions/git" >> /home/$USERNAME/.bashrc

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

# Python deps used by the auv_simulation nodes (gps node needs pymavlink).
# tf-transformations comes from the ros-jazzy-tf-transformations apt package above.
RUN pip3 install --break-system-packages pymavlink

# Set up environment variables
ENV ROS_DOMAIN_ID=0
ENV ROS_LOG_DIR=/home/cosma_auv/swarm-vehicle/ros2_ws/logs
ENV PYTHONUNBUFFERED=1
ENV RCUTILS_CONSOLE_OUTPUT_FORMAT="[{severity}] [{date_time_with_ms}] [{name}]: {message}"

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