#!/bin/bash

# uninstall

if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo)"
  exit
fi

echo "Uninstalling FastFlowLM-gtk..."

INSTALL_DIR="/usr/share/fastflowlm-gtk"
BIN_PATH="/usr/bin/fastflowlm-gtk"
ICON_PATH="/usr/share/icons/hicolor/256x256/apps/com.marley.FastFlowLM-gtk.png"
DESKTOP_PATH="/usr/share/applications/com.marley.FastFlowLM-gtk.desktop"

# Remove files
rm -f "$BIN_PATH"
rm -rf "$INSTALL_DIR"
rm -f "$ICON_PATH"
rm -f "$DESKTOP_PATH"

# Update Desktop/Icon Database
update-desktop-database -q
gtk-update-icon-cache -f -t /usr/share/icons/hicolor

# Remove memlock fixes (only the file we actually install)
echo "Reverting memlock system fixes (99-fastflowlm-gtk.conf)..."
rm -f /etc/security/limits.d/99-fastflowlm-gtk.conf
echo "     You may want to log out/in or reboot if you had other memlock-dependent apps running."

# Clean up any very old legacy entries if they exist (best-effort, non-destructive)
if [ -f /etc/security/limits.conf ]; then
    sed -i '/fastflowlm-gtk/d' /etc/security/limits.conf 2>/dev/null || true
fi
if [ -f /etc/systemd/system.conf ]; then
    sed -i 's/^DefaultLimitMEMLOCK=infinity/#DefaultLimitMEMLOCK=infinity/' /etc/systemd/system.conf 2>/dev/null || true
fi

echo "Uninstallation complete!"
read -p "Press enter to exit..."
