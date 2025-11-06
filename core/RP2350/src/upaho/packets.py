import struct
from .enums import (
    PacketType, MQTTProtocolVersion, ConnectFlag, ReasonCode
)
from .properties import (
    Properties, _encode_variable_length,
    _encode_utf8, _decode_utf8, _encode_binary, _decode_binary
)

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


class MQTTPacket:
    def __init__(self, packet_type, flags=0):
        self.packet_type = packet_type
        self.flags = flags
    
    def pack(self):
        raise NotImplementedError
    
    def _pack_fixed_header(self, remaining_length):
        byte1 = (self.packet_type & 0xF0) | (self.flags & 0x0F)
        return bytes([byte1]) + _encode_variable_length(remaining_length)


class ConnectPacket(MQTTPacket):
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
        variable_header = bytearray()
        
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.extend(_encode_utf8("MQTT"))
            variable_header.append(0x05)
        else:
            variable_header.extend(_encode_utf8("MQTT"))
            variable_header.append(0x04)
        
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
        
        variable_header.extend(struct.pack('!H', self.keepalive))
        
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.extend(self.properties.pack())
        
        payload = bytearray()
        payload.extend(_encode_utf8(self.client_id))
        if self.will_topic and self.protocol_version == MQTTProtocolVersion.MQTTv5:
            payload.extend(self.will_properties.pack())
        
        if self.will_topic:
            payload.extend(_encode_utf8(self.will_topic))
            if self.will_payload:
                payload.extend(_encode_binary(self.will_payload))
            else:
                payload.extend(_encode_utf8(""))
        
        if self.username:
            payload.extend(_encode_utf8(self.username))
        
        if self.password:
            payload.extend(_encode_binary(self.password))
        
        packet = variable_header + payload
        return self._pack_fixed_header(len(packet)) + bytes(packet)


class ConnackPacket(MQTTPacket):
    def __init__(self):
        super().__init__(PacketType.CONNACK)
        self.session_present = False
        self.return_code = 0
        self.reason_code = ReasonCode.SUCCESS
        self.properties = Properties()
    
    @staticmethod
    def unpack(data):
        packet = ConnackPacket()
        offset = 0
        
        connack_flags = data[offset]
        offset += 1
        packet.session_present = (connack_flags & 0x01) != 0
        
        packet.return_code = data[offset]
        packet.reason_code = data[offset]
        offset += 1
        
        if offset < len(data):
            packet.properties, offset = Properties.unpack(data, offset)
        
        return packet


class PublishPacket(MQTTPacket):
    def __init__(self, topic, payload=None, qos=0, retain=False, dup=False,
                 mid=0, protocol_version=MQTTProtocolVersion.MQTTv5,
                 properties=None):
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
        variable_header = bytearray()
        
        variable_header.extend(_encode_utf8(self.topic))
        
        if self.qos > 0:
            variable_header.extend(struct.pack('!H', self.mid))
        
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.extend(self.properties.pack())
        
        if isinstance(self.payload, str):
            payload = self.payload.encode('utf-8')
        else:
            payload = self.payload
        
        packet = variable_header + payload
        return self._pack_fixed_header(len(packet)) + bytes(packet)
    
    @staticmethod
    def unpack(flags, data, protocol_version=MQTTProtocolVersion.MQTTv5):
        packet = PublishPacket("", protocol_version=protocol_version)
        
        packet.dup = (flags & 0x08) != 0
        packet.qos = (flags >> 1) & 0x03
        packet.retain = (flags & 0x01) != 0
        packet.flags = flags
        
        offset = 0
        packet.topic, offset = _decode_utf8(data, offset)
        if packet.qos > 0:
            packet.mid = struct.unpack_from('!H', data, offset)[0]
            offset += 2
        
        if protocol_version == MQTTProtocolVersion.MQTTv5:
            packet.properties, offset = Properties.unpack(data, offset)

        packet.payload = bytes(data[offset:])
        
        return packet


class PubackPacket(MQTTPacket):
    def __init__(self, mid, reason_code=ReasonCode.SUCCESS, 
                 protocol_version=MQTTProtocolVersion.MQTTv5,
                 properties=None):
        super().__init__(PacketType.PUBACK)
        self.mid = mid
        self.reason_code = reason_code
        self.protocol_version = protocol_version
        self.properties = properties or Properties()
    
    def pack(self):
        variable_header = bytearray()
        
        variable_header.extend(struct.pack('!H', self.mid))
        
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.append(self.reason_code)
            variable_header.extend(self.properties.pack())
        
        return self._pack_fixed_header(len(variable_header)) + bytes(variable_header)
    
    @staticmethod
    def unpack(data, protocol_version=MQTTProtocolVersion.MQTTv5):
        offset = 0
        
        mid = struct.unpack_from('!H', data, offset)[0]
        offset += 2
        
        reason_code = ReasonCode.SUCCESS
        properties = Properties()
        
        if protocol_version == MQTTProtocolVersion.MQTTv5 and offset < len(data):
            reason_code = data[offset]
            offset += 1
            
            if offset < len(data):
                properties, offset = Properties.unpack(data, offset)
        
        return PubackPacket(mid, reason_code, protocol_version, properties)


class SubscribePacket(MQTTPacket):
    def __init__(self, mid, topics, protocol_version=MQTTProtocolVersion.MQTTv5,
                 properties=None):
        super().__init__(PacketType.SUBSCRIBE, flags=0x02)
        self.mid = mid
        self.topics = topics
        self.protocol_version = protocol_version
        self.properties = properties or Properties()
    
    def pack(self):
        variable_header = bytearray()
        variable_header.extend(struct.pack('!H', self.mid))
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.extend(self.properties.pack())
        
        payload = bytearray()
        for item in self.topics:
            if len(item) == 2:
                topic, qos = item
                options = qos & 0x03
            else:
                topic, qos, options = item
            
            payload.extend(_encode_utf8(topic))
            
            if self.protocol_version == MQTTProtocolVersion.MQTTv5:
                payload.append(options)
            else:
                payload.append(qos & 0x03)
        
        packet = variable_header + payload
        return self._pack_fixed_header(len(packet)) + bytes(packet)


class SubackPacket(MQTTPacket):
    def __init__(self):
        super().__init__(PacketType.SUBACK)
        self.mid = 0
        self.return_codes = []
        self.reason_codes = []
        self.properties = Properties()
    
    @staticmethod
    def unpack(data, protocol_version=MQTTProtocolVersion.MQTTv5):
        packet = SubackPacket()
        offset = 0
        
        packet.mid = struct.unpack_from('!H', data, offset)[0]
        offset += 2
        
        if protocol_version == MQTTProtocolVersion.MQTTv5:
            packet.properties, offset = Properties.unpack(data, offset)
        
        while offset < len(data):
            code = data[offset]
            offset += 1
            packet.return_codes.append(code)
            packet.reason_codes.append(code)
        
        return packet


class UnsubscribePacket(MQTTPacket):
    def __init__(self, mid, topics, protocol_version=MQTTProtocolVersion.MQTTv5,
                 properties=None):
        super().__init__(PacketType.UNSUBSCRIBE, flags=0x02)
        self.mid = mid
        self.topics = topics
        self.protocol_version = protocol_version
        self.properties = properties or Properties()
    
    def pack(self):
        variable_header = bytearray()
        
        variable_header.extend(struct.pack('!H', self.mid))
        
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.extend(self.properties.pack())
        
        payload = bytearray()
        for topic in self.topics:
            payload.extend(_encode_utf8(topic))
        
        packet = variable_header + payload
        return self._pack_fixed_header(len(packet)) + bytes(packet)


class UnsubackPacket(MQTTPacket):
    def __init__(self):
        super().__init__(PacketType.UNSUBACK)
        self.mid = 0
        self.reason_codes = []
        self.properties = Properties()
    
    @staticmethod
    def unpack(data, protocol_version=MQTTProtocolVersion.MQTTv5):
        packet = UnsubackPacket()
        offset = 0
        
        packet.mid = struct.unpack_from('!H', data, offset)[0]
        offset += 2
        
        if protocol_version == MQTTProtocolVersion.MQTTv5:
            packet.properties, offset = Properties.unpack(data, offset)
            
            while offset < len(data):
                packet.reason_codes.append(data[offset])
                offset += 1
        
        return packet


class PingReqPacket(MQTTPacket):
    def __init__(self):
        super().__init__(PacketType.PINGREQ)
    
    def pack(self):
        return self._pack_fixed_header(0)


class PingRespPacket(MQTTPacket):
    def __init__(self):
        super().__init__(PacketType.PINGRESP)
    
    @staticmethod
    def unpack():
        return PingRespPacket()


class DisconnectPacket(MQTTPacket):
    def __init__(self, reason_code=ReasonCode.NORMAL_DISCONNECTION,
                 protocol_version=MQTTProtocolVersion.MQTTv5,
                 properties=None):
        super().__init__(PacketType.DISCONNECT)
        self.reason_code = reason_code
        self.protocol_version = protocol_version
        self.properties = properties or Properties()
    
    def pack(self):
        if self.protocol_version == MQTTProtocolVersion.MQTTv311:
            return self._pack_fixed_header(0)
        
        variable_header = bytearray()
        variable_header.append(self.reason_code)
        variable_header.extend(self.properties.pack())
        
        return self._pack_fixed_header(len(variable_header)) + bytes(variable_header)
    
    @staticmethod
    def unpack(data, protocol_version=MQTTProtocolVersion.MQTTv5):
        if protocol_version == MQTTProtocolVersion.MQTTv311:
            return DisconnectPacket(protocol_version=protocol_version)
        
        reason_code = ReasonCode.NORMAL_DISCONNECTION
        properties = Properties()
        
        if len(data) > 0:
            reason_code = data[0]
            if len(data) > 1:
                properties, _ = Properties.unpack(data, 1)
        
        return DisconnectPacket(reason_code, protocol_version, properties)


class PubrecPacket(MQTTPacket):
    def __init__(self, packet_id, reason_code=ReasonCode.SUCCESS, 
                 protocol_version=MQTTProtocolVersion.MQTTv5, properties=None):
        super().__init__(PacketType.PUBREC)
        self.packet_id = packet_id
        self.reason_code = reason_code
        self.protocol_version = protocol_version
        self.properties = properties if properties else Properties()
    
    def pack(self):
        variable_header = bytearray()
        variable_header.extend(struct.pack('!H', self.packet_id))
        
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.append(self.reason_code)
            variable_header.extend(self.properties.pack())
        
        return self._pack_fixed_header(len(variable_header)) + bytes(variable_header)
    
    @staticmethod
    def unpack(data, protocol_version=MQTTProtocolVersion.MQTTv5):
        packet_id = struct.unpack('!H', data[0:2])[0]
        
        if protocol_version == MQTTProtocolVersion.MQTTv311:
            return PubrecPacket(packet_id, protocol_version=protocol_version)
        
        reason_code = ReasonCode.SUCCESS
        properties = Properties()
        
        if len(data) > 2:
            reason_code = data[2]
            if len(data) > 3:
                properties, _ = Properties.unpack(data, 3)
        
        return PubrecPacket(packet_id, reason_code, protocol_version, properties)


class PubrelPacket(MQTTPacket):
    def __init__(self, packet_id, reason_code=ReasonCode.SUCCESS,
                 protocol_version=MQTTProtocolVersion.MQTTv5, properties=None):
        super().__init__(PacketType.PUBREL, flags=0x02)
        self.packet_id = packet_id
        self.reason_code = reason_code
        self.protocol_version = protocol_version
        self.properties = properties if properties else Properties()
    
    def pack(self):
        variable_header = bytearray()
        variable_header.extend(struct.pack('!H', self.packet_id))
        
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.append(self.reason_code)
            variable_header.extend(self.properties.pack())
        
        return self._pack_fixed_header(len(variable_header)) + bytes(variable_header)
    
    @staticmethod
    def unpack(data, protocol_version=MQTTProtocolVersion.MQTTv5):
        packet_id = struct.unpack('!H', data[0:2])[0]
        
        if protocol_version == MQTTProtocolVersion.MQTTv311:
            return PubrelPacket(packet_id, protocol_version=protocol_version)
        
        reason_code = ReasonCode.SUCCESS
        properties = Properties()
        
        if len(data) > 2:
            reason_code = data[2]
            if len(data) > 3:
                properties, _ = Properties.unpack(data, 3)
        
        return PubrelPacket(packet_id, reason_code, protocol_version, properties)


class PubcompPacket(MQTTPacket):
    def __init__(self, packet_id, reason_code=ReasonCode.SUCCESS,
                 protocol_version=MQTTProtocolVersion.MQTTv5, properties=None):
        super().__init__(PacketType.PUBCOMP)
        self.packet_id = packet_id
        self.reason_code = reason_code
        self.protocol_version = protocol_version
        self.properties = properties if properties else Properties()
    
    def pack(self):
        variable_header = bytearray()
        variable_header.extend(struct.pack('!H', self.packet_id))
        
        if self.protocol_version == MQTTProtocolVersion.MQTTv5:
            variable_header.append(self.reason_code)
            variable_header.extend(self.properties.pack())
        
        return self._pack_fixed_header(len(variable_header)) + bytes(variable_header)
    
    @staticmethod
    def unpack(data, protocol_version=MQTTProtocolVersion.MQTTv5):
        packet_id = struct.unpack('!H', data[0:2])[0]
        
        if protocol_version == MQTTProtocolVersion.MQTTv311:
            return PubcompPacket(packet_id, protocol_version=protocol_version)
        
        reason_code = ReasonCode.SUCCESS
        properties = Properties()
        
        if len(data) > 2:
            reason_code = data[2]
            if len(data) > 3:
                properties, _ = Properties.unpack(data, 3)
        
        return PubcompPacket(packet_id, reason_code, protocol_version, properties)
