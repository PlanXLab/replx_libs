class Thermometer: 
    """
    Infrared thermometer sensor controller for MLX90614.
    
    This class provides an interface for the MLX90614 non-contact infrared
    thermometer sensor, capable of measuring both ambient temperature and
    object surface temperature without physical contact.
    
    Key Features:
    
        - Non-contact temperature measurement
        - Ambient and object temperature modes
        - High accuracy (±0.5°C typical)
        - Wide measurement range (-40°C to +125°C ambient, -70°C to +380°C object)
    """

    def __init__(self) -> None:
        """
        Initialize the IR thermometer sensor.
        
        Sets up I2C communication with the MLX90614 sensor at address 0x5A.
        Uses 50kHz I2C frequency for reliable communication.
        
        Example
        --------
        ```python
            >>> thermo = Thermometer()
            >>> 
            >>> # Read object temperature
            >>> temp = thermo.object()
            >>> print(f"Object temperature: {temp}°C")
            >>> 
            >>> # Read ambient temperature
            >>> ambient = thermo.ambient()
            >>> print(f"Ambient temperature: {ambient}°C")
        ```
        """

    def read(self, object: bool = True, eeprom: bool = False) -> int:
        """
        Read raw temperature data from the sensor.
        
        Returns the raw 16-bit temperature value from the sensor.
        Use ambient() or object() methods for converted temperature values.
        
        :param object: If True, read object temperature; if False, read ambient temperature
        :param eeprom: If True, read from EEPROM; if False, read from RAM
        :return: Raw 16-bit temperature value
        
        Example
        --------
        ```python
            >>> thermo = Thermometer()
            >>> 
            >>> # Read raw object temperature
            >>> raw = thermo.read(object=True)
            >>> print(f"Raw value: {raw}")
            >>> 
            >>> # Read raw ambient temperature
            >>> raw_ambient = thermo.read(object=False)
            >>> 
            >>> # Convert raw to Celsius
            >>> temp_c = raw * 0.02 - 273.15
            >>> print(f"Temperature: {temp_c:.1f}°C")
        ```
        """

    def ambient(self) -> float:
        """
        Read the ambient temperature.
        
        Returns the temperature of the sensor's surrounding environment
        (not the target object).
        
        :return: Ambient temperature in degrees Celsius (rounded to 1 decimal)
        
        Example
        --------
        ```python
            >>> thermo = Thermometer()
            >>> 
            >>> # Read ambient temperature
            >>> ambient = thermo.ambient()
            >>> print(f"Room temperature: {ambient}°C")
            >>> 
            >>> # Monitor ambient over time
            >>> while True:
            ...     temp = thermo.ambient()
            ...     print(f"Ambient: {temp}°C")
            ...     utime.sleep(60)
            >>> 
            >>> # Temperature logging
            >>> readings = []
            >>> for _ in range(10):
            ...     readings.append(thermo.ambient())
            ...     utime.sleep(1)
            >>> avg = sum(readings) / len(readings)
            >>> print(f"Average ambient: {avg:.1f}°C")
        ```
        """

    def object(self) -> float:
        """
        Read the object (target) temperature.
        
        Returns the temperature of the object in the sensor's field of view
        using non-contact infrared measurement.
        
        :return: Object temperature in degrees Celsius (rounded to 1 decimal)
        
        Example
        --------
        ```python
            >>> thermo = Thermometer()
            >>> 
            >>> # Read object temperature
            >>> temp = thermo.object()
            >>> print(f"Object temperature: {temp}°C")
            >>> 
            >>> # Fever detection
            >>> body_temp = thermo.object()
            >>> if body_temp > 37.5:
            ...     print("Elevated temperature detected!")
            >>> 
            >>> # Surface temperature monitoring
            >>> while True:
            ...     obj = thermo.object()
            ...     amb = thermo.ambient()
            ...     diff = obj - amb
            ...     print(f"Object: {obj}°C, Ambient: {amb}°C, Diff: {diff:+.1f}°C")
            ...     utime.sleep(1)
            >>> 
            >>> # Hot spot detection
            >>> threshold = 50.0
            >>> if thermo.object() > threshold:
            ...     print(f"Warning: Temperature exceeds {threshold}°C!")
        ```
        """
