"""
u-paho-mqtt Client

MicroPython MQTT 5.0 client with paho-mqtt compatible API.
No threading support - use loop() or loop_forever() methods.
"""

import usocket
import uselect
import time
import struct
import gc

from .enums import (
    MQTTProtocolVersion, PacketType, ReasonCode, QoS,
    ConnectReturnCode, PropertyType
)
from .properties import Properties
from .message import MQTTMessage, MQTTMessageInfo
from .packets import (
    ConnectPacket, PublishPacket, PubackPacket, PubrecPacket,
    PubrelPacket, PubcompPacket, SubscribePacket,
    UnsubscribePacket, PingReqPacket, DisconnectPacket
)
from .mqtt5 import read_packet_from_socket, send_packet_to_socket


class Client:
    """
    MicroPython MQTT 5.0 Client (paho-mqtt inspired)
    
    Key Differences from paho-mqtt:
    - MQTT 5.0 by default (3.1.1 fallback available)
    - No threading support (no loop_start/loop_stop)
    - Simplified for MicroPython constraints
    - Memory optimized with __slots__
    
    Example:
        >>> client = Client(client_id="device001")
        >>> client.username_pw_set("user", "pass")
        >>> client.on_connect = lambda c, u, f, rc, p: print("Connected")
        >>> client.on_message = lambda c, u, m: print(m.payload)
        >>> client.connect("mqtt.example.com", 1883, 60)
        >>> client.subscribe("sensor/#", qos=1)
        >>> client.loop_forever()
    """
    
    __slots__ = [
        # Connection parameters
        '_client_id', '_clean_start', '_protocol', '_transport',
        '_host', '_port', '_keepalive', '_sock', '_connected',
        
        # Authentication
        '_username', '_password', '_ssl_context',
        
        # Properties
        '_connect_properties', '_will_properties',
        
        # Last Will and Testament
        '_will_topic', '_will_payload', '_will_qos', '_will_retain',
        
        # Callbacks
        'on_connect', 'on_disconnect', 'on_message',
        'on_publish', 'on_subscribe', 'on_unsubscribe', 'on_log',
        
        # Message handling
        '_out_packet', '_in_packet', '_inflight_messages',
        
        # Subscriptions
        '_subscriptions', '_message_callbacks',
        
        # Internal state
        '_last_mid', '_last_ping', '_last_recv', '_ping_pending',
        
        # MQTT 5.0 server capabilities
        '_server_keepalive', '_server_max_packet_size', '_server_topic_alias_max',
        '_receive_maximum', '_topic_alias_outbound', '_topic_alias_inbound',
        
        # User data
        '_userdata',
        
        # Options
        '_reconnect_on_failure', '_auto_reconnect', '_socket_timeout'
    ]
    
    def __init__(self, client_id="", clean_session=None, userdata=None,
                 protocol=MQTTProtocolVersion.MQTTv5, transport="tcp"):
        """
        Initialize MQTT Client
        
        :param client_id: Unique client identifier (empty = broker assigns)
        :param clean_session: MQTT 3.1.1 clean session (deprecated, use protocol-specific)
        :param userdata: User-defined data passed to callbacks
        :param protocol: MQTTv5 or MQTTv311
        :param transport: "tcp" only (websockets not supported)
        """
        # Basic settings
        self._client_id = client_id
        self._protocol = protocol
        self._transport = transport
        self._userdata = userdata
        
        # Clean session/start
        if clean_session is None:
            self._clean_start = True
        else:
            self._clean_start = clean_session
        
        # Connection state
        self._host = None
        self._port = 1883
        self._keepalive = 60
        self._sock = None
        self._connected = False
        self._socket_timeout = 1.0
        
        # Authentication
        self._username = None
        self._password = None
        self._ssl_context = None
        
        # MQTT 5.0 properties
        self._connect_properties = Properties()
        self._will_properties = Properties()
        
        # Last Will and Testament
        self._will_topic = None
        self._will_payload = None
        self._will_qos = 0
        self._will_retain = False
        
        # Callbacks (paho compatible)
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None
        self.on_publish = None
        self.on_subscribe = None
        self.on_unsubscribe = None
        self.on_log = None
        
        # Message queues
        self._out_packet = []
        self._in_packet = {}
        self._inflight_messages = {}
        
        # QoS 2 message tracking
        self._qos2_pubrec_received = {}  # {mid: MQTTMessageInfo}
        self._qos2_pubrel_sent = set()   # {mid}
        
        # Subscriptions
        self._subscriptions = {}
        self._message_callbacks = {}
        
        # Internal state
        self._last_mid = 0
        self._last_ping = 0
        self._last_recv = 0
        self._ping_pending = False
        
        # MQTT 5.0 server capabilities (negotiated during connect)
        self._server_keepalive = None
        self._server_max_packet_size = None
        self._server_topic_alias_max = 0
        self._receive_maximum = 65535
        self._topic_alias_outbound = {}
        self._topic_alias_inbound = {}
        
        # Auto reconnect
        self._reconnect_on_failure = True
        self._auto_reconnect = False
    
    # ==========================================
    # Configuration Methods
    # ==========================================
    
    def username_pw_set(self, username, password=None):
        """
        Set username and password for broker authentication
        
        :param username: Username string
        :param password: Password string (optional)
        """
        self._username = username
        self._password = password
    
    def tls_set(self, ca_certs=None, certfile=None, keyfile=None,
                cert_reqs=None, tls_version=None, ciphers=None):
        """
        Configure TLS/SSL encryption
        
        Simplified for MicroPython ssl module constraints.
        
        :param ca_certs: CA certificates file path
        :param certfile: Client certificate file path
        :param keyfile: Client key file path
        :param cert_reqs: Certificate requirements (not used in MicroPython)
        :param tls_version: TLS version (not configurable in MicroPython)
        :param ciphers: Cipher suite (not configurable in MicroPython)
        """
        self._ssl_context = {}
        
        if ca_certs:
            self._ssl_context['ca_certs'] = ca_certs
        if certfile:
            self._ssl_context['certfile'] = certfile
        if keyfile:
            self._ssl_context['keyfile'] = keyfile
    
    def tls_insecure_set(self, value):
        """
        Disable SSL certificate verification (insecure!)
        
        :param value: True to disable verification
        """
        if self._ssl_context is None:
            self._ssl_context = {}
        self._ssl_context['cert_reqs'] = not value
    
    def will_set(self, topic, payload=None, qos=0, retain=False, properties=None):
        """
        Set Last Will and Testament message
        
        :param topic: Will topic
        :param payload: Will message payload
        :param qos: Will QoS (0, 1, or 2)
        :param retain: Will retain flag
        :param properties: MQTT 5.0 will properties
        """
        self._will_topic = topic
        self._will_payload = payload if payload is not None else b""
        self._will_qos = qos
        self._will_retain = retain
        
        if properties and self._protocol == MQTTProtocolVersion.MQTTv5:
            self._will_properties = properties
    
    def will_clear(self):
        """Clear the Last Will and Testament"""
        self._will_topic = None
        self._will_payload = None
        self._will_qos = 0
        self._will_retain = False
        self._will_properties = Properties()
    
    def reconnect_delay_set(self, min_delay=1, max_delay=120):
        """
        Set reconnection delay (not implemented - manual reconnect only)
        
        MicroPython limitation: no background threading.
        """
        pass
    
    def max_inflight_messages_set(self, inflight):
        """
        Set maximum number of inflight QoS 1/2 messages
        
        :param inflight: Maximum inflight messages (default: 20)
        """
        self._receive_maximum = inflight
    
    def message_retry_set(self, retry):
        """
        Set message retry interval (not implemented)
        
        MQTT 5.0 handles this at protocol level.
        """
        pass
    
    def user_data_set(self, userdata):
        """Set user data passed to callbacks"""
        self._userdata = userdata
    
    # ==========================================
    # Connection Methods
    # ==========================================
    
    def connect(self, host, port=1883, keepalive=60, bind_address=""):
        """
        Connect to MQTT broker (blocking)
        
        :param host: Broker hostname or IP
        :param port: Broker port (default: 1883, SSL: 8883)
        :param keepalive: Keep alive interval in seconds
        :param bind_address: Local address to bind (not supported)
        :return: ReasonCode (MQTT 5.0) or return code (MQTT 3.1.1)
        """
        self._host = host
        self._port = port
        self._keepalive = keepalive
        
        # Resolve hostname
        try:
            addr_info = usocket.getaddrinfo(host, port)[0]
            addr = addr_info[-1]
        except OSError as e:
            self._log(f"DNS lookup failed for {host}: {e}")
            if self.on_connect:
                self.on_connect(self, self._userdata, {}, 
                              ReasonCode.NETWORK_ERROR, None)
            return ReasonCode.NETWORK_ERROR
        
        # Connect with retries
        max_retries = 3
        connected = False
        
        for attempt in range(max_retries):
            if attempt > 0:
                time.sleep(2)
            
            # Create new socket for each attempt
            try:
                if self._sock:
                    try:
                        self._sock.close()
                    except:
                        pass
                
                self._sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
                # MicroPython: longer timeout for slow networks
                self._sock.settimeout(30.0)
            except Exception as e:
                self._log(f"Socket creation failed: {e}")
                continue
            
            # Try to connect
            try:
                self._sock.connect(addr)
                connected = True
                break
            except OSError as e:
                if attempt == max_retries - 1:
                    # Last attempt failed
                    self._log(f"Socket connect failed after {max_retries} attempts: {e}")
        
        if not connected:
            try:
                if self._sock:
                    self._sock.close()
            except:
                pass
            self._sock = None
            if self.on_connect:
                self.on_connect(self, self._userdata, {},
                              ReasonCode.NETWORK_ERROR, None)
            return ReasonCode.NETWORK_ERROR
        
        # Apply SSL/TLS
        if self._ssl_context is not None:
            try:
                import ssl
                ssl_params = self._ssl_context.copy()
                ssl_params['server_hostname'] = host
                self._sock = ssl.wrap_socket(self._sock, **ssl_params)
            except Exception as e:
                self._log(f"SSL/TLS wrap failed: {e}")
                self._sock.close()
                self._sock = None
                if self.on_connect:
                    self.on_connect(self, self._userdata, {},
                                  ReasonCode.UNSPECIFIED_ERROR, None)
                return ReasonCode.UNSPECIFIED_ERROR
        
        # Send CONNECT packet
        connect_packet = ConnectPacket(
            client_id=self._client_id,
            clean_start=self._clean_start,
            keepalive=self._keepalive,
            username=self._username,
            password=self._password,
            will_topic=self._will_topic,
            will_payload=self._will_payload,
            will_qos=self._will_qos,
            will_retain=self._will_retain,
            protocol_version=self._protocol,
            properties=self._connect_properties,
            will_properties=self._will_properties
        )
        
        try:
            send_packet_to_socket(self._sock, connect_packet)
        except Exception as e:
            import sys
            sys.print_exception(e)
            self._log(f"Failed to send CONNECT: {e}")
            try:
                self._sock.close()
            except:
                pass
            self._sock = None
            if self.on_connect:
                self.on_connect(self, self._userdata, {},
                              ReasonCode.NETWORK_ERROR, None)
            return ReasonCode.NETWORK_ERROR
        
        # Wait for CONNACK
        self._sock.settimeout(10.0)
        try:
            connack = read_packet_from_socket(self._sock, self._protocol)
        except Exception as e:
            import sys
            sys.print_exception(e)
            self._log(f"Failed to receive CONNACK: {e}")
            try:
                self._sock.close()
            except:
                pass
            self._sock = None
            if self.on_connect:
                self.on_connect(self, self._userdata, {},
                              ReasonCode.UNSPECIFIED_ERROR, None)
            return ReasonCode.UNSPECIFIED_ERROR
        
        if connack is None:
            self._log("CONNACK not received (timeout or connection closed)")
            try:
                self._sock.close()
            except:
                pass
            self._sock = None
            if self.on_connect:
                self.on_connect(self, self._userdata, {},
                              ReasonCode.PROTOCOL_ERROR, None)
            return ReasonCode.PROTOCOL_ERROR
        
        if connack.packet_type != PacketType.CONNACK:
            self._log(f"Invalid packet received (expected CONNACK, got {hex(connack.packet_type)})")
            try:
                self._sock.close()
            except:
                pass
            self._sock = None
            if self.on_connect:
                self.on_connect(self, self._userdata, {},
                              ReasonCode.PROTOCOL_ERROR, None)
            return ReasonCode.PROTOCOL_ERROR
        
        # Check connection result
        if connack.reason_code != ReasonCode.SUCCESS:
            self._log(f"Connection refused: {connack.reason_code}")
            self._sock.close()
            self._sock = None
            if self.on_connect:
                flags = {'session_present': connack.session_present}
                self.on_connect(self, self._userdata, flags,
                              connack.reason_code, connack.properties)
            return connack.reason_code
        
        # Connection successful
        self._connected = True
        self._last_recv = time.ticks_ms()
        self._sock.settimeout(self._socket_timeout)
        
        # Process MQTT 5.0 server properties
        if self._protocol == MQTTProtocolVersion.MQTTv5:
            self._process_connack_properties(connack.properties)
        
        # Trigger on_connect callback
        if self.on_connect:
            flags = {'session_present': connack.session_present}
            self.on_connect(self, self._userdata, flags,
                          connack.reason_code, connack.properties)
        
        self._log(f"Connected to {host}:{port}", level=1)  # INFO level
        return ReasonCode.SUCCESS
    
    def connect_async(self, host, port=1883, keepalive=60, bind_address=""):
        """
        Asynchronous connect (not implemented - use connect())
        
        MicroPython limitation: no background threading.
        """
        return self.connect(host, port, keepalive, bind_address)
    
    def reconnect(self):
        """
        Reconnect to the broker
        
        :return: ReasonCode
        """
        if self._host is None:
            raise ValueError("connect() must be called before reconnect()")
        
        if self._connected:
            self.disconnect()
        
        return self.connect(self._host, self._port, self._keepalive)
    
    def disconnect(self, reasoncode=None, properties=None):
        """
        Disconnect from broker gracefully
        
        :param reasoncode: MQTT 5.0 reason code
        :param properties: MQTT 5.0 disconnect properties
        :return: ReasonCode
        """
        if not self._connected:
            return ReasonCode.SUCCESS
        
        # Send DISCONNECT packet
        if reasoncode is None:
            reasoncode = ReasonCode.NORMAL_DISCONNECTION
        
        disconnect_packet = DisconnectPacket(
            reason_code=reasoncode,
            protocol_version=self._protocol,
            properties=properties or Properties()
        )
        
        try:
            send_packet_to_socket(self._sock, disconnect_packet)
            time.sleep_ms(100)  # Allow packet to be sent
        except:
            pass
        
        # Close socket
        try:
            self._sock.close()
        except:
            pass
        
        self._sock = None
        self._connected = False
        
        # Trigger on_disconnect callback
        if self.on_disconnect:
            self.on_disconnect(self, self._userdata, reasoncode, properties)
        
        self._log("Disconnected from broker", level=1)  # INFO level
        return ReasonCode.SUCCESS
    
    def _process_connack_properties(self, properties):
        """Process MQTT 5.0 CONNACK properties"""
        # Server Keep Alive
        if properties.has(PropertyType.SERVER_KEEP_ALIVE):
            self._server_keepalive = properties.get(PropertyType.SERVER_KEEP_ALIVE)
            self._keepalive = self._server_keepalive
            self._log(f"Server override keepalive: {self._server_keepalive}s")
        
        # Maximum Packet Size
        if properties.has(PropertyType.MAXIMUM_PACKET_SIZE):
            self._server_max_packet_size = properties.get(PropertyType.MAXIMUM_PACKET_SIZE)
            self._log(f"Server max packet size: {self._server_max_packet_size}")
        
        # Topic Alias Maximum
        if properties.has(PropertyType.TOPIC_ALIAS_MAXIMUM):
            self._server_topic_alias_max = properties.get(PropertyType.TOPIC_ALIAS_MAXIMUM)
            self._log(f"Server topic alias max: {self._server_topic_alias_max}")
        
        # Receive Maximum
        if properties.has(PropertyType.RECEIVE_MAXIMUM):
            self._receive_maximum = properties.get(PropertyType.RECEIVE_MAXIMUM)
            self._log(f"Server receive maximum: {self._receive_maximum}")
    
    # ==========================================
    # Publishing Methods
    # ==========================================
    
    def publish(self, topic, payload=None, qos=0, retain=False, properties=None):
        """
        Publish a message to a topic
        
        :param topic: Topic string
        :param payload: Message payload (bytes, str, or None)
        :param qos: Quality of Service (0, 1, or 2)
        :param retain: Retain flag
        :param properties: MQTT 5.0 properties
        :return: MQTTMessageInfo
        """
        if not self._connected:
            self._log("Cannot publish: not connected")
            info = MQTTMessageInfo(0)
            return info
        
        if qos < 0 or qos > 2:
            raise ValueError("QoS must be 0, 1, or 2")
        
        mid = self._get_next_mid() if qos > 0 else 0
        
        # Create PUBLISH packet
        publish_packet = PublishPacket(
            topic=topic,
            payload=payload,
            qos=qos,
            retain=retain,
            mid=mid,
            protocol_version=self._protocol,
            properties=properties or Properties()
        )
        
        # Send packet
        try:
            send_packet_to_socket(self._sock, publish_packet)
        except Exception as e:
            self._log(f"Publish failed: {e}")
            self._connected = False
            return MQTTMessageInfo(mid)
        
        # Create message info
        msg_info = MQTTMessageInfo(mid)
        
        if qos == 0:
            msg_info._set_published()
            if self.on_publish:
                self.on_publish(self, self._userdata, mid)
        else:
            # QoS 1: Wait for PUBACK
            self._inflight_messages[mid] = msg_info
        
        return msg_info
    
    # ==========================================
    # Subscription Methods
    # ==========================================
    
    def subscribe(self, topic, qos=0, options=None, properties=None):
        """
        Subscribe to topic(s)
        
        :param topic: Single topic string or list of (topic, qos) tuples
        :param qos: QoS for single topic
        :param options: MQTT 5.0 subscription options
        :param properties: MQTT 5.0 properties
        :return: (result, mid)
        """
        if not self._connected:
            self._log("Cannot subscribe: not connected")
            return (ReasonCode.NOT_AUTHORIZED, None)
        
        # Normalize topic input
        if isinstance(topic, str):
            topic_list = [(topic, qos)]
        elif isinstance(topic, list):
            topic_list = topic
        elif isinstance(topic, tuple):
            topic_list = [topic]
        else:
            raise ValueError("Invalid topic format")
        
        mid = self._get_next_mid()
        
        # Create SUBSCRIBE packet
        subscribe_packet = SubscribePacket(
            mid=mid,
            topics=topic_list,
            protocol_version=self._protocol,
            properties=properties or Properties()
        )
        
        # Send packet
        try:
            send_packet_to_socket(self._sock, subscribe_packet)
        except Exception as e:
            self._log(f"Subscribe failed: {e}")
            self._connected = False
            return (ReasonCode.UNSPECIFIED_ERROR, mid)
        
        # Store subscription (for reconnection)
        for t, q in topic_list:
            self._subscriptions[t] = (q, properties)
        
        return (ReasonCode.SUCCESS, mid)
    
    def unsubscribe(self, topic, properties=None):
        """
        Unsubscribe from topic(s)
        
        :param topic: Single topic string or list of topics
        :param properties: MQTT 5.0 properties
        :return: (result, mid)
        """
        if not self._connected:
            self._log("Cannot unsubscribe: not connected")
            return (ReasonCode.NOT_AUTHORIZED, None)
        
        # Normalize topic input
        if isinstance(topic, str):
            topic_list = [topic]
        else:
            topic_list = list(topic)
        
        mid = self._get_next_mid()
        
        # Create UNSUBSCRIBE packet
        unsubscribe_packet = UnsubscribePacket(
            mid=mid,
            topics=topic_list,
            protocol_version=self._protocol,
            properties=properties or Properties()
        )
        
        # Send packet
        try:
            send_packet_to_socket(self._sock, unsubscribe_packet)
        except Exception as e:
            self._log(f"Unsubscribe failed: {e}")
            self._connected = False
            return (ReasonCode.UNSPECIFIED_ERROR, mid)
        
        # Remove from subscriptions
        for t in topic_list:
            self._subscriptions.pop(t, None)
            self._message_callbacks.pop(t, None)
        
        return (ReasonCode.SUCCESS, mid)
    
    def message_callback_add(self, sub, callback):
        """
        Add message callback for specific subscription
        
        :param sub: Topic subscription pattern
        :param callback: Callback function (client, userdata, message)
        """
        self._message_callbacks[sub] = callback
    
    def message_callback_remove(self, sub):
        """Remove message callback for subscription"""
        self._message_callbacks.pop(sub, None)
    
    # ==========================================
    # Loop Methods (No Threading!)
    # ==========================================
    
    def loop(self, timeout=1.0, max_packets=1):
        """
        Process network events (call regularly!)
        
        ⚠️ Must be called periodically by user code
        
        :param timeout: Maximum time to wait for data (seconds)
        :param max_packets: Maximum packets to process (not used)
        :return: ReasonCode (SUCCESS or error)
        """
        if not self._connected:
            return ReasonCode.NOT_AUTHORIZED
        
        now = time.ticks_ms()
        
        # Check keepalive timeout
        if self._keepalive > 0:
            time_since_recv = time.ticks_diff(now, self._last_recv) / 1000
            
            if time_since_recv >= (self._keepalive * 1.5):
                # Keepalive timeout - disconnect
                self._log("Keepalive timeout - disconnecting")
                self._connected = False
                if self.on_disconnect:
                    self.on_disconnect(self, self._userdata,
                                     ReasonCode.KEEPALIVE_TIMEOUT, None)
                return ReasonCode.KEEPALIVE_TIMEOUT
            
            elif time_since_recv >= self._keepalive:
                # Send PINGREQ if no ping pending
                if not self._ping_pending:
                    self._send_pingreq()
                    self._ping_pending = True
                    self._last_ping = now
        
        # Check for incoming data
        poller = uselect.poll()
        poller.register(self._sock, uselect.POLLIN)
        
        events = poller.poll(int(timeout * 1000))
        
        if events:
            try:
                packet = read_packet_from_socket(self._sock, self._protocol)
                
                if packet:
                    self._last_recv = time.ticks_ms()
                    self._handle_packet(packet)
                else:
                    # Connection closed
                    self._log("Connection closed by broker")
                    self._connected = False
                    if self.on_disconnect:
                        self.on_disconnect(self, self._userdata,
                                         ReasonCode.UNSPECIFIED_ERROR, None)
                    return ReasonCode.UNSPECIFIED_ERROR
            
            except Exception as e:
                self._log(f"Loop error: {e}")
                self._connected = False
                if self.on_disconnect:
                    self.on_disconnect(self, self._userdata,
                                     ReasonCode.NETWORK_ERROR, None)
                return ReasonCode.NETWORK_ERROR
        
        # Periodic garbage collection
        if time.ticks_diff(now, self._last_recv) > 10000:
            gc.collect()
        
        return ReasonCode.SUCCESS
    
    def loop_forever(self, timeout=1.0, max_packets=1, retry_first_connection=False):
        """
        Run loop forever (blocking)
        
        ⚠️ This blocks execution - use in main loop only
        
        :param timeout: Loop timeout
        :param max_packets: Max packets per loop (not used)
        :param retry_first_connection: Retry if first connection fails
        """
        if not self._connected and retry_first_connection:
            while not self._connected:
                try:
                    self.reconnect()
                    time.sleep(5)
                except:
                    time.sleep(5)
        
        while True:
            rc = self.loop(timeout, max_packets)
            
            if rc != ReasonCode.SUCCESS:
                if self._auto_reconnect:
                    time.sleep(5)
                    try:
                        self.reconnect()
                    except:
                        pass
                else:
                    break
    
    def loop_start(self):
        """
        Start background loop (NOT SUPPORTED)
        
        MicroPython limitation: no threading support in u-paho-mqtt.
        Use loop() or loop_forever() instead.
        """
        raise NotImplementedError("Threading not supported. Use loop() or loop_forever()")
    
    def loop_stop(self, force=False):
        """Stop background loop (NOT SUPPORTED)"""
        raise NotImplementedError("Threading not supported")
    
    # ==========================================
    # Packet Handlers
    # ==========================================
    
    def _handle_packet(self, packet):
        """Handle received packet"""
        if packet.packet_type == PacketType.PUBLISH:
            self._handle_publish(packet)
        
        elif packet.packet_type == PacketType.PUBACK:
            self._handle_puback(packet)
        
        elif packet.packet_type == PacketType.PUBREC:
            self._handle_pubrec(packet)
        
        elif packet.packet_type == PacketType.PUBREL:
            self._handle_pubrel(packet)
        
        elif packet.packet_type == PacketType.PUBCOMP:
            self._handle_pubcomp(packet)
        
        elif packet.packet_type == PacketType.SUBACK:
            self._handle_suback(packet)
        
        elif packet.packet_type == PacketType.UNSUBACK:
            self._handle_unsuback(packet)
        
        elif packet.packet_type == PacketType.PINGRESP:
            self._handle_pingresp(packet)
        
        elif packet.packet_type == PacketType.DISCONNECT:
            self._handle_disconnect(packet)
    
    def _handle_publish(self, packet):
        """Handle PUBLISH packet"""
        # Create MQTTMessage
        message = MQTTMessage(mid=packet.mid)
        message.topic = packet.topic
        message.payload = packet.payload
        message.qos = packet.qos
        message.retain = packet.retain
        message.properties = packet.properties
        
        # Send PUBACK if QoS 1
        if packet.qos == 1:
            puback = PubackPacket(
                mid=packet.mid,
                reason_code=ReasonCode.SUCCESS,
                protocol_version=self._protocol
            )
            try:
                send_packet_to_socket(self._sock, puback)
            except:
                pass
        
        # Send PUBREC if QoS 2 (step 1 of 4-way handshake)
        elif packet.qos == 2:
            pubrec = PubrecPacket(
                packet_id=packet.mid,
                reason_code=ReasonCode.SUCCESS,
                protocol_version=self._protocol
            )
            try:
                send_packet_to_socket(self._sock, pubrec)
                # Store mid for PUBREL/PUBCOMP handling
                self._in_packet[packet.mid] = message
            except:
                pass
            # Don't deliver message yet - wait for PUBREL
            return
        
        # Check for topic-specific callback
        callback = None
        for pattern, cb in self._message_callbacks.items():
            if self._topic_matches(pattern, message.topic):
                callback = cb
                break
        
        # Call callback
        if callback:
            callback(self, self._userdata, message)
        elif self.on_message:
            self.on_message(self, self._userdata, message)
    
    def _handle_puback(self, packet):
        """Handle PUBACK packet (QoS 1)"""
        if packet.mid in self._inflight_messages:
            msg_info = self._inflight_messages.pop(packet.mid)
            msg_info._set_confirmed()
            
            if self.on_publish:
                self.on_publish(self, self._userdata, packet.mid)
    
    def _handle_pubrec(self, packet):
        """Handle PUBREC packet (QoS 2, step 2 of 4-way handshake)"""
        # PUBREC received - send PUBREL
        if packet.packet_id in self._inflight_messages:
            # Store that we received PUBREC
            self._qos2_pubrec_received[packet.packet_id] = self._inflight_messages[packet.packet_id]
            
            # Send PUBREL (step 3)
            pubrel = PubrelPacket(
                packet_id=packet.packet_id,
                reason_code=ReasonCode.SUCCESS,
                protocol_version=self._protocol
            )
            try:
                send_packet_to_socket(self._sock, pubrel)
                self._qos2_pubrel_sent.add(packet.packet_id)
            except:
                pass
    
    def _handle_pubrel(self, packet):
        """Handle PUBREL packet (QoS 2, step 3 - receiving side)"""
        # PUBREL received - deliver message and send PUBCOMP
        if packet.packet_id in self._in_packet:
            message = self._in_packet.pop(packet.packet_id)
            
            # Deliver message to callback
            callback = None
            for pattern, cb in self._message_callbacks.items():
                if self._topic_matches(pattern, message.topic):
                    callback = cb
                    break
            
            if callback:
                callback(self, self._userdata, message)
            elif self.on_message:
                self.on_message(self, self._userdata, message)
        
        # Send PUBCOMP (step 4)
        pubcomp = PubcompPacket(
            packet_id=packet.packet_id,
            reason_code=ReasonCode.SUCCESS,
            protocol_version=self._protocol
        )
        try:
            send_packet_to_socket(self._sock, pubcomp)
        except:
            pass
    
    def _handle_pubcomp(self, packet):
        """Handle PUBCOMP packet (QoS 2, step 4 of 4-way handshake)"""
        # QoS 2 flow complete
        if packet.packet_id in self._inflight_messages:
            msg_info = self._inflight_messages.pop(packet.packet_id)
            msg_info._set_confirmed()
            
            # Clean up QoS 2 tracking
            self._qos2_pubrec_received.pop(packet.packet_id, None)
            self._qos2_pubrel_sent.discard(packet.packet_id)
            
            if self.on_publish:
                self.on_publish(self, self._userdata, packet.packet_id)
    
    def _handle_suback(self, packet):
        """Handle SUBACK packet"""
        if self.on_subscribe:
            self.on_subscribe(self, self._userdata, packet.mid,
                            packet.return_codes, packet.properties)
    
    def _handle_unsuback(self, packet):
        """Handle UNSUBACK packet"""
        if self.on_unsubscribe:
            if self._protocol == MQTTProtocolVersion.MQTTv5:
                self.on_unsubscribe(self, self._userdata, packet.mid,
                                  packet.properties, packet.reason_codes)
            else:
                self.on_unsubscribe(self, self._userdata, packet.mid,
                                  None, None)
    
    def _handle_pingresp(self, packet):
        """Handle PINGRESP packet"""
        self._ping_pending = False
    
    def _handle_disconnect(self, packet):
        """Handle DISCONNECT packet from server"""
        self._connected = False
        
        if self.on_disconnect:
            self.on_disconnect(self, self._userdata,
                             packet.reason_code, packet.properties)
    
    def _send_pingreq(self):
        """Send PINGREQ packet"""
        try:
            ping = PingReqPacket()
            send_packet_to_socket(self._sock, ping)
        except Exception as e:
            self._log(f"Failed to send PINGREQ: {e}")
            self._connected = False
    
    @staticmethod
    def _topic_matches(pattern, topic):
        """
        Check if topic matches subscription pattern
        
        Supports MQTT wildcards: + (single level), # (multi level)
        """
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        pi = 0
        ti = 0
        
        while pi < len(pattern_parts) and ti < len(topic_parts):
            if pattern_parts[pi] == '#':
                return True
            elif pattern_parts[pi] == '+':
                pi += 1
                ti += 1
            elif pattern_parts[pi] == topic_parts[ti]:
                pi += 1
                ti += 1
            else:
                return False
        
        return pi == len(pattern_parts) and ti == len(topic_parts)
    
    # ==========================================
    # Utility Methods
    # ==========================================
    
    def is_connected(self):
        """Check if connected to broker"""
        return self._connected
    
    def enable_logger(self, logger=None):
        """
        Enable logging (simplified)
        
        :param logger: Not used (use on_log callback instead)
        """
        pass
    
    def disable_logger(self):
        """Disable logging"""
        self.on_log = None
    
    def _log(self, message, level=0):
        """
        Internal logging
        
        Levels (compatible with paho-mqtt):
        - 0: ERROR
        - 1: INFO (connection/disconnection events)
        - 2: DEBUG (detailed packet info)
        """
        if self.on_log:
            self.on_log(self, self._userdata, level, message)
        # Only print errors by default (level 0)
        elif level == 0:
            print(f"[MQTT ERROR] {message}")
    
    def _get_next_mid(self):
        """Generate next message ID"""
        self._last_mid = (self._last_mid % 65535) + 1
        return self._last_mid
