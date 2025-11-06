"""
MQTT Packet Encoding and Decoding

Implements MQTT 3.1.1 and 5.0 packet structures.
"""

import struct
from .enums import (
    PacketType, MQTTProtocolVersion, ConnectFlag, 
    QoS, ReasonCode, SubscriptionOption
)
from .properties import (
    Properties, _encode_variable_length, _decode_variable_length,
    _encode_utf8, _decode_utf8, _encode_binary, _decode_binary
)


class MQTTPacket:
    """Base class for MQTT packets"""
    
    def __init__(self, packet_type, flags=0):
        self.packet_type = packet_type
        self.flags = flags
    
    def pack(self):
        """Encode packet to bytes"""
        raise NotImplementedError
    
    @staticmethod
    def unpack(packet_type, flags, data):
        """Decode packet from bytes"""
        raise NotImplementedError
    
    def _pack_fixed_header(self, remaining_length):
        """Pack fixed header (byte 1 + remaining length)"""
        byte1 = (self.packet_type & 0xF0) | (self.flags & 0x0F)
        return bytes([byte1]) + _encode_variable_length(remaining_length)


class ConnectPacket(MQTTPacket):
    """MQTT CONNECT packet"""
    
    def __init__(self, client_id, clean_start=True, keepalive=60,
                 username=None, password=None,
                 will_topic=None, will_payload=None, will_qos=0, will_retain=False,
                 protocol_version=MQTTProtocolVersion.MQTTv5,
                 properties=None, will_properties=None):
        super().__init__(PacketType.CONNECT)
        
        self.client_id = client_id
        self.clean_start = clean_start
        self.keepalive = keepalive
        self.username = username
        self.password = password
        self.will_topic = will_topic
        self.will_payload = will_payload
        self.will_qos = will_qos
        self.will_retain = will_retain
        self.protocol_version = protocol_version
        self.properties = properties or Properties()
        self.will_properties = will_properties or Properties()
    
    def pack(self):
        """Encode CONNECT packet"""
        variable_header = bytearray()
        
        # Protocol Name
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.extend(_encode_utf8("MQTT"))
            variable_header.append(0x05)  # Protocol Level
        else:  # MQTTv311
            variable_header.extend(_encode_utf8("MQTT"))
            variable_header.append(0x04)  # Protocol Level
        
        # Connect Flags
        connect_flags = 0
        if self.clean_start:
            connect_flags |= ConnectFlag.CLEAN_START
        if self.will_topic:
            connect_flags |= ConnectFlag.WILL_FLAG
            connect_flags |= (self.will_qos & 0x03) << 3
            if self.will_retain:
                connect_flags |= ConnectFlag.WILL_RETAIN
        if self.username:
            connect_flags |= ConnectFlag.USERNAME
        if self.password:
            connect_flags |= ConnectFlag.PASSWORD
        
        variable_header.append(connect_flags)
        
        # Keep Alive
        variable_header.extend(struct.pack('!H', self.keepalive))
        
        # Properties (MQTT 5.0 only)
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.extend(self.properties.pack())
        
        # Payload
        payload = bytearray()
        
        # Client ID
        payload.extend(_encode_utf8(self.client_id))
        
        # Will Properties (MQTT 5.0 only)
        if self.will_topic and self.protocol_version == MQTTProtocolVersion.MQTTv5:
            payload.extend(self.will_properties.pack())
        
        # Will Topic and Message
        if self.will_topic:
            payload.extend(_encode_utf8(self.will_topic))
            if self.will_payload:
                payload.extend(_encode_binary(self.will_payload))
            else:
                payload.extend(struct.pack('!H', 0))
        
        # Username
        if self.username:
            payload.extend(_encode_utf8(self.username))
        
        # Password
        if self.password:
            payload.extend(_encode_utf8(self.password))
        
        # Combine
        packet = variable_header + payload
        return self._pack_fixed_header(len(packet)) + bytes(packet)


class ConnackPacket(MQTTPacket):
    """MQTT CONNACK packet"""
    
    def __init__(self):
        super().__init__(PacketType.CONNACK)
        self.session_present = False
        self.return_code = 0
        self.reason_code = ReasonCode.SUCCESS
        self.properties = Properties()
    
    @staticmethod
    def unpack(flags, data):
        """Decode CONNACK packet"""
        packet = ConnackPacket()
        offset = 0
        
        # Connect Acknowledge Flags
        ack_flags = data[offset]
        offset += 1
        packet.session_present = (ack_flags & 0x01) != 0
        
        # Return/Reason Code
        packet.return_code = data[offset]
        packet.reason_code = data[offset]
        offset += 1
        
        # Properties (MQTT 5.0)
        if offset < len(data):
            packet.properties, offset = Properties.unpack(data, offset)
        
        return packet


class PublishPacket(MQTTPacket):
    """MQTT PUBLISH packet"""
    
    def __init__(self, topic, payload=None, qos=0, retain=False, dup=False,
                 mid=0, protocol_version=MQTTProtocolVersion.MQTTv5,
                 properties=None):
        # Flags: DUP(3), QoS(2:1), RETAIN(0)
        flags = 0
        if dup:
            flags |= 0x08
        flags |= (qos & 0x03) << 1
        if retain:
            flags |= 0x01
        
        super().__init__(PacketType.PUBLISH, flags)
        
        self.topic = topic
        self.payload = payload if payload is not None else b""
        self.qos = qos
        self.retain = retain
        self.dup = dup
        self.mid = mid
        self.protocol_version = protocol_version
        self.properties = properties or Properties()
    
    def pack(self):
        """Encode PUBLISH packet"""
        variable_header = bytearray()
        
        # Topic Name
        variable_header.extend(_encode_utf8(self.topic))
        
        # Packet Identifier (if QoS > 0)
        if self.qos > 0:
            variable_header.extend(struct.pack('!H', self.mid))
        
        # Properties (MQTT 5.0 only)
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.extend(self.properties.pack())
        
        # Payload
        if isinstance(self.payload, str):
            payload = self.payload.encode('utf-8')
        else:
            payload = self.payload
        
        packet = variable_header + payload
        return self._pack_fixed_header(len(packet)) + bytes(packet)
    
    @staticmethod
    def unpack(flags, data, protocol_version=MQTTProtocolVersion.MQTTv5):
        """Decode PUBLISH packet"""
        packet = PublishPacket("", protocol_version=protocol_version)
        
        # Parse flags
        packet.dup = (flags & 0x08) != 0
        packet.qos = (flags >> 1) & 0x03
        packet.retain = (flags & 0x01) != 0
        packet.flags = flags
        
        offset = 0
        
        # Topic Name
        packet.topic, offset = _decode_utf8(data, offset)
        
        # Packet Identifier (if QoS > 0)
        if packet.qos > 0:
            packet.mid = struct.unpack_from('!H', data, offset)[0]
            offset += 2
        
        # Properties (MQTT 5.0)
        if protocol_version == MQTTProtocolVersion.MQTTv5:
            packet.properties, offset = Properties.unpack(data, offset)
        
        # Payload
        packet.payload = bytes(data[offset:])
        
        return packet


class PubackPacket(MQTTPacket):
    """MQTT PUBACK packet (QoS 1 acknowledgment)"""
    
    def __init__(self, mid, reason_code=ReasonCode.SUCCESS, 
                 protocol_version=MQTTProtocolVersion.MQTTv5,
                 properties=None):
        super().__init__(PacketType.PUBACK)
        self.mid = mid
        self.reason_code = reason_code
        self.protocol_version = protocol_version
        self.properties = properties or Properties()
    
    def pack(self):
        """Encode PUBACK packet"""
        variable_header = bytearray()
        
        # Packet Identifier
        variable_header.extend(struct.pack('!H', self.mid))
        
        # Reason Code (MQTT 5.0 only)
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.append(self.reason_code)
            variable_header.extend(self.properties.pack())
        
        return self._pack_fixed_header(len(variable_header)) + bytes(variable_header)
    
    @staticmethod
    def unpack(flags, data, protocol_version=MQTTProtocolVersion.MQTTv5):
        """Decode PUBACK packet"""
        offset = 0
        
        # Packet Identifier
        mid = struct.unpack_from('!H', data, offset)[0]
        offset += 2
        
        reason_code = ReasonCode.SUCCESS
        properties = Properties()
        
        # Reason Code (MQTT 5.0)
        if protocol_version == MQTTProtocolVersion.MQTTv5 and offset < len(data):
            reason_code = data[offset]
            offset += 1
            
            if offset < len(data):
                properties, offset = Properties.unpack(data, offset)
        
        return PubackPacket(mid, reason_code, protocol_version, properties)


class SubscribePacket(MQTTPacket):
    """MQTT SUBSCRIBE packet"""
    
    def __init__(self, mid, topics, protocol_version=MQTTProtocolVersion.MQTTv5,
                 properties=None):
        super().__init__(PacketType.SUBSCRIBE, flags=0x02)  # Fixed flags
        self.mid = mid
        self.topics = topics  # List of (topic, qos) or (topic, qos, options)
        self.protocol_version = protocol_version
        self.properties = properties or Properties()
    
    def pack(self):
        """Encode SUBSCRIBE packet"""
        variable_header = bytearray()
        
        # Packet Identifier
        variable_header.extend(struct.pack('!H', self.mid))
        
        # Properties (MQTT 5.0 only)
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.extend(self.properties.pack())
        
        # Payload (Topic Filters)
        payload = bytearray()
        for item in self.topics:
            if len(item) == 2:
                topic, qos = item
                options = qos & 0x03  # MQTT 3.1.1 style
            else:
                topic, qos, options = item
            
            payload.extend(_encode_utf8(topic))
            
            if self.protocol_version == MQTTProtocolVersion.MQTTv5:
                # Subscription Options
                payload.append(options)
            else:
                # QoS only
                payload.append(qos & 0x03)
        
        packet = variable_header + payload
        return self._pack_fixed_header(len(packet)) + bytes(packet)


class SubackPacket(MQTTPacket):
    """MQTT SUBACK packet"""
    
    def __init__(self):
        super().__init__(PacketType.SUBACK)
        self.mid = 0
        self.return_codes = []
        self.reason_codes = []
        self.properties = Properties()
    
    @staticmethod
    def unpack(flags, data, protocol_version=MQTTProtocolVersion.MQTTv5):
        """Decode SUBACK packet"""
        packet = SubackPacket()
        offset = 0
        
        # Packet Identifier
        packet.mid = struct.unpack_from('!H', data, offset)[0]
        offset += 2
        
        # Properties (MQTT 5.0)
        if protocol_version == MQTTProtocolVersion.MQTTv5:
            packet.properties, offset = Properties.unpack(data, offset)
        
        # Return/Reason Codes
        while offset < len(data):
            code = data[offset]
            offset += 1
            packet.return_codes.append(code)
            packet.reason_codes.append(code)
        
        return packet


class UnsubscribePacket(MQTTPacket):
    """MQTT UNSUBSCRIBE packet"""
    
    def __init__(self, mid, topics, protocol_version=MQTTProtocolVersion.MQTTv5,
                 properties=None):
        super().__init__(PacketType.UNSUBSCRIBE, flags=0x02)  # Fixed flags
        self.mid = mid
        self.topics = topics
        self.protocol_version = protocol_version
        self.properties = properties or Properties()
    
    def pack(self):
        """Encode UNSUBSCRIBE packet"""
        variable_header = bytearray()
        
        # Packet Identifier
        variable_header.extend(struct.pack('!H', self.mid))
        
        # Properties (MQTT 5.0 only)
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.extend(self.properties.pack())
        
        # Payload (Topic Filters)
        payload = bytearray()
        for topic in self.topics:
            payload.extend(_encode_utf8(topic))
        
        packet = variable_header + payload
        return self._pack_fixed_header(len(packet)) + bytes(packet)


class UnsubackPacket(MQTTPacket):
    """MQTT UNSUBACK packet"""
    
    def __init__(self):
        super().__init__(PacketType.UNSUBACK)
        self.mid = 0
        self.reason_codes = []
        self.properties = Properties()
    
    @staticmethod
    def unpack(flags, data, protocol_version=MQTTProtocolVersion.MQTTv5):
        """Decode UNSUBACK packet"""
        packet = UnsubackPacket()
        offset = 0
        
        # Packet Identifier
        packet.mid = struct.unpack_from('!H', data, offset)[0]
        offset += 2
        
        # Properties (MQTT 5.0)
        if protocol_version == MQTTProtocolVersion.MQTTv5:
            packet.properties, offset = Properties.unpack(data, offset)
            
            # Reason Codes
            while offset < len(data):
                packet.reason_codes.append(data[offset])
                offset += 1
        
        return packet


class PingReqPacket(MQTTPacket):
    """MQTT PINGREQ packet"""
    
    def __init__(self):
        super().__init__(PacketType.PINGREQ)
    
    def pack(self):
        """Encode PINGREQ packet (no variable header or payload)"""
        return self._pack_fixed_header(0)


class PingRespPacket(MQTTPacket):
    """MQTT PINGRESP packet"""
    
    def __init__(self):
        super().__init__(PacketType.PINGRESP)
    
    @staticmethod
    def unpack(flags, data):
        """Decode PINGRESP packet"""
        return PingRespPacket()


class DisconnectPacket(MQTTPacket):
    """MQTT DISCONNECT packet"""
    
    def __init__(self, reason_code=ReasonCode.NORMAL_DISCONNECTION,
                 protocol_version=MQTTProtocolVersion.MQTTv5,
                 properties=None):
        super().__init__(PacketType.DISCONNECT)
        self.reason_code = reason_code
        self.protocol_version = protocol_version
        self.properties = properties or Properties()
    
    def pack(self):
        """Encode DISCONNECT packet"""
        if self.protocol_version == MQTTProtocolVersion.MQTTv311:
            # MQTT 3.1.1 has no variable header or payload
            return self._pack_fixed_header(0)
        
        # MQTT 5.0
        variable_header = bytearray()
        variable_header.append(self.reason_code)
        variable_header.extend(self.properties.pack())
        
        return self._pack_fixed_header(len(variable_header)) + bytes(variable_header)
    
    @staticmethod
    def unpack(flags, data, protocol_version=MQTTProtocolVersion.MQTTv5):
        """Decode DISCONNECT packet"""
        if protocol_version == MQTTProtocolVersion.MQTTv311:
            return DisconnectPacket(protocol_version=protocol_version)
        
        # MQTT 5.0
        reason_code = ReasonCode.NORMAL_DISCONNECTION
        properties = Properties()
        
        if len(data) > 0:
            reason_code = data[0]
            if len(data) > 1:
                properties, _ = Properties.unpack(data, 1)
        
        return DisconnectPacket(reason_code, protocol_version, properties)


class PubrecPacket(MQTTPacket):
    """MQTT PUBREC packet (QoS 2, step 2)"""
    
    def __init__(self, packet_id, reason_code=ReasonCode.SUCCESS, 
                 protocol_version=MQTTProtocolVersion.MQTTv5, properties=None):
        super().__init__(PacketType.PUBREC)
        self.packet_id = packet_id
        self.reason_code = reason_code
        self.protocol_version = protocol_version
        self.properties = properties if properties else Properties()
    
    def pack(self):
        """Encode PUBREC packet"""
        variable_header = bytearray()
        variable_header.extend(struct.pack('!H', self.packet_id))
        
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.append(self.reason_code)
            variable_header.extend(self.properties.pack())
        
        return self._pack_fixed_header(len(variable_header)) + bytes(variable_header)
    
    @staticmethod
    def unpack(flags, data, protocol_version=MQTTProtocolVersion.MQTTv5):
        """Decode PUBREC packet"""
        packet_id = struct.unpack('!H', data[0:2])[0]
        
        if protocol_version == MQTTProtocolVersion.MQTTv311:
            return PubrecPacket(packet_id, protocol_version=protocol_version)
        
        # MQTT 5.0
        reason_code = ReasonCode.SUCCESS
        properties = Properties()
        
        if len(data) > 2:
            reason_code = data[2]
            if len(data) > 3:
                properties, _ = Properties.unpack(data, 3)
        
        return PubrecPacket(packet_id, reason_code, protocol_version, properties)


class PubrelPacket(MQTTPacket):
    """MQTT PUBREL packet (QoS 2, step 3)"""
    
    def __init__(self, packet_id, reason_code=ReasonCode.SUCCESS,
                 protocol_version=MQTTProtocolVersion.MQTTv5, properties=None):
        super().__init__(PacketType.PUBREL, flags=0x02)  # Fixed flags for PUBREL
        self.packet_id = packet_id
        self.reason_code = reason_code
        self.protocol_version = protocol_version
        self.properties = properties if properties else Properties()
    
    def pack(self):
        """Encode PUBREL packet"""
        variable_header = bytearray()
        variable_header.extend(struct.pack('!H', self.packet_id))
        
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.append(self.reason_code)
            variable_header.extend(self.properties.pack())
        
        return self._pack_fixed_header(len(variable_header)) + bytes(variable_header)
    
    @staticmethod
    def unpack(flags, data, protocol_version=MQTTProtocolVersion.MQTTv5):
        """Decode PUBREL packet"""
        packet_id = struct.unpack('!H', data[0:2])[0]
        
        if protocol_version == MQTTProtocolVersion.MQTTv311:
            return PubrelPacket(packet_id, protocol_version=protocol_version)
        
        # MQTT 5.0
        reason_code = ReasonCode.SUCCESS
        properties = Properties()
        
        if len(data) > 2:
            reason_code = data[2]
            if len(data) > 3:
                properties, _ = Properties.unpack(data, 3)
        
        return PubrelPacket(packet_id, reason_code, protocol_version, properties)


class PubcompPacket(MQTTPacket):
    """MQTT PUBCOMP packet (QoS 2, step 4)"""
    
    def __init__(self, packet_id, reason_code=ReasonCode.SUCCESS,
                 protocol_version=MQTTProtocolVersion.MQTTv5, properties=None):
        super().__init__(PacketType.PUBCOMP)
        self.packet_id = packet_id
        self.reason_code = reason_code
        self.protocol_version = protocol_version
        self.properties = properties if properties else Properties()
    
    def pack(self):
        """Encode PUBCOMP packet"""
        variable_header = bytearray()
        variable_header.extend(struct.pack('!H', self.packet_id))
        
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.append(self.reason_code)
            variable_header.extend(self.properties.pack())
        
        return self._pack_fixed_header(len(variable_header)) + bytes(variable_header)
    
    @staticmethod
    def unpack(flags, data, protocol_version=MQTTProtocolVersion.MQTTv5):
        """Decode PUBCOMP packet"""
        packet_id = struct.unpack('!H', data[0:2])[0]
        
        if protocol_version == MQTTProtocolVersion.MQTTv311:
            return PubcompPacket(packet_id, protocol_version=protocol_version)
        
        # MQTT 5.0
        reason_code = ReasonCode.SUCCESS
        properties = Properties()
        
        if len(data) > 2:
            reason_code = data[2]
            if len(data) > 3:
                properties, _ = Properties.unpack(data, 3)
        
        return PubcompPacket(packet_id, reason_code, protocol_version, properties)
