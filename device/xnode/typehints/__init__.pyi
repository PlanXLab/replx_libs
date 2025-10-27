import gc
import uos
import usys
import utime
import ustruct
import machine
 
from micropython import const
import xbee

import utools
from utools import ANSIEC

def get_sys_info() -> tuple:
    """
    Get system information including core frequency and temperature.  
    :return: tuple of (frequency, temperature)
    """

def get_mem_info() -> tuple:
    """
    Get memory usage information of TiCLE.
    
    :return: tuple of (free, used, total) memory in bytes
    """

def get_fs_info(path='/') -> tuple:
    """
    Get filesystem information for the given path.
    :param path: Path to check filesystem info for.
    :return: tuple of (total, used, free, usage percentage)
    """


class Din:
    """
    A class representing a digital input pin.
    This class allows reading the state of a digital input pin, with options for pull-up or pull-down resistors.
    """
    LOW         = 0
    HIGH        = 1
    PULL_DOWN   = machine.Pin.PULL_DOWN
    PULL_UP     = machine.Pin.PULL_UP
    
    def __init__(self, pin:str, *, pull:int|None=None):
        """
        Initializes the digital input pin with the specified pin number and pull configuration.
        :param pin: The pin string to use for the digital input.
        :param pull: The pull configuration (PULL_DOWN or PULL_UP). Default is None (no pull).
        """

    def value(self):
        """
        Reads the current value of the digital input pin.
        :return: The current value of the pin (0 or 1).
        """


class Dout:
    """
    A class representing a digital output pin.
    This class allows controlling the state of a digital output pin, with options for pull-up or pull-down resistors.
    """
    LOW         = 0
    HIGH        = 1
    PULL_DOWN   = machine.Pin.PULL_DOWN
    PULL_UP     = machine.Pin.PULL_UP
    
    def __init__(self, pin:str, *, pull:int|None=None, value:int|None=LOW):
        """
        Initializes the digital output pin with the specified pin number, pull configuration, and initial value.
        :param pin: The pin string to use for the digital output.
        :param pull: The pull configuration (PULL_DOWN or PULL_UP). Default is None (no pull).
        :param value: The initial value of the pin (0 or 1). Default is LOW.
        """
             
    def value(self):
        """
        Reads the current value of the digital output pin.
        :return: The current value of the pin (0 or 1).
        """

    def value(self, n):
        """
        Sets the value of the digital output pin.
        :param n: The value to set the pin to (0 or 1).
        """

    def toggle(self):
        """
        Toggles the current value of the digital output pin.
        """

def Wdt(timeout:int) -> machine.WDT:
    """
    Creates a watchdog timer (WDT) object with the specified timeout.
    :param timeout: The timeout in seconds.
    :return: A WDT object.
    """

def i2cdetect(show:bool=False) -> list | None:
    """
    Detect I2C devices on the specified bus.
    :param show: If True, it prints the entire status, if False, it returns only the recognized device addresses in a list.
    :return: A list of detected I2C devices.
    """


class I2c:
    """
    A class to handle I2C communication with a device.
    This class provides methods to read and write unsigned 8-bit and 16-bit values to specified registers,
    as well as methods for reading and writing bytes to and from the I2C device.
    """

    def __init__(self, addr:int, freq:int=400_000):
        """
        Initializes the I2C object with the specified address, bus ID, and frequency.
        :param addr: The I2C address of the device.
        :param freq: The frequency of the I2C bus in Hz (default is 400000).
        """

    def read_u8(self, reg: int) -> int:
        """
        Read an unsigned 8-bit value from the specified register.
        :param reg: The register address to read from.
        :return: The value read from the register.
        """

    def read_u16(self, reg: int, *, little_endian: bool = True) -> int:
        """
        Read an unsigned 16-bit value from the specified register.
        :param reg: The register address to read from.
        :param little_endian: If True, read the value in little-endian format, otherwise in big-endian format.
        :return: The value read from the register.
        """

    def write_u8(self, reg: int, val: int) -> None:
        """
        Write an unsigned 8-bit value to the specified register.
        :param reg: The register address to write to.
        :param val: The value to write to the register (0-255).
        """

    def write_u16(self, reg: int, val: int, *, little_endian: bool = True) -> None:
        """
        Write an unsigned 16-bit value to the specified register.
        :param reg: The register address to write to.
        :param val: The value to write to the register (0-65535).
        :param little_endian: If True, write the value in little-endian format, otherwise in big-endian format.
        """

    def readfrom(self, nbytes: int, *, stop: bool = True) -> bytes:
        """
        Read a specified number of bytes from the I2C device.
        :param nbytes: The number of bytes to read.
        :param stop: If True, send a stop condition after reading.
        :return: The bytes read from the I2C device.
        """

    def readinto(self, buf: bytearray, *, stop: bool = True) -> int:
        """
        Read bytes into a buffer from the I2C device.
        :param buf: The buffer to read the bytes into.
        :param stop: If True, send a stop condition after reading.
        :return: The number of bytes read into the buffer.
        """

    def readfrom_mem(self, reg: int, nbytes: int, *, addrsize: int = 8) -> bytes:
        """
        Read a specified number of bytes from a specific register in the I2C device.
        :param reg: The register address to read from.
        :param nbytes: The number of bytes to read.
        :param addrsize: The address size in bits (default is 8 bits).
        :return: The bytes read from the specified register.
        """

    def readfrom_mem_into(self, reg: int, buf: bytearray, *, addrsize: int = 8) -> int:
        """
        Read bytes from a specific register in the I2C device into a buffer.
        :param reg: The register address to read from.
        :param buf: The buffer to read the bytes into.
        :param addrsize: The address size in bits (default is 8 bits).
        :return: The number of bytes read into the buffer.
        """

    def writeto(self, buf: bytes, *, stop: bool = True) -> int:
        """
        Write bytes to the I2C device.
        :param buf: The bytes to write to the I2C device.
        :param stop: If True, send a stop condition after writing.
        :return: The number of bytes written to the I2C device.
        """

    def writeto_mem(self, reg: int, buf: bytes, *, addrsize: int = 8) -> int:
        """
        Write bytes to a specific register in the I2C device.
        :param reg: The register address to write to.
        :param buf: The bytes to write to the specified register.
        :param addrsize: The address size in bits (default is 8 bits).
        :return: The number of bytes written to the specified register.
        """

class ReplSerial:
    """
    A class to handle reading and writing to the REPL (Read-Eval-Print Loop) UART.
    This class provides methods to read and write data to the REPL UART with optional timeout.
    """
    
    def __init__(self, timeout:int|float|None=None):
        """
        Initializes the ReplSerial object with an optional timeout.
        :param timeout: The timeout in seconds. Default is None (no timeout).
        """

    @property
    def timeout(self) -> int|float|None:
        """
        Returns the current timeout value.
        :return: The timeout value in seconds.
        """
    
    @timeout.setter
    def timeout(self, n:int|float|None):
        """
        Sets the timeout value.
        :param n: The timeout value in seconds.
        """

    def read(self, size:int=1) -> bytes: 
        """
        Reads data from the REPL UART.
        :param size: The number of bytes to read. Default is 1 byte.
        :return: A byte string containing the read data.
        """
        
    def read_until(self, expected:bytes=b'\n', size:int|None=None) -> bytes:
        """
        Reads data from the REPL UART until the expected byte sequence is found or the specified size is reached.
        :param expected: The expected byte sequence to look for. Default is b'\n'.
        :param size: The maximum number of bytes to read. Default is None (no limit).
        :return: A byte string containing the read data.
        """
                    
    def write(self, data:bytes) -> int:
        """
        Writes data to the REPL UART.
        :param data: The data to write as a byte string.
        :return: The number of bytes written.
        """


class Led:
    """
    A class to control the onboard LED of the XNode.
    This class provides methods to turn the LED on, off, toggle its state, and read its current value.
    """
    
    def __init__(self):
        """
        Initializes the Led object and sets up the LED pin.
        """

    def on(self):
        """
        Turns the LED on.
        """
        
    def off(self):
        """
        Turns the LED off.
        """

    def toggle(self):
        """
        Toggles the current state of the LED.
        """
        
    def value(self):
        """
        Returns the current value of the LED.
        """

    def value(self, n):
        """
        Sets the value of the LED.
        """


class SupplyVoltage(machine.ADC):
    """
    A class to read the supply voltage of the XNode.
    This class inherits from machine.ADC and provides a method to read the supply voltage.
    """
 
    def __init__(self):
        """
        Initializes the SupplyVoltage object and sets up the ADC pin for reading the supply voltage.
        """
        
    def read(self) -> float:
        """
        Reads the supply voltage from the ADC pin.
        :return: The supply voltage in volts, rounded to one decimal place.
        """


class Illuminance:
    """
    A class to read illuminance from a BH1750 sensor.
    This class provides methods to initialize the sensor, read illuminance values, and handle power management.
    """
    
    def __init__(self, scale_factor=2.8):
        """
        Initializes the Illuminance object and sets up the I2C communication with the BH1750 sensor.
        :param scale_factor: The scale factor to convert the raw sensor data to lux. Default is 2.8.
        """

    def read(self, continuous:bool=True) -> int:
        """
        Reads the illuminance value from the BH1750 sensor.
        :param continuous: If True, reads in continuous mode, otherwise in one-time mode.
        :return: The illuminance value in lux, rounded to the nearest integer.
        """ 


class Tphg:
    """
    A class to read temperature, pressure, humidity, and gas from a BME680 sensor.
    This class provides methods to initialize the sensor, read the sensor values, and calculate IAQ (Indoor Air Quality).
    """
        
    def __init__(self, temp_weighting=0.10,  pressure_weighting=0.05, humi_weighting=0.20, gas_weighting=0.65, gas_ema_alpha=0.1, temp_baseline=23.0,  pressure_baseline=1013.25, humi_baseline=45.0, gas_baseline=450_000):
        """
        Initializes the Tphg object and sets up the I2C communication with the BME680 sensor.
        :param temp_weighting: Weighting factor for temperature in IAQ calculation. Default is 0.10.
        :param pressure_weighting: Weighting factor for pressure in IAQ calculation. Default is 0.05.
        :param humi_weighting: Weighting factor for humidity in IAQ calculation. Default is 0.20.
        :param gas_weighting: Weighting factor for gas in IAQ calculation. Default is 0.65.
        :param gas_ema_alpha: Exponential moving average alpha for gas baseline. Default is 0.1.
        :param temp_baseline: Baseline temperature for IAQ calculation. Default is 23.0 degrees Celsius.
        :param pressure_baseline: Baseline pressure for IAQ calculation. Default is 1013.25 hPa.
        """
            
    def set_temperature_correction(self, value):
        """
        Sets the temperature correction value for the sensor.
        :param value: The temperature correction value to be added to the sensor readings.
        """

    def read(self, gas=False) -> tuple:
        """
        Reads temperature, pressure, humidity, and optionally gas from the BME680 sensor.
        :param gas: If True, reads gas data; otherwise, only reads temperature, pressure, and humidity.
        :return: A tuple containing temperature, pressure, humidity, and gas (if requested).
        """
        
    def sealevel(self, altitude:float) -> tuple:
        """
        Calculates the pressure at sea level based on the current altitude.
        :param altitude: The altitude in meters above sea level.
        :return: A tuple containing the pressure at sea level and the current pressure.
        """
        
    def altitude(self, sealevel:float) -> tuple:
        """
        Calculates the altitude based on the current pressure and a given sea level pressure.
        :param sealevel: The sea level pressure in hPa.
        :return: A tuple containing the calculated altitude in meters and the current pressure.
        """ 

    def iaq(self):
        """
        Calculates the Indoor Air Quality (IAQ) score based on the sensor readings.
        :return: A tuple containing the IAQ score, temperature, pressure, humidity, and gas readings.
        """
        
    def burnIn(self, threshold=0.01, count=10, timeout_sec=180): 
        """
        Monitors the gas sensor for a stable reading over a specified period.
        :param threshold: The relative change threshold for gas readings to consider them stable. Default is 0.01 (1%).
        :param count: The number of consecutive stable readings required to consider the sensor burned in. Default is 10.
        :param timeout_sec: The maximum time in seconds to wait for stable readings before timing out. Default is 180 seconds.
        :return: A generator that yields tuples of (is_burned_in, current_gas, gas_change).
        """
