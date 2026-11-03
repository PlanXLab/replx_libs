# @package: gm67
# @version: 1.0
# @type: device-std
# @category: input
# @sensor_type: CMOS
# @interface: UART
# @depends: none
# @platforms: *
# @tags: gm67, input, uart, barcode
# @author: PlanXLab Development Team

import time
from machine import UART, Pin
from micropython import const

if hasattr(time, "ticks_ms"):
    _ticks_ms = time.ticks_ms
    _ticks_diff = time.ticks_diff
    _sleep_ms = time.sleep_ms
else:
    _ticks_ms = lambda: int(time.monotonic() * 1000)
    _ticks_diff = lambda now, old: now - old
    _sleep_ms = lambda ms: time.sleep(ms / 1000.0)


_SRC_HOST            = const(0x04)
_SRC_DEVICE          = const(0x00)
_STATUS_TEMP         = const(0x00)
_STATUS_PERMANENT    = const(0x08)

_OP_PARAM_SEND       = const(0xC6)
_OP_CMD_ACK          = const(0xD0)
_OP_CMD_NAK          = const(0xD1)
_OP_START_DECODE     = const(0xE4)
_OP_STOP_DECODE      = const(0xE5)
_OP_CUSTOM_BUZZER    = const(0xE6)
_OP_LED_ON           = const(0xE7)
_OP_LED_OFF          = const(0xE8)
_OP_SCAN_ENABLE      = const(0xE9)
_OP_SCAN_DISABLE     = const(0xEA)
_OP_SLEEP            = const(0xEB)
_OP_RESET            = const(0xFA)

class GM67:
    """UART barcode reader; construction does not change the scanner's saved mode.

    Repeated codes are suppressed for antipassback_ms (zero disables filtering).
    reset_uart_profile() permanently configures UART/115200 after the setup QR.
    """

    MODE_BUTTON_HOLD     = const(0x00)
    MODE_BUTTON_TRIGGER  = const(0x02)
    MODE_CONTINUOUS      = const(0x04)
    MODE_HOST            = const(0x08)
    MODE_INDUCTION       = const(0x09)

    TERM_NONE            = const(0x00)
    TERM_CRLF            = const(0x01)
    TERM_CR              = const(0x02)
    TERM_TAB             = const(0x03)

    LIGHT_ON_READ        = const(0x00)
    LIGHT_ALWAYS_ON      = const(0x01)
    LIGHT_ALWAYS_OFF     = const(0x02)

    BAUD_MAP = {
        1200: 0x03, 2400: 0x04, 4800: 0x05, 9600: 0x06,
        19200: 0x07, 38400: 0x08, 57600: 0x09, 115200: 0x0A
    }

    def __init__(
        self,
        uart_id: int = 1,
        tx_pin: int = 4,
        rx_pin: int = 5,
        baudrate: int = 115200,
        max_buffer_size: int = 512,
        char_timeout_ms: int = 15,
        antipassback_ms: int = 2000
    ):
        if max_buffer_size <= 0:
            raise ValueError("max_buffer_size must be positive")
        if char_timeout_ms < 0 or antipassback_ms < 0:
            raise ValueError("Receive timeouts must not be negative")

        self.uart_id = uart_id
        self.tx_pin = tx_pin
        self.rx_pin = rx_pin
        self.target_baudrate = baudrate

        self._max_buf = max_buffer_size
        self._rx_buf = bytearray()
        self._response_buf = bytearray()
        self._pending_codes: list[str] = []
        self._discarding_code = False
        self._delimiters = (0x0D, 0x0A)
        self._last_rx_tick = 0
        self.char_timeout_ms = char_timeout_ms

        self.antipassback_ms = antipassback_ms
        self._last_code = None
        self._last_code_tick = 0
        self.last_nak_cause = 0
        self.last_profile_error = None
        self.last_response = b""
        self.last_baud_sync_responses = {}
        self.last_baud_change_response = b""
        self.last_baud_change_nak_cause = 0

        self.uart = None
        self._init_mcu_uart(self.target_baudrate)

    def _init_mcu_uart(self, baud: int) -> None:
        settings = {
            "baudrate": baud, "bits": 8, "parity": None, "stop": 1,
            "tx": Pin(self.tx_pin), "rx": Pin(self.rx_pin), "rxbuf": self._max_buf,
        }
        if self.uart is None:
            self.uart = UART(self.uart_id, **settings)
        else:
            self.uart.init(**settings)
        _sleep_ms(20)
        self.flush()

    @staticmethod
    def calc_checksum(payload_without_cs: bytes | bytearray | list[int]) -> tuple[int, int]:
        total = sum(payload_without_cs) & 0xFFFF
        cs = (0x10000 - total) & 0xFFFF
        return (cs >> 8) & 0xFF, cs & 0xFF

    @classmethod
    def build_packet(cls, opcode: int, data: list[int] | None = None, permanent: bool = True) -> bytes:
        payload = data if data is not None else []
        length = 4 + len(payload)
        status = _STATUS_PERMANENT if (opcode == _OP_PARAM_SEND and permanent) else _STATUS_TEMP
        body = [length, opcode, _SRC_HOST, status] + payload
        cs_h, cs_l = cls.calc_checksum(body)
        return bytes(body + [cs_h, cs_l])

    def wakeup(self) -> None:
        if self.uart.write(b'\x00') != 1:
            raise OSError("GM67 wakeup write failed")
        _sleep_ms(55)

    def flush(self) -> None:
        while self.uart.any():
            if not self.uart.read(self.uart.any()):
                break
        # Slice assignment is supported by MicroPython bytearrays.
        self._rx_buf[:] = b""
        self._response_buf[:] = b""
        self._pending_codes.clear()
        self._discarding_code = False

    def send_command(self, packet: bytes, wait_ack: bool = True, timeout_ms: int = 250) -> bool:
        """Wait for a complete, checksummed response without dropping scan data."""
        if not packet or timeout_ms < 0:
            raise ValueError("A command packet and non-negative timeout are required")
        self.last_nak_cause = 0
        self.last_response = b""
        self.wakeup()
        t_start = _ticks_ms()
        while _ticks_diff(_ticks_ms(), t_start) < timeout_ms:
            remaining = timeout_ms - _ticks_diff(_ticks_ms(), t_start)
            if self._read_response(timeout_ms=remaining) is None:
                break
        self._response_buf[:] = b""
        if self.uart.write(packet) != len(packet):
            raise OSError("GM67 command write incomplete")

        if not wait_ack:
            return True

        t_start = _ticks_ms()
        resp = bytearray()
        while _ticks_diff(_ticks_ms(), t_start) < timeout_ms:
            remaining = timeout_ms - _ticks_diff(_ticks_ms(), t_start)
            response = self._read_response(resp, timeout_ms=remaining)
            self.last_response = bytes(resp)
            if response is not None:
                if response[1] == _OP_CMD_NAK:
                    self.last_nak_cause = response[4]
                    return False
                return True
            _sleep_ms(5)
        return False

    def _read_response(
        self,
        received: bytearray | None = None,
        timeout_ms: int | None = None
    ) -> bytes | None:
        t_start = _ticks_ms()
        for _ in range(self.uart.any()):
            if timeout_ms is not None and _ticks_diff(_ticks_ms(), t_start) >= timeout_ms:
                break
            chunk = self.uart.read(1)
            if not chunk:
                break
            if received is not None:
                received.extend(chunk)
            self._response_buf.extend(chunk)

            while self._response_buf:
                length = self._response_buf[0]
                if length in (0x04, 0x05):
                    opcode = _OP_CMD_ACK if length == 0x04 else _OP_CMD_NAK
                    header = bytes((length, opcode, _SRC_DEVICE, _STATUS_TEMP))
                    prefix_length = min(len(self._response_buf), len(header))
                    if self._response_buf[:prefix_length] == header[:prefix_length]:
                        packet_size = length + 2
                        if len(self._response_buf) < packet_size:
                            break
                        response = bytes(self._response_buf[:packet_size])
                        self._response_buf[:packet_size] = b""
                        if self.calc_checksum(response[:-2]) == (response[-2], response[-1]):
                            return response
                        continue
                value = self._response_buf[0]
                self._response_buf[:1] = b""
                self._append_scan_byte(value)
        return None

    def set_parameter(self, param_bytes: list[int], permanent: bool = True) -> bool:
        pkt = self.build_packet(_OP_PARAM_SEND, [0x00] + param_bytes, permanent=permanent)
        return self.send_command(pkt, wait_ack=True)

    def start_decode(self) -> bool:
        return self.send_command(self.build_packet(_OP_START_DECODE, permanent=False))

    def stop_decode(self) -> bool:
        return self.send_command(self.build_packet(_OP_STOP_DECODE, permanent=False))

    def enable_scan(self) -> bool:
        return self.send_command(self.build_packet(_OP_SCAN_ENABLE, permanent=False))

    def disable_scan(self) -> bool:
        return self.send_command(self.build_packet(_OP_SCAN_DISABLE, permanent=False))

    def led_on(self) -> bool:
        return self.send_command(self.build_packet(_OP_LED_ON, [0x01], permanent=False))

    def led_off(self) -> bool:
        return self.send_command(self.build_packet(_OP_LED_OFF, [0x01], permanent=False))

    def beep(self, tone: int = 1) -> bool:
        return self.send_command(self.build_packet(_OP_CUSTOM_BUZZER, [0x01 if tone else 0x00], permanent=False))

    def sleep(self) -> bool:
        return self.send_command(self.build_packet(_OP_SLEEP, permanent=False))

    def reboot_module(self) -> bool:
        res = self.send_command(self.build_packet(_OP_RESET, permanent=False), wait_ack=False)
        _sleep_ms(500)
        self.flush()
        return res

    def set_trigger_mode(self, mode: int) -> bool:
        return self.set_parameter([0x8A, mode & 0xFF])

    def set_terminator(self, term_code: int = TERM_CRLF) -> bool:
        if term_code not in (self.TERM_NONE, self.TERM_CRLF, self.TERM_CR, self.TERM_TAB):
            raise ValueError("Unsupported barcode terminator")
        if not self.set_parameter([0xF2, 0x05, term_code]):
            return False
        self._delimiters = ((), (0x0D, 0x0A), (0x0D,), (0x09,))[term_code]
        return True

    def set_single_scan_duration(self, tenth_seconds: int = 30) -> bool:
        return self.set_parameter([0x88, max(5, min(255, tenth_seconds))])

    def set_same_code_delay(self, hundred_ms: int = 5) -> bool:
        return self.set_parameter([0xF3, 0x03, max(0, min(99, hundred_ms))])

    def set_lighting(self, mode: int = LIGHT_ON_READ) -> bool:
        return self.set_parameter([0xF2, 0x02, mode & 0xFF])

    def set_collimation(self, mode: int = LIGHT_ON_READ) -> bool:
        return self.set_parameter([0xF2, 0x03, mode & 0xFF])

    def set_decode_beep(self, enable: bool = True) -> bool:
        return self.set_parameter([0x38, 0x01 if enable else 0x00])

    def set_silent_mode(self, silent: bool = False) -> bool:
        return self.set_parameter([0xF2, 0x0C, 0x01 if silent else 0x00])

    def _filter_antipassback(self, code: str) -> str | None:
        if not code:
            return None
        now = _ticks_ms()
        if self.antipassback_ms > 0 and code == self._last_code:
            if _ticks_diff(now, self._last_code_tick) < self.antipassback_ms:
                return None
        self._last_code = code
        self._last_code_tick = now
        return code

    def _append_scan_byte(self, value: int) -> None:
        self._last_rx_tick = _ticks_ms()
        if value in self._delimiters:
            self._finish_code()
        elif not self._discarding_code:
            if len(self._rx_buf) >= self._max_buf:
                self._rx_buf[:] = b""
                self._discarding_code = True
                raise ValueError("GM67 barcode exceeds max_buffer_size")
            self._rx_buf.append(value)

    def _finish_code(self) -> None:
        data = bytes(self._rx_buf).strip(b'\x00')
        self._rx_buf[:] = b""
        discarding = self._discarding_code
        self._discarding_code = False
        if data and not discarding:
            try:
                code = data.decode('utf-8')
            except UnicodeError:
                code = data.decode('latin-1')
            self._pending_codes.append(code)

    def poll(self) -> str | None:
        """Read using the configured suffix (CR/LF by default) or the idle timeout.

        Oversized codes raise ValueError and are discarded through their suffix.
        """
        for _ in range(self.uart.any()):
            if self._read_response() is None or self._pending_codes:
                break
        if (
            (self._rx_buf or self._discarding_code)
            and _ticks_diff(_ticks_ms(), self._last_rx_tick) >= self.char_timeout_ms
        ):
            self._finish_code()
        while self._pending_codes:
            code = self._filter_antipassback(self._pending_codes.pop(0))
            if code is not None:
                return code
        return None

    def scan_once(self, timeout_ms: int = 3000) -> str | None:
        """Read a fresh code in temporary HOST mode; report failure to stop decoding."""
        if timeout_ms < 0:
            raise ValueError("timeout_ms must not be negative")
        if not self.set_parameter([0x8A, self.MODE_HOST], permanent=False):
            return None
        self.flush()
        if not self.start_decode():
            return None
        t_start = _ticks_ms()
        code = None
        try:
            while _ticks_diff(_ticks_ms(), t_start) < timeout_ms:
                code = self.poll()
                if code is not None:
                    break
                _sleep_ms(5)
        finally:
            stopped = self.stop_decode()
        if not stopped:
            raise OSError("GM67 stop_decode failed")
        return code

    def reset_uart_profile(
        self,
        mode: int = MODE_CONTINUOUS,
        terminator: int = TERM_CRLF
    ) -> bool:
        """Set and verify the permanent 115200 baud profile after USB-to-UART setup.

        Probe at 9600 first, then try 115200 if that probe fails. The baud
        setting is written permanently and verified at 115200.
        Failures set last_profile_error to baud_sync, baud_save, baud_verify,
        or the failed profile step.
        """
        target_baudrate = 115200
        self.target_baudrate = target_baudrate
        self.last_profile_error = None
        self.last_nak_cause = 0
        self.last_baud_sync_responses = {}
        self.last_baud_change_response = b""
        self.last_baud_change_nak_cause = 0

        handshake = self.build_packet(_OP_PARAM_SEND, [0x00, 0x9F, 0x01])
        for baudrate in (9600, target_baudrate):
            self._init_mcu_uart(baudrate)
            connected = self.send_command(handshake)
            self.last_baud_sync_responses[baudrate] = self.last_response
            if connected:
                break
        else:
            self.last_profile_error = "baud_sync"
            return False

        # A baud transition can lose the ACK; confirm and retry the save at 115200.
        for _ in range(2):
            baud_change_ack = self.set_parameter([0x9C, self.BAUD_MAP[target_baudrate]])
            self.last_baud_change_response = self.last_response
            self.last_baud_change_nak_cause = self.last_nak_cause
            if not baud_change_ack and self.last_baud_change_nak_cause:
                self.last_profile_error = "baud_save"
                return False
            _sleep_ms(100)
            self._init_mcu_uart(target_baudrate)
            connected = self.send_command(handshake)
            self.last_baud_sync_responses[target_baudrate] = self.last_response
            if not connected:
                self.last_profile_error = "baud_verify"
                return False
            if baud_change_ack:
                break
        else:
            self.last_profile_error = "baud_save"
            return False

        profile_steps = (
            ("interface_uart", lambda: self.set_parameter([0xF2, 0x01, 0x00])),
            ("terminator", lambda: self.set_terminator(terminator)),
            ("trigger_mode", lambda: self.set_trigger_mode(mode)),
            ("scan_duration", lambda: self.set_single_scan_duration(30)),
            ("lighting", lambda: self.set_lighting(self.LIGHT_ON_READ)),
            ("collimation", lambda: self.set_collimation(self.LIGHT_ON_READ)),
            ("silent_mode", lambda: self.set_silent_mode(False)),
            ("scan_enable", lambda: self.enable_scan()),
        )
        for step, apply_step in profile_steps:
            if not apply_step():
                self.last_profile_error = step
                self.flush()
                return False

        self.flush()
        return True