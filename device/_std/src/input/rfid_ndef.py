# @package: rfid_ndef
# @version: 1.0
# @type: device-std
# @category: input
# @sensor_type: Contactless
# @interface: none
# @depends: none
# @platforms: *
# @tags: rfid, ndef, ntag
# @author: PlanXLab Development Team

_URI_PREFIXES = (
    "", "http://www.", "https://www.", "http://", "https://", "tel:",
    "mailto:", "ftp://anonymous:anonymous@", "ftp://ftp.", "ftps://",
    "sftp://", "smb://", "nfs://", "ftp://", "dav://", "news:", "telnet://",
    "imap:", "rtsp://", "urn:", "pop:", "sip:", "sips:", "tftp:", "btspp://",
    "btl2cap://", "btgoep://", "tcpobex://", "irdaobex://", "file://",
    "urn:epc:id:", "urn:epc:tag:", "urn:epc:pat:", "urn:epc:raw:",
    "urn:epc:", "urn:nfc:",
)


class NdefRecord:
    def __init__(self, tnf: int, record_type: bytes, payload: bytes,
                 identifier: bytes = b""):
        if not 0 <= tnf <= 5:
            raise ValueError("Chunked/reserved NDEF record types are unsupported")
        if len(record_type) > 255 or len(identifier) > 255:
            raise ValueError("NDEF type or identifier is too long")
        if tnf == 0 and (record_type or payload or identifier):
            raise ValueError("An empty NDEF record must have no fields")
        if tnf == 5 and record_type:
            raise ValueError("An unknown NDEF record must have no type")
        if tnf in (1, 2, 3, 4) and not record_type:
            raise ValueError("NDEF record type is required")
        self.tnf = tnf
        self.record_type = record_type
        self.payload = payload
        self.identifier = identifier


def encode_message(records: list[NdefRecord]) -> bytes:
    message = bytearray()
    for index, record in enumerate(records):
        short = len(record.payload) <= 255
        flags = record.tnf
        flags |= 0x80 if index == 0 else 0
        flags |= 0x40 if index == len(records) - 1 else 0
        flags |= 0x10 if short else 0
        flags |= 0x08 if record.identifier else 0
        message.append(flags)
        message.append(len(record.record_type))
        if short:
            message.append(len(record.payload))
        else:
            message.extend(len(record.payload).to_bytes(4, "big"))
        if record.identifier:
            message.append(len(record.identifier))
        message.extend(record.record_type)
        message.extend(record.identifier)
        message.extend(record.payload)
    return bytes(message)


def decode_message(message: bytes) -> list[NdefRecord]:
    records = []
    position = 0
    while position < len(message):
        if len(message) - position < 3:
            raise ValueError("Truncated NDEF record header")
        flags, type_length = message[position:position + 2]
        if bool(flags & 0x80) != (not records) or flags & 0x20:
            raise ValueError("Invalid or chunked NDEF record sequence")
        position += 2
        length_size = 1 if flags & 0x10 else 4
        if position + length_size + bool(flags & 0x08) > len(message):
            raise ValueError("Truncated NDEF record length")
        payload_length = int.from_bytes(message[position:position + length_size], "big")
        position += length_size
        id_length = message[position] if flags & 0x08 else 0
        position += bool(flags & 0x08)
        end = position + type_length + id_length + payload_length
        if end > len(message):
            raise ValueError("Truncated NDEF record payload")
        record_type = message[position:position + type_length]
        position += type_length
        identifier = message[position:position + id_length]
        position += id_length
        payload = message[position:end]
        position = end
        records.append(NdefRecord(flags & 0x07, record_type, payload, identifier))
        if flags & 0x40:
            if position != len(message):
                raise ValueError("Bytes after the final NDEF record")
            return records
    if records:
        raise ValueError("NDEF message has no final record")
    return records


def _validate_uri(uri: str) -> None:
    if not isinstance(uri, str):
        raise TypeError("URI must be a string")
    scheme = uri.split(":", 1)[0]
    if (
        ":" not in uri or not scheme or not (
            "A" <= scheme[0] <= "Z" or "a" <= scheme[0] <= "z"
        )
        or any(
            not (
                "A" <= char <= "Z" or "a" <= char <= "z"
                or "0" <= char <= "9" or char in "+-."
            )
            for char in scheme
        )
        or any(ord(char) <= 32 or ord(char) == 127 for char in uri)
    ):
        raise ValueError("A URI must include a scheme and contain no control/space characters")


def encode_uri(uri: str) -> bytes:
    _validate_uri(uri)
    prefix_code = 0
    for code, prefix in enumerate(_URI_PREFIXES):
        if uri.startswith(prefix) and len(prefix) > len(_URI_PREFIXES[prefix_code]):
            prefix_code = code
    payload = bytes((prefix_code,)) + uri[len(_URI_PREFIXES[prefix_code]):].encode("utf-8")
    return encode_message([NdefRecord(1, b"U", payload)])


def decode_uri(message: bytes) -> str | None:
    for record in decode_message(message):
        if record.tnf == 1 and record.record_type == b"U":
            if not record.payload or record.payload[0] >= len(_URI_PREFIXES):
                raise ValueError("Invalid NDEF URI prefix")
            uri = _URI_PREFIXES[record.payload[0]] + record.payload[1:].decode("utf-8")
            _validate_uri(uri)
            return uri
        if record.tnf == 3:
            uri = record.record_type.decode("utf-8")
            _validate_uri(uri)
            return uri
    return None


def parse_cc(cc: bytes, physical_capacity: int) -> tuple[int, bool]:
    if (
        len(cc) != 4 or cc[0] != 0xE1 or cc[1] >> 4 != 1
        or not 0 < cc[2] * 8 <= physical_capacity
        or cc[3] >> 4 != 0 or cc[3] & 0x0F not in (0, 0x0F)
    ):
        raise ValueError("Invalid or inaccessible Type 2 Capability Container")
    return cc[2] * 8, cc[3] & 0x0F == 0


class Type2Memory:
    def __init__(self, data: bytes):
        self.data = data
        reserved = set()
        mapping = []
        entries = []
        cursor = 0
        append_at = 0
        ndef_entry = None

        def take(length):
            nonlocal cursor
            if length > len(data):
                raise ValueError("TLV length exceeds Type 2 memory")
            value = bytearray()
            for _ in range(length):
                while cursor in reserved:
                    cursor += 1
                if cursor >= len(data):
                    raise ValueError("Truncated Type 2 TLV")
                mapping.append(cursor)
                value.append(data[cursor])
                cursor += 1
            return bytes(value)

        while cursor < len(data):
            while cursor in reserved:
                cursor += 1
            if cursor >= len(data):
                break
            start = len(mapping)
            tag = take(1)[0]
            if tag == 0:
                continue
            if tag == 0xFE:
                break
            length = take(1)[0]
            if length == 0xFF:
                length = int.from_bytes(take(2), "big")
            value = take(length)
            end = len(mapping)
            entries.append((tag, start, end))
            if tag == 0x03:
                if ndef_entry is not None:
                    raise ValueError("Multiple NDEF TLVs")
                ndef_entry = (start, end, value)
            if tag in (0x01, 0x02):
                if len(value) != 3:
                    raise ValueError("Invalid lock/memory control TLV")
                page_size = 1 << (value[2] & 0x0F)
                byte_offset = value[0] & 0x0F
                if byte_offset >= page_size:
                    raise ValueError("Invalid control TLV byte offset")
                position = (value[0] >> 4) * page_size + byte_offset - 16
                count = value[1] or 256
                if tag == 0x01:
                    count = (count + 7) // 8
                for offset in range(max(0, position), min(len(data), position + count)):
                    if offset in mapping:
                        raise ValueError("Control TLV reserves previously parsed bytes")
                    reserved.add(offset)
            append_at = end

        mapping.extend(offset for offset in range(cursor, len(data))
                       if offset not in reserved)
        self.mapping = mapping
        self.start = ndef_entry[0] if ndef_entry is not None else append_at
        self.limit = len(mapping)
        if ndef_entry is not None:
            for _, start, _ in entries:
                if start >= ndef_entry[1]:
                    self.limit = start
                    break
        self.message = ndef_entry[2] if ndef_entry is not None else None

    @property
    def capacity(self) -> int:
        available = self.limit - self.start
        short = max(0, min(254, available - 2))
        return max(short, available - 4 if available >= 259 else 0)

    def replace(self, message: bytes) -> tuple[bytes, tuple[int, ...]]:
        decode_message(message)
        if len(message) > 0xFFFF or len(message) > self.capacity:
            raise ValueError("NDEF message exceeds the available TLV area")
        length = (
            bytes((len(message),)) if len(message) < 255
            else b"\xFF" + len(message).to_bytes(2, "big")
        )
        encoded = b"\x03" + length + message
        available = self.limit - self.start
        if len(encoded) > available:
            raise ValueError("No space for an NDEF TLV")
        if self.limit == len(self.mapping) and len(encoded) < available:
            encoded += b"\xFE"
        encoded += bytes(available - len(encoded))
        updated = bytearray(self.data)
        for index, value in enumerate(encoded, self.start):
            updated[self.mapping[index]] = value
        header = tuple(self.mapping[self.start:self.start + 1 + len(length)])
        return bytes(updated), header
