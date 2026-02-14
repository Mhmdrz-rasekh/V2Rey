# Xray Linux Client

A lightweight, concurrent, and thread-safe graphical client for managing V2Ray/Xray subscriptions on Linux (Manjaro/Ubuntu).

## Features
- **Concurrent Ping Test:** Ping all servers simultaneously using a thread pool.
- **System Proxy Integration:** Automatically configures SOCKS, HTTP, and FTP proxy settings for GNOME and KDE Plasma.
- **Smart Subscription Parsing:** Decodes dummy nodes and extracts subscription data (Upload, Download, Expiry) accurately.
- **Dual Inbounds:** Binds separate ports for SOCKS and HTTP to prevent protocol mismatch errors in Linux utilities.
- **Self-Contained Execution:** Downloads its own Xray-core binary without requiring root privileges for system-wide installation.

## Prerequisites
- `wget` and `unzip`
- `python3`

## Installation
Run the following commands in your terminal. The script will automatically install dependencies, download the latest Xray-core, build a Python virtual environment, and create an app menu shortcut.

```bash
git clone https://github.com/Mhmdrz-rasekh/V2Rey.git
cd V2rey
chmod +x install.sh
./install.sh
```

## Usage
After installation, you can launch the app directly from your Linux Application Launcher by searching for **Xray Linux Client**. 
Alternatively, you can run it via terminal:
\`\`\`bash
./run.sh
\`\`\`
