# @package: button_async
# @version: 1.1.0
# @type: device-std
# @category: input
# @sensor_type: C
# @interface: GPIO
# @depends: button
# @platforms: *
# @tags: button, input, gpio, gesture, async, asyncio
# @author: PlanXLab Development Team

import asyncio

from .button import Button

class ButtonAsync:
    
    def __init__(self, device: Button):
        self._device = device
    
    def __enter__(self) -> "ButtonAsync":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass
    
    def __len__(self) -> int:
        return len(self._device)
    
    def __getitem__(self, idx: int | slice) -> "Button._View":
        return self._device[idx]
    
    @property
    def device(self) -> Button:
        return self._device
    
    async def wait_for_press(self, idx: int = 0, timeout_ms: int = 0, poll_ms: int = 10) -> bool:
        if timeout_ms <= 0:
            while not self._device._get_pressed(idx):
                await asyncio.sleep_ms(poll_ms)
            return True
        
        elapsed = 0
        while not self._device._get_pressed(idx):
            if elapsed >= timeout_ms:
                return False
            await asyncio.sleep_ms(poll_ms)
            elapsed += poll_ms
        return True
    
    async def wait_for_release(self, idx: int = 0, timeout_ms: int = 0, poll_ms: int = 10) -> bool:
        if timeout_ms <= 0:
            while self._device._get_pressed(idx):
                await asyncio.sleep_ms(poll_ms)
            return True
        
        elapsed = 0
        while self._device._get_pressed(idx):
            if elapsed >= timeout_ms:
                return False
            await asyncio.sleep_ms(poll_ms)
            elapsed += poll_ms
        return True
    
    async def wait_for_click(self, idx: int = 0, timeout_ms: int = 0, poll_ms: int = 10) -> bool:
        if timeout_ms <= 0:
            if not await self.wait_for_press(idx, 0, poll_ms):
                return False
            return await self.wait_for_release(idx, 0, poll_ms)
        
        if not await self.wait_for_press(idx, timeout_ms, poll_ms):
            return False
        
        remaining = max(0, timeout_ms - poll_ms)
        return await self.wait_for_release(idx, remaining, poll_ms)
    
    async def wait_for_event(
        self,
        idx: int = 0,
        event: str = 'click',
        timeout_ms: int = 0,
        poll_ms: int = 10
    ) -> bool:
        elapsed = 0
        while True:
            result = self._device._update_single(idx)
            if result == event:
                return True
            
            if timeout_ms > 0 and elapsed >= timeout_ms:
                return False
            
            await asyncio.sleep_ms(poll_ms)
            elapsed += poll_ms
    
    def events(self, poll_ms: int = 10) -> "_EventsIter":
        return _EventsIter(self._device, poll_ms)

    def events_for(self, indices: list[int] | None = None, poll_ms: int = 10) -> "_EventsForIter":
        if indices is None:
            indices = list(range(len(self._device)))
        return _EventsForIter(self._device, indices, poll_ms)


class _EventsIter:
    def __init__(self, device, poll_ms: int):
        self._device = device
        self._poll_ms = poll_ms
        self._pending = []

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            if self._pending:
                return self._pending.pop(0)
            results = self._device.update()
            if results:
                self._pending.extend(results[1:])
                return results[0]
            await asyncio.sleep_ms(self._poll_ms)


class _EventsForIter:
    def __init__(self, device, indices: list, poll_ms: int):
        self._device = device
        self._indices = indices
        self._poll_ms = poll_ms
        self._pending = []

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            if self._pending:
                return self._pending.pop(0)
            for idx in self._indices:
                event = self._device._update_single(idx)
                if event:
                    self._pending.append((idx, event))
            if self._pending:
                return self._pending.pop(0)
            await asyncio.sleep_ms(self._poll_ms)
