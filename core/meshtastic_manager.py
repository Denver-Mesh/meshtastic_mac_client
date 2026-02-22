import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="meshtastic.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize SQLite tables."""
        if not os.path.exists(self.db_path):
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Messages table
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
                # Nodes table
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (node_id, role, payload, channel)
                VALUES (?, ?, ?, ?)
            ''', (node_id, role, payload, channel))
            conn.commit()

    def get_messages(self, limit=50):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM messages ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return cursor.fetchall()

    def save_node(self, node):
        """Save or update node info."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO nodes 
                (id, short_name, long_name, snr, battery, last_heard, position_lat, position_lon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                node.id,
                node.short_name,
                node.long_name,
                node.metrics.snr if hasattr(node, 'metrics') and node.metrics else 0,
                node.device_metrics.battery_level if hasattr(node, 'device_metrics') and node.device_metrics else None,
                datetime.now().isoformat(),
                node.position.lat if hasattr(node, 'position') and node.position else None,
                node.position.lon if hasattr(node, 'position') and node.position else None
            ))
            conn.commit()

    def get_nodes(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM nodes ORDER BY last_heard DESC')
            return cursor.fetchall()

