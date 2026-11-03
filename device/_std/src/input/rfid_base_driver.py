# @package: rfid_base_driver
# @version: 1.0
# @type: device-std
# @category: input
# @sensor_type: Contactless
# @interface: none
# @depends: none
# @platforms: *
# @tags: input, rfid
# @author: PlanXLab Development Team

import micropython

_CLASSIC_COUNTS = {
    0x09: 20,   # Classic Mini
    0x08: 64,   # Classic 1K
    0x28: 64,   # Classic 1K + ISO14443-4 (SmartMX)
    0x88: 64,   # Classic 1K (Infineon)
    0x10: 128,  # MIFARE Plus 2K (SL1)
    0x18: 256,  # Classic 4K
    0x38: 256,  # Classic 4K + ISO14443-4 (SmartMX)
    0x11: 256,  # MIFARE Plus 4K (SL1)
}

_CLASSIC_SAKS = tuple(_CLASSIC_COUNTS.keys())
_CARD_TYPES = {
    0x00: "Ultralight/NTAG-compatible (SAK only)",
    0x08: "MIFARE Classic 1K / compatible",
    0x09: "MIFARE Classic Mini / compatible",
    0x10: "MIFARE Plus 2K (Classic-compatible SAK)",
    0x11: "MIFARE Plus 4K (Classic-compatible SAK)",
    0x18: "MIFARE Classic 4K / compatible",
    0x20: "ISO14443-4 Type A",
    0x28: "MIFARE Classic 1K (SmartMX / Dual)",
    0x38: "MIFARE Classic 4K (SmartMX / Dual)",
    0x40: "ISO18092-compatible (SAK only)",
    0x88: "MIFARE Classic 1K (Infineon / compatible)",
}


class MemoryLayout:
    def __init__(self, family: str, name: str, unit_size: int,
                 unit_count: int, data_units: tuple[int, ...]):
        self.family = family
        self.name = name
        self.unit_size = unit_size
        self.unit_count = unit_count
        self.data_units = data_units

    @property
    def capacity(self) -> int:
        return len(self.data_units) * self.unit_size

    def sector(self, unit: int) -> int:
        if self.family != "classic" or not 0 <= unit < self.unit_count:
            raise ValueError("Not a valid Classic block")
        return unit // 4 if unit < 128 else 32 + (unit - 128) // 16

    @staticmethod
    def is_classic_data_block(block: int) -> bool:
        return (
            0 < block < 256
            and (block % 4 != 3 if block < 128 else block % 16 != 15)
        )

class RFIDCommunicationError(OSError):
    """Raised when the host cannot communicate with an RFID reader."""


class BaseRFIDDriver:
    LEVEL_0 = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4

    last_error: str | None = None
    last_uid: list[int] | None = None
    last_atqa: int | None = None
    last_sak: int | None = None
    _memory_layout: MemoryLayout | None = None

    @property
    def card_type(self) -> str | None:
        if self._memory_layout is not None:
            return self._memory_layout.name
        if self.last_sak is None:
            return None
        return _CARD_TYPES.get(self.last_sak & 0x7F, "Unknown ISO14443-A")

    def get_memory_layout(self) -> MemoryLayout | None:
        if self.last_uid is None or self.last_sak is None:
            self.last_error = "no_session"
            return None
        if self._memory_layout is not None:
            return self._memory_layout

        sak = self.last_sak if self.last_sak in _CLASSIC_COUNTS else (self.last_sak & 0x7F)
        if sak in _CLASSIC_COUNTS:
            count = _CLASSIC_COUNTS[sak]
            self._memory_layout = MemoryLayout(
                "classic", _CARD_TYPES[sak], 16, count,
                tuple(unit for unit in range(count)
                      if MemoryLayout.is_classic_data_block(unit)),
            )
        elif sak == 0:
            version = self._read_tag_version()
            if version is None:
                return None
            models = {
                0x0F: ("NTAG213", 45, 40),
                0x11: ("NTAG215", 135, 130),
                0x13: ("NTAG216", 231, 226),
            }

            if (
                len(version) != 8 or version[:3] != b"\x00\x04\x04"
                or version[3] not in (0x02, 0x04, 0x05)
                or version[4:6] != b"\x01\x00" or version[7] != 0x03
                or version[6] not in models
            ):
                self.last_error = "unsupported_layout"
                return None
            name, count, data_end = models[version[6]]
            self._memory_layout = MemoryLayout(
                "ntag", name, 4, count, tuple(range(4, data_end))
            )
        else:
            self.last_error = "unsupported_layout"
        return self._memory_layout

    def get_data_blocks(self) -> tuple[int, ...] | None:
        layout = self.get_memory_layout()
        return layout.data_units if layout is not None else None

    def _read_tag_version(self) -> bytes | None:
        raise NotImplementedError

    def read_storage_unit(self, uid: list[int], unit: int, key: tuple,
                          key_type: str) -> bytes | None:
        raise NotImplementedError

    def write_storage_unit(self, uid: list[int], unit: int, data: bytes,
                           key: tuple, key_type: str) -> bool:
        raise NotImplementedError

    def _storage_layout(self, uid, unit, write=False) -> MemoryLayout | None:
        self.last_error = None
        if self.last_uid is None or uid != self.last_uid:
            self.last_error = "no_session"
            return None
        layout = self.get_memory_layout()
        if layout is None:
            return None
        if not isinstance(unit, int) or not 0 <= unit < layout.unit_count:
            self.last_error = "unit_range"
            return None
        if write and unit not in layout.data_units:
            self.last_error = "protected_unit"
            return None
        return layout

    def _validate_classic_access(self, uid, block, key, key_type, write=False) -> bool:
        self.last_error = None
        if key_type not in ("A", "B"):
            raise ValueError("key_type must be 'A' or 'B'")
        if len(key) != 6 or any(
            not isinstance(value, int) or not 0 <= value <= 255 for value in key
        ):
            raise ValueError("key must contain exactly six bytes")
        if len(uid) not in (4, 7, 10):
            raise ValueError("UID must contain 4, 7 or 10 bytes")
        if self.last_sak is None or self.last_uid != uid:
            self.last_error = "no_session"
            return False
        sak = self.last_sak if self.last_sak in _CLASSIC_COUNTS else (self.last_sak & 0x7F)
        if sak not in _CLASSIC_SAKS:
            self.last_error = "unsupported_card"
            return False
        if not isinstance(block, int) or not 0 <= block < _CLASSIC_COUNTS[sak]:
            self.last_error = "unit_range"
            return False
        if write and not MemoryLayout.is_classic_data_block(block):
            self.last_error = "protected_unit"
            return False
        return True

    @staticmethod
    @micropython.native
    def crc_a(data) -> bytes:
        crc = 0x6363
        for value in data:
            value ^= crc & 0xFF
            value ^= (value << 4) & 0xFF
            crc = ((crc >> 8) ^ (value << 8) ^ (value << 3) ^ (value >> 4)) & 0xFFFF
        return bytes((crc & 0xFF, crc >> 8))

    def init_hardware(self) -> None:
        raise NotImplementedError

    def check_connection(self) -> None:
        raise NotImplementedError

    def connect_tag(self) -> list[int] | None:
        raise NotImplementedError

    def read_authenticated_block(self, uid: list[int], block: int, key: tuple, key_type: str) -> list[int] | None:
        raise NotImplementedError

    def write_authenticated_block(self, uid: list[int], block: int, data: list, key: tuple, key_type: str) -> bool:
        raise NotImplementedError

    def end_session(self) -> None:
        raise NotImplementedError

    def is_writable_block(self, block: int) -> bool:
        count = _CLASSIC_COUNTS.get(
            self.last_sak & 0x7F if self.last_sak is not None else -1, 256
        )
        return block < count and MemoryLayout.is_classic_data_block(block)

    def set_rx_level(self, level: int) -> None:
        raise NotImplementedError

    def get_rx_level(self) -> int:
        raise NotImplementedError

    def set_tx_level(self, level: int) -> None:
        raise NotImplementedError

    def get_tx_level(self) -> int:
        raise NotImplementedError
