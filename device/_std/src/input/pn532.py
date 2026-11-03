# @package: pn532
# @version: 1.0
# @type: device-std
# @category: input
# @sensor_type: Contactless
# @interface: I2C
# @depends: rfid_base_driver
# @platforms: *
# @tags: pn532, input, i2c, rfid
# @author: PlanXLab Development Team

from machine import I2C, Pin
from micropython import const
import micropython
import time
from rfid_base_driver import BaseRFIDDriver, RFIDCommunicationError

_PN532_CMD_GET_FIRMWARE_VERSION = const(0x02)
_PN532_CMD_SETPARAMETERS   = const(0x12)
_PN532_CMD_SAMCONFIG       = const(0x14)
_PN532_CMD_RFCONFIGURATION = const(0x32)
_PN532_CMD_INDATAEXCHANGE  = const(0x40)
_PN532_CMD_INCOMMTHRU      = const(0x42)
_PN532_CMD_INLISTPASSIVE   = const(0x4A)
_PN532_CMD_INRELEASE       = const(0x52)

_RF_CFG_FIELD              = const(0x01)
_RF_CFG_TIMINGS            = const(0x02)
_RF_CFG_MAX_RETRIES        = const(0x05)
_RF_CFG_ANALOG_106A        = const(0x0A)

_MIFARE_CMD_AUTH_A         = const(0x60)
_MIFARE_CMD_AUTH_B         = const(0x61)
_MIFARE_CMD_READ           = const(0x30)
_MIFARE_CMD_WRITE          = const(0xA0)
_NTAG_GET_VERSION          = const(0x60)
_NTAG_WRITE                = const(0xA2)

_ACK_FRAME = b'\x00\x00\xFF\x00\xFF\x00'

class PN532Driver(BaseRFIDDriver):
    _RX_GAIN_LEVELS = (0x48, 0x58, 0x59, 0x68, 0x78)  # 33dB ~ 48dB
    _TX_CW_LEVELS   = (0x1F, 0x27, 0x3F, 0x3F, 0x3F)
    _TX_MOD_LEVELS  = (0x0F, 0x11, 0x11, 0x17, 0x1F)
    
    def __init__(self, i2c_bus=0, scl=22, sda=21, addr=0x24, rst=None, irq=None, freq=400000):
        self.i2c = I2C(i2c_bus, scl=Pin(scl), sda=Pin(sda), freq=freq)
        self.addr = addr
        self.rst = Pin(rst, Pin.OUT, value=1) if rst is not None else None
        self.irq = Pin(irq, Pin.IN, Pin.PULL_UP) if irq is not None else None

        self._tx_buf = bytearray(64)
        self._rx_buf = bytearray(96)
        self._ack_buf = bytearray(7)
        self._target_in_session = False
        self._auth_state = None
        self._rx_level = self.LEVEL_3
        self._tx_level = self.LEVEL_3
        
        self.init_hardware()

    def init_hardware(self) -> None:
        if self.rst is not None:
            self.rst.value(0)
            time.sleep_ms(10)
            self.rst.value(1)
            time.sleep_ms(50)

        try:
            self.i2c.readfrom(self.addr, 1)
        except OSError:
            pass
        time.sleep_ms(20)

        self._call_function(_PN532_CMD_SAMCONFIG, [0x01, 0x14, 0x01], response_len=0, timeout_ms=100)
        self._call_function(_PN532_CMD_SETPARAMETERS, [0x04], response_len=0, timeout_ms=50)
        self._call_function(_PN532_CMD_RFCONFIGURATION, [_RF_CFG_TIMINGS, 0x00, 0x0B, 0x0A], response_len=0, timeout_ms=50)
        self._call_function(_PN532_CMD_RFCONFIGURATION, [_RF_CFG_MAX_RETRIES, 0xFF, 0x01, 0x02], response_len=0, timeout_ms=50)
        self._apply_rf_analog()
        self._target_in_session = False

    def _apply_rf_analog(self) -> None:
        rf_cfg = self._RX_GAIN_LEVELS[self._rx_level]
        cw_gsp = self._TX_CW_LEVELS[self._tx_level]
        mod_gsp = self._TX_MOD_LEVELS[self._tx_level]

        analog_106a = [
            _RF_CFG_ANALOG_106A,
            rf_cfg, 0xF4, cw_gsp, mod_gsp, 0x4D, 0x55, 0x61, 0x6F, 0x26, 0x62, 0x87
        ]
        self._call_function(_PN532_CMD_RFCONFIGURATION, analog_106a, response_len=0, timeout_ms=50)

    def set_rx_level(self, level: int) -> None:
        if not isinstance(level, int) or not 0 <= level <= 4:
            raise ValueError("RX level must be an integer from 0 to 4")
        self._rx_level = level
        self._apply_rf_analog()

    def get_rx_level(self) -> int:
        return self._rx_level

    def set_tx_level(self, level: int) -> None:
        if not isinstance(level, int) or not 0 <= level <= 4:
            raise ValueError("TX level must be an integer from 0 to 4")
        self._tx_level = level
        self._apply_rf_analog()

    def get_tx_level(self) -> int:
        return self._tx_level

    def check_connection(self) -> None:
        response = self._call_function(
            _PN532_CMD_GET_FIRMWARE_VERSION, [], response_len=4, timeout_ms=100
        )
        if response is None or len(response) != 4 or response[0] != 0x32:
            raise RFIDCommunicationError(
                "PN532 I2C communication failed while reading firmware version"
            )

    def connect_tag(self) -> list[int] | None:
        self.last_error = None
        self.last_uid = None
        self.last_atqa = None
        self.last_sak = None
        self._memory_layout = None
        self._target_in_session = False
        self._auth_state = None
        
        resp = None
        comm_ok = False
        for _ in range(4):
            resp = self._call_function(_PN532_CMD_INLISTPASSIVE, [0x01, 0x00], response_len=64, timeout_ms=150)
            if resp is not None:
                comm_ok = True
                if len(resp) >= 1 and resp[0] > 0:
                    break

            self._call_function(_PN532_CMD_RFCONFIGURATION, [_RF_CFG_FIELD, 0x00], response_len=0, timeout_ms=50)
            time.sleep_ms(15)
            self._call_function(_PN532_CMD_RFCONFIGURATION, [_RF_CFG_FIELD, 0x01], response_len=0, timeout_ms=50)
            time.sleep_ms(20)

        if not resp or resp[0] < 1:
            self.last_error = "no_tag" if comm_ok else "request"
            return None

        if len(resp) < 6:
            self.last_error = "request"
            return None

        uid_len = resp[5]
        if uid_len not in (4, 7, 10) or len(resp) < 6 + uid_len:
            self.last_error = "uid"
            return None

        self._target_in_session = True
        self.last_atqa = (resp[2] << 8) | resp[3]
        self.last_sak = resp[4]
        self.last_uid = list(resp[6 : 6 + uid_len])
        return self.last_uid[:]

    def read_authenticated_block(self, uid: list, block: int, key: tuple, key_type: str = "A") -> list[int] | None:
        if not self._validate_classic_access(uid, block, key, key_type):
            return None
        if not self._target_in_session:
            self.last_error = "no_session"
            return None
        if not self._authenticate(uid, block, key, key_type):
            self.last_error = "authentication"
            return None

        resp = self._call_function(_PN532_CMD_INDATAEXCHANGE, [0x01, _MIFARE_CMD_READ, block], response_len=17, timeout_ms=50)
        if resp and len(resp) == 17 and resp[0] == 0x00:
            return list(resp[1:17])
        self._auth_state = None
        self.last_error = "read"
        return None

    def write_authenticated_block(self, uid: list, block: int, data: list, key: tuple, key_type: str = "A") -> bool:
        if not self._validate_classic_access(uid, block, key, key_type, write=True):
            return False
        if not self._target_in_session:
            self.last_error = "no_session"
            return False 
        if not self._authenticate(uid, block, key, key_type):
            self.last_error = "authentication"
            return False 

        params = [0x01, _MIFARE_CMD_WRITE, block] + list(data[:16])
        resp = self._call_function(_PN532_CMD_INDATAEXCHANGE, params, response_len=1, timeout_ms=70)
        written = bool(resp and len(resp) >= 1 and resp[0] == 0x00)
        if not written:
            self._auth_state = None
            self.last_error = "write"
        return written

    def end_session(self) -> None:
        self._auth_state = None
        if self._target_in_session:
            self._call_function(_PN532_CMD_INRELEASE, [0x00], response_len=1, timeout_ms=30)
            self._target_in_session = False

    def read_storage_unit(self, uid: list[int], unit: int, key: tuple, key_type: str) -> bytes | None:
        layout = self._storage_layout(uid, unit)
        if layout is None:
            return None

        if layout.family == "classic":
            data = self.read_authenticated_block(uid, unit, key, key_type)
            return bytes(data) if data is not None else None

        if not self._target_in_session:
            self.last_error = "no_session"
            return None

        response = self._call_function(
            _PN532_CMD_INDATAEXCHANGE,
            [0x01, _MIFARE_CMD_READ, unit],
            response_len=17,
            timeout_ms=50,
        )
        if response is not None and len(response) == 17 and response[0] == 0:
            return bytes(response[1:5])

        self.last_error = "read"
        return None

    def write_storage_unit(self, uid, unit, data, key, key_type) -> bool:
        layout = self._storage_layout(uid, unit, write=True)
        if layout is None:
            return False
        if len(data) != layout.unit_size:
            raise ValueError("Storage unit data has the wrong size")
        if layout.family == "classic":
            return self.write_authenticated_block(uid, unit, list(data), key, key_type)
        if not self._target_in_session:
            self.last_error = "no_session"
            return False 
        resp = self._call_function(
            _PN532_CMD_INDATAEXCHANGE, [0x01, _NTAG_WRITE, unit] + list(data),
            response_len=2, timeout_ms=70,
        )
        written = bool(resp and resp[0] == 0 and (len(resp) == 1 or resp[1:] == [0x0A]))
        if not written:
            self.last_error = "write"
        return written

    def _authenticate(self, uid: list, block: int, key: tuple, key_type: str) -> bool:
        sector = block // 4 if block < 128 else 32 + (block - 128) // 16
        state = (sector, bytes(key[:6]), key_type)
        if self._auth_state == state:
            return True

        auth_cmd = _MIFARE_CMD_AUTH_A if key_type == "A" else _MIFARE_CMD_AUTH_B
        params = [0x01, auth_cmd, block] + list(key[:6]) + list(uid[-4:])
        resp = self._call_function(_PN532_CMD_INDATAEXCHANGE, params, response_len=1, timeout_ms=50)
        if resp and len(resp) >= 1 and resp[0] == 0x00:
            self._auth_state = state
            return True
        self._auth_state = None
        return False

    def _read_tag_version(self) -> bytes | None:
        if not self._target_in_session:
            self.last_error = "no_session"
            return None

        resp = self._call_function(_PN532_CMD_INCOMMTHRU, [_NTAG_GET_VERSION], response_len=9, timeout_ms=50)
        if resp and len(resp) == 9 and resp[0] == 0x00:
            return bytes(resp[1:9])
        self.last_error = "version"
        return None

    def _wait_ready(self, timeout_ms: int) -> bool:
        t_start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t_start) < timeout_ms:
            if self.irq is not None:
                if self.irq.value() == 0:
                    return True
            else:
                try:
                    status = self.i2c.readfrom(self.addr, 1)
                    if status and (status[0] & 0x01) == 0x01:
                        return True
                except OSError:
                    pass
            time.sleep_ms(2)
        return False

    @micropython.native
    def _write_frame(self, cmd: int, params: list) -> bool:
        param_len = len(params)
        if param_len > 54:
            raise ValueError("PN532 frame parameter overflow")
        length = param_len + 2
        lcs = (~length + 1) & 0xFF

        tx = self._tx_buf
        tx[0] = 0x00
        tx[1] = 0x00
        tx[2] = 0xFF
        tx[3] = length
        tx[4] = lcs
        tx[5] = 0xD4
        tx[6] = cmd & 0xFF

        dcs_sum = 0xD4 + (cmd & 0xFF)
        idx = 7
        for b in params:
            val = b & 0xFF
            tx[idx] = val
            dcs_sum += val
            idx += 1

        tx[idx] = (~dcs_sum + 1) & 0xFF
        tx[idx + 1] = 0x00

        try:
            self.i2c.writeto(self.addr, memoryview(tx)[:idx + 2])
            return True
        except OSError:
            return False

    def _read_ack(self) -> bool:
        if not self._wait_ready(25):
            return False
        try:
            self.i2c.readfrom_into(self.addr, self._ack_buf)
            return memoryview(self._ack_buf)[1:7] == _ACK_FRAME
        except OSError:
            return False

    def _call_function(self, cmd: int, params: list, response_len: int, timeout_ms: int) -> list[int] | None:
        if not self._write_frame(cmd, params):
            return None
        if not self._read_ack():
            return None
        if not self._wait_ready(timeout_ms):
            # 타임아웃 시 ACK 프레임을 전송해 PN532 내부의 진행 중인 명령을 즉시 중단(Abort)
            try:
                self.i2c.writeto(self.addr, _ACK_FRAME)
            except OSError:
                pass
            return None

        read_len = min(len(self._rx_buf), response_len + 12)
        try:
            self.i2c.readfrom_into(self.addr, memoryview(self._rx_buf)[:read_len])
        except OSError:
            return None

        offset = 1
        while offset < read_len - 2:
            if self._rx_buf[offset] == 0x00 and self._rx_buf[offset + 1] == 0xFF:
                break
            offset += 1
        else:
            return None

        frame_len = self._rx_buf[offset + 2]
        lcs = self._rx_buf[offset + 3]
        if ((frame_len + lcs) & 0xFF) != 0:
            return None

        tfi = self._rx_buf[offset + 4]
        cmd_resp = self._rx_buf[offset + 5]
        if tfi != 0xD5 or cmd_resp != (cmd + 1):
            return None

        data_len = frame_len - 2
        data_start = offset + 6
        data_end = data_start + data_len
        if data_end >= read_len:
            return None

        dcs_calc = tfi + cmd_resp
        for i in range(data_start, data_end):
            dcs_calc += self._rx_buf[i]
        dcs_received = self._rx_buf[data_end]
        if ((dcs_calc + dcs_received) & 0xFF) != 0:
            return None

        return list(memoryview(self._rx_buf)[data_start:data_end])