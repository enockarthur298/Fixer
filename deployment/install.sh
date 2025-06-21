#!/bin/bash

# Fixer AI Installation Script
# This script installs the Fixer AI Repair Agent and sets up the systemd service

# Display colorful messages
GREEN="\033[0;32m"
RED="\033[0;31m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

# Function to display status messages
log_message() {
  echo -e "${BLUE}[Fixer AI]${NC} $1"
}

# Function to display error messages
log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Function to display success messages
log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to display warning messages
log_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check for root privileges
if [ "$(id -u)" -ne 0 ]; then
  log_error "This script requires root privileges. Please run with sudo."
  exit 1
fi

# Set installation directory
INSTALL_DIR="/opt/fixer-ai"
SERVICE_FILE="/etc/systemd/system/fixer-ai.service"

# Create fixer user if it doesn't exist
if ! id -u fixer &>/dev/null; then
  log_message "Creating fixer user..."
  useradd -m -s /bin/bash fixer
fi

# Create installation directory
log_message "Creating installation directory..."
mkdir -p $INSTALL_DIR
chown fixer:fixer $INSTALL_DIR

# Copy files to installation directory
log_message "Copying files to installation directory..."
cp -r ./* $INSTALL_DIR/
chown -R fixer:fixer $INSTALL_DIR

# Install dependencies
log_message "Installing dependencies..."
pip3 install -r $INSTALL_DIR/requirements.txt

# Copy systemd service file
log_message "Setting up systemd service..."
cp $INSTALL_DIR/deployment/fixer-ai.service $SERVICE_FILE
systemctl daemon-reload
systemctl enable fixer-ai.service

# Create logs directory
log_message "Creating logs directory..."
mkdir -p $INSTALL_DIR/logs
chown -R fixer:fixer $INSTALL_DIR/logs

# Create .env file if it doesn't exist
if [ ! -f "$INSTALL_DIR/.env" ]; then
  log_message "Creating .env file..."
  cp $INSTALL_DIR/.env.example $INSTALL_DIR/.env
  log_warning "Please edit $INSTALL_DIR/.env to set your API keys and configuration"
fi

log_success "Installation completed successfully!"
log_message "To start the service, run: sudo systemctl start fixer-ai"
log_message "To check service status, run: sudo systemctl status fixer-ai"
log_message "To view logs, run: sudo journalctl -u fixer-ai -f"
