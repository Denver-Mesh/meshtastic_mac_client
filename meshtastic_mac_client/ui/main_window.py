from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget,
                             QVBoxLayout, QWidget, QMessageBox, QStatusBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from meshtastic_mac_client.core.database import DatabaseManager
from meshtastic_mac_client.core.meshtastic_manager import MeshtasticManager
from meshtastic_mac_client.ui.connection_panel import ConnectionPanel
from meshtastic_mac_client.ui.chat_panel import ChatPanel
from meshtastic_mac_client.ui.node_list_panel import NodeListPanel
from meshtastic_mac_client.ui.config_panel import ConfigPanel
from meshtastic_mac_client.ui.map_panel import MapPanel
from meshtastic_mac_client.ui.telemetry_panel import TelemetryPanel
from meshtastic_mac_client.ui.admin_panel import AdminPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Meshtastic macOS Client")
        self.resize(1200, 800)

        # Initialize Core
        self.db = DatabaseManager()
        self.manager = MeshtasticManager(self.db)

        # UI Setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create Panels
        self.conn_panel = ConnectionPanel(self)
        self.chat_panel = ChatPanel(self)
        self.nodes_panel = NodeListPanel(self)
        self.config_panel = ConfigPanel(self)
        self.map_panel = MapPanel(self)
        self.telemetry_panel = TelemetryPanel(self)
        self.admin_panel = AdminPanel(self)

        # Add to Tabs
        self.tabs.addTab(self.conn_panel, "Connection")
        self.tabs.addTab(self.chat_panel, "Chat")
        self.tabs.addTab(self.nodes_panel, "NodeDB")
        self.tabs.addTab(self.config_panel, "Config")
        self.tabs.addTab(self.map_panel, "Map")
        self.tabs.addTab(self.telemetry_panel, "Telemetry")
        self.tabs.addTab(self.admin_panel, "Admin")

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Disconnected")

        # Connect Manager Signals to UI Slots
        self.manager.on_message_received_cb = self.chat_panel.on_new_message
        self.manager.on_node_updated_cb = self.nodes_panel.on_node_update

    def update_status(self, message):
        self.status_bar.showMessage(message)

if __name__ == "__main__":
    import sys
    import qasync
    from PyQt6.QtWidgets import QApplication

    # Create the QApplication
    app = QApplication(sys.argv)

    # Create the Event Loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Create and Show Window
    window = MainWindow()
    window.show()

    # Run the loop
    with loop:
        loop.run_forever()

