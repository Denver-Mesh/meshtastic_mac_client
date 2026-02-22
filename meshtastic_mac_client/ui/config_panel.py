from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFormLayout, 
                             QSpinBox, QComboBox, QPushButton, QGroupBox)
from PyQt6.QtCore import pyqtSignal
from core.meshtastic_manager import MeshtasticManager

class ConfigPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
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
        # Construct config object (simplified)
        config = {
            "radio": {
                "region": self.spin_region.value(),
                "modemConfig": self.combo_modem.currentText()
            }
        }
        success = await self.main.manager.send_config(config)
        if success:
            print("Config sent")

