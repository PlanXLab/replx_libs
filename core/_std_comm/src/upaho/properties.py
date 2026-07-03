
from .enums import PropertyType, PROPERTY_DATA_TYPE
import struct
import micropython

class Properties:
    # Singleton empty properties to avoid repeated allocations
    _EMPTY = None
    
    @classmethod
    def empty(cls):
        """Return a singleton empty Properties instance (read-only use only)."""
        if cls._EMPTY is None:
            cls._EMPTY = cls()
        return cls._EMPTY
    
    def __init__(self):
        self._properties = {}
    
    def set(self, property_id, value):
        if property_id == PropertyType.USER_PROPERTY:
            if property_id not in self._properties:
                self._properties[property_id] = []
            self._properties[property_id].append(value)
        else:
            self._properties[property_id] = value
    
    def get(self, property_id, default=None):
        return self._properties.get(property_id, default)
    
    def has(self, property_id):
        return property_id in self._properties
    
    def remove(self, property_id):
        self._properties.pop(property_id, None)
    
    def clear(self):
        self._properties.clear()
    
    # Pre-allocated constant for empty properties (avoids allocation)
    _EMPTY_PACKED = b"\x00"
    
    def pack(self):
        if not self._properties:
            return Properties._EMPTY_PACKED
        
        data = bytearray()
        
        for prop_id, value in self._properties.items():
            data_type = PROPERTY_DATA_TYPE.get(prop_id)
            
            if data_type is None:
                continue
            
            if prop_id == PropertyType.USER_PROPERTY:
                for key, val in value:
                    data.append(prop_id)
                    data.extend(_encode_utf8_pair(key, val))
            else:
                data.append(prop_id)
                data.extend(self._encode_property_value(value, data_type))
        
        return _encode_variable_length(len(data)) + bytes(data)
    
    @staticmethod
    def _encode_property_value(value, data_type):
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
        props = Properties()
        
        prop_length, offset = _decode_variable_length(data, offset)
        
        if prop_length == 0:
            return props, offset
        
        end_offset = offset + prop_length
        
        while offset < end_offset:
            prop_id = data[offset]
            offset += 1
            
            data_type = PROPERTY_DATA_TYPE.get(prop_id)
            if data_type is None:
                break
            
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

@micropython.native
def _encode_variable_length(value):
    """Encode a variable length integer for MQTT packets."""
    result = bytearray(4)  # Max 4 bytes for variable length
    i = 0
    while True:
        byte = value & 0x7F
        value >>= 7
        if value > 0:
            byte |= 0x80
        result[i] = byte
        i += 1
        if value == 0:
            break
    return bytes(result[:i])

@micropython.native
def _decode_variable_length(data, offset):
    """Decode a variable length integer from MQTT packet."""
    multiplier = 1
    value = 0
    start = offset
    
    while True:
        if offset >= len(data):
            raise ValueError("Malformed variable length")
        
        byte = data[offset]
        offset += 1
        
        value += (byte & 0x7F) * multiplier
        
        if (byte & 0x80) == 0:
            break
        
        multiplier <<= 7  # *= 128, faster bit shift
        if offset - start > 4:
            raise ValueError("Variable length too large")
    
    return value, offset

@micropython.native
def _encode_utf8(string):
    if isinstance(string, str):
        encoded = string.encode('utf-8')
    else:
        encoded = string
    
    return struct.pack('!H', len(encoded)) + encoded

@micropython.native
def _decode_utf8(data, offset):
    length = struct.unpack_from('!H', data, offset)[0]
    offset += 2
    
    string = data[offset:offset + length].decode('utf-8')
    offset += length
    
    return string, offset

def _encode_binary(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    return struct.pack('!H', len(data)) + data

def _decode_binary(data, offset):
    length = struct.unpack_from('!H', data, offset)[0]
    offset += 2
    
    binary = bytes(data[offset:offset + length])
    offset += length
    
    return binary, offset

def _encode_utf8_pair(key, value):
    return _encode_utf8(key) + _encode_utf8(value)
