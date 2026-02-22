# Meshtastic macOS Client

A native, fully-featured desktop application built with **PyQt6** and **qasync** to manage Meshtastic nodes via Bluetooth Low Energy (BLE) on macOS. This client provides a comprehensive interface for messaging, node management, configuration, and telemetry visualization without freezing the GUI.

## Features

*   **Native GUI:** Built with PyQt6 for a seamless macOS experience.
*   **Asynchronous BLE:** Uses `qasync` and `bleak` to handle Bluetooth connections without blocking the interface.
*   **Messaging:** Send and receive text messages on Primary, Secondary, and Direct Channels.
*   **NodeDB Management:** Live, sortable list of all mesh nodes with details (SNR, Battery, Position).
*   **Configuration:** Modify LoRa radio settings (Region, Modem Presets) and Channel configurations.
*   **Offline Mapping:** Integrated `folium` and `PyQtWebEngine` to visualize node locations. Supports loading local map tiles for off-grid use.
*   **Telemetry Dashboard:** Real-time plotting of battery voltage and signal strength using `pyqtgraph`.
*   **Local Persistence:** SQLite database logs all messages and node history locally.

## Prerequisites

*   **macOS:** 10.15 (Catalina) or later.
*   **Python:** 3.10 or higher.
*   **pipx:** A tool for installing and running Python applications in isolated environments. Install it via Homebrew (`brew install pipx`) or via pip (`pip install pipx`).
*   **Hardware:** A Meshtastic device (e.g., Heltec V3, RAK4631, T-Echo) with Bluetooth enabled.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd meshtastic_mac_client
    ```

2.  **Install the application:**
    *Note: Ensure you have a `pyproject.toml` or `setup.py` file in the root directory for `pipx install .` to work correctly.*
    ```bash
    pipx install .
    ```

## Usage

1.  **Run the application:**
    ```bash
    meshtastic-mac-client
    ```

2.  **Grant Bluetooth Permissions:**
    *   On macOS, go to **System Settings > Privacy & Security > Bluetooth**.
    *   Ensure your Python application (or Terminal) has permission to access Bluetooth.

3.  **Connect:**
    *   Click **Scan Devices** to find your Meshtastic node.
    *   Select it from the dropdown and click **Connect**.

## Offline Maps

The application includes a mapping feature that can load tiles from a local directory to function without an internet connection.

1.  Create a folder named `offline_tiles` inside the `assets` directory.
2.  Download OpenStreetMap tiles (`.png` files) for your area of interest and place them into this folder.
3.  Update the `map_panel.py` file to point the `QWebEngineProfile` cache location to this folder.

## Project Structure

The application is modular, separating logic from UI components:

```text
meshtastic_mac_client/
├── main.py                 # Entry point (qasync loop setup)
├── requirements.txt        # Python dependencies
├── core/
│   ├── __init__.py
│   ├── database.py         # SQLite persistence layer
│   └── meshtastic_manager.py # BLE connection & API bridge
├── ui/
│   ├── __init__.py
│   ├── main_window.py      # Main container
│   ├── connection_panel.py # Scan/Connect UI
│   ├── chat_panel.py       # Messaging UI
│   ├── node_list_panel.py  # NodeDB visualization
│   ├── config_panel.py     # Radio/Channel settings
│   ├── map_panel.py        # WebEngine mapping
│   ├── telemetry_panel.py  # Graphs
│   └── admin_panel.py      # Remote commands
└── assets/
    └── offline_tiles/      # (Optional) Local map tiles

