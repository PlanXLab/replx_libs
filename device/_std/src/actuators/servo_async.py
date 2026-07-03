# @package: servo_async
# @version: 1.1.1
# @type: device-std
# @category: actuators
# @interface: PWM
# @depends: servo
# @platforms: *
# @tags: servo, motor, async, asyncio, actuator
# @author: PlanXLab Development Team

import asyncio
from .servo import Servo


class ServoAsync:
    def __init__(self, servo: Servo):
        self._servo = servo

    def __enter__(self) -> "ServoAsync":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._servo.deinit()

    def __len__(self) -> int:
        return len(self._servo)

    def __getitem__(self, idx: int | slice) -> "ServoAsyncView":
        return ServoAsyncView(self._servo[idx])

    @property
    def device(self) -> Servo:
        return self._servo

    @property
    def servo(self) -> Servo:
        return self._servo

    def deinit(self) -> None:
        self._servo.deinit()


class ServoAsyncView:
    def __init__(self, view):
        self._view = view

    def __len__(self) -> int:
        return len(self._view)

    def __getitem__(self, idx: int | slice) -> "ServoAsyncView":
        return ServoAsyncView(self._view[idx])

    @property
    def angle(self) -> list[float]:
        return self._view.angle

    @angle.setter
    def angle(self, val: float | list[float]) -> None:
        self._view.angle = val

    @property
    def speed(self) -> list[float]:
        return self._view.speed

    @speed.setter
    def speed(self, val: float | list[float]) -> None:
        self._view.speed = val

    @property
    def duty_us(self) -> list[int]:
        return self._view.duty_us

    @duty_us.setter
    def duty_us(self, val: int | list[int]) -> None:
        self._view.duty_us = val

    @property
    def is_moving(self) -> list[bool]:
        return self._view.is_moving

    @property
    def home_angle(self) -> list[float]:
        return self._view.home_angle

    @home_angle.setter
    def home_angle(self, val: float | list[float]) -> None:
        self._view.home_angle = val

    @property
    def calibration(self) -> list[dict]:
        return self._view.calibration

    @calibration.setter
    def calibration(self, params: dict) -> None:
        self._view.calibration = params

    def stop(self) -> None:
        self._view.stop()

    async def wait(self, timeout_ms: int = 10000) -> bool:
        elapsed = 0
        poll_ms = 10
        
        while any(self.is_moving):
            if elapsed >= timeout_ms:
                return False
            await asyncio.sleep_ms(poll_ms)
            elapsed += poll_ms
        
        return True

    async def move_to(self, deg: float, ms: int | None = None, easing: str = 'linear', *, wait: bool = True, timeout_ms: int = 10000) -> bool:
        self._view.move_to(deg, ms, easing)
        
        if wait:
            return await self.wait(timeout_ms)
        return True

    async def home(self, ms: int | None = None, easing: str = 'quad', *, wait: bool = True, timeout_ms: int = 10000) -> bool:
        self._view.home(ms, easing)
        
        if wait:
            return await self.wait(timeout_ms)
        return True

    async def sweep(self, start: float, end: float, ms: int | None = None, easing: str = 'linear', *, repeat: int = 1) -> None:
        count = 0
        while repeat == 0 or count < repeat:
            await self.move_to(start, ms, easing)
            await self.move_to(end, ms, easing)
            count += 1

    async def sequence(self, positions: list[tuple[float, int | None]], easing: str = 'linear') -> None:
        for deg, ms in positions:
            await self.move_to(deg, ms, easing)


AsyncServo = ServoAsync
AsyncServoView = ServoAsyncView
