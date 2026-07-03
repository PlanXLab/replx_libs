"""
Async wrapper for BME68x environmental sensor.

Provides non-blocking async methods for reading temperature, pressure,
humidity, and gas measurements.
"""

from typing import AsyncGenerator, AsyncIterator
from .bme68x import BME68x

class BME68xAsync:
    """
    Async wrapper for BME68x sensor.
    
    Wraps synchronous BME68x driver to provide asyncio-compatible
    non-blocking measurement methods.
    
    Example
    -------
    ```python
    import asyncio
    from bme68x import BME68x
    from bme68x_async import BME68xAsync
    
    async def main():
        sensor = BME68x(scl=1, sda=0)
        async_sensor = BME68xAsync(sensor)
        
        # Single read
        temp, pres, humi = await async_sensor.read()
        print(f"Temp: {temp:.1f}°C")
        
        # Read with gas
        temp, pres, humi, gas = await async_sensor.read(gas=True)
        print(f"Gas: {gas:.0f} Ω")
        
        # Continuous streaming
        async for temp, pres, humi in async_sensor.stream(interval_ms=3000):
            print(f"T={temp:.1f}°C P={pres:.1f}hPa H={humi:.1f}%")
    
    asyncio.run(main())
    ```
    """
    
    def __init__(self, device: BME68x, poll_ms: int = 10) -> None:
        """
        Initialize async wrapper.
        
        :param device: BME68x sensor instance.
        :param poll_ms: Polling interval for ready() checks (min 5ms).
        """
        ...
    
    async def read(
        self,
        *,
        gas: bool = False,
    ) -> tuple[float, float, float] | tuple[float, float, float, float]:
        """
        Perform async measurement.
        
        :param gas: If True, include gas measurement.
        :return: (temp_c, pressure_hpa, humidity_rh) or
                 (temp_c, pressure_hpa, humidity_rh, gas_ohm) if gas=True.
        
        Example
        -------
        ```python
        temp, pres, humi = await async_sensor.read()
        ```
        """
        ...
    
    async def read_tph(self) -> tuple[float, float, float]:
        """
        Read temperature, pressure, humidity (no gas).
        
        :return: (temp_c, pressure_hpa, humidity_rh).
        
        Example
        -------
        ```python
        temp, pres, humi = await async_sensor.read_tph()
        ```
        """
        ...
    
    async def read_gas(self) -> tuple[float, float, float, float]:
        """
        Read all measurements including gas.
        
        :return: (temp_c, pressure_hpa, humidity_rh, gas_ohm).
        
        Example
        -------
        ```python
        temp, pres, humi, gas = await async_sensor.read_gas()
        ```
        """
        ...
    
    def stream(
        self,
        *,
        gas: bool = False,
        interval_ms: int = 0,
    ) -> AsyncIterator[tuple[float, float, float] | tuple[float, float, float, float]]:
        """
        Continuous measurement stream.
        
        :param gas: If True, include gas in each measurement.
        :param interval_ms: Minimum interval between measurements (0 = as fast as possible).
        :yields: Measurement tuples (temp, pressure, humidity[, gas]).
        
        Example
        -------
        ```python
        async for temp, pres, humi in async_sensor.stream(interval_ms=3000):
            print(f"{temp:.1f}°C")
        ```
        """
        ...
    
    def burn_in(
        self,
        mode: str = "simple",
    ) -> AsyncIterator[dict]:
        """
        Async generator for gas sensor burn-in calibration.
        
        Non-blocking version of BME68x.burn_in() that yields to the event loop
        during wait periods. Run for several minutes to stabilize gas baseline.
        
        :param mode: Burn-in mode.
        :yields: Progress dicts with phase, success status, and metrics.
        
        Example
        -------
        ```python
        async for status in async_sensor.burn_in():
            print(f"Phase: {status['phase']}")
            if status["success"]:
                print(f"Baseline: {status['baseline_ohm']} Ω")
                break
        ```
        """
        ...
    
    def __aiter__(self) -> "BME68xAsync":
        """
        Async iterator for TPH measurements.
        
        Example
        -------
        ```python
        async for temp, pres, humi in async_sensor:
            print(f"{temp:.1f}°C")
        ```
        """
        ...
    
    async def __anext__(self) -> tuple[float, float, float]:
        """
        Get next TPH measurement.
        
        :return: (temp_c, pressure_hpa, humidity_rh).
        
        Example
        -------
        ```python
        data = await async_sensor.__anext__()
        ```
        """
        ...
