FROM balenalib/jetson-nano-ubuntu:latest

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies, including CMake
RUN apt-get update && apt-get install -y \
    python3 python3-venv python3-pip python3-full \
    git curl udev cmake build-essential && \
    rm -rf /var/lib/apt/lists/*

# Create a virtual environment for PlatformIO
RUN python3 -m venv /root/.platformio/penv && \
    /root/.platformio/penv/bin/pip install --upgrade pip platformio

# Ensure PlatformIO uses the correct virtual environment
ENV PATH="/root/.platformio/penv/bin:$PATH"

# Create a working directory
WORKDIR /workspace

# Set up udev rules for PlatformIO (optional)
RUN curl -fsSL https://raw.githubusercontent.com/platformio/platformio-core/develop/platformio/assets/system/99-platformio-udev.rules -o /etc/udev/rules.d/99-platformio-udev.rules || true

# Ensure udev rules are available (Skip error if udev is not running)
RUN test -f /etc/udev/rules.d/99-platformio-udev.rules && \
    (command -v udevadm && udevadm control --reload-rules && udevadm trigger) || echo "udevadm not found, skipping reload"

# Default command
CMD ["bash"]

