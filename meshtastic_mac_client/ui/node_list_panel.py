from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel)
from PyQt6.QtCore import pyqtSignal
from meshtastic_mac_client.core.database import DatabaseManager

class NodeListPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Short Name", "SNR", "Battery", "Last Heard"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.table)

    def on_node_update(self, node):
        # Update UI with new node data
        # In a real app, we would check if row exists, else append
        # For simplicity, we refresh the list from DB on connection
        self.refresh_list()

    def refresh_list(self):
        nodes = self.main.db.get_nodes()
        self.table.setRowCount(len(nodes))
        for row, node_data in enumerate(nodes):
            self.table.setItem(row, 0, QTableWidgetItem(node_data['id']))
            self.table.setItem(row, 1, QTableWidgetItem(node_data['short_name'] or "N/A"))
            self.table.setItem(row, 2, QTableWidgetItem(str(node_data['snr'])))
            self.table.setItem(row, 3, QTableWidgetItem(str(node_data['battery'])))
            self.table.setItem(row, 4, QTableWidgetItem(node_data['last_heard']))
