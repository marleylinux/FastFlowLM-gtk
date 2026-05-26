#!/bin/bash

# FastFlowLM-gtk Manual Installation Script
# This script mirrors the AUR PKGBUILD installation logic.
# Run with sudo: sudo ./install.sh

if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo)"
  exit
fi

echo "Installing system dependencies (Arch Linux)..."
if command -v pacman >/dev/null 2>&1; then
    pacman -S --needed --noconfirm fastflowlm python python-gobject gtk4 libadwaita libsoup3 gtksourceview5 python-psutil xrt-plugin-amdxdna 2>/dev/null || echo "  -> Warning: pacman dependency installation step failed or was skipped. Please ensure all dependencies are installed manually."
else
    echo "  -> Non-Arch system detected. Skipping pacman step. Please install dependencies manually:"
    echo "     gtk4 libadwaita gtksourceview5 libsoup3 python-gobject python-psutil fastflowlm xrt-plugin-amdxdna"
fi

echo "Installing FastFlowLM-gtk files..."

INSTALL_DIR="/usr/share/fastflowlm-gtk"
BIN_DIR="/usr/bin"
ICON_DIR="/usr/share/icons/hicolor/256x256/apps"
APP_DIR="/usr/share/applications"

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/assets"
mkdir -p "$ICON_DIR"
mkdir -p "$APP_DIR"

# Install all Python files
cp src/*.py "$INSTALL_DIR/"
chmod 644 "$INSTALL_DIR"/*.py
chmod 755 "$INSTALL_DIR/app.py"

# Install custom model avatars
cp src/assets/*.png "$INSTALL_DIR/assets/"
chmod 644 "$INSTALL_DIR/assets"/*.png

# Install icon
install -m644 "src/assets/com.marley.FastFlowLM-gtk.png" "$ICON_DIR/com.marley.FastFlowLM-gtk.png"
chmod 644 "$ICON_DIR/com.marley.FastFlowLM-gtk.png"

# Install Desktop file
cp com.marley.FastFlowLM-gtk.desktop "$APP_DIR/com.marley.FastFlowLM-gtk.desktop"
chmod 644 "$APP_DIR/com.marley.FastFlowLM-gtk.desktop"

# Install memlock limits config (auto setup)
echo "  -> Installing memlock configuration (unlimited memory locking)..."
mkdir -p /etc/security/limits.d
echo '* - memlock unlimited' > /etc/security/limits.d/99-fastflowlm-gtk.conf
chmod 644 /etc/security/limits.d/99-fastflowlm-gtk.conf
echo "     Memlock config installed. You MUST log out and back in (or reboot) for it to take effect."
echo "     The app will show a hard blocking page until unlimited memlock is active."

# Create executable wrapper
cat <<EOF > "$BIN_DIR/fastflowlm-gtk"
#!/bin/sh
export PYTHONPATH="$INSTALL_DIR:\$PYTHONPATH"
exec python3 $INSTALL_DIR/app.py "\$@"
EOF
chmod 755 "$BIN_DIR/fastflowlm-gtk"

# Update Desktop/Icon Database
update-desktop-database -q
gtk-update-icon-cache -f -t /usr/share/icons/hicolor

echo "Installation complete! You can now launch 'FastFlowLM-gtk' from your app menu."
read -p "Press enter to exit..."
