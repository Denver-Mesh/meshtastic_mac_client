from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import pyqtSignal
from meshtastic_mac_client.core.meshtastic_manager import MeshtasticManager

class AdminPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("Remote Configuration"))
        
        self.txt_dest = QLineEdit()
        self.txt_dest.setPlaceholderText("Destination Node ID")
        self.layout.addWidget(self.txt_dest)

        self.txt_cmd = QLineEdit()
        self.txt_cmd.setPlaceholderText("Command (e.g. reboot)")
        self.layout.addWidget(self.txt_cmd)

        self.btn_exec = QPushButton("Execute Command")
        self.btn_exec.clicked.connect(self.execute_cmd)
        self.layout.addWidget(self.btn_exec)

    async def execute_cmd(self):
        dest = self.txt_dest.text()
        cmd = self.txt_cmd.text()
        
        if not dest or not cmd:
            QMessageBox.warning(self, "Error", "Please enter Destination ID and Command")
            return

        # Logic to send remote command would go here
        # This is a placeholder for the specific protobuf handling required by Meshtastic
        QMessageBox.information(self, "Sent", f"Command '{cmd}' sent to {dest}")

