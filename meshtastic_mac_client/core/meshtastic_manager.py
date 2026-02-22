import asyncio
import logging
from bleak import BleakScanner, BleakClient
from meshtastic import bluetooth_interface, mesh_interface
from meshtastic.protobuf import mesh_pb2
from meshtastic_mac_client.core.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeshtasticManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.client = None
        self.device_name = None
        self.is_connected = False
        self.loop = asyncio.get_running_loop()

    async def scan_devices(self):
        """Scan for Meshtastic BLE devices."""
        devices = await BleakScanner.discover()
        meshtastic_devices = []
        for device in devices:
            # Meshtastic devices usually advertise 'Meshtastic'
            if 'Meshtastic' in device.name or 'meshtastic' in device.name.lower():
                meshtastic_devices.append(device)
        return meshtastic_devices

    async def connect(self, device_name):
        """Connect to a specific device using Meshtastic library."""
        try:
            # The meshtastic library handles the BLE connection internally
            # We use the bluetooth_interface which is async
            self.client = bluetooth_interface.BluetoothInterface(
                deviceName=device_name,
                debug=False
            )
            
            # Connect logic
            await self.client.connect()
            self.is_connected = True
            self.device_name = device_name
            
            # Start listening
            self.client.onReceive = self.on_receive
            self.client.onNode = self.on_node_update
            
            logger.info(f"Connected to {device_name}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        if self.client:
            await self.client.close()
            self.is_connected = False
            self.client = None

    async def send_text(self, text, channel_index=0, destination=None):
        """Send a text message."""
        if not self.is_connected:
            return False
        
        try:
            # destination=None implies broadcast
            await self.client.sendText(
                text,
                channelIndex=channel_index,
                destinationId=destination
            )
            return True
        except Exception as e:
            logger.error(f"Send failed: {e}")
            return False

    async def send_config(self, config):
        """Send configuration to the node."""
        if not self.is_connected:
            return False
        try:
            await self.client.sendConfig(config)
            return True
        except Exception as e:
            logger.error(f"Config send failed: {e}")
            return False

    # --- Callbacks ---

    def on_receive(self, packet, interface):
        """Handle incoming packets."""
        # Extract data
        node_id = packet.get("from", "Unknown")
        role = packet.get("role", "UNKNOWN")
        payload = packet.get("decoded", {}).get("payload", "")
        channel = packet.get("channel", 0)
        
        # Persist
        self.db.save_message(node_id, role, payload, channel)
        
        # Trigger UI update (via event loop)
        asyncio.run_coroutine_threadsafe(
            self.loop.call_soon_threadsafe(self.on_message_received_cb, node_id, role, payload, channel),
            self.loop
        )

    def on_node_update(self, node, interface):
        """Handle node database updates."""
        # Persist
        self.db.save_node(node)
        
        # Trigger UI update
        asyncio.run_coroutine_threadsafe(
            self.loop.call_soon_threadsafe(self.on_node_updated_cb, node),
            self.loop
        )

    # --- UI Callback Slots ---
    def on_message_received_cb(self, node_id, role, payload, channel):
        # This will be connected to a signal in the UI
        pass

    def on_node_updated_cb(self, node):
        # This will be connected to a signal in the UI
        pass
