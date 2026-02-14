#!/bin/bash
# install.sh

set -e

echo ">>> Phase 1: OS Detection and Package Installation"
if [ -f /etc/os-release ]; then
    source /etc/os-release
    if [[ "$ID" == "manjaro" || "$ID" == "arch" ]]; then
        sudo pacman -Syu --needed --noconfirm python python-pip python-virtualenv wget unzip
    elif [[ "$ID" == "ubuntu" || "$ID" == "debian" ]]; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-venv python3-pip wget unzip
    else
        echo "Unsupported OS. Please install Python, wget, and unzip manually."
    fi
fi

echo ">>> Phase 2: Fetching Xray-core Binary"
ARCH=$(uname -m)
XRAY_URL=""

if [[ "$ARCH" == "x86_64" ]]; then
    XRAY_URL="https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
elif [[ "$ARCH" == "aarch64" ]]; then
    XRAY_URL="https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-arm64-v8a.zip"
else
    echo "Architecture $ARCH is not supported by this script."
    exit 1
fi

mkdir -p bin
wget -qO xray.zip "$XRAY_URL"
unzip -qo xray.zip xray -d bin/
rm xray.zip
chmod +x bin/xray

echo ">>> Phase 3: Setting up Python Virtual Environment"
python3 -m venv venv
./venv/bin/pip install --upgrade pip

# تغییر کلیدی در این خط اعمال شده است:
./venv/bin/pip install PyQt5 "requests[socks]" pysocks

echo ">>> Phase 4: Creating XDG Desktop Entry (App Menu Integration)"
APP_DIR=$(pwd)
DESKTOP_FILE="$HOME/.local/share/applications/xray-linux-client.desktop"

mkdir -p "$HOME/.local/share/applications"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=Xray Linux Client
Comment=Graphical Proxy Manager for Xray
Exec=$APP_DIR/run.sh
Path=$APP_DIR
Icon=network-vpn
Terminal=false
Categories=Network;Utility;
EOF

chmod +x "$DESKTOP_FILE"
chmod +x run.sh

echo ">>> Installation Complete. You can now find 'Xray Linux Client' in your application menu."
