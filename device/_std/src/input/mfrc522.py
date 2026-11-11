# @package: mfrc522
# @version: 1.0
# @type: device-std
# @category: input
# @sensor_type: Contactless
# @interface: SPI
# @depends: rfid_base_driver
# @platforms: *
# @tags: mfrc522, input, spi, rfid
# @author: PlanXLab Development Team

import time
from machine import Pin, SPI
from micropython import const
from .rfid_base_driver import BaseRFIDDriver, RFIDCommunicationError


_CMD_IDLE         = const(0x00)
_CMD_AUTHENT      = const(0x0E)
_CMD_TRANSCEIVE   = const(0x0C)
_CMD_RESETPHASE   = const(0x0F)

_PICC_REQIDL      = const(0x26)
_PICC_WUPA        = const(0x52)
_PICC_SEL_CL1     = const(0x93)
_PICC_SEL_CL2     = const(0x95)
_PICC_SEL_CL3     = const(0x97)
_PICC_CT          = const(0x88)
_PICC_AUTHENT1A   = const(0x60)
_PICC_AUTHENT1B   = const(0x61)
_PICC_READ        = const(0x30)
_PICC_WRITE       = const(0xA0)
_PICC_HALT        = const(0x50)
_NTAG_GET_VERSION = const(0x60)
_NTAG_WRITE       = const(0xA2)

_REG_COMMAND      = const(0x01)
_REG_COM_IEN      = const(0x02)
_REG_COM_IRQ      = const(0x04)
_REG_ERROR        = const(0x06)
_REG_STATUS2      = const(0x08)
_REG_FIFO_DATA    = const(0x09)
_REG_FIFO_LEVEL   = const(0x0A)
_REG_CONTROL      = const(0x0C)
_REG_BIT_FRAMING  = const(0x0D)
_REG_MODE         = const(0x11)
_REG_TX_CONTROL   = const(0x14)
_REG_TX_ASK       = const(0x15)
_REG_RF_CFG       = const(0x26)
_REG_GS_N         = const(0x27)
_REG_CW_GS_P      = const(0x28)
_REG_T_MODE       = const(0x2A)
_REG_T_PRESCALER  = const(0x2B)
_REG_T_RELOAD_H   = const(0x2C)
_REG_T_RELOAD_L   = const(0x2D)
_REG_VERSION      = const(0x37)

_OK       = const(0)
_NOTAGERR = const(1)
_ERR      = const(2)


class MFRC522Driver(BaseRFIDDriver):
    _RX_GAIN_LEVELS = (0x40, 0x48, 0x50, 0x60, 0x70)  # 33dB ~ 48dB
    _TX_DRIVE_LEVELS = (
        (8,  32),
        (10, 36),
        (12, 40),
        (14, 48),
        (15, 63),
    )

    def __init__(self, spi_bus=1, sck=14, mosi=13, miso=12, cs=15, baudrate=1000000):
        self.cs = Pin(cs, Pin.OUT, value=1)

        self.spi = SPI(
            spi_bus,
            baudrate=baudrate,
            polarity=0,
            phase=0,
            sck=Pin(sck),
            mosi=Pin(mosi),
            miso=Pin(miso)
        )

        self._tx2 = bytearray(2)
        self._rx2 = bytearray(2)
        self._bit_framing = 0x00
        self._session_active = False
        self._rx_gain: int | None = None
        self._tx_drive: tuple[int, int] | None = None
        self.last_error: str | None = None
        self.last_uid: list[int] | None = None
        self.last_atqa: int | None = None
        self.last_sak: int | None = None

        self.init_hardware()

    def init_hardware(self) -> None:
        self._wreg(_REG_COMMAND, _CMD_RESETPHASE)
        time.sleep_ms(50)

        self._wreg(_REG_T_MODE, 0x8D)
        self._wreg(_REG_T_PRESCALER, 0x3E)
        self._wreg(_REG_T_RELOAD_L, 30)
        self._wreg(_REG_T_RELOAD_H, 0)
        self._wreg(_REG_TX_ASK, 0x40)
        self._wreg(_REG_MODE, 0x3D)

        if self._rx_gain is not None:
            self._wreg(_REG_RF_CFG, self._rx_gain)
        if self._tx_drive is not None:
            n_drive, p_drive = self._tx_drive
            self._wreg(_REG_GS_N, (n_drive << 4) | 0x08)
            self._wreg(_REG_CW_GS_P, p_drive & 0x3F)

        self._antenna_on()
        self._session_active = False
        self._auth_state = None
        self._memory_layout = None
        self.last_error = None
        self.last_uid = None
        self.last_atqa = None
        self.last_sak = None

    def set_rx_level(self, level: int) -> None:
        if not isinstance(level, int) or not 0 <= level <= 4:
            raise ValueError("RX level must be an integer from 0 to 4")
        gain = self._RX_GAIN_LEVELS[level]
        self._wreg(_REG_RF_CFG, gain)
        self._rx_gain = gain

    def get_rx_level(self) -> int:
        current_gain = self._rreg(_REG_RF_CFG) & 0x7F
        try:
            return self._RX_GAIN_LEVELS.index(current_gain)
        except ValueError:
            return self.LEVEL_2

    def set_tx_level(self, level: int) -> None:
        if not isinstance(level, int) or not 0 <= level <= 4:
            raise ValueError("TX level must be an integer from 0 to 4")
        n_drive, p_drive = self._TX_DRIVE_LEVELS[level]
        self._wreg(_REG_GS_N, (n_drive << 4) | 0x08)
        self._wreg(_REG_CW_GS_P, p_drive & 0x3F)
        self._tx_drive = (n_drive, p_drive)

    def get_tx_level(self) -> int:
        n_drive = (self._rreg(_REG_GS_N) >> 4) & 0x0F
        p_drive = self._rreg(_REG_CW_GS_P) & 0x3F
        try:
            return self._TX_DRIVE_LEVELS.index((n_drive, p_drive))
        except ValueError:
            return self.LEVEL_2

    def get_version(self) -> int:
        return self._rreg(_REG_VERSION)

    def check_connection(self) -> None:
        version_a = self.get_version()
        version_b = self.get_version()
        if version_a in (0x00, 0xFF) or version_a != version_b:
            raise RFIDCommunicationError(
                "MFRC522 SPI communication failed "
                "(VersionReg reads 0x%02X and 0x%02X)"
                % (version_a, version_b)
            )

    def connect_tag(self) -> list[int] | None:
        self.last_error = None
        self.last_uid = None
        self.last_atqa = None
        self.last_sak = None
        self._memory_layout = None
        self._session_active = False
        self._auth_state = None
        self._stop_crypto1()

        for _ in range(3):
            stat, atqa = self._request(_PICC_WUPA)
            if stat != _OK:
                stat, atqa = self._request(_PICC_REQIDL)
            if stat != _OK:
                self.last_error = "no_tag" if stat == _NOTAGERR else "request"
                time.sleep_ms(10)
                continue

            self.last_atqa = atqa
            uid = []

            for selector in (_PICC_SEL_CL1, _PICC_SEL_CL2, _PICC_SEL_CL3):
                stat, raw_uid = self._anticoll(selector)
                if stat != _OK:
                    self.last_error = "anticollision"
                    break
                stat, sak = self._select_tag(raw_uid, selector)
                if stat != _OK or sak is None:
                    self.last_error = "select"
                    break

                if sak & 0x04:
                    if raw_uid[0] != _PICC_CT or selector == _PICC_SEL_CL3:
                        self.last_error = "uid"
                        break
                    uid.extend(raw_uid[1:4])
                else:
                    if raw_uid[0] == _PICC_CT:
                        self.last_error = "uid"
                        break
                    uid.extend(raw_uid[:4])
                    self.last_uid = uid[:]
                    self.last_sak = sak
                    self._session_active = True
                    return uid

            self._stop_crypto1()
            time.sleep_ms(10)

        return None

    def read_authenticated_block(self, uid: list[int], block: int, key: tuple, key_type: str = "A") -> list[int] | None:
        if not self._authenticate_classic(uid, block, key, key_type):
            return None
        data = self._read_block(block)
        if data is None:
            self.last_error = "read"
        return data

    def write_authenticated_block(self, uid: list[int], block: int, data: list, key: tuple, key_type: str = "A") -> bool:
        if not self._authenticate_classic(uid, block, key, key_type, write=True):
            return False
        written = self._write_block(block, data)
        if not written:
            self.last_error = "write"
        return written

    def _authenticate_classic(self, uid, block, key, key_type, write=False) -> bool:
        if not self._validate_classic_access(uid, block, key, key_type, write):
            return False
        if not self._session_active:
            self.last_error = "no_session"
            return False

        sector = block // 4 if block < 128 else 32 + (block - 128) // 16
        state = (sector, bytes(key[:6]), key_type)
        if self._auth_state == state and (self._rreg(_REG_STATUS2) & 0x08):
            return True

        auth_cmd = _PICC_AUTHENT1A if key_type == "A" else _PICC_AUTHENT1B
        if self._auth(auth_cmd, block, key, uid) != _OK:
            self._auth_state = None
            self._stop_crypto1()
            self.last_error = "authentication"
            return False
        self._auth_state = state
        return True

    def end_session(self) -> None:
        self._auth_state = None
        if self._session_active:
            self._halt()
            self._session_active = False
        self._stop_crypto1()

    def _transceive_crc(self, data, response_size) -> bytes | None:
        crc = self._calculate_crc(data)
        if crc is None:
            return None
        stat, recv, bits = self._tocard(
            _CMD_TRANSCEIVE, list(data) + [crc[0], crc[1]]
        )
        if stat != _OK or len(recv) != response_size + 2 or bits != (response_size + 2) * 8:
            return None
        crc = self._calculate_crc(recv[:-2])
        if crc is None or recv[-2:] != [crc[0], crc[1]]:
            return None
        return bytes(recv[:-2])

    def _read_tag_version(self) -> bytes | None:
        if not self._session_active:
            self.last_error = "no_session"
            return None
        version = self._transceive_crc([_NTAG_GET_VERSION], 8)
        if version is None:
            self.last_error = "version"
        return version

    def read_storage_unit(self, uid, unit, key, key_type) -> bytes | None:
        layout = self._storage_layout(uid, unit)
        if layout is None:
            return None
        if layout.family == "classic":
            data = self.read_authenticated_block(uid, unit, key, key_type)
            return bytes(data) if data is not None else None
        if not self._session_active:
            self.last_error = "no_session"
            return None
        data = self._transceive_crc([_PICC_READ, unit], 16)
        if data is None:
            self.last_error = "read"
            return None
        return data[:4]

    def write_storage_unit(self, uid, unit, data, key, key_type) -> bool:
        layout = self._storage_layout(uid, unit, write=True)
        if layout is None:
            return False
        if len(data) != layout.unit_size:
            raise ValueError("Storage unit data has the wrong size")
        if layout.family == "classic":
            return self.write_authenticated_block(uid, unit, list(data), key, key_type)
        if not self._session_active:
            self.last_error = "no_session"
            return False
        packet = [_NTAG_WRITE, unit] + list(data)
        crc = self._calculate_crc(packet)
        stat, recv, bits = self._tocard(_CMD_TRANSCEIVE, packet + [crc[0], crc[1]])
        written = (
            stat == _OK
            and bits == 4
            and len(recv) == 1
            and (recv[0] & 0x0F) == 0x0A
        )
        if not written:
            self.last_error = "write"
        return written

    def _wreg(self, reg, val):
        self.cs.value(0)
        self._tx2[0] = (reg << 1) & 0x7E
        self._tx2[1] = val & 0xFF
        self.spi.write(self._tx2)
        self.cs.value(1)

    def _rreg(self, reg):
        self.cs.value(0)
        self._tx2[0] = ((reg << 1) & 0x7E) | 0x80
        self._tx2[1] = 0x00
        self.spi.write_readinto(self._tx2, self._rx2)
        self.cs.value(1)
        return self._rx2[1]

    def _sflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) | mask)

    def _cflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) & (~mask))

    def _antenna_on(self):
        self._wreg(_REG_TX_CONTROL, 0x83)

    def _calculate_crc(self, data) -> bytearray:
        return bytearray(self.crc_a(data))

    def _tocard(self, cmd, send_data):
        recv = []
        bits = irq_en = wait_irq = 0

        if cmd == _CMD_AUTHENT:
            irq_en = 0x12
            wait_irq = 0x10
        elif cmd == _CMD_TRANSCEIVE:
            irq_en = 0x77
            wait_irq = 0x20

        self._wreg(_REG_COMMAND, _CMD_IDLE)
        self._wreg(_REG_COM_IEN, irq_en | 0x80)
        self._wreg(_REG_COM_IRQ, 0x7F)
        self._wreg(_REG_FIFO_LEVEL, 0x80)

        for c in send_data:
            self._wreg(_REG_FIFO_DATA, c)

        self._wreg(_REG_COMMAND, cmd)
        if cmd == _CMD_TRANSCEIVE:
            self._wreg(_REG_BIT_FRAMING, self._bit_framing | 0x80)

        t_start = time.ticks_us()
        n = 0
        while time.ticks_diff(time.ticks_us(), t_start) < 35000:
            n = self._rreg(_REG_COM_IRQ)
            if (n & wait_irq) or (n & 0x01):
                break

        if cmd == _CMD_TRANSCEIVE:
            self._wreg(_REG_BIT_FRAMING, self._bit_framing)

        error = self._rreg(_REG_ERROR)
        if (error & 0x1B) != 0x00:
            return _ERR, [], 0

        if cmd == _CMD_TRANSCEIVE:
            if n & wait_irq:
                fifo_len = self._rreg(_REG_FIFO_LEVEL)
                last_bits = self._rreg(_REG_CONTROL) & 0x07
                bits = (fifo_len - 1) * 8 + last_bits if last_bits != 0 else fifo_len * 8
                if not 0 < fifo_len <= 64:
                    return _ERR, [], 0
                for _ in range(fifo_len):
                    recv.append(self._rreg(_REG_FIFO_DATA))
                return _OK, recv, bits
            return _NOTAGERR, [], 0

        if not (n & wait_irq):
            return _NOTAGERR, [], 0

        return _OK, recv, bits

    def _request(self, mode):
        self._bit_framing = 0x07
        self._wreg(_REG_BIT_FRAMING, 0x07)
        stat, recv, bits = self._tocard(_CMD_TRANSCEIVE, [mode])
        if stat != _OK:
            return stat, None
        if bits != 0x10 or len(recv) != 2:
            return _ERR, None
        return _OK, recv[0] | (recv[1] << 8)

    def _anticoll(self, selector=_PICC_SEL_CL1):
        self._bit_framing = 0x00
        self._wreg(_REG_BIT_FRAMING, 0x00)
        stat, recv, bits = self._tocard(_CMD_TRANSCEIVE, [selector, 0x20])
        if stat == _OK and len(recv) == 5 and bits == 40:
            bcc = 0
            for i in range(4):
                bcc ^= recv[i]
            if bcc == recv[4]:
                return _OK, recv
        return _ERR, []

    def _select_tag(self, ser_num, selector=_PICC_SEL_CL1):
        self._bit_framing = 0x00
        self._wreg(_REG_BIT_FRAMING, 0x00)
        buf = [selector, 0x70] + list(ser_num[:5])
        crc = self._calculate_crc(buf)
        buf += [crc[0], crc[1]]
        stat, recv, bits = self._tocard(_CMD_TRANSCEIVE, buf)
        if stat != _OK or bits != 0x18 or len(recv) != 3:
            return _ERR, None
        crc = self._calculate_crc([recv[0]])
        if recv[1] != crc[0] or recv[2] != crc[1]:
            return _ERR, None
        return _OK, recv[0]

    def _auth(self, mode, addr, sect_key, uid):
        buf = [mode, addr] + list(sect_key[:6]) + list(uid[-4:])
        stat, _, _ = self._tocard(_CMD_AUTHENT, buf)
        if (self._rreg(_REG_STATUS2) & 0x08) == 0:
            return _ERR
        return stat

    def _stop_crypto1(self):
        self._cflags(_REG_STATUS2, 0x08)

    def _halt(self):
        self._bit_framing = 0x00
        self._wreg(_REG_BIT_FRAMING, 0x00)
        buf = [_PICC_HALT, 0]
        crc = self._calculate_crc(buf)
        buf += [crc[0], crc[1]]
        self._tocard(_CMD_TRANSCEIVE, buf)

    def _read_block(self, addr):
        self._bit_framing = 0x00
        self._wreg(_REG_BIT_FRAMING, 0x00)
        data = self._transceive_crc([_PICC_READ, addr], 16)
        return list(data) if data is not None else None

    def _write_block(self, addr, data_16bytes):
        self._bit_framing = 0x00
        self._wreg(_REG_BIT_FRAMING, 0x00)
        buf = [_PICC_WRITE, addr]
        crc = self._calculate_crc(buf)
        buf += [crc[0], crc[1]]
        stat, recv, bits = self._tocard(_CMD_TRANSCEIVE, buf)
        if not (stat == _OK and bits == 4 and len(recv) == 1 and (recv[0] & 0x0F) == 0x0A):
            return False

        buf_data = list(data_16bytes[:16])
        crc = self._calculate_crc(buf_data)
        buf_data += [crc[0], crc[1]]
        stat, recv, bits = self._tocard(_CMD_TRANSCEIVE, buf_data)
        return stat == _OK and bits == 4 and len(recv) == 1 and (recv[0] & 0x0F) == 0x0A