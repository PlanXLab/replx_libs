"""
WS2812 LED Matrix Module

Advanced WS2812/NeoPixel LED matrix controller with text rendering,
visual effects, and hardware-accelerated updates using RP2040 PIO/DMA.

Features:

- Multi-panel LED matrix support with flexible grid arrangements
- Hardware-accelerated updates via PIO state machines
- Text rendering with custom bitmap fonts
- Visual effects: rainbow, fire, plasma, particles, etc.
- Pixel-level and vector graphics drawing
- Brightness and gamma correction

Example
-------
```python
from display.ws2812 import Matrix, Effect

# Create 16x16 matrix on pin 0 (SM auto-selected)
matrix = Matrix([0], panel_width=16, panel_height=16)

# Basic usage
matrix.fill((255, 0, 0))  # Red fill
matrix.update()

# Text rendering
matrix.clear()
matrix.draw_text("Hi", x=0, y=0, color=(0, 255, 0))
matrix.update()

# Effects
effect = Effect(matrix)
effect.start_rainbow()
```

Classes:

- Matrix: Main LED matrix controller
- Effect: Animation effects manager

"""

from .matrix import Matrix
from .effect import Effect

__all__ = ['Matrix', 'Effect']
