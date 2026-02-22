import os
import folium
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

class MapPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)

    def update_map(self, nodes):
        # Default to Longmont, CO (NV0N)
        center_lat, center_lon = 40.1672, -105.1019
        
        # If we have nodes with positions, center on the first one found
        for node in nodes:
            if node['position_lat'] and node['position_lon']:
                center_lat = node['position_lat']
                center_lon = node['position_lon']
                break

        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        # Add Markers
        for node in nodes:
            lat = node.get('position_lat')
            lon = node.get('position_lon')
            if lat and lon:
                name = node.get('long_name') or node.get('short_name') or node.get('id')
                folium.Marker(
                    [lat, lon],
                    popup=f"<b>{name}</b><br>ID: {node['id']}<br>SNR: {node['snr']}",
                    tooltip=node.get('short_name', 'Unknown')
                ).add_to(m)

        # Use an absolute path for the temp file to avoid permission/location issues
        temp_path = os.path.abspath("temp_map.html")
        m.save(temp_path)

        # Load using QUrl from local file - this is more stable than setHtml for Folium
        self.web_view.setUrl(QUrl.fromLocalFile(temp_path))