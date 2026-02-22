from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFormLayout,
                             QSpinBox, QComboBox, QPushButton, QGroupBox)
from PyQt6.QtCore import pyqtSignal
from meshtastic_mac_client.core.meshtastic_manager import MeshtasticManager

class ConfigPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.main = parent
        self.layout = QVBoxLayout(self)

        # Radio Settings Group
        radio_group = QGroupBox("Radio Settings")
        radio_layout = QFormLayout()

        self.spin_region = QSpinBox()
        self.spin_region.setRange(0, 255) # Example range
        self.spin_region.setValue(9)      # Default US
        radio_layout.addRow("Region Code:", self.spin_region)

        self.combo_modem = QComboBox()
        self.combo_modem.addItems(["LongFast", "MediumSlow", "ShortFast"])
        radio_layout.addRow("Modem Preset:", self.combo_modem)

        radio_group.setLayout(radio_layout)
        self.layout.addWidget(radio_group)

        # Apply Button
        self.btn_apply = QPushButton("Apply Configuration")
        self.btn_apply.clicked.connect(self.apply_config)
        self.layout.addWidget(self.btn_apply)

    async def apply_config(self):
        # Construct config object
        config = {
            "radio": {
                "region": self.spin_region.value(),
                "modemConfig": self.combo_modem.currentText()
            }
        }

        # Disable button to prevent double-clicks
        self.btn_apply.setEnabled(False)
        self.btn_apply.setText("Applying...")

        try:
            # Call the newly added manager method
            success = await self.main.manager.send_config(config)
            
            if success:
                QMessageBox.information(self, "Success", "Configuration applied and radio rebooting.")
            else:
                QMessageBox.warning(self, "Error", "Failed to apply configuration.")
        finally:
            self.btn_apply.setEnabled(True)
            self.btn_apply.setText("Apply Configuration")