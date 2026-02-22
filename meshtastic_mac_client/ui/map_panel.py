import os
import re
import folium
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView

class MapPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)

    def update_map(self, nodes):
        # Default to Longmont, CO (NV0N area)
        center_lat, center_lon = 40.1672, -105.1019
        
        valid_nodes = [n for n in nodes if n.get('position_lat') and n.get('position_lon')]
        if valid_nodes:
            center_lat = valid_nodes[0]['position_lat']
            center_lon = valid_nodes[0]['position_lon']

        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        for node in valid_nodes:
            # Note: We use the names as stored in the SQLite DB (snake_case)
            name = node.get('long_name') or node.get('short_name') or str(node.get('id'))
            folium.Marker(
                [node['position_lat'], node['position_lon']],
                popup=f"<b>{name}</b><br>ID: {node['id']}",
                tooltip=name
            ).add_to(m)

        # 1. Generate the raw HTML
        raw_html = m.get_root().render()

        # 2. Robust Fix for "L is not defined" and "SyntaxError"
        # We use a regex to find inline <script> blocks and wrap them in a retry loop.
        def protect_script(match):
            full_tag = match.group(0)
            script_content = match.group(1)
            
            # Skip external scripts (those with a 'src' attribute)
            if 'src=' in full_tag.lower():
                return full_tag
            
            # If the script uses Leaflet (L) or the window loader, wrap it
            if 'L.' in script_content or 'window.onload' in script_content:
                return (
                    "<script>\n"
                    "(function retry() {\n"
                    "  if (typeof L !== 'undefined') {\n"
                    f"    {script_content}\n"
                    "  } else {\n"
                    "    setTimeout(retry, 100);\n"
                    "  }\n"
                    "})();\n"
                    "</script>"
                )
            return full_tag

        # This regex matches everything inside <script>...</script> pairs
        protected_html = re.sub(r'<script[^>]*>(.*?)</script>', protect_script, raw_html, flags=re.DOTALL)

        # 3. Save and Load
        temp_path = os.path.abspath("temp_map.html")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(protected_html)
        
        self.web_view.setUrl(QUrl.fromLocalFile(temp_path))