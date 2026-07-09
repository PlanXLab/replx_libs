"""
AS5600 Async Wrapper for asyncio Compatibility

Provides async interface for AS5600 magnetic encoder operations.
Enables cooperative multitasking with other async tasks while
reading angle, velocity, and turn data.

Features:

- Async wrappers for all sensor methods
- Continuous data streaming via async generators
- Configurable polling intervals
- Frame-consistent data access

"""

from typing import AsyncGenerator, AsyncIterator, Dict, Tuple
from i2c import I2CController
from .as5600 import AS5600


class AS5600Async:
    """
    Async wrapper for AS5600 magnetic encoder.
    
    Provides asyncio-compatible interface for angle, velocity, and turn tracking.
    Use stream() for continuous monitoring or individual async methods for
    single reads.
    
    Example
    -------
    ```python
        >>> import asyncio
        >>> from as5600 import AS5600
        >>> from as5600_async import AS5600Async
        >>> 
        >>> i2c = I2CController(sda=4, scl=5)
        >>> encoder = AS5600(i2c)
        >>> async_enc = AS5600Async(encoder)
        >>> 
        >>> async def monitor():
        ...     async for data in async_enc.stream(poll_ms=20):
        ...         print(f"Angle: {data['angle']:.3f} rad")
        ...         print(f"Velocity: {data['velocity']:.2f} rad/s")
        >>> 
        >>> asyncio.run(monitor())
    ```
    """
    
    def __init__(self, device: AS5600) -> None:
        """
        Initialize async wrapper with AS5600 device.
        
        :param device: AS5600 instance to wrap
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> async_enc = AS5600Async(encoder)
        ```
        """
        ...
    
    @property
    def device(self) -> AS5600:
        """
        Access the underlying AS5600 device.
        
        :return: The wrapped AS5600 instance
        """
        ...
    
    async def angle(self, *, soft_zero: bool = True, filtered: bool = False) -> float:
        """
        Read current angle asynchronously.
        
        :param soft_zero: If True, angle is relative to soft-zero position
        :param filtered: If True, apply EMA filtering
        :return: Angle in radians (0 to 2π)
        
        Example
        -------
        ```python
            >>> angle = await async_enc.angle()
            >>> print(f"Angle: {angle:.3f} rad")
        ```
        """
        ...

    async def angle_deg(self, *, soft_zero: bool = True, filtered: bool = False) -> float:
        """
        Read current angle in degrees asynchronously.
        
        :param soft_zero: If True, angle is relative to soft-zero position
        :param filtered: If True, apply EMA filtering
        :return: Angle in degrees (0 to 360)
        
        Example
        -------
        ```python
            >>> deg = await async_enc.angle_deg()
            >>> print(f"Angle: {deg:.1f}°")
        ```
        """
        ...
    
    async def velocity(
        self,
        *,
        filtered: bool = False,
        tick_emit: int = 4,
        tick_hold: int = 2,
        dt_min_s: float = 0.003,
        dt_max_s: float = 0.5,
        omega_clip: float | None = None
    ) -> float:
        """
        Read current angular velocity asynchronously.
        
        :param filtered: If True, apply low-pass and slew-rate filtering
        :param tick_emit: Minimum tick change to emit velocity
        :param tick_hold: Dead-zone threshold for noise rejection
        :param dt_min_s: Minimum time between velocity updates
        :param dt_max_s: Maximum time before velocity resets to zero
        :param omega_clip: Optional velocity clipping limit (rad/s)
        :return: Angular velocity in rad/s
        
        Example
        -------
        ```python
            >>> vel = await async_enc.velocity(filtered=True)
            >>> rpm = vel * AS5600.VELOCITY_UNIT_RAD_S_TO_RPM
            >>> print(f"Speed: {rpm:.1f} RPM")
        ```
        """
        ...

    async def velocity_rpm(self, *, filtered: bool = False) -> float:
        """
        Read current velocity in RPM asynchronously.
        
        :param filtered: If True, apply filtering
        :return: Angular velocity in RPM
        
        Example
        -------
        ```python
            >>> rpm = await async_enc.velocity_rpm(filtered=True)
            >>> print(f"Speed: {rpm:.1f} RPM")
        ```
        """
        ...
    
    async def turn(
        self,
        *,
        soft_zero: bool = True,
        filtered: bool = False,
        tick_thr: int = 2,
        confirm_samples: int = 3
    ) -> Tuple[float, float]:
        """
        Read multi-turn tracking data asynchronously.
        
        :param soft_zero: If True, angle relative to soft-zero position
        :param filtered: If True, apply EMA filtering
        :param tick_thr: Threshold ticks before committing motion
        :param confirm_samples: Consecutive samples needed to confirm motion
        :return: Tuple of (net_turns, path_turns) in revolution units
        
        Example
        -------
        ```python
            >>> net, path = await async_enc.turn()
            >>> print(f"Net: {net:.2f} rev, Total: {path:.2f} rev")
        ```
        """
        ...
    
    def reset_turn(self) -> None:
        """
        Reset multi-turn accumulator.
        
        Clears net and path turn counters to zero.
        """
        ...

    def reset_velocity(self) -> None:
        """
        Reset velocity tracking state.
        
        Clears internal state for velocity calculation.
        """
        ...
    
    async def status(self) -> int:
        """
        Read magnet status asynchronously.
        
        :return: Status code (STATUS_NORMAL, STATUS_NO_MAGNET, etc.)
        
        Example
        -------
        ```python
            >>> status = await async_enc.status()
            >>> if status == AS5600.STATUS_NORMAL:
            ...     print("Magnet OK")
        ```
        """
        ...
    
    def stream(
        self,
        poll_ms: int = 10,
        count: int = 0
    ) -> AsyncIterator[Dict[str, float]]:
        """
        Stream all encoder data continuously.
        
        Yields dictionaries containing angle, velocity, and turn data
        at the specified polling interval.
        
        :param poll_ms: Polling interval in milliseconds
        :param count: Number of samples (0 = infinite)
        :yields: Dict with 'angle', 'velocity', 'turn_net', 'turn_path' keys
        
        Example
        -------
        ```python
            >>> async for data in async_enc.stream(poll_ms=20):
            ...     print(f"Angle: {data['angle']:.3f}")
            ...     print(f"Vel: {data['velocity']:.2f}")
            ...     print(f"Turns: {data['turn_net']:.2f}")
        ```
        """
        ...
    
    def stream_angle(
        self,
        poll_ms: int = 10,
        count: int = 0,
        *,
        soft_zero: bool = True,
        filtered: bool = False
    ) -> AsyncIterator[float]:
        """
        Stream angle values continuously.
        
        :param poll_ms: Polling interval in milliseconds
        :param count: Number of samples (0 = infinite)
        :param soft_zero: If True, angle relative to soft-zero position
        :param filtered: If True, apply EMA filtering
        :yields: Angle in radians (0 to 2π)
        
        Example
        -------
        ```python
            >>> async for angle in async_enc.stream_angle(poll_ms=10):
            ...     print(f"Angle: {angle:.3f} rad")
        ```
        """
        ...
    
    def stream_velocity(
        self,
        poll_ms: int = 10,
        count: int = 0,
        *,
        filtered: bool = False
    ) -> AsyncIterator[float]:
        """
        Stream velocity values continuously.
        
        :param poll_ms: Polling interval in milliseconds
        :param count: Number of samples (0 = infinite)
        :param filtered: If True, apply filtering
        :yields: Angular velocity in rad/s
        
        Example
        -------
        ```python
            >>> async for vel in async_enc.stream_velocity(poll_ms=20, filtered=True):
            ...     print(f"Velocity: {vel:.2f} rad/s")
        ```
        """
        ...
