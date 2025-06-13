FROM osrf/ros:humble-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Set working directory
WORKDIR /home/ros/ros2_ws

# Install ROS 2 tools and ROS-GZ bridge
RUN apt update && apt install -y \
    ros-humble-ros-gz-sim \
    ros-humble-nav2-bringup \
    python3-colcon-common-extensions \
    ros-humble-xacro \
    ros-humble-joint-state-publisher-gui \
    ros-humble-rviz2 \
    mesa-utils \
    curl gnupg2 lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Add the OSRF Gazebo apt repo and key
RUN curl -fsSL https://packages.osrfoundation.org/gazebo.key \
    | gpg --dearmor -o /usr/share/keyrings/gazebo-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gazebo-archive-keyring.gpg] \
    http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/gazebo-stable.list && \
    apt update && apt install -y \
    ignition-fortress \
    ignition-tools \
    libignition-fuel-tools7-dev \
    && rm -rf /var/lib/apt/lists/*

# Set NVIDIA env vars for GPU passthrough (if using --gpus)
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute

# Gazebo resource path for fuel models
ENV GZ_SIM_RESOURCE_PATH=/root/.ignition/fuel

# Pre-download a world from Gazebo Fuel
RUN ign fuel download -u "https://fuel.gazebosim.org/1.0/RichardTops/worlds/tugbot_depot"

# Always source ROS Humble setup in bash
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc

# Launch Gazebo by default
CMD ["ign", "gazebo", "/root/.ignition/fuel/fuel.gazebosim.org/richardtops/worlds/tugbot_depot/1/tugbot_depot.sdf"]
