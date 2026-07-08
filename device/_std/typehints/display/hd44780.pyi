"""
HD44780-compatible Character LCD Driver (PCF8574 I2C Backpack)

This module provides a driver for HD44780-compatible character LCDs
controlled via PCF8574 I2C I/O expander.

Hardware Configuration:

- PCF8574 default address: 0x20 ~ 0x27 (set by A0-A2 pins)
- PCF8574A default address: 0x38 ~ 0x3F (set by A0-A2 pins)
- Common LCD module defaults: 0x27 or 0x3F

PCF8574 I/O Expander Pin Mapping (Standard):

- P0: RS (Register Select)
- P1: RW (Read/Write) - usually GND
- P2: EN (Enable)
- P3: BL (Backlight control)
- P4-P7: D4-D7 (4-bit data)

Compatible LCD Controllers:

- Hitachi HD44780 (original)
- Samsung KS0066
- Sunplus SPLC780D
- Sitronix ST7066U
- AIPO AIP31066

Features:

- Text output with cursor positioning
- Custom character creation (CGRAM)
- Horizontal progress bar display
- Simple graphics mode using custom characters
- Batch I2C transfer for efficiency
- Backlight control

"""


from typing import Sequence, ContextManager


class HD44780_PCF8574:
    """
    HD44780-compatible Character LCD Driver (PCF8574 I2C Backpack).
    
    Controls HD44780-compatible LCDs in 4-bit mode via PCF8574 I/O Expander.
    Supports text output, custom characters, progress bars, and graphics mode.

    Example
    -------
    ```python
        >>> from ticle.hd44780 import HD44780_PCF8574
        >>> 
        >>> # 16x2 LCD (default)
        >>> lcd = HD44780_PCF8574(scl=1, sda=0, addr=0x27)
        >>> lcd.text("Hello World!", 0, 0)
        >>> 
        >>> # 20x4 LCD
        >>> lcd = HD44780_PCF8574(scl=1, sda=0, addr=0x3F, cols=20, rows=4)
        >>> 
        >>> # Auto cleanup with context manager
        >>> with HD44780_PCF8574(scl=1, sda=0) as lcd:
        ...     lcd.text("Auto cleanup")
    ```
    """
    
    MODE_TEXT: int
    """Text mode - text(), bar() available."""
    
    MODE_GFX: int
    """Graphics mode - g_*() functions available."""
    
    def __init__(
        self,
        sda: int,
        scl: int,
        *,
        addr: int = 0x27,
        id: int = 0,
        freq: int = 400_000,
        cols: int = 16,
        rows: int = 2,
        backlight_on: bool = True,
        bl_active_high: bool = True,
        bl_mask: int = 0x08
    ) -> None:
        """
        Initialize HD44780_PCF8574 LCD driver.
        
        :param sda: I2C SDA pin number
        :param scl: I2C SCL pin number
        :param addr: PCF8574 I2C address (default: 0x27)

            - PCF8574: 0x20 ~ 0x27 (set by A0-A2)
            - PCF8574A: 0x38 ~ 0x3F (set by A0-A2)
            - Common LCD modules: 0x27 or 0x3F

        :param id: I2C bus ID (default: 0)
        :param freq: I2C clock frequency in Hz (default: 400000)
        :param cols: Number of LCD columns (default: 16). Typically 16 or 20
        :param rows: Number of LCD rows (default: 2). Typically 1, 2, or 4
        :param backlight_on: Initial backlight state (default: True)
        :param bl_active_high: Backlight active polarity (default: True)

            - True: HIGH = ON (most modules)
            - False: LOW = ON

        :param bl_mask: Backlight control bit mask (default: 0x08 = P3)

        Example
        -------
        ```python
            >>> # Default 16x2 LCD
            >>> lcd = HD44780_PCF8574(sda=0, scl=1)
            >>> 
            >>> # 20x4 LCD with different I2C address
            >>> lcd = HD44780_PCF8574(sda=0, scl=1, addr=0x3F, cols=20, rows=4)
            >>> 
            >>> # Using I2C1 bus
            >>> lcd = HD44780_PCF8574(sda=2, scl=3, id=1)
        ```
        """
        ...
    
    def __enter__(self) -> "HD44780_PCF8574":
        """
        Enter context manager.
        
        Example
        -------
        ```python
            >>> with HD44780_PCF8574(scl=1, sda=0) as lcd:
            ...     lcd.text("Hello")
        ```
        """
        ...
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit context manager - calls deinit().
        
        Example
        -------
        ```python
            >>> with HD44780_PCF8574(scl=1, sda=0) as lcd:
            ...     lcd.text("Auto cleanup")
            >>> # deinit() called automatically
        ```
        """
        ...
    
    def deinit(self) -> None:
        """
        Release LCD resources.
        
        Turns off the display and clears the screen.
        
        Example
        -------
        ```python
            >>> lcd = HD44780_PCF8574(sda=0, scl=1)
            >>> # ... use lcd ...
            >>> lcd.deinit()
        ```
        """
        ...

    def __len__(self) -> int:
        """
        Return the number of LCD rows.

        :return: Row count.

        Example
        -------
        ```python
            >>> lcd = HD44780_PCF8574(sda=0, scl=1, rows=4)
            >>> len(lcd)
            4
        ```
        """
        ...

    @property
    def cols(self) -> int:
        """
        Number of LCD columns.

        :return: Column count.

        Example
        -------
        ```python
            >>> lcd = HD44780_PCF8574(sda=0, scl=1, cols=20)
            >>> lcd.cols
            20
        ```
        """
        ...

    @property
    def rows(self) -> int:
        """
        Number of LCD rows.

        :return: Row count.

        Example
        -------
        ```python
            >>> lcd = HD44780_PCF8574(sda=0, scl=1, rows=4)
            >>> lcd.rows
            4
        ```
        """
        ...

    # ===== Backlight =====
    
    def backlight(self, on: bool = True) -> None:
        """
        Control backlight.
        
        :param on: True to turn on, False to turn off (default: True)

        Example
        -------
        ```python
            >>> lcd.backlight(True)   # Turn on backlight
            >>> lcd.backlight(False)  # Turn off backlight
        ```
        """
        ...
    
    # ===== Display Control =====
    
    def clear(self) -> None:
        """
        Clear the entire screen.
        
        Clears all text and moves cursor to (0, 0).
        
        Example
        -------
        ```python
            >>> lcd.clear()
        ```
        """
        ...
    
    def home(self) -> None:
        """
        Move cursor to home position (0, 0).
        
        Screen content is preserved.
        
        Example
        -------
        ```python
            >>> lcd.home()
        ```
        """
        ...
    
    def set_display(
        self,
        on: bool | None = None,
        cursor: bool | None = None,
        blink: bool | None = None
    ) -> None:
        """
        Configure display, cursor, and blink settings.
        
        :param on: Turn display on/off. None keeps current state
        :param cursor: Show underline cursor. None keeps current state
        :param blink: Blink at cursor position. None keeps current state

        Example
        -------
        ```python
            >>> # Turn off display only
            >>> lcd.set_display(on=False)
            >>> 
            >>> # Show cursor
            >>> lcd.set_display(cursor=True)
            >>> 
            >>> # Blinking cursor
            >>> lcd.set_display(cursor=True, blink=True)
        ```
        """
        ...
    
    @property
    def mode(self) -> int:
        """
        Current mode (MODE_TEXT or MODE_GFX).
        
        :return: MODE_TEXT (0) or MODE_GFX (1)
        
        Example
        -------
        ```python
            >>> lcd.mode
            0
        ```
        """
        ...
    
    @mode.setter
    def mode(self, n: int) -> None:
        """
        Set mode.
        
        Example
        -------
        ```python
            >>> lcd.mode = HD44780_PCF8574.MODE_GFX
        ```
        """
        ...
    
    # ===== Text Mode =====
    
    def text(
        self,
        text: str | bytes,
        x: int | None = None,
        y: int | None = None,
        *,
        wrap: bool = False
    ) -> None:
        """
        Output text.
        
        :param text: Text to output. Use '\\n' for line breaks
        :param x: Starting column (0-based). None uses current position
        :param y: Starting row (0-based). None uses current position
        :param wrap: True to auto-wrap at end of line (default: False)

        Example
        -------
        ```python
            >>> # Position specified
            >>> lcd.text("Hello", 0, 0)  # First line
            >>> lcd.text("World", 0, 1)  # Second line
            >>> 
            >>> # Continue at current position
            >>> lcd.text("ABC")
            >>> 
            >>> # Using newline character
            >>> lcd.text("Line1\\nLine2", 0, 0)
            >>> 
            >>> # Auto wrap
            >>> lcd.text("This is a very long text", 0, 0, wrap=True)
        ```
        """
        ...
    
    def scroll_left(self, n: int = 1) -> None:
        """
        Scroll screen to the left.
        
        :param n: Number of positions to scroll (default: 1)
        
        Example
        -------
        ```python
            >>> lcd.scroll_left()
            >>> lcd.scroll_left(3)
        ```
        """
        ...
    
    def scroll_right(self, n: int = 1) -> None:
        """
        Scroll screen to the right.
        
        :param n: Number of positions to scroll (default: 1)
        
        Example
        -------
        ```python
            >>> lcd.scroll_right()
            >>> lcd.scroll_right(2)
        ```
        """
        ...
    
    # ===== Custom Characters =====
    
    def create_char(self, slot: int, pattern8: Sequence[int]) -> None:
        """
        Create custom character (CGRAM).
        
        HD44780_PCF8574 can store up to 8 custom characters.
        Each character is 5x8 pixels.
        
        :param slot: Character slot number (0-7)
        :param pattern8: 8 rows of bitmap data. Each value uses lower 5 bits
        
        Note: In graphics mode, slots 0-5 are used internally.

        Example
        -------
        ```python
            >>> # Create heart symbol
            >>> heart = [
            ...     0b00000,
            ...     0b01010,
            ...     0b11111,
            ...     0b11111,
            ...     0b11111,
            ...     0b01110,
            ...     0b00100,
            ...     0b00000
            ... ]
            >>> lcd.create_char(0, heart)
            >>> 
            >>> # Output custom character (chr(0) ~ chr(7))
            >>> lcd.text(chr(0), 0, 0)
        ```
        """
        ...
    
    # ===== Progress Bar =====
    
    @property
    def bar_patterns(self) -> int:
        """
        Progress bar pattern row mask.
        
        Determines which pixel rows to draw the bar on.
        
        :return: 8-bit mask (bit7 = topmost row)
        
        Example
        -------
        ```python
            >>> lcd.bar_patterns
            255
        ```
        """
        ...
    
    @bar_patterns.setter
    def bar_patterns(self, mask: int) -> None:
        """
        Set progress bar pattern.
        
        :param mask: 8-bit mask (default: 0xFF = all rows)

        Example
        -------
        ```python
            >>> # Use only middle 4 rows
            >>> lcd.bar_patterns = 0b00111100
        ```
        """
        ...
    
    def bar(
        self,
        row: int,
        value: int,
        *,
        max_value: int = 100,
        start_col: int = 0,
        end_col: int = -1
    ) -> None:
        """
        Display progress bar.
        
        Draws a horizontal progress bar on the specified row.
        Internally uses CGRAM slots 0-5.
        
        :param row: Row number to display bar (0-based)
        :param value: Current value (0 ~ max_value)
        :param max_value: Maximum value (default: 100)
        :param start_col: Starting column (default: 0)
        :param end_col: Ending column (default: -1 = last column)
        
        :raises RuntimeError: When called in graphics mode (MODE_GFX)

        Example
        -------
        ```python
            >>> # Display 50% bar on row 0
            >>> lcd.bar(0, 50)
            >>> 
            >>> # Display 80 out of 0-100 range
            >>> lcd.bar(0, 80, max_value=100)
            >>> 
            >>> # Display bar in columns 5-15
            >>> lcd.bar(1, 75, start_col=5, end_col=15)
            >>> 
            >>> # Right-to-left bar
            >>> lcd.bar(0, 50, start_col=15, end_col=0)
        ```
        """
        ...
    
    # ===== Batch Operations =====
    
    def begin_batch(self) -> None:
        """
        Start batch mode.
        
        Queues I2C transmissions for efficient sending.
        Data is sent when end_batch() or flush() is called.
        
        Note: Using batch() context manager is recommended.
        
        Example
        -------
        ```python
            >>> lcd.begin_batch()
            >>> lcd.text("Line 1", 0, 0)
            >>> lcd.text("Line 2", 0, 1)
            >>> lcd.end_batch()
        ```
        """
        ...
    
    def end_batch(self) -> None:
        """
        End batch mode and transmit.
        
        Sends queued data over I2C.
        
        Example
        -------
        ```python
            >>> lcd.begin_batch()
            >>> lcd.text("Done")
            >>> lcd.end_batch()
        ```
        """
        ...
    
    def batch(self) -> ContextManager["HD44780_PCF8574"]:
        """
        Batch mode context manager.
        
        Collects all commands within the with block and sends them efficiently.
        
        :return: Context manager

        Example
        -------
        ```python
            >>> with lcd.batch():
            ...     lcd.text("Line 1", 0, 0)
            ...     lcd.text("Line 2", 0, 1)
            ...     lcd.text("Line 3", 0, 2)
            >>> # Data sent at block exit
        ```
        """
        ...
    
    def flush(self) -> None:
        """
        Immediately send queued data.
        
        Can explicitly flush even outside batch mode.
        
        Example
        -------
        ```python
            >>> lcd.flush()
        ```
        """
        ...
    
    # ===== Graphics Mode =====
    
    @property
    def g_width(self) -> int:
        """
        Graphics framebuffer width (pixels).
        
        cols * 5 (5 pixels per character)
        
        :return: Width (e.g., 16x2 LCD = 80 pixels)
        
        Example
        -------
        ```python
            >>> lcd.g_width
            80
        ```
        """
        ...
    
    @property
    def g_height(self) -> int:
        """
        Graphics framebuffer height (pixels).
        
        rows * 8 (8 pixels per character)
        
        :return: Height (e.g., 16x2 LCD = 16 pixels)
        
        Example
        -------
        ```python
            >>> lcd.g_height
            16
        ```
        """
        ...
    
    def g_clear(self, on: bool = False) -> None:
        """
        Clear graphics framebuffer.
        
        :param on: True to fill, False to clear (default: False)
        
        Note: Call g_update() to apply changes to screen.
        
        Example
        -------
        ```python
            >>> lcd.g_clear()        # Clear framebuffer
            >>> lcd.g_clear(on=True) # Fill framebuffer
            >>> lcd.g_update()
        ```
        """
        ...
    
    def g_point(self, x: int, y: int, on: bool = True) -> None:
        """
        Draw a point.
        
        :param x: X coordinate (0 ~ g_width-1)
        :param y: Y coordinate (0 ~ g_height-1)
        :param on: True to turn on, False to turn off (default: True)
        
        Note: Call g_update() to apply changes to screen.
        
        Example
        -------
        ```python
            >>> lcd.g_point(10, 5)
            >>> lcd.g_point(20, 8, on=False)  # Erase point
            >>> lcd.g_update()
        ```
        """
        ...
    
    def g_rect(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        fill: bool = False,
        on: bool = True
    ) -> None:
        """
        Draw a rectangle.
        
        :param x: Top-left X coordinate
        :param y: Top-left Y coordinate
        :param w: Width (pixels)
        :param h: Height (pixels)
        :param fill: True to fill, False for outline only (default: False)
        :param on: True to turn on, False to turn off (default: True)
        
        Note: Call g_update() to apply changes to screen.
        
        Example
        -------
        ```python
            >>> lcd.g_rect(0, 0, 20, 10)             # Outline
            >>> lcd.g_rect(30, 0, 20, 10, fill=True) # Filled
            >>> lcd.g_update()
        ```
        """
        ...
    
    def g_line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        on: bool = True
    ) -> None:
        """
        Draw a line (Bresenham's algorithm).
        
        :param x0: Start point X coordinate
        :param y0: Start point Y coordinate
        :param x1: End point X coordinate
        :param y1: End point Y coordinate
        :param on: True to turn on, False to turn off (default: True)
        
        Note: Call g_update() to apply changes to screen.
        
        Example
        -------
        ```python
            >>> lcd.g_line(0, 0, 79, 15)  # Diagonal line
            >>> lcd.g_line(0, 8, 79, 8)   # Horizontal line
            >>> lcd.g_update()
        ```
        """
        ...
    
    def g_update(self) -> None:
        """
        Send graphics framebuffer to LCD.
        
        Analyzes framebuffer content and generates optimal custom character
        combinations to display on screen.
        
        Internally uses all CGRAM slots 0-7.
        If more than 8 unique patterns are needed, approximates
        with the most similar patterns.
        
        :raises RuntimeError: When called in text mode (MODE_TEXT)

        Example
        -------
        ```python
            >>> lcd.mode = HD44780_PCF8574.MODE_GFX
            >>> lcd.g_clear()
            >>> lcd.g_rect(0, 0, 40, 8, fill=True)
            >>> lcd.g_line(0, 0, 79, 15)
            >>> lcd.g_update()  # Apply to screen
        ```
        """
        ...
