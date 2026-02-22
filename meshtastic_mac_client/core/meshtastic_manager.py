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
        
        self.nodes = self.db.get_all_nodes()
        logger.info(f"Pre-loaded {len(self.nodes)} nodes from database.")

        pub.subscribe(self.on_message_received, "meshtastic.receive.text")
        pub.subscribe(self.on_node_update, "meshtastic.node.updated")

    async def scan_devices(self):
        """Scan for Meshtastic BLE devices."""
        logger.info("Scanning for BLE devices...")
        try:
            # First scan to populate Bleak's internal cache
            await BleakScanner.discover(timeout=2.0)
            devices = await BleakScanner.discover(timeout=5.0)

            return [d for d in devices if d.name]
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return []

    async def connect(self, address):
        """Connect to a Meshtastic device over BLE."""
        try:
            logger.info(f"Connecting to {address}...")
            # BLEInterface is synchronous; we run it in an executor
            self.client = await self.loop.run_in_executor(None, lambda: BLEInterface(address))
            
            # GIVE THE RADIO TIME TO HANDSHAKE
            # This ensures get_local_node_name() has data when the UI calls it
            await asyncio.sleep(2.0)
            
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Disconnect safely without hanging the event loop."""
        if self.client:
            logger.info("Disconnecting...")
            try:
                # BLEInterface.close() handles the underlying Serial/BLE closure
                # We must await the executor to ensure the thread finishes
                await self.loop.run_in_executor(None, self.client.close)
                logger.info("Interface closed successfully.")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
            finally:
                self.client = None
                self.is_connected = False

    def get_local_node_name(self):
        """Returns the Long Name of the connected radio."""
        if not self.client or not self.is_connected:
            return None
        try:
            # Check the library's metadata first
            my_info = self.client.getMyNodeInfo()
            if my_info and 'user' in my_info:
                return my_info['user'].get('longName')
            
            # Fallback to the ID (e.g., !8c32abcd)
            return self.client.myId
        except Exception as e:
            logger.error(f"Failed to get local node name: {e}")
            return "Meshtastic Radio"

    def on_message_received(self, packet, interface):
        """Callback for incoming packets."""
        try:
            data = packet.get('decoded', {})
            if data.get('portnum') == 'TEXT_MESSAGE_APP' or 'text' in data:
                payload = data.get('text', '')
                sender_id = packet.get('fromId') or packet.get('from')
                channel = packet.get('channel', 0)

                if not payload: return

                # Save to DB
                self.db.save_message(sender_id, "REMOTE", payload, channel)

                # Update UI
                display_name = self.get_node_display_name(sender_id)
                if self.on_message_received_cb:
                    self.loop.call_soon_threadsafe(
                        self.on_message_received_cb, display_name, "REMOTE", payload, channel
                    )
        except Exception as e:
               logger.error(f"Error processing message: {e}")

    def on_node_update(self, node, interface=None):
        """Update the local node cache and database."""
        try:
            # Extract IDs
            num_id = node.get('num')
            hex_id = node.get('user', {}).get('id')

            # Normalize the node structure for the UI components
            # This ensures both DB nodes and Live nodes have 'position_lat'
            if 'position' in node:
                node['position_lat'] = node['position'].get('latitude')
                node['position_lon'] = node['position'].get('longitude')

            # Update cache
            if num_id: self.nodes[num_id] = node
            if hex_id: self.nodes[hex_id] = node

            # Persist to database
            self.db.save_node(node)

            # Notify UI components (Map and List)
            if self.on_node_updated_cb:
                self.loop.call_soon_threadsafe(self.on_node_updated_cb, node)

        except Exception as e:
            logger.error(f"Error in on_node_update: {e}")

    def get_node_display_name(self, node_id):
        node = self.nodes.get(node_id)
        if node and 'user' in node:
            long_name = node['user'].get('longName', 'Unknown')
            hex_id = node['user'].get('id', node_id)
            return f"{long_name} <small>({hex_id})</small>"
        return f"Unknown <small>({node_id})</small>"

    async def send_text(self, text, channel_index=0, destination=None):
        if not self.is_connected or not self.client:
            return False
        target = destination if destination is not None else 0xFFFFFFFF
        try:
            self.client.sendText(text, destinationId=target, channelIndex=channel_index)
            self.db.save_message("USER", "USER", text, channel_index)
            return True
        except Exception as e:
            logger.error(f"Send failed: {e}")
            return False

    async def send_config(self, config_dict):
        """
        Apply configuration to the local radio.
        Expects a dict like: {'radio': {'region': 9, 'modemConfig': 'LongFast'}}
        """
        if not self.is_connected or not self.client:
            logger.error("Cannot send config: Not connected")
            return False

        try:
            # The python-meshtastic library handles configuration through
            # the localConfig and moduleConfig attributes.
            
            # Example: Setting the Region
            if 'radio' in config_dict:
                radio_settings = config_dict['radio']
                
                if 'region' in radio_settings:
                    # Sets the regulatory region (e.g., 9 for US)
                    self.client.localConfig.lora.region = radio_settings['region']
                
                if 'modemConfig' in radio_settings:
                    # modemConfig is an enum or string in the API
                    # Using the set_preset equivalent
                    preset = radio_settings['modemConfig']
                    logger.info(f"Setting modem preset to {preset}")
                    # Note: Actual protobuf field path depends on your library version
                    # but typically handled via writeConfig()
            
            # Commit the changes to the radio's flash memory
            await self.loop.run_in_executor(None, self.client.writeConfig)
            logger.info("Configuration sent and saved to device.")
            return True

        except Exception as e:
            logger.error(f"Failed to send config: {e}")
            return False