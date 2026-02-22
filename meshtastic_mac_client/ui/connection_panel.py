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
        self.layout = QVBoxLayout(self)

        # Scan Button
        self.btn_scan = QPushButton("Scan Devices")
        self.btn_scan.clicked.connect(self.scan_devices)
        self.layout.addWidget(self.btn_scan)

        # Device Selection
        self.layout.addWidget(QLabel("Select Device:"))
        self.combo_devices = QComboBox()
        self.layout.addWidget(self.combo_devices)

        # Connect Button
        self.btn_scan.clicked.connect(lambda: asyncio.create_task(self.scan_devices()))
        self.btn_connect.clicked.connect(lambda: asyncio.create_task(self.connect_device()))
        self.layout.addWidget(self.btn_connect)

        # Disconnect Button
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.clicked.connect(self.disconnect_device)
        self.btn_disconnect.setEnabled(False)
        self.layout.addWidget(self.btn_disconnect)

        # Status
        self.lbl_status = QLabel("Status: Idle")
        self.layout.addWidget(self.lbl_status)

    async def scan_devices(self):
        self.lbl_status.setText("Scanning...")
        devices = await self.main.manager.scan_devices()
        self.combo_devices.clear()
        for dev in devices:
            self.combo_devices.addItem(dev.name, dev.address)
        self.lbl_status.setText(f"Found {len(devices)} devices")

    async def connect_device(self):
        address = self.combo_devices.currentData()
        if not address:
            return
        
        success = await self.main.manager.connect(address)
        if success:
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
            self.lbl_status.setText("Status: Connected")
            self.signals.connected.emit(address)

    async def disconnect_device(self):
        await self.main.manager.disconnect()
        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.lbl_status.setText("Status: Disconnected")
        self.signals.disconnected.emit()

