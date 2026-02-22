import asyncio
import logging
from bleak import BleakScanner, BleakClient
from pubsub import pub
from meshtastic.ble_interface import BLEInterface
from meshtastic.protobuf import mesh_pb2
from meshtastic_mac_client.core.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeshtasticManager:
    def __init__(self, db_manager, loop):
        self.db = db_manager
        self.loop = loop

    async def scan_devices(self):
        """Scan for Meshtastic BLE devices."""
        devices = await BleakScanner.discover(timeout=10.0)
        meshtastic_devices = []
        for device in devices:
            if device.name and ('Meshtastic' in device.name or 'meshtastic' in device.name.lower()):
                meshtastic_devices.append(device)
        return meshtastic_devices

    async def connect(self, device_address):
        """Connect to a specific device using Meshtastic library."""
        try:
            self.client = BLEInterface(address=device_address, noProto=False)
            
            pub.subscribe(self.on_receive, "meshtastic.receive")
            pub.subscribe(self.on_node_update, "meshtastic.node.updated")
            
            self.is_connected = True
            self.device_name = device_address
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    async def disconnect(self):
        if self.client:
            await self.client.close()
            self.is_connected = False
            self.client = None

    async def send_text(self, text, channel_index=0, destination=None):
        if not self.is_connected:
            return False
        try:
            self.client.sendText(text, channelIndex=channel_index, destinationId=destination)
            return True
        except Exception as e:
            logger.error(f"Send failed: {e}")
            return False

    def on_receive(self, packet, interface):
        """Handle incoming packets and persist to DB."""
        node_id = packet.get("fromId", packet.get("from", "Unknown"))
        decoded = packet.get("decoded", {})
        payload = decoded.get("text", "")
        channel = packet.get("channel", 0)
        
        # Save to SQLite
        self.db.save_message(node_id, "REMOTE", payload, channel)
        
        # Update UI safely
        if self.on_message_received_cb:
            self.loop.call_soon_threadsafe(
                self.on_message_received_cb, node_id, "REMOTE", payload, channel
            )

    def on_node_update(self, node, interface):
        """Handle node database updates."""
        self.db.save_node(node)
        
        if self.on_node_updated_cb:
            self.loop.call_soon_threadsafe(self.on_node_updated_cb, node)