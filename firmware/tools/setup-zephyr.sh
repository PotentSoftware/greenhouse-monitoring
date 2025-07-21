#!/bin/bash
# Zephyr Development Environment Setup Script
# Sets up the complete development environment for BeagleConnect Freedom firmware

set -e  # Exit on any error

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}==== BeagleConnect Freedom Development Setup ====${NC}"

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIRMWARE_DIR="$PROJECT_ROOT/firmware/beagleconnect-freedom"
ZEPHYR_SDK_VERSION="0.16.3"
ZEPHYR_SDK_DIR="$HOME/zephyr-sdk-$ZEPHYR_SDK_VERSION"

echo -e "${YELLOW}Project root: $PROJECT_ROOT${NC}"
echo -e "${YELLOW}Firmware directory: $FIRMWARE_DIR${NC}"

# Check if running in project directory
if [ ! -f "$PROJECT_ROOT/README.md" ] || [ ! -d "$FIRMWARE_DIR" ]; then
    echo -e "${RED}Error: Must run from greenhouse-monitoring project directory${NC}"
    echo -e "${RED}Current location: $(pwd)${NC}"
    echo -e "${RED}Expected project root: $PROJECT_ROOT${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is required but not installed${NC}"
    exit 1
fi

if ! command_exists git; then
    echo -e "${RED}Error: Git is required but not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"

# Initialize submodules
echo -e "${BLUE}Initializing git submodules...${NC}"
cd "$PROJECT_ROOT"
git submodule update --init --recursive
echo -e "${GREEN}✓ Submodules initialized${NC}"

# Set up Python virtual environment
echo -e "${BLUE}Setting up Python virtual environment...${NC}"
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    python3 -m venv "$PROJECT_ROOT/.venv"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment and install west
echo -e "${BLUE}Installing west build tool...${NC}"
source "$PROJECT_ROOT/.venv/bin/activate"
pip install --upgrade pip
pip install west
echo -e "${GREEN}✓ West installed${NC}"

# Initialize west workspace
echo -e "${BLUE}Initializing west workspace...${NC}"
cd "$FIRMWARE_DIR"
if [ ! -f ".west/config" ]; then
    west init -l .
    echo -e "${GREEN}✓ West workspace initialized${NC}"
else
    echo -e "${YELLOW}West workspace already initialized${NC}"
fi

# Update west dependencies
echo -e "${BLUE}Updating west dependencies...${NC}"
west update
echo -e "${GREEN}✓ West dependencies updated${NC}"

# Check for Zephyr SDK
echo -e "${BLUE}Checking Zephyr SDK installation...${NC}"
if [ ! -d "$ZEPHYR_SDK_DIR" ]; then
    echo -e "${YELLOW}Zephyr SDK not found. Installing...${NC}"
    
    # Download and install Zephyr SDK
    cd "$HOME"
    SDK_FILE="zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64.tar.xz"
    
    if [ ! -f "$SDK_FILE" ]; then
        echo -e "${BLUE}Downloading Zephyr SDK $ZEPHYR_SDK_VERSION...${NC}"
        wget "https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${ZEPHYR_SDK_VERSION}/${SDK_FILE}"
    fi
    
    echo -e "${BLUE}Extracting Zephyr SDK...${NC}"
    tar xf "$SDK_FILE"
    
    echo -e "${BLUE}Setting up Zephyr SDK...${NC}"
    cd "$ZEPHYR_SDK_DIR"
    ./setup.sh
    
    echo -e "${GREEN}✓ Zephyr SDK installed${NC}"
else
    echo -e "${YELLOW}Zephyr SDK already installed at $ZEPHYR_SDK_DIR${NC}"
fi

# Create environment setup script
echo -e "${BLUE}Creating environment setup script...${NC}"
cat > "$PROJECT_ROOT/firmware/tools/env-setup.sh" << EOF
#!/bin/bash
# Source this script to set up the development environment
# Usage: source firmware/tools/env-setup.sh

export ZEPHYR_TOOLCHAIN_VARIANT=zephyr
export ZEPHYR_SDK_INSTALL_DIR=$ZEPHYR_SDK_DIR

# Activate Python virtual environment
source "$PROJECT_ROOT/.venv/bin/activate"

echo "Zephyr development environment activated"
echo "ZEPHYR_SDK_INSTALL_DIR: \$ZEPHYR_SDK_INSTALL_DIR"
echo "Virtual environment: \$VIRTUAL_ENV"
EOF

chmod +x "$PROJECT_ROOT/firmware/tools/env-setup.sh"
echo -e "${GREEN}✓ Environment setup script created${NC}"

# Test build
echo -e "${BLUE}Testing firmware build...${NC}"
cd "$FIRMWARE_DIR"
source "$PROJECT_ROOT/firmware/tools/env-setup.sh"

if west build -b beagleconnect_freedom --pristine; then
    echo -e "${GREEN}✓ Test build successful${NC}"
    echo -e "${GREEN}Firmware binary: $FIRMWARE_DIR/build/zephyr/zephyr.bin${NC}"
else
    echo -e "${RED}✗ Test build failed${NC}"
    echo -e "${YELLOW}This may be due to missing dependencies or configuration issues${NC}"
fi

echo -e "${GREEN}${BOLD}==== Setup Complete ====${NC}"
echo -e "${YELLOW}To activate the development environment in future sessions:${NC}"
echo -e "${BLUE}  source firmware/tools/env-setup.sh${NC}"
echo -e "${YELLOW}To build firmware:${NC}"
echo -e "${BLUE}  cd firmware/beagleconnect-freedom && west build -b beagleconnect_freedom${NC}"
echo -e "${YELLOW}To flash firmware:${NC}"
echo -e "${BLUE}  ./firmware/tools/build-and-flash.sh${NC}"
echo -e "${YELLOW}For complete documentation:${NC}"
echo -e "${BLUE}  docs/firmware/beagleconnect-freedom-development.md${NC}"
