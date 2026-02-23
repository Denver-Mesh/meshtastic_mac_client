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

To ensure Bluetooth stability on macOS, it is recommended to use Python 3.13.

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd meshtastic_mac_client
    ```

2.  **Install the application:**
    *Note: Ensure you have the `pyproject.toml` file in the root directory for `pipx install .` to work correctly.*
    ```bash
    pipx install --python python3.13 -e . --force    ```

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

### 4. Implementation Steps
1.  **Sync Files:** Update your `pyproject.toml` with the version pins above.
2.  **Clean Environment:**
    ```bash
    pipx uninstall meshtastic-mac-client
    rm -rf *.egg-info
    ```
3.  **Reinstall:**
    ```bash
    pipx install --python python3.13 -e .
    ```

By pinning `meshtastic>=2.7.7` in the `toml`, `pipx` will guarantee that the `meshtastic.ble` module is present in the virtual environment it creates.

## Offline Maps

The application includes a mapping feature that can load tiles from a local directory to function without an internet connection.

1.  Create a folder named `offline_tiles` inside the `assets` directory.
2.  Download OpenStreetMap tiles (`.png` files) for your area of interest and place them into this folder.
3.  Update the `map_panel.py` file to point the `QWebEngineProfile` cache location to this folder.
