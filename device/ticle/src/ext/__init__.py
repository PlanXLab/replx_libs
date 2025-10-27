__version__ = "1.0.0"
__author__ = "PlanX Lab Development Team"


import sys
import math
import utime
import ustruct
import array

import gc
import machine
import micropython
import rp2

import utools
import ticle
from ticle import I2CMaster
from ticle import Dout


__all__ = (
    "AS5600", "AS5600NB", "BME68x", "BME68xNB", "BNO055", "BNO055NB", "BtAudioAmpCtrl", "Button",  "ButtonNB", "Buttons", "HD44780I2c", 
    "KY022",  "KY022NB", "MPU6050", "MPU6050NB", "Relays", "Servos",  "SR04", "SR04NB", "SR04s", "VL53L0X", "VL53L0XNB", "WS2812Matrix",
)

_lazy_map = {
    "AS5600": (".as5600", "AS5600"),
    "AS5600NB": (".as5600_nb", "AS5600NB"),
    "BME68x": (".bme68x", "BME68x"),
    "BME68xNB": (".bme68x_nb", "BME68xNB"),
    "BNO055": (".bno055", "BNO055"),
    "BNO055NB": (".bno055_nb", "BNO055NB"),
    "BtAudioAmpCtrl": (".btaac", "BtAudioAmpCtrl"),
    "Button": (".button", "Button"),
    "ButtonNB": (".button_nb", "ButtonNB"),
    "Buttons": (".buttons", "Buttons"),
    "HD44780I2c": (".hd44780i2c", "HD44780I2c"),
    "KY022": (".ky022", "KY022"),
    "KY022NB": (".ky022_nb", "KY022NB"),
    "MPU6050": (".mpu6050", "MPU6050"),
    "MPU6050NB": (".mpu6050_nb", "MPU6050NB"),
    "Relays": (".relays", "Relays"),
    "Servos": (".servos", "Servos"),
    "SR04": (".sr04", "SR04"),
    "SR04NB": (".sr04_nb", "SR04NB"),
    "SR04s": (".sr04s", "SR04s"),
    "VL53L0X": (".vl53l0x", "VL53L0X"),
    "VL53L0XNB": (".vl53l0x_nb", "VL53L0XNB"),
    "WS2812Matrix": (".ws2812", "WS2812Matrix"),
}


def __getattr__(name):
    try:
        rel_mod, attr = _lazy_map[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    
    fullname = __name__ + rel_mod
    __import__(fullname)
    mod = sys.modules[fullname]
        
    obj = getattr(mod, attr)
    globals()[name] = obj
    return obj

def __dir__():
    return sorted(list(globals().keys()) + list(_lazy_map.keys()))