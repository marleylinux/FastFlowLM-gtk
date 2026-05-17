#!/bin/bash

# FastFlowLM-GTK Installation Script
# Run with sudo: sudo ./install.sh

if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo)"
  exit
fi

echo "Installing FastFlowLM-GTK..."

# Install files
cp flm-gtk /usr/bin/flm-gtk
chmod +x /usr/bin/flm-gtk

cp flm-gtk.png /usr/share/pixmaps/flm-gtk.png
cp flm-gtk.desktop /usr/share/applications/flm-gtk.desktop

# Update Desktop Database
update-desktop-database

echo "Installation complete! You can now launch 'flm-gtk' from your app menu."
