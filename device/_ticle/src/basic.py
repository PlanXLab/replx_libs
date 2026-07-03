# @package: basic
# @version: 1.0.0
# @type: device-specific
# @category: board
# @interface: GPIO
# @depends: none
# @platforms: rp2
# @tags: led, button, bootsel, onboard, pico2w
# @author: PlanXLab Development Team

import machine
import rp2

class Led(machine.Pin):
    def __init__(self):
        super().__init__("WL_GPIO0", machine.Pin.OUT)

class Button:
    @staticmethod
    def read() -> bool:
        return rp2.bootsel_button() == 1
