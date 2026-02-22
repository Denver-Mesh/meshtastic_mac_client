# database.py

import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="meshtastic.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize SQLite tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT,
                    role TEXT,
                    payload TEXT,
                    channel INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    short_name TEXT,
                    long_name TEXT,
                    snr REAL,
                    battery INTEGER,
                    last_heard DATETIME,
                    position_lat REAL,
                    position_lon REAL
                )
            ''')
            conn.commit()

    def save_message(self, node_id, role, payload, channel):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO messages (node_id, role, payload, channel)
                    VALUES (?, ?, ?, ?)
                ''', (node_id, role, payload, channel))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save message: {e}")

    def save_node(self, node):
        """Save or update node info using dictionary-safe lookups."""
        user = node.get('user', {})
        node_id = user.get('id')
        
        if not node_id:
            return # Skip nodes with no ID yet

        # Handle nested position data (Library uses latitude/longitude)
        pos = node.get('position', {})
        lat = pos.get('latitude')
        lon = pos.get('longitude')

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO nodes
                    (id, short_name, long_name, snr, battery, last_heard, position_lat, position_lon)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    node_id,
                    user.get('shortName'),
                    user.get('longName'),
                    node.get('snr', 0),
                    node.get('device_metrics', {}).get('battery_level'),
                    datetime.now().isoformat(),
                    lat,
                    lon
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving node {node_id}: {e}")

    def get_all_nodes(self):
        """Fetch all nodes for the Manager cache."""
        nodes = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM nodes")
                for row in cursor.fetchall():
                    nodes[row['id']] = {
                        'id': row['id'],
                        'user': {
                            'longName': row['long_name'],
                            'shortName': row['short_name'],
                            'id': row['id']
                        },
                        'snr': row['snr'],
                        'position_lat': row['position_lat'],
                        'position_lon': row['position_lon']
                    }
        except Exception as e:
            logger.error(f"Error loading nodes: {e}")
        return nodes

    def get_nodes(self):
        """Fetch all nodes as rows for the UI list."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM nodes ORDER BY last_heard DESC')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching nodes for list: {e}")
            return []