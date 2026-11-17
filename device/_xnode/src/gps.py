# @package: gps
# @version: 1.3.0
# @type: device-specific
# @category: board
# @interface: UART, I2C
# @depends: none
# @platforms: xbee
# @tags: uart, gps, sensor

import utime
import gc
import machine
from micropython import const

SC16IS750_ADDR = const(0x4D)

RHR = const(0x00)
THR = const(0x00)
IER = const(0x01)
FCR = const(0x02)
IIR = const(0x02)
LCR = const(0x03)
MCR = const(0x04)
LSR = const(0x05)
MSR = const(0x06)
SPR = const(0x07)
TXLVL = const(0x08)
RXLVL = const(0x09)
IODIR = const(0x0A)
IOSTATE = const(0x0B)
IOINTENA = const(0x0C)
IOCTRL = const(0x0E)
EFCR = const(0x0F)

DLL = const(0x00)
DLH = const(0x01)

LSR_DR = const(0x01)
LSR_OE = const(0x02)
LSR_PE = const(0x04)
LSR_FE = const(0x08)
LSR_BI = const(0x10)
LSR_THRE = const(0x20)
LSR_TEMT = const(0x40)
LSR_FIFOE = const(0x80)

FCR_FIFO_ENABLE = const(0x01)
FCR_FIFO_RCVR_RESET = const(0x02)
FCR_FIFO_XMIT_RESET = const(0x04)
FCR_FIFO_DMA_MODE = const(0x08)
FCR_FIFO_64 = const(0x20)
FCR_FIFO_RCVR_TRIGGER_MASK = const(0xC0)
FCR_FIFO_RCVR_TRIGGER_8 = const(0x00)
FCR_FIFO_RCVR_TRIGGER_16 = const(0x40)
FCR_FIFO_RCVR_TRIGGER_32 = const(0x80)
FCR_FIFO_RCVR_TRIGGER_60 = const(0xC0)

MCR_DTR = const(0x01)
MCR_RTS = const(0x02)
MCR_LOOP = const(0x10)

class _I2CtoUart:
    def __init__(self, baudrate=9600, data_bits=8, stop_bits=1, parity='N'):
        self._i2c = machine.I2C(1)
        self._buf1 = bytearray(1)
        self._data_bits = data_bits
        self._stop_bits = stop_bits
        self._parity = parity
        self._baudrate = baudrate

        self.reset()
        self.set_baudrate(baudrate)

        self._write(FCR, FCR_FIFO_ENABLE | FCR_FIFO_RCVR_RESET | FCR_FIFO_XMIT_RESET | FCR_FIFO_RCVR_TRIGGER_16)
        self._write(IER, 0x01)

    def _build_lcr(self):
        if self._data_bits == 8:
            lcr = 0x03
        elif self._data_bits == 7:
            lcr = 0x02
        elif self._data_bits == 6:
            lcr = 0x01
        elif self._data_bits == 5:
            lcr = 0x00
        else:
            raise ValueError("Invalid number of data bits")

        if self._stop_bits == 2:
            lcr |= 0x04

        if self._parity == 'E':
            lcr |= 0x18
        elif self._parity == 'O':
            lcr |= 0x08
        return lcr

    def set_baudrate(self, baudrate):
        self._baudrate = baudrate
        crystal_freq = 12000000  # XNode crystal frequency: 12MHz
        divisor = crystal_freq // (baudrate * 16)

        lcr = self._read(LCR)
        self._write(LCR, lcr | 0x80)
        self._write(DLL, divisor & 0xFF)
        self._write(DLH, (divisor >> 8) & 0xFF)
        self._write(LCR, self._build_lcr() & 0x7F)

    def _read(self, reg):
        self._i2c.readfrom_mem_into(SC16IS750_ADDR, reg, self._buf1)
        return self._buf1[0]

    def _write(self, reg, data):
        self._buf1[0] = data & 0xFF
        self._i2c.writeto_mem(SC16IS750_ADDR, reg, self._buf1)

    def reset(self):
        self._write(IOCTRL, 0x02)
        utime.sleep_ms(1)

    def flush(self):
        self._write(FCR, FCR_FIFO_ENABLE | FCR_FIFO_RCVR_RESET | FCR_FIFO_XMIT_RESET | FCR_FIFO_RCVR_TRIGGER_16)

    def available(self):
        return self._read(RXLVL)

    def read(self, size=1):
        avail = self.available()
        if avail <= 0 or size <= 0:
            return b''
        to_read = size if size < avail else avail
        return self._i2c.readfrom_mem(SC16IS750_ADDR, RHR, to_read)

    def write(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        for byte in data:
            while not (self._read(LSR) & LSR_THRE):
                pass
            self._write(THR, byte)

class Gps:
    UPDATE_1HZ = "$PMTK220,1000*1F"
    UPDATE_2HZ = "$PMTK220,500*2B"
    UPDATE_5HZ = "$PMTK220,200*2C"
    UPDATE_10HZ = "$PMTK220,100*2F"

    GPGGA = "$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29"
    GPVTG = "$PMTK314,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29"
    GPRMC = "$PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29"
    GPGGA_GPRMC = "$PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*28"
    ALL_NMEA = "$PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0*28"

    BAUD_9600 = "$PMTK251,9600*17"
    BAUD_19200 = "$PMTK251,19200*22"
    BAUD_38400 = "$PMTK251,38400*27"
    BAUD_115200 = "$PMTK251,115200*1F"

    _BAUD_MAP = {
        BAUD_9600: 9600,
        BAUD_19200: 19200,
        BAUD_38400: 38400,
        BAUD_115200: 115200,
        9600: 9600,
        19200: 19200,
        38400: 38400,
        115200: 115200,
    }

    _BAUD_CMD = {
        9600: BAUD_9600,
        19200: BAUD_19200,
        38400: BAUD_38400,
        115200: BAUD_115200,
    }

    def __init__(self, fast_update=True, gps_mode=None, baudrate=None, *, first_update=None):
        if first_update is not None:
            fast_update = first_update
        if gps_mode is None:
            gps_mode = self.GPGGA
        if baudrate is None:
            baudrate = self.BAUD_9600

        if baudrate not in self._BAUD_MAP:
            raise ValueError("Invalid baudrate")

        self._uart = _I2CtoUart(9600)
        self.set_baudrate(baudrate)
        self.set_fast_update(fast_update)
        self.set_mode(gps_mode)

        self.latest_nmea = ""
        self._rx_buf = bytearray()
        self._latitude = 0.0
        self._longitude = 0.0
        self._altitude = 0.0
        self._hdop = 0.0
        self._fix_quality = 0
        self._satellites_in_use = 0
        self._timestamp = None
        self._date = None
        self.speed_over_ground_knots = 0.0
        self.speed_over_ground_kmh = 0.0
        self.course_over_ground = 0.0
        self._fix_status = 'V'

    def _send_command(self, command):
        self._uart.write(command + '\r\n')
        utime.sleep_ms(50)

    _sendCommand = _send_command

    def set_baudrate(self, baudrate):
        if baudrate not in self._BAUD_MAP:
            raise ValueError("Invalid baudrate")
        uart_baud = self._BAUD_MAP[baudrate]
        cmd = self._BAUD_CMD[uart_baud]
        self._send_command(cmd)
        if self._uart._baudrate != uart_baud:
            self._uart.set_baudrate(uart_baud)
            self._uart.flush()

    setBaudrate = set_baudrate

    def set_update_rate(self, rate_cmd):
        self._send_command(rate_cmd)

    def set_fast_update(self, fast_update=True):
        self._send_command(self.UPDATE_5HZ if fast_update else self.UPDATE_1HZ)

    setFastUpdate = set_fast_update

    def set_mode(self, gps_mode):
        self.gps_mode = gps_mode
        self._send_command(gps_mode)

    setGpsMode = set_mode

    @staticmethod
    def verify_checksum(sentence):
        s = sentence.strip()
        if not s.startswith('$'):
            return False
        star_idx = s.rfind('*')
        if star_idx == -1 or star_idx + 3 > len(s):
            return False
        try:
            expected = int(s[star_idx + 1:star_idx + 3], 16)
        except ValueError:
            return False
        calc = 0
        for i in range(1, star_idx):
            calc ^= ord(s[i])
        return calc == expected

    def update(self, timeout_ms=2000):
        start_time = utime.ticks_ms()
        rx_buf = self._rx_buf
        while utime.ticks_diff(utime.ticks_ms(), start_time) < timeout_ms:
            avail = self._uart.available()
            if avail > 0:
                chunk = self._uart.read(avail)
                for b in chunk:
                    rx_buf.append(b)
                    if b == 10:  # '\n'
                        try:
                            sentence = rx_buf.decode('ascii').strip()
                        except Exception:
                            sentence = ""
                        rx_buf[:] = b''
                        if not sentence:
                            continue
                        self.latest_nmea = sentence
                        if self._parse_nmea(sentence):
                            return True
            else:
                utime.sleep_ms(2)
        return False

    def _parse_nmea_gpgga(self, nmea_sentence):
        if nmea_sentence.startswith(("$GPGGA", "$GNGGA")):
            star = nmea_sentence.find('*')
            clean = nmea_sentence[:star] if star != -1 else nmea_sentence
            parts = clean.split(",")
            if len(parts) >= 10 and parts[1] and parts[2] and parts[3] and parts[4] and parts[5] and parts[6] and parts[9]:
                try:
                    self._timestamp = parts[1]
                    lat_deg = int(parts[2][:2])
                    lat_min = float(parts[2][2:])
                    lat = lat_deg + lat_min / 60.0
                    self._latitude = -lat if parts[3] == "S" else lat

                    lon_deg = int(parts[4][:3])
                    lon_min = float(parts[4][3:])
                    lon = lon_deg + lon_min / 60.0
                    self._longitude = -lon if parts[5] == "W" else lon

                    self._fix_quality = int(parts[6])
                    self._satellites_in_use = int(parts[7]) if parts[7] else 0
                    if parts[8]:
                        self._hdop = float(parts[8])
                    self._altitude = float(parts[9])
                    return True
                except ValueError:
                    return False
        return False

    def _parse_nmea_gprmc(self, nmea_sentence):
        if nmea_sentence.startswith(("$GPRMC", "$GNRMC")):
            star = nmea_sentence.find('*')
            clean = nmea_sentence[:star] if star != -1 else nmea_sentence
            parts = clean.split(",")
            if len(parts) >= 10 and parts[1] and parts[2] and parts[3] and parts[4] and parts[5] and parts[6]:
                try:
                    self._timestamp = parts[1]
                    self._fix_status = parts[2]

                    lat_deg = int(parts[3][:2])
                    lat_min = float(parts[3][2:])
                    lat = lat_deg + lat_min / 60.0
                    self._latitude = -lat if parts[4] == "S" else lat

                    lon_deg = int(parts[5][:3])
                    lon_min = float(parts[5][3:])
                    lon = lon_deg + lon_min / 60.0
                    self._longitude = -lon if parts[6] == "W" else lon

                    if parts[7]:
                        self.speed_over_ground_knots = float(parts[7])
                        self.speed_over_ground_kmh = round(self.speed_over_ground_knots * 1.852, 2)
                    if parts[8]:
                        self.course_over_ground = float(parts[8])
                    if parts[9]:
                        self._date = parts[9]
                    return True
                except ValueError:
                    return False
        return False

    def _parse_nmea_gpvtg(self, nmea_sentence):
        if nmea_sentence.startswith(("$GPVTG", "$GNVTG")):
            star = nmea_sentence.find('*')
            clean = nmea_sentence[:star] if star != -1 else nmea_sentence
            parts = clean.split(",")
            if len(parts) >= 8 and (parts[1] or parts[5] or parts[7]):
                try:
                    if parts[1]:
                        self.course_over_ground = float(parts[1])
                    if parts[5]:
                        self.speed_over_ground_knots = float(parts[5])
                    if parts[7]:
                        self.speed_over_ground_kmh = float(parts[7])
                    elif parts[5]:
                        self.speed_over_ground_kmh = round(self.speed_over_ground_knots * 1.852, 2)
                    return True
                except ValueError:
                    return False
        return False

    def _parse_nmea(self, nmea_sentence):
        if '*' in nmea_sentence and not self.verify_checksum(nmea_sentence):
            return False
        if nmea_sentence.startswith(("$GPGGA", "$GNGGA")):
            return self._parse_nmea_gpgga(nmea_sentence)
        if nmea_sentence.startswith(("$GPRMC", "$GNRMC")):
            return self._parse_nmea_gprmc(nmea_sentence)
        if nmea_sentence.startswith(("$GPVTG", "$GNVTG")):
            return self._parse_nmea_gpvtg(nmea_sentence)
        return False

    @property
    def has_fix(self):
        return self._fix_quality > 0 or self._fix_status == 'A'

    @property
    def position(self):
        return self._latitude, self._longitude, self._altitude

    @property
    def latitude(self):
        return self._latitude

    @property
    def longitude(self):
        return self._longitude

    @property
    def altitude(self):
        return self._altitude

    @property
    def hdop(self):
        return self._hdop

    @property
    def fix_quality(self):
        return self._fix_quality

    @property
    def satellites_in_use(self):
        return self._satellites_in_use

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, val):
        self._date = val

    @property
    def fix_status(self):
        return self._fix_status

    @property
    def speed_knots(self):
        return self.speed_over_ground_knots

    @property
    def speed_kmh(self):
        return self.speed_over_ground_kmh

    @property
    def course(self):
        return self.course_over_ground

gc.collect()
