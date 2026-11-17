# @package: gps
# @version: 1.1.0
# @type: device-specific
# @category: board
# @interface: UART, I2C
# @depends: none
# @platforms: xbee
# @tags: uart, gps, sensor

import time
import machine
from micropython import const


SC16IS750_ADDR = const(0x4D)

# Register addresses (using datasheet table 21 as a reference)
RHR = const(0x00)  # Receive Holding Register (read)
THR = const(0x00)  # Transmit Holding Register (write)
IER = const(0x01)  # Interrupt Enable Register
FCR = const(0x02)  # FIFO Control Register
IIR = const(0x02)  # Interrupt Identification Register
LCR = const(0x03)  # Line Control Register
MCR = const(0x04)  # Modem Control Register
LSR = const(0x05)  # Line Status Register
MSR = const(0x06)  # Modem Status Register
SPR = const(0x07)  # Scratchpad Register
TXLVL = const(0x08)  # Transmit FIFO Level
RXLVL = const(0x09)  # Receive FIFO Level
IODIR = const(0x0A)  # IO pin direction control
IOSTATE = const(0x0B) # IO pin state control
IOINTENA = const(0x0C) # IO interrupt enable
IOCTRL = const(0x0E)  # IO control configuration
EFCR = const(0x0F)  # Extra features control register

DLL = const(0x00)  # Divisor Latch LSB (when LCR[7] = 1)
DLH = const(0x01)  # Divisor Latch MSB (when LCR[7] = 1)

# Line Status Register (LSR) bits
LSR_DR = const(0x01)  # Data Ready
LSR_OE = const(0x02)  # Overrun Error
LSR_PE = const(0x04)  # Parity Error
LSR_FE = const(0x08)  # Framing Error
LSR_BI = const(0x10)  # Break Interrupt
LSR_THRE = const(0x20)  # Transmitter Holding Register Empty
LSR_TEMT = const(0x40)  # Transmitter Empty
LSR_FIFOE = const(0x80) # FIFO Error

# FIFO Control Register (FCR) bits
FCR_FIFO_ENABLE = const(0x01)  # FIFO enable
FCR_FIFO_RCVR_RESET = const(0x02) # Reset Receiver FIFO
FCR_FIFO_XMIT_RESET = const(0x04) # Reset Transmitter FIFO
FCR_FIFO_DMA_MODE = const(0x08)  # DMA mode
FCR_FIFO_64 = const(0x20) # Enable 64 byte FIFO (SC16IS750/760)
FCR_FIFO_RCVR_TRIGGER_MASK = const(0xC0)  # Receiver FIFO trigger level
FCR_FIFO_RCVR_TRIGGER_8 = const(0x00)  # 8 bytes
FCR_FIFO_RCVR_TRIGGER_16 = const(0x40) # 16 bytes
FCR_FIFO_RCVR_TRIGGER_32 = const(0x80) # 32 bytes
FCR_FIFO_RCVR_TRIGGER_60 = const(0xC0) # 60 bytes

# Modem Control Register (MCR) bits
MCR_DTR = const(0x01)  # DTR output
MCR_RTS = const(0x02)  # RTS output
MCR_LOOP = const(0x10) # Loop back mode


class _I2CtoUart:
    def __init__(self, baudrate=9600, data_bits=8, stop_bits=1, parity='N'):
        self._i2c = machine.I2C(1)

        crystal_freq = 12_000_000   # XNode crystal frequency: 12MHz
        
        # Calculate divisor
        divisor = int(crystal_freq / (baudrate * 16))
        
        self.reset()
        
        # Enable access to divisor registers
        lcr = self._read(LCR)
        self._write(LCR, lcr | 0x80)

        # Write divisor
        self._write(DLL, divisor & 0xFF)           # Division Register LSB
        self._write(DLH, (divisor >> 8) & 0xFF)    

        # Set data bits, stop bits, and parity
        lcr = 0
        if data_bits == 8:
            lcr |= 0x03
        elif data_bits == 7:
            lcr |= 0x02
        elif data_bits == 6:
            lcr |= 0x01
        elif data_bits == 5:
            lcr |= 0x00
        else:
            raise ValueError("Invalid number of data bits")

        if stop_bits == 2:
            lcr |= 0x04

        if parity == 'E':
            lcr |= 0x18
        elif parity == 'O':
            lcr |= 0x08        

        # Disable divisor access and set communication parameters
        self._write(LCR, lcr & 0x7F)

        # Configure FIFO
        self._write(FCR, FCR_FIFO_ENABLE | \
                                  FCR_FIFO_RCVR_RESET | \
                                  FCR_FIFO_XMIT_RESET | \
                                  FCR_FIFO_RCVR_TRIGGER_16)

        # Enable RX interrupts
        self._write(IER, 0x01)

    def _read(self, reg):
        return self._i2c.readfrom_mem(SC16IS750_ADDR, reg, 1)[0]

    def _write(self, reg, data):
        self._i2c.writeto_mem(SC16IS750_ADDR, reg, bytes([data]))

    def reset(self):
        # Software reset via IOControl register
        self._write(IOCTRL, 0x02)
        time.sleep_ms(1)
    
    def available(self):
        return self._read(RXLVL)
            
    def read(self, size=1):
        
        if size == 1:
            if self.available() > 0:
                return bytes([self._read(RHR)])
            else:
                return bytes()
        else:
            data = bytearray()
            for _ in range(size):
                if self.available() > 0:
                    data.append(self._read(RHR))
                else:
                    break
            return bytes(data)
        
    def write(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')

        for byte in data:
            while not (self._read(LSR) & LSR_THRE):
                pass  # Wait until TX FIFO is not full
            self._write(THR, byte)


class Gps:
    # FGPMMOPA6H(MediaTek MT3339) GPS Module
    # NMEA Checksum Calculator: https://nmeachecksum.eqth.net/
    UPDATE_1HZ = "$PMTK220,1000*1F"
    UPDATE_2HZ = "$PMTK220,200*2C"
    UPDATE_10HZ = "$PMTK220,100*2F"

    GPGGA = "$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29"
    GPVTG = "$PMTK314,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29"
    GPRMC = "$PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29"    
    
    BAUD_9600   = "$PMTK251,9600*17"
    BAUD_19200  = "$PMTK251,19200*22"
    BAUD_38400  = "$PMTK251,38400*27"   #Do Not!!!
    BAUD_115200 = "$PMTK251,115200*1F"  #Do Not!!!
        
    def __init__(self, first_update=True, gps_mode=GPGGA, baudrate=BAUD_9600):
        if baudrate == self.BAUD_9600:
            i2c_uart_bourate = 9600
        elif baudrate == self.BAUD_19200:
            i2c_uart_bourate = 19200
        elif baudrate == self.BAUD_38400:
            i2c_uart_bourate = 38400
        elif baudrate == self.BAUD_115200:
            i2c_uart_bourate = 115200
        else:
            raise ValueError("Invalid baudrate")
         
        self._uart = _I2CtoUart(i2c_uart_bourate)
        self.setBaudrate(baudrate)
                
        self.setFastUpdate(first_update)
        self.setGpsMode(gps_mode)
        
        self.latest_nmea = ""
        self._latitude = 0.0
        self._longitude = 0.0
        self._altitude = 0.0
        self._fix_quality = 0
        self._satellites_in_use = 0
        self._timestamp = None
        self.speed_over_ground_knots = 0.0
        self.speed_over_ground_kmh = 0.0
        self.course_over_ground = 0.0
        self._fix_status = 'V'
        
    def _sendCommand(self, command):
        self._uart.write(command + '\r\n')
        time.sleep_ms(50)

    def setBaudrate(self, baudrate):
        self._sendCommand(baudrate)

    def setFastUpdate(self, first_update):
        self._sendCommand(self.UPDATE_2HZ if first_update else self.UPDATE_1HZ) 
    
    def setGpsMode(self, gps_mode):
        self.gps_mode = gps_mode
        self._sendCommand(gps_mode) 

    def update(self, timeout_ms = 2000):

        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            if self._uart.available():
                nmea_char = self._uart.read().decode("ascii")
                self.latest_nmea += nmea_char
                if nmea_char == "\n":
                    if self._parse_nmea(self.latest_nmea):
                        self.latest_nmea = ""
                        return True
                    else:
                        self.latest_nmea = ""
                        return False
        return False

    def _parse_nmea_gpgga(self, nmea_sentence):
        if nmea_sentence.startswith("$GPGGA"):
            parts = nmea_sentence.split(",")
            if len(parts) >= 10 and all(parts[i] for i in [1, 2, 3, 4, 5, 6, 9]):  # Check for empty fields
                try:
                    # Time (UTC)
                    self._timestamp = parts[1]

                    # Latitude
                    lat_degrees = int(parts[2][:2])
                    lat_minutes = float(parts[2][2:])
                    self._latitude = lat_degrees + lat_minutes / 60.0
                    if parts[3] == "S":
                        self._latitude = -self._latitude

                    # Longitude
                    lon_degrees = int(parts[4][:3])
                    lon_minutes = float(parts[4][3:])
                    self._longitude = lon_degrees + lon_minutes / 60.0
                    if parts[5] == "W":
                        self._longitude = -self._longitude

                    # Fix quality
                    self._fix_quality = int(parts[6])

                    # Satellites in use
                    self._satellites_in_use = int(parts[7])
                    
                    # Altitude
                    self._altitude = float(parts[9])

                    return True
                except ValueError:
                    return False
            else:
                return False
        return False
    
    def _parse_nmea_gprmc(self, nmea_sentence):
        if nmea_sentence.startswith("$GPRMC"):
            parts = nmea_sentence.split(",")
            if len(parts) >= 10 and all(parts[i] for i in [1, 2, 3, 4, 5, 7, 8, 9]): # Check for empty fields
                try:
                    # Time (UTC)
                    self._timestamp = parts[1]

                    # Fix status (A: active, V: void)
                    self._fix_status = parts[2]

                    # Latitude
                    lat_degrees = int(parts[3][:2])
                    lat_minutes = float(parts[3][2:])
                    self._latitude = lat_degrees + lat_minutes / 60.0
                    if parts[4] == "S":
                        self._latitude = -self._latitude

                    # Longitude
                    lon_degrees = int(parts[5][:3])
                    lon_minutes = float(parts[5][3:])
                    self._longitude = lon_degrees + lon_minutes / 60.0
                    if parts[6] == "W":
                        self._longitude = -self._longitude

                    # Speed over ground (knots)
                    self.speed_over_ground_knots = float(parts[7])

                    # Course over ground (degrees)
                    self.course_over_ground = float(parts[8])

                    # Date (DDMMYY)
                    self.date = parts[9] # You might want to store and use the date

                    return True

                except ValueError:
                    return False
            else:
                return False
        return False
    
    def _parse_nmea_gpvtg(self, nmea_sentence):
        if nmea_sentence.startswith("$GPVTG"):
            parts = nmea_sentence.split(",")
            if len(parts) >= 8 and all(parts[i] for i in [1, 5, 7]): # Check for empty fields
                try:
                    # Course over ground (degrees) - True
                    if parts[1]:
                        self.course_over_ground = float(parts[1])
                    # Course over ground (degrees) - Magnetic
                    # if parts[3]:
                    #     self.course_over_ground_magnetic = float(parts[3])
                    # Speed over ground (knots)
                    if parts[5]:
                        self.speed_over_ground_knots = float(parts[5])

                    # Speed over ground (km/h)
                    if parts[7]:
                        self.speed_over_ground_kmh = float(parts[7])
                        
                    return True
                
                except ValueError:
                    return False
            else:
                return False
        return False
    
    def _parse_nmea(self, nmea_sentence):
        if self.gps_mode == self.GPGGA:
            return self._parse_nmea_gpgga(nmea_sentence)
        elif self.gps_mode == self.GPVTG:
            return self._parse_nmea_gpvtg(nmea_sentence)
        elif self.gps_mode == self.GPRMC:
            return self._parse_nmea_gprmc(nmea_sentence)
        return False

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
    def fix_quality(self):
        return self._fix_quality

    @property
    def satellites_in_use(self):
        return self._satellites_in_use

    @property
    def timestamp(self):
        return self._timestamp
    
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
