#!/bin/bash

if [ -f "/home/cosma_auv/swarm-vehicle/ros2_ws/install/setup.bash" ]; then
	source /home/cosma_auv/swarm-vehicle/ros2_ws/src/orca4/setup.bash
else
	source /opt/ros/jazzy/setup.bash
fi

git config --global --add safe.directory /root/swarm-vehicle

# Check if discovery IP argument is provided
if [ -n "$1" ]; then
	# Update super_client_configuration_file.xml with the provided IP
	DISCOVERY_IP="$1"
	sudo sed -i "s|<address>.*</address>|<address>${DISCOVERY_IP}</address>|" /etc/dds/super_client_configuration_file.xml
	echo "Updated discovery server IP to: ${DISCOVERY_IP}"
else
	DISCOVERY_IP="127.0.0.1"
fi

export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/dds/super_client_configuration_file.xml
export ROS_DISCOVERY_SERVER="${DISCOVERY_IP}:11811"


# Restart ROS2 daemon to get update DDS config
ros2 daemon stop
ros2 daemon start

git config --global --add safe.directory /home/cosma_auv/swarm-vehicle

exec /bin/bash