# Xray Cross-Platform GUI Client

A lightweight, concurrent, and thread-safe graphical interface for managing V2Ray/Xray subscriptions. Designed for seamless operation on both Linux distributions and Windows.

## Features
* **Cross-Platform Compatibility:** Native execution on Linux (GNOME/KDE Plasma) and Windows systems.
* **Concurrent Ping Test:** Asynchronous batch latency testing via thread pooling, preventing GUI freezes.
* **Smart Subscription Parsing:** Auto-decodes customized "Dummy Nodes" to extract metadata (Data Usage & Expiry) and translates localized metrics.
* **Automated System Proxy:** Direct API interaction with Windows Registry, `gsettings`, and `kwriteconfig5` for global routing without requiring administrative privileges.
* **Dual-Inbound Routing:** Segregates SOCKS and HTTP traffic to prevent protocol mismatch errors in CLI utilities.

## Installation

### Linux (Ubuntu, Debian, Arch, Fedora, openSUSE)
Open your terminal and run:
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
cd YOUR_REPOSITORY_NAME
chmod +x install.sh
./install.sh
```
*An application shortcut will be added to your OS Application Menu.*

### Windows
1. Clone or download the repository as a ZIP file.
2. Ensure you have [Python](https://www.python.org/downloads/) installed (check "Add python.exe to PATH" during installation).
3. Double-click the `install.bat` file.
4. *A shortcut will be automatically created on your Desktop.*

## Project Structure
* `core.py`: Manages OS interactions, Xray-core binary execution, and HTTP parsing.
* `ui.py`: Contains the PyQt5 interface structure and dialog models.
* `main.py`: The application controller handling state and thread concurrence.
