from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget,
                             QVBoxLayout, QWidget, QMessageBox, QStatusBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
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
        self.manager.on_node_updated_cb = self.on_node_updated

        # Connect ConnectionPanel signals to update the Status Bar
        self.conn_panel.signals.connecting.connect(self.on_connecting)
        self.conn_panel.signals.connected.connect(self.on_device_connected)
        self.conn_panel.signals.disconnected.connect(self.on_device_disconnected)

        # Initial load from Database
        QTimer.singleShot(500, self.nodes_panel.refresh_list)
        QTimer.singleShot(1000, self.refresh_map)
        
        # Telemetry
        self.manager.on_telemetry_received_cb = self.telemetry_panel.handle_real_telemetry

        # Pre-populate map and list with nodes already in the database
        if self.manager.nodes:
            initial_nodes = list(self.manager.nodes.values())
            self.map_panel.update_map(initial_nodes)
            self.nodes_panel.refresh_list()

        # Connect the manager's update callback so new updates also refresh the map
        self.manager.on_node_updated_cb = self.on_node_updated

    def on_node_updated(self, node):
        """Called when a node's info is updated."""
        # Refresh data from manager
        all_nodes = list(self.manager.nodes.values())

        # Update the Map
        if hasattr(self, 'map_panel'):
            self.map_panel.update_map(all_nodes)

        # Update the List
        if hasattr(self, 'node_list_panel'):
            self.node_list_panel.refresh_list()

    def refresh_map(self):
        """Fetch all nodes from DB and refresh the map markers."""
        all_nodes = self.db.get_nodes()
        self.map_panel.update_map(all_nodes)

    def on_connecting(self, name):
        self.status_bar.showMessage(f"Connecting to {name}...")

    def on_device_connected(self, address):
        # Fetch the radio name from the manager
        radio_name = self.manager.get_local_node_name()
        self.status_bar.showMessage(f"Connected: {radio_name}")

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
        print("Starting graceful shutdown...")
        try:
            if self.manager:
                # 1. Wait for the manager to finish closing the radio
                await asyncio.wait_for(self.manager.disconnect(), timeout=5.0)

            # 2. Shutdown the executor to ensure no background threads are hanging
            # This is the "secret sauce" to prevent the force-quit requirement
            executor = self.loop._default_executor
            if executor:
                executor.shutdown(wait=True)

        except Exception as e:
            print(f"Shutdown notice: {e}")
        finally:
            # 3. Stop the loop and finally quit the application
            self.loop.stop()
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

