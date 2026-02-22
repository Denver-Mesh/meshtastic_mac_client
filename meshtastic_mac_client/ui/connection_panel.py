from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                             QComboBox, QLabel, QProgressBar)
from PyQt6.QtCore import pyqtSignal, QObject
import asyncio
from meshtastic_mac_client.core.meshtastic_manager import MeshtasticManager

class ConnectionSignals(QObject):
    connected = pyqtSignal(str)
    disconnected = pyqtSignal()

class ConnectionPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.main = parent
        self.signals = ConnectionSignals()
        self._is_connecting = False  # Add a guard flag
        self.layout = QVBoxLayout(self)

        # ... (Scan button setup)
        self.btn_scan = QPushButton("Scan Devices")
        self.btn_scan.clicked.connect(lambda: asyncio.create_task(self.scan_devices()))
        self.layout.addWidget(self.btn_scan)

        # ... (Combo setup)
        self.layout.addWidget(QLabel("Select Device:"))
        self.combo_devices = QComboBox()
        self.layout.addWidget(self.combo_devices)

        # Connect Button
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.clicked.connect(lambda: asyncio.create_task(self.connect_device()))
        self.layout.addWidget(self.btn_connect)

        # Disconnect Button
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.clicked.connect(lambda: asyncio.create_task(self.disconnect_device()))
        self.btn_disconnect.setEnabled(False)
        self.layout.addWidget(self.btn_disconnect)

        self.lbl_status = QLabel("Status: Idle")
        self.layout.addWidget(self.lbl_status)

    async def scan_devices(self):
        self.lbl_status.setText("Waking up Bluetooth...") # Feedback for the pulse
        devices = await self.main.manager.scan_devices()
        
        self.combo_devices.clear()
        for dev in devices:
            self.combo_devices.addItem(dev.name, dev.address)
        
        self.lbl_status.setText(f"Found {len(devices)} devices")

    async def connect_device(self):
        # Don't allow multiple clicks
        if self._is_connecting or self.main.manager.is_connected:
            return
            
        address = self.combo_devices.currentData()
        if not address:
            self.lbl_status.setText("Status: Select a device first")
            return
        
        self._is_connecting = True
        self.btn_connect.setEnabled(False)
        self.btn_scan.setEnabled(False)
        self.lbl_status.setText(f"Status: Connecting to {self.combo_devices.currentText()}...")

        try:
            # 2. Call the manager
            success = await self.main.manager.connect(address)
            
            if success:
                self.btn_disconnect.setEnabled(True)
                radio_name = self.main.manager.get_local_node_name() or "Connected"
                self.lbl_status.setText(f"Status: Connected to {radio_name}")
                self.signals.connected.emit(address)
            else:
                self.btn_connect.setEnabled(True)
                self.btn_scan.setEnabled(True)
                self.lbl_status.setText("Status: Connection Failed")
        finally:
            self._is_connecting = False

    async def disconnect_device(self):
        await self.main.manager.disconnect()
        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.lbl_status.setText("Status: Disconnected")
        self.signals.disconnected.emit()

