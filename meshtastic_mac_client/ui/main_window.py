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
import asyncio

class MainWindow(QMainWindow):
    def __init__(self, loop):
        super().__init__()
        self.loop = loop
        self.db = DatabaseManager()
        self.manager = MeshtasticManager(self.db, self.loop)

        # UI Setup
        self.setWindowTitle("Meshtastic macOS Client")
        self.resize(1200, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

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

        # Connect ConnectionPanel signals to update the Status Bar
        self.conn_panel.signals.connected.connect(self.on_device_connected)
        self.conn_panel.signals.disconnected.connect(self.on_device_disconnected)

        # Initial map load from Database
        self.refresh_map()

    def on_node_updated(self, node, interface):
        """Called by the manager when a node changes."""
        # Update the Node List tab
        self.nodes_panel.on_node_update(node, interface)
        
        # Update the Map tab
        self.refresh_map()

    def refresh_map(self):
        """Fetch all nodes from DB and refresh the map markers."""
        all_nodes = self.db.get_nodes()
        self.map_panel.update_map(all_nodes)

    def on_device_connected(self, address):
        # Fetch the radio name from the manager
        radio_name = self.manager.get_local_node_name() or "Radio"
        self.status_bar.showMessage(f"Connected: {radio_name})")

    def on_device_disconnected(self):
        self.status_bar.showMessage("Disconnected")

    def update_status(self, message):
        self.status_bar.showMessage(message)

    def closeEvent(self, event):
        """Handle graceful shutdown when the user clicks 'X'."""
        # Hide the window immediately so the user sees the app 'closing'
        self.hide()

        # Create the task for cleanup
        asyncio.create_task(self.handle_exit(event))

        # Ignore the event for now; handle_exit will call QApplication.quit()
        # which will properly destroy everything once cleanup is done.
        event.ignore()

    async def handle_exit(self, event):
        """Cleanup resources and stop the loop."""
        self.status_bar.showMessage("Shutting down...")

        try:
            # 1. Disconnect the radio if connected
            # We use a shield to ensure the disconnect finishes even if the window closes
            if self.manager.is_connected:
                await asyncio.shield(asyncio.wait_for(self.manager.disconnect(), timeout=2.0))

        except asyncio.TimeoutError:
            print("Shutdown: Disconnect timed out.")
        except Exception as e:
            print(f"Error during shutdown: {e}")

        finally:
            # 2. Crucially: Stop the qasync loop first
            self.loop.stop()
            # 3. Then tell the application to exit
            QApplication.instance().quit()

if __name__ == "__main__":
    import sys
    import qasync
    import asyncio
    from PyQt6.QtWidgets import QApplication

    # Create the QApplication
    app = QApplication(sys.argv)

    # Create the Event Loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Create and Show Window
    window = MainWindow(loop)
    window.show()

    # Run the loop
    with loop:
        loop.run_forever()

