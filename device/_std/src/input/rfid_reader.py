# @package: rfid_reader
# @version: 1.0
# @type: device-std
# @category: input
# @sensor_type: Contactless
# @interface: none
# @depends: rfid_base_driver, rfid_ndef
# @platforms: *
# @tags: rfid, input, ndef
# @author: PlanXLab Development Team

import time
from .rfid_base_driver import BaseRFIDDriver, MemoryLayout
from .rfid_ndef import Type2Memory, decode_message, decode_uri, encode_uri, parse_cc


class RFIDReader:
    DEFAULT_KEY = (0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF)
    NMDEF_KEY = (0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7)
    MAD_KEY = (0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5)
    ZERO_KEY = (0x00, 0x00, 0x00, 0x00, 0x00, 0x00)
    
    def __init__(self, driver: BaseRFIDDriver, max_retries=2, err_reset_threshold=10):
        if not isinstance(driver, BaseRFIDDriver):
            raise TypeError("driver must be an instance of BaseRFIDDriver")
        driver.check_connection()
        self.drv = driver
        self.max_retries = max_retries
        self._err_count = 0
        self._err_threshold = err_reset_threshold
        self.last_error: str | None = None
        self.last_failed_unit: int | None = None

    def _check_hardware_health(self, success: bool):
        if success:
            self._err_count = 0
        else:
            self._err_count += 1
            if self._err_count >= self._err_threshold:
                self.drv.init_hardware()
                self._err_count = 0

    def scan_tag_uid(self):
        self.last_error = None
        for _ in range(max(1, self.max_retries)):
            try:
                uid = self.drv.connect_tag()
                if uid is not None:
                    self.last_error = None
                    self._check_hardware_health(True)
                    return uid
                self.last_error = self.drv.last_error or "connect"
                if self.last_error == "no_tag":
                    return None
                
                self._check_hardware_health(False)
                time.sleep_ms(20)
            finally:
                self.drv.end_session()
        return None

    def read_data_block(self, block: int, key=DEFAULT_KEY, key_type="A"):
        self.last_error = None
        for _ in range(max(1, self.max_retries)):
            try:
                uid = self.drv.connect_tag()
                if not uid:
                    self.last_error = self.drv.last_error or "connect"
                    if self.last_error != "no_tag":
                        self._check_hardware_health(False)
                    time.sleep_ms(20)
                    continue
                data = self.drv.read_authenticated_block(uid, block, key, key_type)
                if data is not None:
                    self.last_error = None
                    self._check_hardware_health(True)
                    return data
                self.last_error = self.drv.last_error or "read"
                if self.last_error == "unsupported_card":
                    return None
                self._check_hardware_health(False)
            finally:
                self.drv.end_session()
        return None

    def write_data_block(self, block: int, payload_16bytes, key=DEFAULT_KEY, key_type="A", verify=True) -> bool:
        self.last_error = None
        if not MemoryLayout.is_classic_data_block(block):
            raise ValueError(f"[Security Block] Block {block} is a system/protected area and cannot be overwritten.")
        if len(payload_16bytes) != 16:
            raise ValueError("Payload must be exactly 16 bytes.")

        target_bytes = list(payload_16bytes)

        for _ in range(max(1, self.max_retries)):
            try:
                uid = self.drv.connect_tag()
                if not uid:
                    self.last_error = self.drv.last_error or "connect"
                    if self.last_error != "no_tag":
                        self._check_hardware_health(False)
                    time.sleep_ms(20)
                    continue
                if not self.drv.is_writable_block(block):
                    self.last_error = "protected_unit"
                    return False
                if self.drv.write_authenticated_block(uid, block, target_bytes, key, key_type):
                    if not verify:
                        self.last_error = None
                        self._check_hardware_health(True)
                        return True
                    verified = self.drv.read_authenticated_block(uid, block, key, key_type)
                    if verified == target_bytes:
                        self.last_error = None
                        self._check_hardware_health(True)
                        return True
                    self.last_error = (
                        self.drv.last_error or "verify_read"
                        if verified is None else "verify_mismatch"
                    )
                else:
                    self.last_error = self.drv.last_error or "write"
                if self.last_error == "unsupported_card":
                    return False
                self._check_hardware_health(False)
            finally:
                self.drv.end_session()
        return False

    def _begin_storage(self, family: str) -> tuple[list[int], MemoryLayout] | None:
        uid = self.drv.connect_tag()
        if uid is None:
            self.last_error = self.drv.last_error or "connect"
            if self.last_error != "no_tag":
                self._check_hardware_health(False)
            return None
        layout = self.drv.get_memory_layout()
        if layout is None:
            self.last_error = self.drv.last_error or "unsupported_layout"
            if self.last_error == "version":
                self._check_hardware_health(False)
            return None
        if layout.family != family:
            self.last_error = "unsupported_storage" if family == "classic" else "unsupported_ndef"
            return None
        self._check_hardware_health(True)
        return uid, layout

    def _reset_storage_error(self) -> None:
        self.last_error = None
        self.last_failed_unit = None

    @staticmethod
    def _validate_range(address: int, length: int, capacity: int | None = None) -> None:
        if not isinstance(address, int) or not isinstance(length, int) or address < 0 or length < 0:
            raise ValueError("Address and length must be non-negative integers")
        if capacity is not None and address + length > capacity:
            raise ValueError("Requested range exceeds user memory")

    @staticmethod
    def _validate_keys(key, key_type, sector_keys) -> None:
        entries = [(key, key_type)]
        if sector_keys is not None:
            if not isinstance(sector_keys, dict):
                raise ValueError("sector_keys must map sector numbers to (key, key_type)")
            for sector, credentials in sector_keys.items():
                if (
                    not isinstance(sector, int) or sector < 0
                    or not isinstance(credentials, (tuple, list)) or len(credentials) != 2
                ):
                    raise ValueError("Invalid sector credentials")
                entries.append(credentials)
        for value, kind in entries:
            if not isinstance(value, (tuple, list, bytes, bytearray)) or kind not in ("A", "B") or len(value) != 6 or any(
                not isinstance(byte, int) or not 0 <= byte <= 255 for byte in value
            ):
                raise ValueError("Credentials require a six-byte key and key_type A or B")

    @staticmethod
    def _credentials(layout, unit, key, key_type, sector_keys):
        if sector_keys is not None:
            return sector_keys.get(layout.sector(unit), (key, key_type))
        return key, key_type

    def _read_unit(self, uid, layout, unit, key, key_type) -> bytes | None:
        retries = max(1, self.max_retries)
        for attempt in range(retries):
            data = self.drv.read_storage_unit(uid, unit, key, key_type)
            if data is not None and len(data) == layout.unit_size:
                return data

            error = self.drv.last_error or "read"
            if error not in ("read", "authentication") or attempt + 1 == retries:
                self.last_error = error
                self.last_failed_unit = unit
                return None
            time.sleep_ms(20)

        self.last_error = self.drv.last_error or "read"
        self.last_failed_unit = unit
        return None

    def _write_unit(self, uid, layout, unit, data, key, key_type, verify) -> bool:
        if not self.drv.write_storage_unit(uid, unit, data, key, key_type):
            self.last_error = self.drv.last_error or "write"
            self.last_failed_unit = unit
            return False
        if verify:
            actual = self._read_unit(uid, layout, unit, key, key_type)
            if actual is None:
                if self.last_error == "read":
                    self.last_error = "verify_read"
                return False
            if actual != data:
                self.last_error = "verify_mismatch"
                self.last_failed_unit = unit
                return False
        return True

    def get_user_capacity(self) -> int | None:
        """Return Classic structural capacity, not a guarantee of sector permissions."""
        self._reset_storage_error()
        try:
            session = self._begin_storage("classic")
            return session[1].capacity if session is not None else None
        finally:
            self.drv.end_session()

    def read_user_data(self, address: int, length: int, key=DEFAULT_KEY,
                       key_type="A", sector_keys=None) -> bytes | None:
        """Read Classic virtual bytes in one selected-tag session."""
        self._reset_storage_error()
        self._validate_range(address, length)
        self._validate_keys(key, key_type, sector_keys)
        try:
            session = self._begin_storage("classic")
            if session is None:
                return None
            uid, layout = session
            self._validate_range(address, length, layout.capacity)
            data = bytearray()
            while len(data) < length:
                index, offset = divmod(address + len(data), layout.unit_size)
                unit = layout.data_units[index]
                unit_key, kind = self._credentials(layout, unit, key, key_type, sector_keys)
                block = self._read_unit(uid, layout, unit, unit_key, kind)
                if block is None:
                    return None
                take = min(length - len(data), layout.unit_size - offset)
                data.extend(block[offset:offset + take])
            return bytes(data)
        finally:
            self.drv.end_session()

    def write_user_data(self, address: int, data: bytes, key=DEFAULT_KEY,
                        key_type="A", verify=True, sector_keys=None) -> bool:
        """Write Classic virtual bytes; failure may leave a written prefix."""
        self._reset_storage_error()
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("User data must be bytes, bytearray or memoryview")
        data = bytes(data)
        self._validate_range(address, len(data))
        self._validate_keys(key, key_type, sector_keys)
        try:
            session = self._begin_storage("classic")
            if session is None:
                return False
            uid, layout = session
            self._validate_range(address, len(data), layout.capacity)
            operations = []
            position = 0
            while position < len(data):
                index, offset = divmod(address + position, layout.unit_size)
                unit = layout.data_units[index]
                take = min(len(data) - position, layout.unit_size - offset)
                unit_key, kind = self._credentials(layout, unit, key, key_type, sector_keys)
                if offset or take != layout.unit_size:
                    old = self._read_unit(uid, layout, unit, unit_key, kind)
                    if old is None:
                        return False
                    block = bytearray(old)
                    block[offset:offset + take] = data[position:position + take]
                else:
                    block = data[position:position + take]
                operations.append((unit, bytes(block), unit_key, kind))
                position += take
            for unit, block, unit_key, kind in operations:
                if not self._write_unit(uid, layout, unit, block, unit_key, kind, verify):
                    return False
            return True
        finally:
            self.drv.end_session()

    def _load_type2(self, uid, layout, writing=False) -> Type2Memory | None:
        cc = self._read_unit(uid, layout, 3, self.DEFAULT_KEY, "A")
        if cc is None:
            return None
        try:
            capacity, writable = parse_cc(cc, layout.capacity)
        except ValueError:
            self.last_error = "invalid_cc"
            self.last_failed_unit = 3
            return None
        if writing and not writable:
            self.last_error = "read_only"
            return None
        data = bytearray()
        for unit in layout.data_units[:capacity // layout.unit_size]:
            block = self._read_unit(uid, layout, unit, self.DEFAULT_KEY, "A")
            if block is None:
                return None
            data.extend(block)
        try:
            return Type2Memory(bytes(data))
        except ValueError:
            self.last_error = "invalid_ndef"
            return None

    def get_ndef_capacity(self) -> int | None:
        """Return NTAG capacity for the encoded NDEF message, excluding TLV overhead."""
        self._reset_storage_error()
        try:
            session = self._begin_storage("ntag")
            if session is None:
                return None
            uid, layout = session
            area = self._load_type2(uid, layout)
            return area.capacity if area is not None else None
        finally:
            self.drv.end_session()

    def read_ndef(self) -> bytes | None:
        self._reset_storage_error()
        try:
            session = self._begin_storage("ntag")
            if session is None:
                return None
            uid, layout = session
            area = self._load_type2(uid, layout)
            if area is None:
                return None
            if area.message is None:
                self.last_error = "ndef_missing"
                return None
            try:
                decode_message(area.message)
            except ValueError:
                self.last_error = "invalid_ndef"
                return None
            return area.message
        finally:
            self.drv.end_session()

    def write_ndef(self, message: bytes, verify=True) -> bool:
        """Update an NTAG NDEF TLV, committing its length after page writes."""
        self._reset_storage_error()
        if not isinstance(message, (bytes, bytearray, memoryview)):
            raise TypeError("NDEF message must be binary")
        message = bytes(message)
        decode_message(message)
        try:
            session = self._begin_storage("ntag")
            if session is None:
                return False
            uid, layout = session
            area = self._load_type2(uid, layout, writing=True)
            if area is None:
                return False
            final, header = area.replace(message)
            if final == area.data:
                return True
            staged = bytearray(final)
            for offset in header[1:]:
                staged[offset] = 0
            header_units = sorted(set(offset // layout.unit_size for offset in header))

            def write_page(index, image):
                start = index * layout.unit_size
                return self._write_unit(
                    uid, layout, layout.data_units[index],
                    bytes(image[start:start + layout.unit_size]), self.DEFAULT_KEY, "A", verify,
                )

            # Publish an empty length before touching payload pages.
            for index in header_units:
                if not write_page(index, staged):
                    return False
            for index in range(len(final) // layout.unit_size):
                start = index * layout.unit_size
                if index not in header_units and final[start:start + layout.unit_size] != area.data[start:start + layout.unit_size]:
                    if not write_page(index, final):
                        return False
            for index in header_units:
                if not write_page(index, final):
                    return False
            return True
        finally:
            self.drv.end_session()

    def read_uri(self) -> str | None:
        message = self.read_ndef()
        if message is None:
            return None
        try:
            uri = decode_uri(message)
        except ValueError:
            self.last_error = "invalid_ndef"
            return None
        if uri is None:
            self.last_error = "no_uri_record"
        return uri

    def write_uri(self, uri: str, verify=True) -> bool:
        return self.write_ndef(encode_uri(uri), verify=verify)
    
    def pack_16bytes(self, text: str) -> bytes:
        raw = text.encode('utf-8')[:16]
        return raw + b'\x00' * (16 - len(raw))

    def unpack_16bytes(self, data_list: list) -> str:
        return bytes(data_list).rstrip(b'\x00').decode('utf-8', 'ignore')