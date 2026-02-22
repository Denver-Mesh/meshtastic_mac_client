from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtCore import QUrl
import folium
import os

class MapPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Setup Web View
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)
        
        # Setup Profile for offline support (Basic setup)
        profile = QWebEngineProfile.defaultProfile()
        # Note: For full offline support, you must download tiles and set cache path
        # profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        # profile.setHttpCacheLocation("/Users/YourName/Downloads/MapCache")

    def update_map(self, nodes):
        # Create Folium Map centered on first node or default
        m = folium.Map(location=[40.7128, -74.0060], zoom_start=13) # Default NYC
        
        # Add Nodes
        for node in nodes:
            lat = node.get('position_lat')
            lon = node.get('position_lon')
            if lat and lon:
                folium.Marker(
                    [lat, lon],
                    popup=f"{node['short_name']}<br>{node['id']}",
                    tooltip=node['short_name']
                ).add_to(m)

        # Save to temp HTML
        temp_file = "temp_map.html"
        m.save(temp_file)
        
        # Load into WebView
        self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(temp_file)))

