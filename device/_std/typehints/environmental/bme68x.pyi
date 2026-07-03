"""
BME68x environmental sensor driver for MicroPython.

Supports BME680/BME688 sensors with temperature, pressure, humidity, 
and gas resistance measurements. Type A polling sensor pattern.
"""

from typing import Generator, Literal

class BME68x:
    """
    BME680/BME688 environmental sensor driver (I2C).
    
    Measures temperature, pressure, humidity, and gas resistance (air quality).
    Supports three profile presets: eco, standard, and precision.
    
    Type A Polling Sensor Pattern:
        - start(gas) -> ready() polling -> result()
        - read(gas) for blocking single measurement
    
    Example
    -------
    ```python
    from bme68x import BME68x
    
    # Basic usage
    sensor = BME68x(scl=1, sda=0)
    print(f"Temp: {sensor.temperature():.1f}°C")
    print(f"Pressure: {sensor.pressure():.1f} hPa")
    print(f"Humidity: {sensor.humidity():.1f}%")
    
    # Type A pattern (non-blocking)
    eta_ms = sensor.start(gas=True)
    while not sensor.ready():
        pass
    temp, pres, humi, gas = sensor.result()
    
    # Blocking read
    temp, pres, humi = sensor.read(gas=False)
    temp, pres, humi, gas = sensor.read(gas=True)
    ```
    """
    
    gas_update_hint_ms: int
    """Gas measurement update hint period in milliseconds (min 200ms)."""
    
    gas_update_hint_maybe_too_short: bool
    """True if current period may be too short for reliable gas measurements."""
    
    require_heat_stab: bool
    """If True, require heater stabilization for valid gas readings."""
    
    gas_baseline: int
    """Gas baseline resistance in ohms for IAQ calculation (80k-320k)."""
    
    gas_baseline_auto_update_ms: int
    """Auto-update interval for gas baseline in milliseconds (min 60000ms)."""
    
    def __init__(
        self,
        sda: int,
        scl: int,
        *,
        addr: int = 0x77,
        profile_preset: Literal["eco", "standard", "precision"] = "standard",
    ) -> None:
        """
        Initialize BME68x sensor.
        
        :param scl: I2C SCL pin number.
        :param sda: I2C SDA pin number.
        :param addr: I2C address (0x76 or 0x77).
        :param profile_preset: Measurement profile preset.
        :raises OSError: If sensor not detected.
        """
        ...
    
    def adjust_temperature_correction(self, delta: float) -> None:
        """
        Adjust temperature correction offset.
        
        When using gas heater, internal temperature may be slightly higher.
        Use negative delta to compensate (e.g., -1.0).
        
        :param delta: Temperature offset to add in °C.
        
        Example
        -------
        ```python
        sensor.adjust_temperature_correction(-1.0)  # Compensate for heater
        ```
        """
        ...
    
    def set_tph_oversampling(
        self,
        *,
        osrs_t: Literal["off", "x1", "x2", "x4", "x8", "x16"] = "x2",
        osrs_p: Literal["off", "x1", "x2", "x4", "x8", "x16"] = "x4",
        osrs_h: Literal["off", "x1", "x2", "x4", "x8", "x16"] = "x1",
    ) -> None:
        """
        Set oversampling rates for temperature, pressure, and humidity.
        
        :param osrs_t: Temperature oversampling.
        :param osrs_p: Pressure oversampling.
        :param osrs_h: Humidity oversampling.
        
        Example
        -------
        ```python
        sensor.set_tph_oversampling(osrs_t='x4', osrs_p='x16', osrs_h='x2')
        ```
        """
        ...
    
    def set_tph_iir_filter(self, coeff: int) -> None:
        """
        Set IIR filter coefficient for T/P measurements.
        
        Higher values = more smoothing but slower response.
        
        :param coeff: Filter coefficient (0, 1, 3, 7, 15, 31, 63, or 127).
        :raises ValueError: If invalid coefficient.
        
        Example
        -------
        ```python
        sensor.set_tph_iir_filter(15)  # Moderate smoothing
        ```
        """
        ...
    
    def set_profile_preset(
        self,
        preset: Literal["eco", "standard", "precision"],
    ) -> None:
        """
        Apply a predefined measurement profile.
        
        - eco: Low power, longer intervals (6s), humidity off
        - standard: Balanced settings (3s intervals)
        - precision: High accuracy, shorter intervals (1.5s)
        
        :param preset: Profile name.
        
        Example
        -------
        ```python
        sensor.set_profile_preset('precision')  # High accuracy mode
        ```
        """
        ...
    
    def set_gas_heater_profiles(
        self,
        temps_c: list[int],
        durations_ms: list[int],
        amb_temp_c: float | None = None,
    ) -> None:
        """
        Configure multi-step gas heater profiles.
        
        :param temps_c: Heater target temperatures (1-10 steps, 200-400°C each).
        :param durations_ms: Heating durations per step.
        :param amb_temp_c: Ambient temperature for calculation (auto if None).
        :raises ValueError: If lists have invalid length or mismatch.
        
        Example
        -------
        ```python
        sensor.set_gas_heater_profiles([320, 350], [100, 150])
        ```
        """
        ...
    
    def set_gas_nb_conv(self, n: int = 0) -> None:
        """
        Set number of gas conversions (heater profile steps - 1).
        
        :param n: Number of conversions (0-9).
        
        Example
        -------
        ```python
        sensor.set_gas_nb_conv(2)  # Use 3 heater profile steps
        ```
        """
        ...
    
    def reset_cache(self) -> None:
        """
        Clear cached measurement values.
        
        Example
        -------
        ```python
        sensor.reset_cache()
        ```
        """
        ...
    
    def start(self, *, gas: bool = False) -> int:
        """
        Start a measurement (Type A pattern).
        
        :param gas: If True, include gas measurement.
        :return: Estimated time until measurement ready (ms).
        
        Example
        -------
        ```python
        eta_ms = sensor.start(gas=True)
        ```
        """
        ...
    
    def ready(self) -> bool:
        """
        Check if measurement is ready (Type A pattern).
        
        :return: True if new data available.
        
        Example
        -------
        ```python
        if sensor.ready():
            data = sensor.result()
        ```
        """
        ...
    
    def result(self) -> tuple[float, float, float] | tuple[float, float, float, float]:
        """
        Get measurement result (Type A pattern).
        
        Call after ready() returns True.
        
        :return: (temp_c, pressure_hpa, humidity_rh) or 
                 (temp_c, pressure_hpa, humidity_rh, gas_ohm) if gas enabled.
        
        Example
        -------
        ```python
        temp, pres, humi = sensor.result()
        ```
        """
        ...
    
    def read(self, *, gas: bool = False) -> tuple[float, float, float] | tuple[float, float, float, float]:
        """
        Perform blocking measurement (combines start/ready/result).
        
        :param gas: If True, include gas measurement.
        :return: (temp_c, pressure_hpa, humidity_rh) or
                 (temp_c, pressure_hpa, humidity_rh, gas_ohm) if gas=True.
        :raises OSError: If measurement times out.
        
        Example
        -------
        ```python
        temp, pres, humi, gas = sensor.read(gas=True)
        ```
        """
        ...
    
    def temperature(self) -> float:
        """
        Get temperature (blocking, uses cache if fresh).
        
        :return: Temperature in °C.
        
        Example
        -------
        ```python
        temp = sensor.temperature()
        print(f"{temp:.1f}°C")
        ```
        """
        ...
    
    def pressure(self) -> float:
        """
        Get pressure (blocking, uses cache if fresh).
        
        :return: Pressure in hPa.
        
        Example
        -------
        ```python
        pres = sensor.pressure()
        print(f"{pres:.1f} hPa")
        ```
        """
        ...
    
    def humidity(self) -> float:
        """
        Get relative humidity (blocking, uses cache if fresh).
        
        :return: Relative humidity in %RH.
        
        Example
        -------
        ```python
        humi = sensor.humidity()
        print(f"{humi:.1f}%")
        ```
        """
        ...
    
    def sea_level(self, altitude: float, temp_c: float | None = None) -> float:
        """
        Calculate sea level pressure from current pressure and altitude.
        
        :param altitude: Current altitude in meters.
        :param temp_c: Temperature for calculation (uses measured if None).
        :return: Sea level pressure in hPa.
        
        Example
        -------
        ```python
        slp = sensor.sea_level(altitude=150)
        print(f"Sea level: {slp:.1f} hPa")
        ```
        """
        ...
    
    def altitude(self, sealevel: float, temp_c: float | None = None) -> float:
        """
        Calculate altitude from current pressure and sea level pressure.
        
        :param sealevel: Sea level pressure in hPa.
        :param temp_c: Temperature for calculation (uses measured if None).
        :return: Altitude in meters.
        
        Example
        -------
        ```python
        alt = sensor.altitude(sealevel=1013.25)
        print(f"Altitude: {alt:.1f} m")
        ```
        """
        ...
    
    def trigger_gas_measurement(self, *, steps: int | None = None) -> int:
        """
        Trigger gas resistance measurement.
        
        :param steps: Number of heater profile steps (1-10, uses current if None).
        :return: Estimated time until measurement ready (ms).
        
        Example
        -------
        ```python
        eta = sensor.trigger_gas_measurement()
        ```
        """
        ...
    
    def gas_measurement_ready(self) -> bool:
        """
        Check if gas measurement is ready.
        
        :return: True if gas measurement complete and valid.
        
        Example
        -------
        ```python
        if sensor.gas_measurement_ready():
            gas = sensor.gas_resistance()
        ```
        """
        ...
    
    def gas_resistance(self) -> float | None:
        """
        Get gas resistance from last measurement.
        
        :return: Gas resistance in ohms, or None if not ready.
        
        Example
        -------
        ```python
        gas = sensor.gas_resistance()
        if gas:
            print(f"Gas: {gas:.0f} Ω")
        ```
        """
        ...
    
    def burn_in(
        self,
        mode: Literal["simple"] = "simple",
    ) -> Generator[dict, None, None]:
        """
        Generator for gas sensor burn-in calibration.
        
        Run for several minutes to stabilize gas baseline.
        
        :param mode: Burn-in mode.
        :yields: Progress dicts with phase, success status, and metrics.
        
        Example
        -------
        ```python
        for status in sensor.burn_in():
            print(status)
            if status["success"]:
                break
        ```
        """
        ...
    
    def iaq_heuristics(
        self,
        *,
        temp_weighting: float = 0.08,
        pressure_weighting: float = 0.02,
        humi_weighting: float = 0.15,
        gas_weighting: float = 0.75,
        gas_ema_alpha: float = 0.02,
        temp_baseline: float = 25.0,
        pressure_baseline: float = 1013.25,
        humi_baseline: float = 50.0,
    ) -> tuple[int, float, float, float, float] | None:
        """
        Calculate heuristic Indoor Air Quality (IAQ) index.
        
        :param temp_weighting: Temperature weight in IAQ calculation.
        :param pressure_weighting: Pressure weight in IAQ calculation.
        :param humi_weighting: Humidity weight in IAQ calculation.
        :param gas_weighting: Gas resistance weight in IAQ calculation.
        :param gas_ema_alpha: EMA alpha for gas baseline auto-update.
        :param temp_baseline: Reference temperature in °C.
        :param pressure_baseline: Reference pressure in hPa.
        :param humi_baseline: Reference humidity in %RH.
        :return: (iaq_index, temp, pressure, humidity, gas_resistance) or None if gas invalid.
                 IAQ index: 0-50 (good), 51-100 (moderate), 101-150 (poor), 
                           151-200 (unhealthy), 201-300 (very unhealthy), 301-500 (hazardous).
        
        Example
        -------
        ```python
        result = sensor.iaq_heuristics()
        if result:
            iaq, temp, pres, humi, gas = result
            print(f"IAQ: {iaq}")
        ```
        """
        ...
