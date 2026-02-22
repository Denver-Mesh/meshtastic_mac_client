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
        """Save or update node info using dictionary-safe lookups."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            user = node.get('user', {})
            cursor.execute('''
                INSERT OR REPLACE INTO nodes
                (id, short_name, long_name, snr, battery, last_heard, position_lat, position_lon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.get('id'),
                user.get('shortName'),
                user.get('longName'),
                node.get('snr', 0),
                node.get('device_metrics', {}).get('battery_level'),
                datetime.now().isoformat(),
                node.get('position', {}).get('lat'),
                node.get('position', {}).get('lon')
            ))
            conn.commit()

    def get_all_nodes(self):
        """Fetch all nodes from the DB and return a dict keyed by node ID."""
        nodes = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # FIX: Query the columns that actually exist
                cursor.execute("SELECT id, long_name FROM nodes")
                rows = cursor.fetchall()
                
                for row in rows:
                    # Reconstruct a structure the Manager expects
                    nodes[row['id']] = {
                        'user': {
                            'longName': row['long_name'],
                            'id': row['id']
                        }
                    }
        except Exception as e:
            print(f"Error loading nodes from DB: {e}")
        return nodes

    def get_nodes(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM nodes ORDER BY last_heard DESC')
            return cursor.fetchall()

