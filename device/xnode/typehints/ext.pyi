import utime
import ustruct
import machine

from micropython import const


class Pir:
    """
    Pir module control class.
    """
    
    ENTER = 2
    LEAVE = 3
    
    def __init__(self) -> None:
        """
        Initialize the PIR module.
        """
        
    def read(self) -> bool:
        """
        Read the state of the PIR sensor.
        
        :return: 1 if motion is detected, 0 otherwise.
        """

    def state(self, timeout:int=1) -> int:
        """
        Return edge status of PIR sensor\r
\1 timeout: Time difference in milliseconds between two points
        
        :return: ENTER when it is a rising edge, LEAVE when it is a falling edge 
          and return the current state if there is no change.
        """
    
    def detect(self, timeout:int=1500) -> bool:
        """
        Return True if motion is detected within the timeout period.\r
\1 timeout: Time difference in milliseconds between two points
        
        :return: True if motion is detected, False otherwise.
        """

class IRThermometer: 
    """
    Infrared thermometer module control class.
    """

    def __init__(self) -> None:
        """
        Initialize the IR thermometer module.
        """

    def read(self, object=True, eeprom=False) -> int:
        """
        Read the raw temperature of the object or the ambient.\r
\1 object: True for object temperature, False for ambient temperature.
        :param eeprom: True to read from EEPROM, False otherwise.
        
        :return: Raw temperature value.
        """

    def ambient(self) -> float:
        """
        Read the ambient temperature.
        
        :return: Ambient temperature in Celsius.
        """

    def object(self) -> float:
        """
        Read the object temperature.
        
        :return: Object temperature in Celsius.
        """

class IMU:
    """
    Inertial Measurement Unit module control class.
    """
    
    ACCELERATION = const(0x08)
    MAGNETIC = const(0x0E)
    GYROSCOPE = const(0x14)
    EULER = const(0x1A)
    QUATERNION = const(0x20)
    ACCEL_LINEAR = const(0x28)
    ACCEL_GRAVITY = const(0x2E)
    TEMPERATURE = const(0x34)
    
    def __init__(self) -> None:
        """
        Initialize the IMU module.
        """
    
    def calibration(self) -> tuple:
        """
        Read the calibration status of the IMU.
        
        :return: Tuple of calibration status for system, gyroscope, accelerometer, and magnetometer.
        """

    def read(self, target:int) -> tuple | int:
        """
        Read the data from the IMU.\r
\1 target: The target of the data to be read. 
            One of ACCELERATION, MAGNETIC, GYROSCOPE, EULER, QUATERNION, ACCEL_LINEAR, ACCEL_GRAVITY, TEMPERATUR.
        
        :return: Tuple or integer data read from the target.
            ACCELERATION: (x, y, z) 
            MAGNETIC: (x, y, z)
            GYROSCOPE: (x, y, z)
            EULER: (heading, roll, pitch)
            QUATERNION: (w, x, y, z)
            ACCEL_LINEAR: (x, y, z)
            ACCEL_GRAVITY: (x, y, z)
            TEMPERATUR: temperature
        """

class Gps:
    """
    GPS module control class.
    """

    UPDATE_1HZ = "$PMTK220,1000*1F"
    UPDATE_2HZ = "$PMTK220,200*2C"
    UPDATE_10HZ = "$PMTK220,100*2F"

    GPGGA = "$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29"
    GPVTG = "$PMTK314,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29"
    GPRMC = "$PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29"    
    
    BAUD_9600   = "$PMTK251,9600*17"
    BAUD_19200  = "$PMTK251,19200*22"
    BAUD_38400  = "$PMTK251,38400*27"   #Do Not!!!
    BAUD_115200 = "$PMTK251,115200*1F"  #Do Not!!!"
                
    def __init__(self, first_update:bool=True, gps_mode:str=GPGGA, baudrate:str=BAUD_9600) -> None:
        """
        Initialize the GPS module. \r
\1 first_update: True to set the fast update rate, False otherwise.
        :param gps_mode: The output NMEA mode of the GPS module.
        :param bourate: The baud rate of the GPS module.
        """

    def setBaudrate(self, baudrate:str) -> None:
        """
        Set the baud rate of the GPS module.\r
\1 baudrate: The baud rate of the GPS module.
        """
                
    def setFastUpdate(self, first_update:bool) -> None:
        """
        Set the update rate of the GPS module.\r
\1 fast: True to set the fast update rate, False otherwise.
        """
    
    def setGpsMode(self, gps_mode:str) -> None:
        """
        Set the output NMEA mode of the GPS module.\r
\1 gps_mode: The output NMEA mode of the GPS module.
        """

    def update(self, timeout_ms:int=2000) -> bool:
        """
        Reads NMEA sentences from the GPS module and parses them.\r
\1 timeout_ms: Maximum time in milliseconds to wait for a complete NMEA sentence.
            
        :return: True if a valid NMEA sentence has been parsed, False otherwise
        """    
        
    @property
    def latitude(self) -> float:
        """
        Get the latitude.

        :return: The latitude.
        """
       
    @property
    def longitude(self) -> float:
        """
        Get the longitude.

        :return: The longitude.
        """
    
    @property
    def altitude(self) -> float:
        """
        Get the altitude.

        :return: The altitude.
        """
    
    @property
    def fix_quality(self) -> int:
        """
        Get the fix quality.

        :return: The fix quality (0: invalid, 1: GPS fix, 2: DGPS fix, etc.).
        """

    @property
    def satellites_in_use(self) -> int:
        """
        Get the number of satellites in use.

        :return: The number of satellites in use.
        """

    @property
    def timestamp(self) -> str:
        """
        Get the timestamp of the last fix.

        :return: The timestamp in HHMMSS.sss format.
        """
    
    @property
    def fix_status(self) -> str:
        """
        Get the fix status from GPRMC sentence.

        :return: 'A' for Active, 'V' for Void (invalid).
        """

    @property
    def speed_knots(self) -> float:
        """
        Get the speed over ground in knots.

        :return: The speed over ground in knots.
        """

    @property
    def speed_kmh(self) -> float:
        """
        Get the speed over ground in km/h.

        :return: The speed over ground in km/h.
        """

    @property
    def course(self) -> float:
        """
        Get the course over ground in degrees.

        :return: The course over ground in degrees.
        """


class Basic:
    """
    Basic module control class.
    """
    
    class Buzzer:
        """
        Buzzer control class.
        """

        def on(self) -> None:
            """
            Turn on the buzzer.
            """

        def off(self) -> None:
            """
            Turn off the buzzer.
            """
            
        def beep(self, delay, on=50, off=10) -> None:
            """
            Beep the buzzer.\r
\1 delay: The number of beeps.
            :param on: The duration of the beep in milliseconds.
            :param off: The duration of the silence in milliseconds.
            """
            
            self.on()
            t_on = utime.ticks_ms()
            t_off = 0
            
            while delay:               
                if t_on and utime.ticks_ms() - t_on > on:        
                    self.off()
                    t_on = 0
                    t_off = utime.ticks_ms()
                    
                if t_off and utime.ticks_ms() - t_off > off:
                    t_on = utime.ticks_ms()
                    t_off = 0
                                
                    self.on()  
                    delay -= 1
                        
            self.off()      

    class _I2CtoGPIO:
        """
        MicroPython driver for PCA9535 and PCA9535C 16-bit I2C I/O expanders.
        """
        PCA9535_ADDR = const(0x24)
                
        def read(self) -> bytes:
            """
            Reads a register or registers.
            
            :return: A bytes object containing the register value(s).
            """

        def write(self, n:int|bytes):
            """
            Writes to a register or registers.\r
\1 n: The value(s) to write
            """
        
    class _LedIter():
        """
        LED iterator class.
        """
            
        def on(self):
            """
            Turn on the LED.
            """
                    
        def off(self):
            """
            Turn off the LED.
            """
            
    class Leds(_I2CtoGPIO):
        """
        LED control class.
        """
            
        def __call__(self) -> tuple:
            """
            Get the status of all LEDs.
            """
        
        def __getitem__(self, index:int) -> bool:
            """
            Get the status of the LED.\r
\1 index: The index of the LED.
            
            :return: True if the LED is on, False otherwise.
            """
        
        def __setitem__(self, index:int, value:bool) -> None:
            """
            Set the status of the LED.\r
\1 index: The index of the LED.
            :param value: True to turn on the LED, False to turn off the LED.
            """
            
        def __iter__(self):
            """
            Get the LED iterator.
            
            :return: The LED iterator.
            """
        
        def __next__(self):
            """
            Get the next LED.
            
            :return: The next LED.
            """

        def write(self, n:int) -> None:
            """
            Write to all LEDs.\r
\1 n: The value to write
            """
            
        def clear(self) -> None:
            """
            Clear all LEDs.
            """

    class Buttons(_I2CtoGPIO):
        """
        Button control class.
        """
        
        def __getitem__(self, index:int) -> bool:
            """
            Get the status of the button.\r
\1 index: The index of the button.
            
            :return: True if the button is pressed, False otherwise.
            """
        
        def __call__(self) -> tuple:
            """
            Get the status of all buttons.
            
            :return: A tuple of button statuses.
            """

