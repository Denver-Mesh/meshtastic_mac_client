import asyncio
import logging
from bleak import BleakScanner
from pubsub import pub
from meshtastic.ble_interface import BLEInterface
from meshtastic_mac_client.core.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeshtasticManager:
    def __init__(self, db_manager, loop):
        self.db = db_manager
        self.loop = loop
        self.client = None
        self.is_connected = False
        self.on_message_received_cb = None
        self.on_node_updated_cb = None
        
        # 1. Initialize the cache and pre-load from DB
        self.nodes = self.db.get_all_nodes()
        logger.info(f"Pre-loaded {len(self.nodes)} nodes from database.")

    def get_node_display_name(self, node_id):
        """Returns name in format: LongName (hexid)"""
        node = self.nodes.get(node_id)
        if node and 'user' in node:
            # Use the data structure stored in your DB
            long_name = node['user'].get('longName', 'Unknown')
            hex_id = node['user'].get('id', node_id)
            return f"{long_name} <small>({hex_id})</small>"
        
        # Fallback if node isn't in cache yet
        return f"Unknown <small>({node_id})</small>"

    async def scan_devices(self):
        """Scan for Meshtastic BLE devices with a cache warm-up."""
        # Warm up the macOS BLE cache
        await BleakScanner.discover(timeout=2.0)
        # Actual scan
        devices = await BleakScanner.discover(timeout=5.0) # 5s is usually plenty after a warmup
        return [d for d in devices if d.name]

    async def connect(self, device_address):
        """Connect to a specific device without blocking the UI."""
        if self.is_connected:
            logger.info("Manager: Already connected, skipping request.")
            return True

        try:
            logger.info(f"Manager: Initializing BLE connection to {device_address}")
            
            def _init_ble():
                # This call is synchronous and contains the 10s internal scan
                return BLEInterface(address=device_address, noProto=False)

            # We use the executor so the UI stays responsive during the 10s scan
            self.client = await self.loop.run_in_executor(None, _init_ble)
            
            pub.subscribe(self.on_receive, "meshtastic.receive")
            pub.subscribe(self.on_node_update, "meshtastic.node.updated")
            
            self.is_connected = True
            logger.info("Manager: Connection successful.")
            return True
        except Exception as e:
            # If the radio is busy or phone is connected, it lands here
            logger.error(f"Manager: Connection failed error: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        if self.client:
            # BLEInterface close is typically synchronous in the library
            self.client.close()
            self.is_connected = False
            self.client = None

    def on_receive(self, packet, interface):
        """Handle incoming packets and persist to DB."""
        decoded = packet.get("decoded", {})
        
        if decoded.get("portnum") != "TEXT_MESSAGE_APP":
            return

        node_id = packet.get("fromId") or packet.get("from") or "Unknown"
        payload = decoded.get("text", "").strip()
        
        if not payload:
            return

        channel = packet.get("channel", 0)
        self.db.save_message(node_id, "REMOTE", payload, channel)
        
        # Get the formatted name for the UI
        display_name = self.get_node_display_name(node_id)
        
        if self.on_message_received_cb:
            self.loop.call_soon_threadsafe(
                self.on_message_received_cb, display_name, "REMOTE", payload, channel
            )

    def on_node_update(self, node, interface):
        """Update the local node cache."""
        node_id_int = node.get('num')
        node_id_hex = node.get('user', {}).get('id')

        if node_id_int:
            self.nodes[node_id_int] = node
        if node_id_hex:
            self.nodes[node_id_hex] = node
            
        self.db.save_node(node)
        if self.on_node_updated_cb:
            self.loop.call_soon_threadsafe(self.on_node_updated_cb, node, interface)

    async def send_text(self, text, channel_index=0, destination=None):
        """Send a text message over the radio."""
        if not self.is_connected or not self.client:
            return False
        try:
            # sendText is a method provided by the Meshtastic BLEInterface
            self.client.sendText(text, channelIndex=channel_index, destinationId=destination)
            
            # Save our own message to the DB for history
            self.db.save_message("USER", "USER", text, channel_index)
            
            # Update the UI locally
            if self.on_message_received_cb:
                # We show 'You' or 'USER' for our own messages
                self.on_message_received_cb("Me", "USER", text, channel_index)
            return True
        except Exception as e:
            logger.error(f"Send failed: {e}")
            return False