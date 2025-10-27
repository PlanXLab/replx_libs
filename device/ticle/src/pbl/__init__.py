import sys
import json
import utime
import math
import urandom

import utools
import machine
import micropython
import ticle
import ticle.ext as ext

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


__all__ = (
    "DistanceScanner", "ServoFnd", "UltrasonicGrid", "WS2812Matrix_Effect", 
)

_lazy_map = {
    "DistanceScanner": (".distance_scanner", "DistanceScanner"),
    "ServoFnd": (".servo_fnd", "ServoFnd"),
    "UltrasonicGrid": (".ultrasonic_grid", "UltrasonicGrid"),
    "WS2812Matrix_Effect": (".ws2812matrix_effect", "WS2812Matrix_Effect"),
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