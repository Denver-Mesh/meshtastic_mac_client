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
            long_name = node['user'].get('longName', 'Unknown')
            hex_id = node['user'].get('id', node_id)
            return f"{long_name} <small>({hex_id})</small>"
        
        return f"Unknown <small>({node_id})</small>"

    async def scan_devices(self):
        """Scan for Meshtastic BLE devices."""
        await BleakScanner.discover(timeout=2.0)
        devices = await BleakScanner.discover(timeout=5.0)
        return [d for d in devices if d.name]

    async def connect(self, device_address):
        """Connect to a specific device."""
        if self.is_connected:
            return True

        try:
            logger.info(f"Manager: Initializing BLE connection to {device_address}")
            
            def _init_ble():
                return BLEInterface(address=device_address, noProto=False)

            self.client = await self.loop.run_in_executor(None, _init_ble)
            
            pub.subscribe(self.on_receive, "meshtastic.receive")
            pub.subscribe(self.on_node_update, "meshtastic.node.updated")
            
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Manager: Connection failed error: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        if self.client:
            pub.unsubscribe(self.on_receive, "meshtastic.receive")
            pub.unsubscribe(self.on_node_update, "meshtastic.node.updated")
            try:
                await self.loop.run_in_executor(None, self.client.close)
                self.is_connected = False
                self.client = None
            except Exception as e:
                logger.error(f"Disconnect error: {e}")

    def on_receive(self, packet, interface):
        """Handle incoming packets."""
        decoded = packet.get("decoded", {})
        if decoded.get("portnum") != "TEXT_MESSAGE_APP":
            return

        node_id = packet.get("fromId") or packet.get("from") or "Unknown"
        payload = decoded.get("text", "").strip()
        if not payload: return

        channel = packet.get("channel", 0)
        self.db.save_message(node_id, "REMOTE", payload, channel)
        display_name = self.get_node_display_name(node_id)
        
        if self.on_message_received_cb:
            self.loop.call_soon_threadsafe(
                self.on_message_received_cb, display_name, "REMOTE", payload, channel
            )

    def on_node_update(self, node, interface):
        """Update the local node cache."""
        node_id_int = node.get('num')
        node_id_hex = node.get('user', {}).get('id')
        if node_id_int: self.nodes[node_id_int] = node
        if node_id_hex: self.nodes[node_id_hex] = node
            
        self.db.save_node(node)
        if self.on_node_updated_cb:
            self.loop.call_soon_threadsafe(self.on_node_updated_cb, node, interface)

    async def send_text(self, text, channel_index=0, destination=None):
        """Send a text message over the radio."""
        if not self.is_connected or not self.client:
            return False
            
        # Use 0xFFFFFFFF for broadcast (all nodes) if no destination is provided
        target = destination if destination is not None else 0xFFFFFFFF
        
        try:
            # Explicitly pass destinationId to avoid None warnings in the library
            self.client.sendText(text, destinationId=target, channelIndex=channel_index)
            
            self.db.save_message("USER", "USER", text, channel_index)
            
            if self.on_message_received_cb:
                self.loop.call_soon_threadsafe(
                    self.on_message_received_cb, "Me", "USER", text, channel_index
                )
            return True
        except Exception as e:
            logger.error(f"Send failed: {e}")
            return False

    def get_local_node_name(self):
        """Returns the Long Name of the connected radio."""
        if not self.client or not self.is_connected:
            return None

        try:
            # For BLE, we fetch the local node info dictionary
            my_node = self.client.getMyNodeInfo()
            if not my_node:
                return None

            # Try to get the ID (usually 'num' or 'user.id')
            my_id_int = my_node.get('num')

            # Check our local cache using the integer ID
            node = self.nodes.get(my_id_int)
            if node and 'user' in node:
                return node['user'].get('longName')

            # Fallback to the user dictionary inside my_node
            return my_node.get('user', {}).get('longName')

        except Exception as e:
            logger.error(f"Failed to get local node name: {e}")
            return None