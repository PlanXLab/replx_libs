import utime
import ustruct
import machine 

from micropython import const


class DIO:
    """
    The DIO class provides static methods required to 
    define DIO port pins for the AutoCtrl.
    """
    
    IN = machine.Pin.IN
    OUT = machine.Pin.OUT
    PULL_UP = machine.Pin.PULL_UP
    PULL_DOWN = machine.Pin.PULL_DOWN
    LOW = const(0)
    HIGH = const(1)

    class Device:
        """
        The Device class is used to specify the device type.
        """
        RELAY = const(0) 
        PWM = const(1)    
    
    P_RELAY = {0:'D0', 1:'D6', 2:'D5'} 
    
    @staticmethod
    def P18() -> machine.Pin:
        """
        Create a pin object for the P18 port of DIO.
        
        Only Input of ActiveHigh(5V ~ 6V) Device(ex: GasDetector). 
        It has a built-in divider resistor that halves the 12V.
        
        :return: The pin object.
        """
    
    @staticmethod
    def P17() -> machine.Pin:
        """
        Create a pin object for the P17 port of DIO. 
        
        Only Input of ActiveLow(GND) Device(ex:PIR, LimitSiwtch ...)
        
        :return: The pin object.
        """
     
    @staticmethod
    def P8(mode:int, pull_value:int=None) -> machine.Pin:
        """
        Create a pin object for the P8 port of DIO.
        
        Operation 3V3 IN/OUT\r
\1 mode: The mode of the pin. DIO.IN or DIO.OUT
        :param pull_value: The pull value of the pin. DIO.PULL_UP or DIO.PULL_DOWN
        
        :return: The pin object.
        """
    
    @staticmethod
    def P23(mode, pull_value=None):
        """
        Create a pin object for the P23 port of DIO.
        
        Operation 3V3 IN/OUT\r
\1 mode: The mode of the pin. DIO.IN or DIO.OUT
        :param pull_value: The pull value of the pin. DIO.PULL_UP or DIO.PULL_DOWN
        
        :return: The pin object.
        """

def Relay(pin, value=0):
    """
    Create a relay object.\r
\1 pin: The pin string of the relay. DIO.P_RELAY[0] ~ DIO.P_RELAY[2]
    :param value: The initial value of the relay. value=0 is Normal open
    
    :return: The relay object.
    """    

class RelayTerminal:
    """
    The RelayTerminal object is used to control the state of the RelayTerminal.
    """
    
    def __init__(self, *relays) -> None:
        """
        Initializes the RelayTerminal object.\r
\1 relays: The relay objects to control the RelayTerminal.
        """
        
    def on(self, pos:int) -> None:
        """
        Turns on the relay.\r
\1 ch: The index number of the relay to turn on.
        """
        
    def off(self, pos:int) -> None:
        """
        Turns off the relay.\r
\1 pos: The index number of the relay to turn off.
        """
        
class DoorLock:
    """
    The DoorLock object is used to control the state of the DoorLock.
    """
    
    def __init__(self, relay, *, dio:int, active_low:bool) -> None:
        """
        Initializes the DoorLock object.
        dio is only Input (ActiveHigh). DIO Pin object (ex P17)\r
\1 relay: The relay object to control the DoorLock.
        :param dio: The feedback pin to read the state of the DoorLock.
        :param active_low: The state of the feedback pin when the DoorLock is opened.        
        
        The open, close, and is_opened methods can only be used when the dio and active_low parameters are given.
        """

    def open(self) -> None:
        """
        Opens the DoorLock when dio and active_low parameters are given.
        """
    
    def close(self) -> None:
        """
        Closes the DoorLock when dio and active_low parameters are given.
        """

    def is_opened(self) -> bool:
        """
        Returns the state of the DoorLock when dio and active_low parameters are given.
        
        :return: ``True`` if the DoorLock is opened, ``False`` if the DoorLock is closed.   
        """
    
    def work(self) -> None:
        """
        Changes the status of the DoorLock.
        """

class Pwm:
    """
    The Pwm object is used to control the state of the PWM.
    """
    
    def __init__(self, freq:int=100) -> None:
        """
        Initializes the Pwm object.\r
\1 freq: The frequency of the PWM signal.
        """
     
    def freq(self, freq: int) -> None:
        """
        Set the frequency of the PWM signal.\r
\1 freq: The frequency of the PWM signal. Maximum frequency is 1526 Hz.
        """

    def pwm(self, ch: int, on: int, off: int) -> None:
        """
        Set the PWM signal.\r
\1 ch: The channel number of the PWM signal.
        :param on: The time the signal is on.
        :param off: The time the signal is off.
        
        duty cycle 0: on is 0, off is 4096
        duty cycle 100: on is 4096, off is 0
        etc: on is 0, off is int((duty_cycle - 1) * (4095 - 1) / (99 - 1) + 1)
        """

    def duty(self, ch:int, value:int) -> None:
        """
        Set the duty cycle of the PWM signal.\r
\1 ch: The channel number of the PWM signal.
        :param value: The duty cycle of the PWM signal.
        """

class GasDetector:
    """
    The GasDetector object is used to read the state of the GasDetector.
    """
    
    def read(self):
        """
        read the state of the GasDetector.
        
        :return: The state of the GasDetector.
        """

class GasBreaker: 
    """
    The GasBreaker object is used to control the state of the GasBreaker.
    """    
    
    def __init__(self, red, black) -> None:
        """
        Initializes the GasBreaker object.\r
\1 red: Channel number to which the red wire of the gas breaker is connected.
        :param black: Channel number to which the black wire of the gas breaker is connected.
        """        
        
    def open(self) -> None:
        """
        Opens the gas breaker.
        """
            
    def close(self, init=False):
        """
        Closes the gas breaker.
        """
    
    def stop(self) -> None:
        """
        Stops the gas breaker.
        """
    
def Fan(type, ch, value:int=0) -> object:
    """
    The Fan object is used to control the state of the Fan.\r
\1 type: The device to control, either DIO.Device.RELAY or DIO.Device.PWM
    :param ch: The channel number of the device to control
    :param value: Initial value
    
    :return: Relay or PWM object
    """
     
def Light(type, ch, value=0) -> object:
    """
    The Light object is used to control the state of the Light.\r
\1 type: The device to control, either DIO.Device.RELAY or DIO.Device.PWM
    :param ch: The channel number of the device to control
    :param value: Initial value
    
    :return: Relay or PWM object
    """
