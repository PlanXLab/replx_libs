"""
MQTT 5.0 Properties

Handles encoding and decoding of MQTT 5.0 properties.
"""

from .enums import PropertyType, PROPERTY_DATA_TYPE
import struct


class Properties:
    """
    MQTT 5.0 Properties container
    
    Stores and manages MQTT 5.0 properties with encoding/decoding support.
    """
    
    def __init__(self):
        self._properties = {}
    
    def set(self, property_id, value):
        """
        Set a property value
        
        :param property_id: PropertyType constant
        :param value: Property value (type depends on property)
        """
        if property_id == PropertyType.USER_PROPERTY:
            # User properties can have multiple values
            if property_id not in self._properties:
                self._properties[property_id] = []
            self._properties[property_id].append(value)
        else:
            self._properties[property_id] = value
    
    def get(self, property_id, default=None):
        """Get a property value"""
        return self._properties.get(property_id, default)
    
    def has(self, property_id):
        """Check if property exists"""
        return property_id in self._properties
    
    def remove(self, property_id):
        """Remove a property"""
        self._properties.pop(property_id, None)
    
    def clear(self):
        """Clear all properties"""
        self._properties.clear()
    
    def pack(self):
        """
        Encode properties to bytes
        
        :return: bytes (property length + properties data)
        """
        if not self._properties:
            return _encode_variable_length(0)
        
        data = bytearray()
        
        for prop_id, value in self._properties.items():
            data_type = PROPERTY_DATA_TYPE.get(prop_id)
            
            if data_type is None:
                continue
            
            if prop_id == PropertyType.USER_PROPERTY:
                # Multiple user properties
                for key, val in value:
                    data.append(prop_id)
                    data.extend(_encode_utf8_pair(key, val))
            else:
                data.append(prop_id)
                data.extend(self._encode_property_value(value, data_type))
        
        # Prepend property length
        return _encode_variable_length(len(data)) + bytes(data)
    
    @staticmethod
    def _encode_property_value(value, data_type):
        """Encode a single property value"""
        if data_type == 'byte':
            return struct.pack('!B', value)
        elif data_type == 'uint16':
            return struct.pack('!H', value)
        elif data_type == 'uint32':
            return struct.pack('!I', value)
        elif data_type == 'utf8':
            return _encode_utf8(value)
        elif data_type == 'binary':
            return _encode_binary(value)
        elif data_type == 'varint':
            return _encode_variable_length(value)
        elif data_type == 'utf8_pair':
            return _encode_utf8_pair(value[0], value[1])
        else:
            return b''
    
    @staticmethod
    def unpack(data, offset=0):
        """
        Decode properties from bytes
        
        :param data: bytes to decode
        :param offset: starting offset
        :return: (Properties object, new offset)
        """
        props = Properties()
        
        # Read property length
        prop_length, offset = _decode_variable_length(data, offset)
        
        if prop_length == 0:
            return props, offset
        
        end_offset = offset + prop_length
        
        while offset < end_offset:
            # Read property ID
            prop_id = data[offset]
            offset += 1
            
            data_type = PROPERTY_DATA_TYPE.get(prop_id)
            if data_type is None:
                # Unknown property, skip
                break
            
            # Decode value
            value, offset = Properties._decode_property_value(data, offset, data_type)
            
            if prop_id == PropertyType.USER_PROPERTY:
                if not props.has(prop_id):
                    props.set(prop_id, value)
                else:
                    props._properties[prop_id].append(value)
            else:
                props.set(prop_id, value)
        
        return props, offset
    
    @staticmethod
    def _decode_property_value(data, offset, data_type):
        """Decode a single property value"""
        if data_type == 'byte':
            value = data[offset]
            return value, offset + 1
        elif data_type == 'uint16':
            value = struct.unpack_from('!H', data, offset)[0]
            return value, offset + 2
        elif data_type == 'uint32':
            value = struct.unpack_from('!I', data, offset)[0]
            return value, offset + 4
        elif data_type == 'utf8':
            return _decode_utf8(data, offset)
        elif data_type == 'binary':
            return _decode_binary(data, offset)
        elif data_type == 'varint':
            return _decode_variable_length(data, offset)
        elif data_type == 'utf8_pair':
            key, offset = _decode_utf8(data, offset)
            val, offset = _decode_utf8(data, offset)
            return (key, val), offset
        else:
            return None, offset
    
    def __repr__(self):
        return f"Properties({self._properties})"


# ==========================================
# Encoding/Decoding Utility Functions
# ==========================================

def _encode_variable_length(value):
    """
    Encode variable length integer (1-4 bytes)
    
    Used for remaining length and some properties.
    """
    result = bytearray()
    while True:
        byte = value % 128
        value //= 128
        if value > 0:
            byte |= 0x80
        result.append(byte)
        if value == 0:
            break
    return bytes(result)


def _decode_variable_length(data, offset):
    """
    Decode variable length integer
    
    :return: (value, new offset)
    """
    multiplier = 1
    value = 0
    
    while True:
        if offset >= len(data):
            raise ValueError("Malformed variable length")
        
        byte = data[offset]
        offset += 1
        
        value += (byte & 0x7F) * multiplier
        
        if (byte & 0x80) == 0:
            break
        
        multiplier *= 128
        if multiplier > 128 * 128 * 128:
            raise ValueError("Variable length too large")
    
    return value, offset


def _encode_utf8(string):
    """Encode UTF-8 string with length prefix"""
    if isinstance(string, str):
        encoded = string.encode('utf-8')
    else:
        encoded = string
    
    return struct.pack('!H', len(encoded)) + encoded


def _decode_utf8(data, offset):
    """
    Decode UTF-8 string with length prefix
    
    :return: (string, new offset)
    """
    length = struct.unpack_from('!H', data, offset)[0]
    offset += 2
    
    string = data[offset:offset + length].decode('utf-8')
    offset += length
    
    return string, offset


def _encode_binary(data):
    """Encode binary data with length prefix"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    return struct.pack('!H', len(data)) + data


def _decode_binary(data, offset):
    """
    Decode binary data with length prefix
    
    :return: (bytes, new offset)
    """
    length = struct.unpack_from('!H', data, offset)[0]
    offset += 2
    
    binary = bytes(data[offset:offset + length])
    offset += length
    
    return binary, offset


def _encode_utf8_pair(key, value):
    """Encode UTF-8 key-value pair (for User Properties)"""
    return _encode_utf8(key) + _encode_utf8(value)
