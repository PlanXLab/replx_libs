"""
MQTT Protocol Handler

Low-level MQTT packet reading and writing.
"""

import struct
from .enums import PacketType, MQTTProtocolVersion
from .properties import _decode_variable_length
from .packets import (
    ConnackPacket, PublishPacket, PubackPacket, PubrecPacket,
    PubrelPacket, PubcompPacket, SubackPacket,
    UnsubackPacket, PingRespPacket, DisconnectPacket
)


def read_packet_from_socket(sock, protocol_version=MQTTProtocolVersion.MQTTv5):
    """
    Read a complete MQTT packet from socket
    
    :param sock: Socket object
    :param protocol_version: MQTT protocol version
    :return: Decoded packet object or None
    """
    try:
        # Read fixed header byte 1
        byte1 = sock.recv(1)
        if not byte1 or len(byte1) == 0:
            return None
        
        packet_type = byte1[0] & 0xF0
        flags = byte1[0] & 0x0F
        
        # Read remaining length
        remaining_length = 0
        multiplier = 1
        
        for _ in range(4):  # Max 4 bytes for remaining length
            byte = sock.recv(1)
            if not byte or len(byte) == 0:
                return None
            
            value = byte[0]
            remaining_length += (value & 0x7F) * multiplier
            
            if (value & 0x80) == 0:
                break
            
            multiplier *= 128
        
        # Read remaining data
        if remaining_length > 0:
            data = bytearray()
            while len(data) < remaining_length:
                chunk = sock.recv(remaining_length - len(data))
                if not chunk or len(chunk) == 0:
                    return None
                data.extend(chunk)
        else:
            data = bytearray()
        
        # Decode packet
        return decode_packet_data(packet_type, flags, bytes(data), protocol_version)
    
    except Exception as e:
        # Socket error or timeout
        return None


def decode_packet_data(packet_type, flags, data, protocol_version):
    """
    Decode packet data based on type
    
    :param packet_type: Packet type (from fixed header)
    :param flags: Packet flags (from fixed header)
    :param data: Variable header + payload
    :param protocol_version: MQTT protocol version
    :return: Decoded packet object
    """
    if packet_type == PacketType.CONNACK:
        return ConnackPacket.unpack(flags, data)
    
    elif packet_type == PacketType.PUBLISH:
        return PublishPacket.unpack(flags, data, protocol_version)
    
    elif packet_type == PacketType.PUBACK:
        return PubackPacket.unpack(flags, data, protocol_version)
    
    elif packet_type == PacketType.PUBREC:
        return PubrecPacket.unpack(flags, data, protocol_version)
    
    elif packet_type == PacketType.PUBREL:
        return PubrelPacket.unpack(flags, data, protocol_version)
    
    elif packet_type == PacketType.PUBCOMP:
        return PubcompPacket.unpack(flags, data, protocol_version)
    
    elif packet_type == PacketType.SUBACK:
        return SubackPacket.unpack(flags, data, protocol_version)
    
    elif packet_type == PacketType.UNSUBACK:
        return UnsubackPacket.unpack(flags, data, protocol_version)
    
    elif packet_type == PacketType.PINGRESP:
        return PingRespPacket.unpack(flags, data)
    
    elif packet_type == PacketType.DISCONNECT:
        return DisconnectPacket.unpack(flags, data, protocol_version)
    
    else:
        # Unknown or unhandled packet type
        return None


def send_packet_to_socket(sock, packet):
    """
    Send an MQTT packet to socket
    
    :param sock: Socket object
    :param packet: Packet object with pack() method
    """
    data = packet.pack()
    # MicroPython compatibility: use send instead of sendall
    total_sent = 0
    while total_sent < len(data):
        try:
            sent = sock.send(data[total_sent:])
            if sent == 0:
                raise OSError("Socket connection broken")
            total_sent += sent
        except OSError as e:
            # Handle EAGAIN/EWOULDBLOCK
            if e.args[0] not in (11, 115):  # EAGAIN, EINPROGRESS
                raise
            # Small delay and retry
            try:
                import time
                time.sleep_ms(10)
            except AttributeError:
                import utime
                utime.sleep_ms(10)
