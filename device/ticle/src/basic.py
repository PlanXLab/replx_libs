import machine
import rp2

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


class Led(machine.Pin):
    def __init__(self):
        super().__init__("WL_GPIO0", machine.Pin.OUT)


class Button:
    @staticmethod
    def read() -> bool:
        return rp2.bootsel_button() == 1
