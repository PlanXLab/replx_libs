import usocket
import uselect
import time
import gc

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


from .enums import (
    MQTTProtocolVersion, PacketType, ReasonCode, PropertyType
)
from .properties import Properties
from .message import MQTTMessage, MQTTMessageInfo
from .packets import (
    ConnectPacket, PublishPacket, PubackPacket, PubrecPacket,
    PubrelPacket, PubcompPacket, SubscribePacket,
    UnsubscribePacket, PingReqPacket, DisconnectPacket,
    ConnackPacket, SubackPacket, UnsubackPacket, PingRespPacket
)


class Client:
    __slots__ = [
        '_client_id', '_clean_start', '_protocol', '_transport',
        '_host', '_port', '_keepalive', '_sock', '_connected',
        '_username', '_password', '_ssl_context',
        '_connect_properties', '_will_properties',
        '_will_topic', '_will_payload', '_will_qos', '_will_retain',
        'on_connect', 'on_disconnect', 'on_message',
        'on_publish', 'on_subscribe', 'on_unsubscribe', 'on_log',
        '_out_packet', '_in_packet', '_inflight_messages',
        '_subscriptions', '_message_callbacks',
        '_last_mid', '_last_ping', '_last_recv', '_ping_pending',
        '_server_keepalive', '_server_max_packet_size', '_server_topic_alias_max',
        '_receive_maximum', '_topic_alias_outbound', '_topic_alias_inbound',
        '_userdata',
        '_reconnect_on_failure', '_auto_reconnect', '_socket_timeout'
    ]
    
    def __init__(self, client_id="", clean_session=None, userdata=None,
                 protocol=MQTTProtocolVersion.MQTTv5, transport="tcp"):
        self._client_id = client_id
        self._protocol = protocol
        self._transport = transport
        self._userdata = userdata
        
        if clean_session is None:
            self._clean_start = True
        else:
            self._clean_start = clean_session
        
        self._host = None
        self._port = 1883
        self._keepalive = 60
        self._sock = None
        self._connected = False
        self._socket_timeout = 1.0
        
        self._username = None
        self._password = None
        self._ssl_context = None
        
        self._connect_properties = Properties()
        self._will_properties = Properties()
        
        self._will_topic = None
        self._will_payload = None
        self._will_qos = 0
        self._will_retain = False
        
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None
        self.on_publish = None
        self.on_subscribe = None
        self.on_unsubscribe = None
        self.on_log = None
        
        self._out_packet = []
        self._in_packet = {}
        self._inflight_messages = {}
        
        self._qos2_pubrec_received = {}  
        self._qos2_pubrel_sent = set()   
        
        self._subscriptions = {}
        self._message_callbacks = {}
        
        self._last_mid = 0
        self._last_ping = 0
        self._last_recv = 0
        self._ping_pending = False
        
        self._server_keepalive = None
        self._server_max_packet_size = None
        self._server_topic_alias_max = 0
        self._receive_maximum = 65535
        self._topic_alias_outbound = {}
        self._topic_alias_inbound = {}
        
        self._reconnect_on_failure = True
        self._auto_reconnect = False
        
    def username_pw_set(self, username, password=None):
        self._username = username
        self._password = password
    
    def tls_set(self, ca_certs=None, certfile=None, keyfile=None):
        self._ssl_context = {}
        
        if ca_certs:
            self._ssl_context['ca_certs'] = ca_certs
        if certfile:
            self._ssl_context['certfile'] = certfile
        if keyfile:
            self._ssl_context['keyfile'] = keyfile
    
    def tls_insecure_set(self, value):
        if self._ssl_context is None:
            self._ssl_context = {}
        self._ssl_context['cert_reqs'] = not value
    
    def will_set(self, topic, payload=None, qos=0, retain=False, properties=None):
        self._will_topic = topic
        self._will_payload = payload if payload is not None else b""
        self._will_qos = qos
        self._will_retain = retain
        
        if properties and self._protocol == MQTTProtocolVersion.MQTTv5:
            self._will_properties = properties
    
    def will_clear(self):
        self._will_topic = None
        self._will_payload = None
        self._will_qos = 0
        self._will_retain = False
        self._will_properties = Properties()
    
    def max_inflight_messages_set(self, inflight):
        self._receive_maximum = inflight
    
    def user_data_set(self, userdata):
        self._userdata = userdata
        
    def connect(self, host, port=1883, keepalive=60):
        self._host = host
        self._port = port
        self._keepalive = keepalive
        
        try:
            addr_info = usocket.getaddrinfo(host, port)[0]
            addr = addr_info[-1]
        except OSError as e:
            self._log(f"DNS lookup failed for {host}: {e}")
            if self.on_connect:
                self.on_connect(self, self._userdata, {}, ReasonCode.NETWORK_ERROR, None)
            return ReasonCode.NETWORK_ERROR
        
        max_retries = 3
        connected = False
        
        for attempt in range(max_retries):
            if attempt > 0:
                time.sleep(2)
            
            try:
                if self._sock:
                    try:
                        self._sock.close()
                    except:
                        pass
                
                self._sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
                self._sock.settimeout(30.0)
            except Exception as e:
                self._log(f"Socket creation failed: {e}")
                continue
            
            try:
                self._sock.connect(addr)
                connected = True
                break
            except OSError as e:
                if attempt == max_retries - 1:
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
            self._send_packet_to_socket(self._sock, connect_packet)
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
        
        self._sock.settimeout(10.0)
        try:
            connack = self._read_packet_from_socket(self._sock, self._protocol)
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
        
        if connack.reason_code != ReasonCode.SUCCESS:
            self._log(f"Connection refused: {connack.reason_code}")
            self._sock.close()
            self._sock = None
            if self.on_connect:
                flags = {'session_present': connack.session_present}
                self.on_connect(self, self._userdata, flags,
                              connack.reason_code, connack.properties)
            return connack.reason_code
        
        self._connected = True
        self._last_recv = time.ticks_ms()
        self._sock.settimeout(self._socket_timeout)
        
        if self._protocol == MQTTProtocolVersion.MQTTv5:
            self._process_connack_properties(connack.properties)
        
        if self.on_connect:
            flags = {'session_present': connack.session_present}
            self.on_connect(self, self._userdata, flags,
                          connack.reason_code, connack.properties)
        
        self._log(f"Connected to {host}:{port}", level=1) 
        return ReasonCode.SUCCESS

    def reconnect(self):
        if self._host is None:
            raise ValueError("connect() must be called before reconnect()")
        
        if self._connected:
            self.disconnect()
        
        return self.connect(self._host, self._port, self._keepalive)
    
    def disconnect(self, reasoncode=None, properties=None):
        if not self._connected:
            return ReasonCode.SUCCESS
        
        if reasoncode is None:
            reasoncode = ReasonCode.NORMAL_DISCONNECTION
        
        disconnect_packet = DisconnectPacket(
            reason_code=reasoncode,
            protocol_version=self._protocol,
            properties=properties or Properties()
        )
        
        try:
            self._send_packet_to_socket(self._sock, disconnect_packet)
            time.sleep_ms(100)
        except:
            pass
        
        try:
            self._sock.close()
        except:
            pass
        
        self._sock = None
        self._connected = False
        
        if self.on_disconnect:
            self.on_disconnect(self, self._userdata, reasoncode, properties)
        
        self._log("Disconnected from broker", level=1)
        return ReasonCode.SUCCESS
    
    def _process_connack_properties(self, properties):
        if properties.has(PropertyType.SERVER_KEEP_ALIVE):
            self._server_keepalive = properties.get(PropertyType.SERVER_KEEP_ALIVE)
            self._keepalive = self._server_keepalive
            self._log(f"Server override keepalive: {self._server_keepalive}s", level=1)
        
        if properties.has(PropertyType.MAXIMUM_PACKET_SIZE):
            self._server_max_packet_size = properties.get(PropertyType.MAXIMUM_PACKET_SIZE)
            self._log(f"Server max packet size: {self._server_max_packet_size}", level=1)
        
        if properties.has(PropertyType.TOPIC_ALIAS_MAXIMUM):
            self._server_topic_alias_max = properties.get(PropertyType.TOPIC_ALIAS_MAXIMUM)
            self._log(f"Server topic alias max: {self._server_topic_alias_max}", level=1)
        
        if properties.has(PropertyType.RECEIVE_MAXIMUM):
            self._receive_maximum = properties.get(PropertyType.RECEIVE_MAXIMUM)
            self._log(f"Server receive maximum: {self._receive_maximum}", level=1)
    
    def publish(self, topic, payload=None, qos=0, retain=False, properties=None):
        if not self._connected:
            self._log("Cannot publish: not connected")
            info = MQTTMessageInfo(0)
            return info
        
        if qos < 0 or qos > 2:
            raise ValueError("QoS must be 0, 1, or 2")
        
        mid = self._get_next_mid() if qos > 0 else 0
        
        publish_packet = PublishPacket(
            topic=topic,
            payload=payload,
            qos=qos,
            retain=retain,
            mid=mid,
            protocol_version=self._protocol,
            properties=properties or Properties()
        )
        
        try:
            self._send_packet_to_socket(self._sock, publish_packet)
        except Exception as e:
            self._log(f"Publish failed: {e}")
            self._connected = False
            return MQTTMessageInfo(mid)
        
        msg_info = MQTTMessageInfo(mid)
        
        if qos == 0:
            msg_info._set_published()
            if self.on_publish:
                self.on_publish(self, self._userdata, mid)
        else:
            self._inflight_messages[mid] = msg_info
        
        return msg_info
    
    def subscribe(self, topic, qos=0, properties=None):
        if not self._connected:
            self._log("Cannot subscribe: not connected")
            return (ReasonCode.NOT_AUTHORIZED, None)
        
        if isinstance(topic, str):
            topic_list = [(topic, qos)]
        elif isinstance(topic, list):
            topic_list = topic
        elif isinstance(topic, tuple):
            topic_list = [topic]
        else:
            raise ValueError("Invalid topic format")
        
        mid = self._get_next_mid()
        
        subscribe_packet = SubscribePacket(
            mid=mid,
            topics=topic_list,
            protocol_version=self._protocol,
            properties=properties or Properties()
        )
        
        try:
            self._send_packet_to_socket(self._sock, subscribe_packet)
        except Exception as e:
            self._log(f"Subscribe failed: {e}")
            self._connected = False
            return (ReasonCode.UNSPECIFIED_ERROR, mid)
        
        for t, q in topic_list:
            self._subscriptions[t] = (q, properties)
        
        return (ReasonCode.SUCCESS, mid)
    
    def unsubscribe(self, topic, properties=None):
        if not self._connected:
            self._log("Cannot unsubscribe: not connected")
            return (ReasonCode.NOT_AUTHORIZED, None)
        
        if isinstance(topic, str):
            topic_list = [topic]
        else:
            topic_list = list(topic)
        
        mid = self._get_next_mid()
        
        unsubscribe_packet = UnsubscribePacket(
            mid=mid,
            topics=topic_list,
            protocol_version=self._protocol,
            properties=properties or Properties()
        )
        
        try:
            self._send_packet_to_socket(self._sock, unsubscribe_packet)
        except Exception as e:
            self._log(f"Unsubscribe failed: {e}")
            self._connected = False
            return (ReasonCode.UNSPECIFIED_ERROR, mid)
        
        for t in topic_list:
            self._subscriptions.pop(t, None)
            self._message_callbacks.pop(t, None)
        
        return (ReasonCode.SUCCESS, mid)
    
    def message_callback_add(self, sub, callback):
        self._message_callbacks[sub] = callback
    
    def message_callback_remove(self, sub):
        self._message_callbacks.pop(sub, None)
    
    def loop(self, timeout=1.0, max_packets=1):
        if not self._connected:
            return ReasonCode.NOT_AUTHORIZED
        
        now = time.ticks_ms()
        
        if self._keepalive > 0:
            time_since_recv = time.ticks_diff(now, self._last_recv) / 1000
            
            if time_since_recv >= (self._keepalive * 1.5):
                self._log("Keepalive timeout - disconnecting")
                self._connected = False
                if self.on_disconnect:
                    self.on_disconnect(self, self._userdata,
                                     ReasonCode.KEEPALIVE_TIMEOUT, None)
                return ReasonCode.KEEPALIVE_TIMEOUT
            
            elif time_since_recv >= self._keepalive:
                if not self._ping_pending:
                    self._send_pingreq()
                    self._ping_pending = True
                    self._last_ping = now
        
        poller = uselect.poll()
        poller.register(self._sock, uselect.POLLIN)
        
        events = poller.poll(int(timeout * 1000))
        
        if events:
            try:
                packet = self._read_packet_from_socket(self._sock, self._protocol)
                
                if packet:
                    self._last_recv = time.ticks_ms()
                    self._handle_packet(packet)
                else:
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
        
        if time.ticks_diff(now, self._last_recv) > 10000:
            gc.collect()
        
        return ReasonCode.SUCCESS
    
    def loop_forever(self, timeout=1.0, max_packets=1, retry_first_connection=False):
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
    
    def _handle_packet(self, packet):
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
            self._handle_pingresp()
        
        elif packet.packet_type == PacketType.DISCONNECT:
            self._handle_disconnect(packet)
    
    def _handle_publish(self, packet):
        message = MQTTMessage(mid=packet.mid)
        message.topic = packet.topic
        message.payload = packet.payload
        message.qos = packet.qos
        message.retain = packet.retain
        message.properties = packet.properties
        
        if packet.qos == 1:
            puback = PubackPacket(
                mid=packet.mid,
                reason_code=ReasonCode.SUCCESS,
                protocol_version=self._protocol
            )
            try:
                self._send_packet_to_socket(self._sock, puback)
            except:
                pass
        
        elif packet.qos == 2:
            pubrec = PubrecPacket(
                packet_id=packet.mid,
                reason_code=ReasonCode.SUCCESS,
                protocol_version=self._protocol
            )
            try:
                self._send_packet_to_socket(self._sock, pubrec)
                self._in_packet[packet.mid] = message
            except:
                pass
            return
        
        callback = None
        for pattern, cb in self._message_callbacks.items():
            if self._topic_matches(pattern, message.topic):
                callback = cb
                break
        
        if callback:
            callback(self, self._userdata, message)
        elif self.on_message:
            self.on_message(self, self._userdata, message)
    
    def _handle_puback(self, packet):
        if packet.mid in self._inflight_messages:
            msg_info = self._inflight_messages.pop(packet.mid)
            msg_info._set_confirmed()
            
            if self.on_publish:
                self.on_publish(self, self._userdata, packet.mid)
    
    def _handle_pubrec(self, packet):
        if packet.packet_id in self._inflight_messages:
            self._qos2_pubrec_received[packet.packet_id] = self._inflight_messages[packet.packet_id]
            
            pubrel = PubrelPacket(
                packet_id=packet.packet_id,
                reason_code=ReasonCode.SUCCESS,
                protocol_version=self._protocol
            )
            try:
                self._send_packet_to_socket(self._sock, pubrel)
                self._qos2_pubrel_sent.add(packet.packet_id)
            except:
                pass
    
    def _handle_pubrel(self, packet):
        if packet.packet_id in self._in_packet:
            message = self._in_packet.pop(packet.packet_id)
            
            callback = None
            for pattern, cb in self._message_callbacks.items():
                if self._topic_matches(pattern, message.topic):
                    callback = cb
                    break
            
            if callback:
                callback(self, self._userdata, message)
            elif self.on_message:
                self.on_message(self, self._userdata, message)
        
        pubcomp = PubcompPacket(
            packet_id=packet.packet_id,
            reason_code=ReasonCode.SUCCESS,
            protocol_version=self._protocol
        )
        try:
            self._send_packet_to_socket(self._sock, pubcomp)
        except:
            pass
    
    def _handle_pubcomp(self, packet):
        if packet.packet_id in self._inflight_messages:
            msg_info = self._inflight_messages.pop(packet.packet_id)
            msg_info._set_confirmed()
            
            self._qos2_pubrec_received.pop(packet.packet_id, None)
            self._qos2_pubrel_sent.discard(packet.packet_id)
            
            if self.on_publish:
                self.on_publish(self, self._userdata, packet.packet_id)
    
    def _handle_suback(self, packet):
        if self.on_subscribe:
            self.on_subscribe(self, self._userdata, packet.mid,
                            packet.return_codes, packet.properties)
    
    def _handle_unsuback(self, packet):
        if self.on_unsubscribe:
            if self._protocol == MQTTProtocolVersion.MQTTv5:
                self.on_unsubscribe(self, self._userdata, packet.mid,
                                  packet.properties, packet.reason_codes)
            else:
                self.on_unsubscribe(self, self._userdata, packet.mid,
                                  None, None)
    
    def _handle_pingresp(self):
        self._ping_pending = False
    
    def _handle_disconnect(self, packet):
        self._connected = False
        
        if self.on_disconnect:
            self.on_disconnect(self, self._userdata,
                             packet.reason_code, packet.properties)
    
    def _send_pingreq(self):
        try:
            ping = PingReqPacket()
            self._send_packet_to_socket(self._sock, ping)
        except Exception as e:
            self._log(f"Failed to send PINGREQ: {e}")
            self._connected = False
    
    @staticmethod
    def _topic_matches(pattern, topic):
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
    
    def is_connected(self):
        return self._connected
    
    def _log(self, message, level=0):
        if self.on_log:
            self.on_log(self, self._userdata, level, message)
        elif level == 0:
            print(f"[MQTT ERROR] {message}")
    
    def _get_next_mid(self):
        self._last_mid = (self._last_mid % 65535) + 1
        return self._last_mid
    
    def _read_packet_from_socket(self, sock, protocol_version=MQTTProtocolVersion.MQTTv5):
        try:
            byte1 = sock.recv(1)
            if not byte1 or len(byte1) == 0:
                return None
            
            packet_type = byte1[0] & 0xF0
            flags = byte1[0] & 0x0F
            
            remaining_length = 0
            multiplier = 1
            
            for _ in range(4):
                byte = sock.recv(1)
                if not byte or len(byte) == 0:
                    return None
                
                value = byte[0]
                remaining_length += (value & 0x7F) * multiplier
                
                if (value & 0x80) == 0:
                    break
                
                multiplier *= 128
            
            if remaining_length > 0:
                data = bytearray()
                while len(data) < remaining_length:
                    chunk = sock.recv(remaining_length - len(data))
                    if not chunk or len(chunk) == 0:
                        return None
                    data.extend(chunk)
            else:
                data = bytearray()
            
            return self._decode_packet_data(packet_type, flags, bytes(data), protocol_version)
        
        except Exception as e:
            return None
    
    def _decode_packet_data(self, packet_type, flags, data, protocol_version):
        if packet_type == PacketType.CONNACK:
            return ConnackPacket.unpack(data)
        
        elif packet_type == PacketType.PUBLISH:
            return PublishPacket.unpack(flags, data, protocol_version)
        
        elif packet_type == PacketType.PUBACK:
            return PubackPacket.unpack(data, protocol_version)
        
        elif packet_type == PacketType.PUBREC:
            return PubrecPacket.unpack(data, protocol_version)
        
        elif packet_type == PacketType.PUBREL:
            return PubrelPacket.unpack(data, protocol_version)
        
        elif packet_type == PacketType.PUBCOMP:
            return PubcompPacket.unpack(data, protocol_version)
        
        elif packet_type == PacketType.SUBACK:
            return SubackPacket.unpack(data, protocol_version)
        
        elif packet_type == PacketType.UNSUBACK:
            return UnsubackPacket.unpack(data, protocol_version)
        
        elif packet_type == PacketType.PINGRESP:
            return PingRespPacket.unpack()
        
        elif packet_type == PacketType.DISCONNECT:
            return DisconnectPacket.unpack(data, protocol_version)
        
        else:
            return None
    
    def _send_packet_to_socket(self, sock, packet):
        data = packet.pack()
        total_sent = 0
        while total_sent < len(data):
            try:
                sent = sock.send(data[total_sent:])
                if sent == 0:
                    raise OSError("Socket connection broken")
                total_sent += sent
            except OSError as e:
                if e.args[0] not in (11, 115):
                    raise
                time.sleep_ms(10)
