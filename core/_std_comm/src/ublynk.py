# @package: ublynk
# @version: 1.0.0
# @type: core
# @category: communication
# @interface: WiFi
# @depends: wifi
# @platforms: rp2, esp32
# @tags: blynk, iot, cloud, virtual-pin
# @author: PlanXLab Development Team

import sys
import time
import json
import socket
import binascii

import machine
from upaho import Client as MQTTClient, ReasonCode

print("""
    ___  __          __
   / _ )/ /_ _____  / /__
  / _  / / // / _ \\/  '_/
 /____/_/\\_, /_//_/_/\\_\\2@MQTT
        /___/ for uPython""" +" (" + sys.platform + ")\n")

class BlynkMQTTClient:
    # Downlink topics (server -> device)
    _DOWNLINK = "downlink/"
    _DOWNLINK_TOPIC_ALL = _DOWNLINK + "#"
    _DOWNLINK_TOPIC_DS = _DOWNLINK + "ds/"
    _DOWNLINK_TOPIC_META = _DOWNLINK + "meta/"
    _DOWNLINK_TOPIC_UTC = _DOWNLINK + "utc/all/json"
    _DOWNLINK_TOPIC_LOC = _DOWNLINK + "loc/all"
    _DOWNLINK_TOPIC_OTA = _DOWNLINK + "ota/json"
    _DOWNLINK_TOPIC_PING = _DOWNLINK + "ping"
    _DOWNLINK_TOPIC_REBOOT = _DOWNLINK + "reboot"
    _DOWNLINK_TOPIC_REDIRECT = _DOWNLINK + "redirect"
    _DOWNLINK_TOPIC_DIAG = _DOWNLINK + "diag"
    
    # Uplink topics (device -> server)
    _UPLINK_INFO_MCU = "info/mcu"
    _UPLINK_DS = "ds/"
    _UPLINK_BATCH_DS = "batch_ds"
    _UPLINK_DS_ERASE = "/erase"
    _UPLINK_DS_PROP = "/prop/"
    _UPLINK_EVENT = "event/"
    _UPLINK_META = "meta/"
    _UPLINK_GET_DS = "get/ds"
    _UPLINK_GET_DS_ALL = "get/ds/all"
    _UPLINK_GET_META = "get/meta"
    _UPLINK_GET_UTC = "get/utc/all/json"
    _UPLINK_GET_LOC = "get/loc/all"
    
    _USER_NAME = "device"

    def __init__(self, auth_token: str, server: str = "blynk.cloud", 
                 keepalive: int = 45, ssl: bool = False, verbose: bool = False,
                 template_id: str = "", fw_version: str = "1.0.0", fw_build: str = "") -> None:      
        self._blynk_server_name = server
        self._blynk_server_port = 8883 if ssl else 1883
        self._keepalive = keepalive
        self._ssl = ssl
        self._verbose = verbose
        
        try:
            socket.getaddrinfo(self._blynk_server_name, self._blynk_server_port)
        except OSError as e:
            if self._verbose:
                print(f"[MQTT] Failed to resolve server {self._blynk_server_name}:{self._blynk_server_port} - {e}")
            raise ValueError(f"Invalid server address: {self._blynk_server_name}")
        
        self._blynk_mqtt_client = MQTTClient(
            client_id=binascii.hexlify(machine.unique_id()).decode()
        )
        self._blynk_mqtt_client.username_pw_set(self._USER_NAME, auth_token)
        
        if self._ssl:
            self._blynk_mqtt_client.tls_set()
            self._blynk_mqtt_client.tls_insecure_set(True)

        self._downlink_callbacks = {}
        self._is_connected = False
        self._last_reconnect_attempt = 0
        self._reconnect_backoff = 10000  # Minimum 10 seconds between reconnection attempts
        self._template_id = template_id
        self._fw_version = fw_version
        self._fw_build = fw_build or time.localtime()[:6]
        self._redirect_server = None
    
    def _publish(self, topic: str, payload: str, retain: bool = False, qos: int = 0) -> None:
        try:
            if not self.is_connected():
                if self._verbose:
                    print(f"[MQTT] Not connected. Cannot publish to topic: {topic}")
                return
            
            self._blynk_mqtt_client.publish(topic, payload.encode(), qos, retain)
            if self._verbose:
                print(f"[MQTT TX] Topic: {topic}, Payload: {payload}")
        except Exception as e:
            if self._verbose:
                print(f"[MQTT] Publish error: {e}")
            self._is_connected = False
                    
    def _on_message(self, client, userdata, msg) -> None:
        topic_str = msg.topic
        payload_str = msg.payload.decode() if isinstance(msg.payload, bytes) else str(msg.payload)
        if self._verbose:
            print(f"[MQTT RX] Topic: {topic_str}, Payload: {payload_str}")

        try:
            if "__all__" in self._downlink_callbacks:
                self._downlink_callbacks["__all__"](topic_str, payload_str)
                return

            # downlink/ds/DATASTREAM
            if topic_str.startswith(self._DOWNLINK_TOPIC_DS):
                ds = topic_str[len(self._DOWNLINK_TOPIC_DS):]
                if ds in self._downlink_callbacks:
                    self._downlink_callbacks[ds](payload_str)

            # downlink/meta/FIELD
            elif topic_str.startswith(self._DOWNLINK_TOPIC_META):
                meta_field = topic_str[len(self._DOWNLINK_TOPIC_META):]
                if "_meta" in self._downlink_callbacks:
                    self._downlink_callbacks["_meta"](meta_field, payload_str)

            # downlink/utc/all/json
            elif topic_str == self._DOWNLINK_TOPIC_UTC:
                if "_utc" in self._downlink_callbacks:
                    self._downlink_callbacks["_utc"](payload_str)

            # downlink/loc/all
            elif topic_str == self._DOWNLINK_TOPIC_LOC:
                if "_loc" in self._downlink_callbacks:
                    self._downlink_callbacks["_loc"](payload_str)

            # downlink/ota/json
            elif topic_str == self._DOWNLINK_TOPIC_OTA:
                if "_ota" in self._downlink_callbacks:
                    self._downlink_callbacks["_ota"](payload_str)

            # downlink/ping
            elif topic_str == self._DOWNLINK_TOPIC_PING:
                # Respond to server ping (QoS 1)
                if self._verbose:
                    print("[MQTT] Received ping from server")

            # downlink/reboot
            elif topic_str == self._DOWNLINK_TOPIC_REBOOT:
                if "_reboot" in self._downlink_callbacks:
                    self._downlink_callbacks["_reboot"]()

            # downlink/redirect
            elif topic_str == self._DOWNLINK_TOPIC_REDIRECT:
                self._handle_redirect(payload_str)

            # downlink/diag
            elif topic_str == self._DOWNLINK_TOPIC_DIAG:
                if self._verbose:
                    print(f"[MQTT] Server diagnostic: {payload_str}")
                if "_diag" in self._downlink_callbacks:
                    self._downlink_callbacks["_diag"](payload_str)

        except KeyError:
            if self._verbose:
                print(f"[MQTT] No callback registered for topic: {topic_str}")
        except Exception as e:
            if self._verbose:
                print(f"[MQTT] Error in callback for topic {topic_str}: {e}")

    def _handle_redirect(self, uri: str) -> None:
        if self._verbose:
            print(f"[MQTT] Server redirect to: {uri}")
        
        self._redirect_server = uri
        
        if "_redirect" in self._downlink_callbacks:
            self._downlink_callbacks["_redirect"](uri)
        
        # Parse URI and reconnect to new server
        try:
            # Remove protocol prefix
            if uri.startswith("mqtts://"):
                new_ssl = True
                uri = uri[8:]
            elif uri.startswith("mqtt://"):
                new_ssl = False
                uri = uri[7:]
            elif uri.startswith("wss://") or uri.startswith("ws://"):
                # WebSocket not supported in this implementation
                if self._verbose:
                    print("[MQTT] WebSocket redirect not supported")
                return
            else:
                if self._verbose:
                    print(f"[MQTT] Unknown protocol in redirect URI: {uri}")
                return
            
            # Remove path if present (e.g., /mqtt)
            if "/" in uri:
                uri = uri.split("/")[0]
            
            # Parse host:port
            if ":" in uri:
                host, port_str = uri.rsplit(":", 1)
                port = int(port_str)
            else:
                host = uri
                port = 8883 if new_ssl else 1883
            
            # Update connection parameters
            self._blynk_server_name = host
            self._blynk_server_port = port
            self._ssl = new_ssl
            
            if self._verbose:
                print(f"[MQTT] Reconnecting to {host}:{port} (SSL: {new_ssl})")
            
            # Disconnect and reconnect
            self.disconnect()
            
            # Reconfigure SSL if changed
            if new_ssl and not self._blynk_mqtt_client._ssl_context:
                self._blynk_mqtt_client.tls_set()
                self._blynk_mqtt_client.tls_insecure_set(True)
            
            self.connect()
            
        except Exception as e:
            if self._verbose:
                print(f"[MQTT] Failed to handle redirect: {e}")

    def connect(self, clean_session: bool = True) -> bool:
        if self._is_connected:
            return True

        self._blynk_mqtt_client._clean_start = clean_session
        result = self._blynk_mqtt_client.connect(
            self._blynk_server_name,
            self._blynk_server_port,
            self._keepalive
        )
        
        if result == ReasonCode.SUCCESS:
            self._blynk_mqtt_client.on_message = self._on_message
            self._blynk_mqtt_client.subscribe(self._DOWNLINK_TOPIC_ALL, 1)
            
            self._is_connected = True
            
            # Send firmware info (required by Blynk API)
            if self._template_id:
                self._send_firmware_info()
            
            if self._verbose:
                print("[MQTT] Connected to Blynk MQTT broker and subscribed to downlink topics.")
            return True
        
        if self._verbose:
            print("[MQTT] Failed to connect to Blynk MQTT broker.")
        self._is_connected = False
        return False
    
    def _send_firmware_info(self) -> None:
        info = {
            "tmpl": self._template_id,
            "ver": self._fw_version,
            "build": str(self._fw_build) if isinstance(self._fw_build, (list, tuple)) else self._fw_build,
            "type": self._template_id,
            "rxbuff": 1024
        }
        payload = json.dumps(info)
        self._publish(self._UPLINK_INFO_MCU, payload, qos=0)
        if self._verbose:
            print(f"[MQTT] Sent firmware info: {payload}")

    def disconnect(self) -> None:
        if self._is_connected:
            time.sleep_ms(100) # Allow time for pending messages
            self._blynk_mqtt_client.disconnect()
            self._is_connected = False
            if self._verbose:
                print("[MQTT] Disconnected from MQTT broker.")

    def is_connected(self) -> bool:
        return self._is_connected

    def reconnect(self, max_attempts: int = 5) -> bool:
        if self.is_connected():
            return True
        
        for attempt in range(max_attempts):
            if self._verbose:
                print(f"Reconnection attempt {attempt + 1}/{max_attempts}...")
            # Note: Blynk currently only supports clean sessions
            if self.connect(clean_session=True):
                if self._verbose:
                    print("Reconnection successful.")
                return True
            # Exponential backoff
            time.sleep(2 ** attempt)
        
        if self._verbose:
            print("Failed to reconnect after multiple attempts.")
        return False

    def add_subscribe_callback(self, datastream: str, callback: callable) -> None:
        self._downlink_callbacks[datastream] = callback
        if self._verbose:
            print(f"[SUB] Registered callback for '{datastream}'")

    def remove_subscribe_callback(self, datastream: str) -> None:
        if datastream in self._downlink_callbacks:
            del self._downlink_callbacks[datastream]
            if self._verbose:
                print(f"[SUB] Removed callback for '{datastream}'")

    def publish(self, datastream: str, value: str | int | float | list, qos: int = 0) -> None:
        topic = f"{self._UPLINK_DS}{datastream}"
        if isinstance(value, list):
            # Multi-value: separate with NUL character
            payload = "\x00".join(str(v) for v in value)
        else:
            payload = str(value)
        self._publish(topic, payload, qos=qos)
    
    def publish_batch(self, datastreams: dict, qos: int = 0) -> None:
        payload = json.dumps(datastreams)
        self._publish(self._UPLINK_BATCH_DS, payload, qos=qos)
    
    def erase_datastream(self, datastream: str, qos: int = 0) -> None:
        topic = f"{self._UPLINK_DS}{datastream}{self._UPLINK_DS_ERASE}"
        self._publish(topic, "", qos=qos)
    
    def set_property(self, datastream: str, prop: str, value: str | int | float | list, qos: int = 0) -> None:
        topic = f"{self._UPLINK_DS}{datastream}{self._UPLINK_DS_PROP}{prop}"
        if isinstance(value, list):
            payload = "\x00".join(str(v) for v in value)
        else:
            payload = str(value)
        self._publish(topic, payload, qos=qos)
    
    def erase_property(self, datastream: str, prop: str, qos: int = 0) -> None:
        topic = f"{self._UPLINK_DS}{datastream}{self._UPLINK_DS_PROP}{prop}/erase"
        self._publish(topic, "", qos=qos)
    
    def log_event(self, event_code: str, description: str = "", qos: int = 0) -> None:
        topic = f"{self._UPLINK_EVENT}{event_code}"
        self._publish(topic, description, qos=qos)
    
    def set_metadata(self, field: str, value: str, qos: int = 0) -> None:
        topic = f"{self._UPLINK_META}{field}"
        self._publish(topic, value, qos=qos)
    
    def get_datastreams(self, *datastreams: str, qos: int = 1) -> None:
        payload = ",".join(datastreams)
        self._publish(self._UPLINK_GET_DS, payload, qos=qos)
    
    def get_all_datastreams(self, qos: int = 1) -> None:
        self._publish(self._UPLINK_GET_DS_ALL, "", qos=qos)
    
    def get_metadata(self, *fields: str, qos: int = 1) -> None:
        payload = ",".join(fields)
        self._publish(self._UPLINK_GET_META, payload, qos=qos)
    
    def get_location(self, qos: int = 1) -> None:
        self._publish(self._UPLINK_GET_LOC, "", qos=qos)

    def get_utc(self, timeout_ms: int = 5000) -> dict | None:
        data = None
        
        def _on_utc_response(payload):
            nonlocal data
            try:
                t_data = json.loads(payload)
                data = {"time": t_data.get("iso8601"), "zone": t_data.get("tz_name")}
            except (ValueError, KeyError) as e:
                if self._verbose:
                    print(f"[MQTT] Error parsing UTC response: {e}")
                data = {}

        self.add_subscribe_callback("_utc", _on_utc_response)
        self._publish(self._UPLINK_GET_UTC, "", qos=1)
        
        start_time = time.ticks_ms()
        while data is None:
            try:
                self._blynk_mqtt_client.loop(timeout=0.1)
            except Exception as e:
                if self._verbose:
                    print(f"[MQTT] Error checking messages: {e}")
                break
            
            if time.ticks_diff(time.ticks_ms(), start_time) > timeout_ms:
                if self._verbose:
                    print(f"[MQTT] UTC time request timed out after {timeout_ms}ms")
                break
            time.sleep_ms(100)
        
        self.remove_subscribe_callback("_utc")
        return data

    def loop(self) -> None:
        if not self.is_connected():
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_reconnect_attempt) >= self._reconnect_backoff:
                self._last_reconnect_attempt = now
                if self._verbose:
                    print(f"[MQTT] Attempting reconnection (backoff: {self._reconnect_backoff}ms)...")
                self.reconnect(max_attempts=1)
            return

        try:
            self._blynk_mqtt_client.loop(timeout=0.01)
        except Exception as e:
            if self._verbose:
                print(f"[MQTT] Error in loop: {e}")
            self._is_connected = False

    def loop_forever(self) -> None:
        while True:
            self.loop()
            time.sleep_ms(10)
