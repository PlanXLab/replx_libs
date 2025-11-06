__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"

import sys
import time
import json
import usocket
import ubinascii

import machine
from umqtt.robust2 import MQTTClient


print("""
    ___  __          __
   / _ )/ /_ _____  / /__
  / _  / / // / _ \\/  '_/
 /____/_/\\_, /_//_/_/\\_\\2@MQTT
        /___/ for uPython v""" + __version__ + " (" + sys.platform + ")\n")


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
            usocket.getaddrinfo(self._blynk_server_name, self._blynk_server_port)
        except OSError as e:
            if self._verbose:
                print(f"[MQTT] Failed to resolve server {self._blynk_server_name}:{self._blynk_server_port} - {e}")
            raise ValueError(f"Invalid server address: {self._blynk_server_name}")
        
        self._blynk_mqtt_client = MQTTClient(
            client_id=ubinascii.hexlify(machine.unique_id()).decode(),
            server=self._blynk_server_name,
            port=self._blynk_server_port,
            user=self._USER_NAME,
            password=auth_token,
            keepalive=self._keepalive,
            ssl=self._ssl,
            ssl_params={"server_hostname": self._blynk_server_name} if self._ssl else {}
        )
        self._blynk_mqtt_client.DEBUG = self._verbose

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
            
            self._blynk_mqtt_client.publish(topic.encode(), payload.encode(), retain, qos)
            if self._verbose:
                print(f"[MQTT TX] Topic: {topic}, Payload: {payload}")
        except Exception as e:
            if self._verbose:
                print(f"[MQTT] Publish error: {e}")
            self._is_connected = False
                    
    def _on_message(self, topic: bytes, payload: bytes, retained: bool, duplicate: bool) -> None:
        topic_str = topic.decode()
        payload_str = payload.decode()
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
                self._redirect_server = payload_str
                if self._verbose:
                    print(f"[MQTT] Server redirect to: {payload_str}")
                if "_redirect" in self._downlink_callbacks:
                    self._downlink_callbacks["_redirect"](payload_str)

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

    def connect(self, clean_session: bool = True) -> bool:
        if self._is_connected:
            return True

        if self._blynk_mqtt_client.connect(clean_session) is not None:
            self._blynk_mqtt_client.set_callback(self._on_message)
            self._blynk_mqtt_client.subscribe(self._DOWNLINK_TOPIC_ALL.encode(), 1)
            
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
        """Send firmware information to Blynk (required on every clean connection)."""
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
            if self.connect(clean_session=False):
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
        """
        Publish a single datastream value.
        For multi-value (array) datastreams, pass a list and values will be separated by \\x00.
        """
        topic = f"{self._UPLINK_DS}{datastream}"
        if isinstance(value, list):
            # Multi-value: separate with NUL character
            payload = "\x00".join(str(v) for v in value)
        else:
            payload = str(value)
        self._publish(topic, payload, qos=qos)
    
    def publish_batch(self, datastreams: dict, qos: int = 0) -> None:
        """
        Publish multiple datastream values in a single message (batch upload).
        More efficient for sending multiple values at once.
        
        Example:
            client.publish_batch({
                "Temperature": 23.5,
                "Humidity": 67,
                "Status": "online"
            })
        """
        payload = json.dumps(datastreams)
        self._publish(self._UPLINK_BATCH_DS, payload, qos=qos)
    
    def erase_datastream(self, datastream: str, qos: int = 0) -> None:
        """Erase the value of a datastream."""
        topic = f"{self._UPLINK_DS}{datastream}{self._UPLINK_DS_ERASE}"
        self._publish(topic, "", qos=qos)
    
    def set_property(self, datastream: str, prop: str, value: str | int | float, qos: int = 0) -> None:
        """Set a widget property dynamically."""
        topic = f"{self._UPLINK_DS}{datastream}{self._UPLINK_DS_PROP}{prop}"
        self._publish(topic, str(value), qos=qos)
    
    def log_event(self, event_code: str, description: str = "", qos: int = 0) -> None:
        """
        Publish an event (for alerts, notifications, logging).
        If description is empty, uses the default description from event settings.
        """
        topic = f"{self._UPLINK_EVENT}{event_code}"
        self._publish(topic, description, qos=qos)
    
    def set_metadata(self, field: str, value: str, qos: int = 0) -> None:
        """Set a metadata field value."""
        topic = f"{self._UPLINK_META}{field}"
        self._publish(topic, value, qos=qos)
    
    def get_datastreams(self, *datastreams: str, qos: int = 1) -> None:
        """
        Request current values for specific datastreams.
        Values will arrive via downlink/ds/DATASTREAM callbacks.
        
        Example:
            client.get_datastreams("Temperature", "Humidity")
        """
        payload = ",".join(datastreams)
        self._publish(self._UPLINK_GET_DS, payload, qos=qos)
    
    def get_all_datastreams(self, qos: int = 1) -> None:
        """
        Request current values for ALL datastreams.
        Requires 'Sync with latest server value' enabled in datastream settings.
        """
        self._publish(self._UPLINK_GET_DS_ALL, "", qos=qos)
    
    def get_metadata(self, *fields: str, qos: int = 1) -> None:
        """
        Request metadata field values.
        Values will arrive via downlink/meta/FIELD callback.
        
        Example:
            client.get_metadata("Device Name", "Time Zone")
        """
        payload = ",".join(fields)
        self._publish(self._UPLINK_GET_META, payload, qos=qos)
    
    def get_location(self, qos: int = 1) -> None:
        """Request device approximate location."""
        self._publish(self._UPLINK_GET_LOC, "", qos=qos)

    def get_utc(self, timeout_ms: int = 5000) -> dict | None:
        """
        Request and wait for UTC time information from server.
        Returns dict with 'time' (ISO8601) and 'zone' (timezone name) or None on timeout.
        """
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
                self._blynk_mqtt_client.check_msg()
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
            self._blynk_mqtt_client.check_msg()
            self._blynk_mqtt_client.send_queue()
        except Exception as e:
            if self._verbose:
                print(f"[MQTT] Error in loop: {e}")
            self._is_connected = False

    def loop_forever(self) -> None:
        while True:
            self.loop()
            time.sleep_ms(10)
