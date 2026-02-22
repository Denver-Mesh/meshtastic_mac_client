import os
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
import folium

class MapPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)

    def update_map(self, nodes):
        # Default to Longmont, CO (NV0N area)
        center_lat, center_lon = 40.1672, -105.1019
        
        # Center on the first node with a valid position
        for node in nodes:
            if node.get('position_lat') and node.get('position_lon'):
                center_lat = node['position_lat']
                center_lon = node['position_lon']
                break

        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        for node in nodes:
            lat = node.get('position_lat')
            lon = node.get('position_lon')
            if lat and lon:
                # Use .get() to avoid KeyErrors if data is missing
                name = node.get('long_name') or node.get('short_name') or node.get('id')
                snr = node.get('snr', 'N/A')
                
                folium.Marker(
                    [lat, lon],
                    popup=f"<b>{name}</b><br>ID: {node['id']}<br>SNR: {snr}",
                    tooltip=node.get('short_name', 'Unknown')
                ).add_to(m)

        # FIX: Use an absolute path for the temporary file
        # This prevents issues where the JS can't find dependencies
        temp_path = os.path.abspath("temp_map.html")
        m.save(temp_path)
        
        # FIX: Load via setUrl + QUrl.fromLocalFile instead of setHtml
        # This allows the browser engine to handle external CDN scripts more reliably
        self.web_view.setUrl(QUrl.fromLocalFile(temp_path))