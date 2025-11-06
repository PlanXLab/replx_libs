"""
Terminal Visualization Library

Advanced terminal graphics and plotting library for MicroPython with ANSI escape codes.
Provides high-level plotting APIs similar to matplotlib, along with low-level pixel
rendering using Unicode Braille characters for maximum resolution in terminal environments.

Features:

- ANSI color support with TrueColor RGB and 256-color modes
- Braille-based pixel rendering (2x4 pixels per character cell)
- Matplotlib-compatible plotting API (plot, scatter, bar, hist)
- Real-time oscilloscope-style data visualization
- Cursor control and screen manipulation
- Semantic color palettes for professional UIs
- Memory-efficient differential rendering
- Micropython viper optimizations for performance

"""

import micropython


__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


class Color:
    """
    ANSI escape code library with TrueColor RGB support and terminal control.
    
    Provides comprehensive terminal formatting capabilities including 24-bit RGB colors,
    cursor positioning, screen manipulation, and text styling attributes. All methods are
    static and return ANSI escape sequence strings ready for terminal output.
    
    The Color class supports both foreground and background coloring through:
    - Dynamic RGB color generation (rgb, hex_color, gray methods)
    - Pre-defined semantic color constants (FG and BG nested classes)
    - Terminal cursor control and positioning
    - Screen and line clearing operations
    - Text styling attributes (bold, italic, underline, etc.)
    
    Example
    -------
    ```python
    >>> # Using predefined foreground colors
    >>> print(Color.FG.RED + "Error message" + Color.RESET)
    >>> print(Color.FG.GREEN + "Success" + Color.RESET)
    >>> print(Color.FG.YELLOW + "Warning" + Color.RESET)
    >>> print(Color.FG.BLUE + "Information" + Color.RESET)
    >>> 
    >>> # Using predefined background colors
    >>> print(Color.BG.BLACK + Color.FG.WHITE + " Inverted text " + Color.RESET)
    >>> print(Color.BG.RED + Color.FG.BRIGHT_WHITE + " Alert! " + Color.RESET)
    >>> 
    >>> # Semantic colors for UI design
    >>> print(Color.FG.PRIMARY + "Primary action" + Color.RESET)
    >>> print(Color.FG.SUCCESS + "✓ Operation successful" + Color.RESET)
    >>> print(Color.FG.WARNING + "⚠ Check configuration" + Color.RESET)
    >>> print(Color.FG.DANGER + "✗ Critical error" + Color.RESET)
    >>> print(Color.FG.INFO + "ℹ Additional information" + Color.RESET)
    >>> print(Color.FG.MUTED + "Secondary text" + Color.RESET)
    >>> 
    >>> # Text styling attributes
    >>> print(Color.BOLD + "Bold text" + Color.RESET)
    >>> print(Color.ITALIC + "Italic text" + Color.RESET)
    >>> print(Color.UNDERLINE + "Underlined text" + Color.RESET)
    >>> print(Color.STRIKE + "Strikethrough text" + Color.RESET)
    >>> print(Color.DIM + "Dimmed text" + Color.RESET)
    >>> print(Color.REVERSE + "Reversed colors" + Color.RESET)
    >>> 
    >>> # Combining colors and styles
    >>> print(Color.BOLD + Color.FG.GREEN + "Bold green text" + Color.RESET)
    >>> print(Color.UNDERLINE + Color.FG.BLUE + "Underlined blue text" + Color.RESET)
    >>> print(Color.BG.YELLOW + Color.FG.BLACK + Color.BOLD + " Highlight " + Color.RESET)
    >>> 
    >>> # Building colored status indicators
    >>> status_ok = Color.FG.SUCCESS + "●" + Color.RESET + " Service running"
    >>> status_err = Color.FG.DANGER + "●" + Color.RESET + " Service stopped"
    >>> status_warn = Color.FG.WARNING + "●" + Color.RESET + " Service degraded"
    >>> print(status_ok)
    >>> print(status_err)
    >>> print(status_warn)
    >>> 
    >>> # Creating a colored progress bar
    >>> def progress_bar(percent, width=40):
    ...     filled = int(width * percent / 100)
    ...     bar = Color.FG.GREEN + "█" * filled + Color.RESET
    ...     bar += Color.FG.MUTED + "░" * (width - filled) + Color.RESET
    ...     return f"{bar} {percent}%"
    >>> print(progress_bar(75))
    >>> 
    >>> # Colored table output
    >>> header = Color.BOLD + Color.FG.CYAN
    >>> data = Color.FG.WHITE
    >>> print(header + "Name        Status      Value" + Color.RESET)
    >>> print(data + "Server-1    " + Color.FG.SUCCESS + "Running" + data + "     99.5%" + Color.RESET)
    >>> print(data + "Server-2    " + Color.FG.DANGER + "Stopped" + data + "     0.0%" + Color.RESET)
    ```
    """
    
    @staticmethod
    def rgb(r: int, g: int, b: int, fg: bool = True) -> str:
        """
        Generate TrueColor (24-bit) RGB ANSI escape sequence.
        
        Creates an ANSI escape code for true color support in modern terminals.
        Each color component can range from 0 (darkest) to 255 (brightest),
        providing 16.7 million possible colors.
        
        :param r: Red component intensity (0-255)
        :param g: Green component intensity (0-255)
        :param b: Blue component intensity (0-255)
        :param fg: If True, applies to foreground (text color); if False, applies to background
        :return: ANSI escape sequence string for the specified RGB color
        
        :raises ValueError: If any color component is outside the valid 0-255 range
        
        Example
        -------
        ```python
        >>> # Basic color usage
        >>> print(Color.rgb(255, 0, 0) + "Red text" + Color.RESET)
        >>> print(Color.rgb(0, 200, 100, fg=False) + "Green background" + Color.RESET)
        >>> 
        >>> # Creating custom color schemes
        >>> brand_primary = Color.rgb(72, 133, 237)
        >>> brand_accent = Color.rgb(255, 171, 64)
        >>> print(brand_primary + "Logo" + Color.RESET + brand_accent + " Tagline" + Color.RESET)
        >>> 
        >>> # Gradient effect
        >>> for i in range(256):
        ...     print(Color.rgb(i, 0, 255-i) + "█", end="")
        >>> print(Color.RESET)
        ```
        """
    
    @staticmethod
    def hex_color(code: str, fg: bool = True) -> str:
        """
        Convert hexadecimal color code to ANSI escape sequence.
        
        Accepts standard web hex color formats and converts them to terminal
        TrueColor ANSI codes. Supports both short (#RGB) and full (#RRGGBB)
        notation, with or without the leading hash symbol.
        
        :param code: Hex color code in format "#RGB", "#RRGGBB", "RGB", or "RRGGBB"
        :param fg: If True, applies to foreground (text color); if False, applies to background
        :return: ANSI escape sequence string for the specified color
        
        :raises ValueError: If hex format is invalid or contains non-hex characters
        
        Example
        -------
        ```python
        >>> # Web color notation
        >>> print(Color.hex_color("#FF5733") + "Coral text" + Color.RESET)
        >>> print(Color.hex_color("3498DB", fg=False) + "Blue background" + Color.RESET)
        >>> 
        >>> # Short notation (expanded automatically)
        >>> print(Color.hex_color("#F00") + "Red" + Color.RESET)  # Expands to #FF0000
        >>> 
        >>> # Reading colors from configuration
        >>> theme_colors = {"primary": "#2C3E50", "accent": "#E74C3C"}
        >>> for name, hex_code in theme_colors.items():
        ...     print(Color.hex_color(hex_code) + name + Color.RESET)
        ```
        """
    
    @staticmethod
    def gray(level: int, fg: bool = True) -> str:
        """
        Generate grayscale ANSI escape sequence.
        
        Creates a gray color by setting all RGB components to the same value.
        This is a convenience method for creating monochrome colors without
        specifying all three color components separately.
        
        :param level: Gray intensity level where 0 is black, 255 is white, and values in between are shades of gray
        :param fg: If True, applies to foreground (text color); if False, applies to background
        :return: ANSI escape sequence string for the specified gray level
        
        :raises ValueError: If level is outside the valid 0-255 range
        
        Example
        -------
        ```python
        >>> # Grayscale gradient
        >>> for level in range(0, 256, 16):
        ...     print(Color.gray(level) + "█" * 4, end="")
        >>> print(Color.RESET)
        >>> 
        >>> # Low-contrast UI elements
        >>> print(Color.gray(64, fg=False) + Color.gray(192) + " Subtle label " + Color.RESET)
        >>> 
        >>> # Creating disabled/muted text
        >>> enabled_text = Color.FG.WHITE + "Active item" + Color.RESET
        >>> disabled_text = Color.gray(128) + "Disabled item" + Color.RESET
        ```
        """
    
    class FG:
        """Foreground color constants."""
        BLACK: str
        RED: str
        GREEN: str
        YELLOW: str
        BLUE: str
        MAGENTA: str
        CYAN: str
        WHITE: str
        BRIGHT_BLACK: str
        BRIGHT_RED: str
        BRIGHT_GREEN: str
        BRIGHT_YELLOW: str
        BRIGHT_BLUE: str
        BRIGHT_MAGENTA: str
        BRIGHT_CYAN: str
        BRIGHT_WHITE: str
        PRIMARY: str
        SUCCESS: str
        WARNING: str
        DANGER: str
        INFO: str
        MUTED: str
        SURFACE: str
    
    class BG:
        """Background color constants."""
        BLACK: str
        RED: str
        GREEN: str
        YELLOW: str
        BLUE: str
        MAGENTA: str
        CYAN: str
        WHITE: str
        BRIGHT_BLACK: str
        BRIGHT_RED: str
        BRIGHT_GREEN: str
        BRIGHT_YELLOW: str
        BRIGHT_BLUE: str
        BRIGHT_MAGENTA: str
        BRIGHT_CYAN: str
        BRIGHT_WHITE: str
        PRIMARY: str
        SUCCESS: str
        WARNING: str
        DANGER: str
        INFO: str
        MUTED: str
        SURFACE: str
    
    RESET: str
    BOLD: str
    DIM: str
    ITALIC: str
    UNDERLINE: str
    REVERSE: str
    HIDDEN: str
    STRIKE: str
    
    @staticmethod
    def cursor_up(n: int = 1) -> str:
        """
        Move cursor up by n lines.
        
        Moves the cursor vertically upward without changing the column position.
        The cursor will not move above the top of the scrolling region.
        
        :param n: Number of lines to move up (default: 1)
        :return: ANSI escape sequence string for cursor movement
        
        Example
        -------
        ```python
        >>> # Move up and overwrite previous line
        >>> print("Line 1")
        >>> print("Line 2")
        >>> print(Color.cursor_up(1) + Color.clear_line() + "Line 2 replaced")
        >>> 
        >>> # Create simple progress indicator
        >>> for i in range(5):
        ...     print(f"Progress: {i*20}%")
        ...     time.sleep(0.5)
        ...     print(Color.cursor_up(1), end="")
        ```
        """
    
    @staticmethod
    def cursor_down(n: int = 1) -> str:
        """
        Move cursor down by n lines.
        
        Moves the cursor vertically downward without changing the column position.
        The cursor will not move below the bottom of the scrolling region.
        
        :param n: Number of lines to move down (default: 1)
        :return: ANSI escape sequence string for cursor movement
        
        Example
        -------
        ```python
        >>> # Leave space and return
        >>> print("Header")
        >>> print(Color.cursor_down(2))
        >>> print("Body (with gap above)")
        ```
        """
    
    @staticmethod
    def cursor_right(n: int = 1) -> str:
        """
        Move cursor right by n columns.
        
        Moves the cursor horizontally to the right without changing the row position.
        The cursor will stop at the right edge of the screen.
        
        :param n: Number of columns to move right (default: 1)
        :return: ANSI escape sequence string for cursor movement
        
        Example
        -------
        ```python
        >>> # Create indented text
        >>> print(Color.cursor_right(4) + "Indented text")
        >>> 
        >>> # Align columns manually
        >>> print("Name:" + Color.cursor_right(10) + "Value")
        ```
        """
    
    @staticmethod
    def cursor_left(n: int = 1) -> str:
        """
        Move cursor left by n columns.
        
        Moves the cursor horizontally to the left without changing the row position.
        The cursor will stop at the left edge of the screen.
        
        :param n: Number of columns to move left (default: 1)
        :return: ANSI escape sequence string for cursor movement
        
        Example
        -------
        ```python
        >>> # Overwrite characters
        >>> print("Hello World", end="")
        >>> print(Color.cursor_left(5) + "There")
        ```
        """
    
    @staticmethod
    def cursor_to(row: int, col: int) -> str:
        """
        Move cursor to absolute position.
        
        Positions the cursor at the specified row and column coordinates.
        Both coordinates are 1-indexed (top-left corner is 1,1).
        
        :param row: Target row number (1-indexed)
        :param col: Target column number (1-indexed)
        :return: ANSI escape sequence string for cursor positioning
        
        Example
        -------
        ```python
        >>> # Draw at specific positions
        >>> print(Color.cursor_to(5, 10) + "X")
        >>> print(Color.cursor_to(10, 20) + "O")
        >>> 
        >>> # Create simple menu
        >>> print(Color.cursor_to(1, 1) + "╔════ Menu ════╗")
        >>> print(Color.cursor_to(2, 1) + "║ 1. Option A ║")
        >>> print(Color.cursor_to(3, 1) + "║ 2. Option B ║")
        >>> print(Color.cursor_to(4, 1) + "╚══════════════╝")
        ```
        """
    
    @staticmethod
    def cursor_home() -> str:
        """
        Move cursor to home position (1,1).
        
        Positions the cursor at the top-left corner of the screen.
        Equivalent to cursor_to(1, 1).
        
        :return: ANSI escape sequence string for cursor home positioning
        
        Example
        -------
        ```python
        >>> # Reset cursor to start
        >>> print(Color.cursor_home() + "Back to top-left")
        >>> 
        >>> # Clear and restart display
        >>> print(Color.cursor_home() + Color.erase_screen())
        ```
        """
    
    @staticmethod
    def cursor_col(n: int) -> str:
        """
        Move cursor to specific column.
        
        Moves the cursor to the specified column on the current line.
        The row position remains unchanged.
        
        :param n: Target column number (1-indexed)
        :return: ANSI escape sequence string for horizontal positioning
        
        Example
        -------
        ```python
        >>> # Align output at specific column
        >>> print("Label:" + Color.cursor_col(20) + "Value")
        >>> print("Another:" + Color.cursor_col(20) + "123")
        ```
        """
    
    @staticmethod
    def cursor_save() -> str:
        """
        Save current cursor position.
        
        Saves the current cursor position to be restored later with cursor_restore().
        Most terminals support only one saved position at a time.
        
        :return: ANSI escape sequence string to save cursor position
        
        Example
        -------
        ```python
        >>> # Save position, draw elsewhere, restore
        >>> print("Original position" + Color.cursor_save())
        >>> print(Color.cursor_to(10, 1) + "Temporary message")
        >>> time.sleep(1)
        >>> print(Color.cursor_restore() + " continues here")
        ```
        """
    
    @staticmethod
    def cursor_restore() -> str:
        """
        Restore previously saved cursor position.
        
        Restores the cursor to the position saved by the last cursor_save() call.
        If no position was saved, behavior is terminal-dependent.
        
        :return: ANSI escape sequence string to restore cursor position
        
        Example
        -------
        ```python
        >>> # Status line pattern
        >>> print(Color.cursor_save())
        >>> print(Color.cursor_to(1, 1) + "Status: Running...")
        >>> process_data()
        >>> print(Color.cursor_restore())
        ```
        """
    
    @staticmethod
    def cursor_hide() -> str:
        """
        Hide the cursor.
        
        Makes the cursor invisible. Useful for animations or clean UI displays
        where the blinking cursor would be distracting.
        
        :return: ANSI escape sequence string to hide cursor
        
        Example
        -------
        ```python
        >>> # Hide cursor during animation
        >>> print(Color.cursor_hide())
        >>> for frame in animation_frames:
        ...     draw_frame(frame)
        ...     time.sleep(0.1)
        >>> print(Color.cursor_show())
        ```
        """
    
    @staticmethod
    def cursor_show() -> str:
        """
        Show the cursor.
        
        Makes the cursor visible again after it was hidden with cursor_hide().
        Should always be called after hiding the cursor to restore normal behavior.
        
        :return: ANSI escape sequence string to show cursor
        
        Example
        -------
        ```python
        >>> # Always restore cursor visibility
        >>> try:
        ...     print(Color.cursor_hide())
        ...     draw_complex_ui()
        >>> finally:
        ...     print(Color.cursor_show())
        ```
        """
    
    @staticmethod
    def cursor_next_line(n: int = 1) -> str:
        """
        Move to beginning of line n rows down.
        
        Moves the cursor down n lines and positions it at column 1.
        Combines cursor_down(n) with cursor_col(1).
        
        :param n: Number of lines to move down (default: 1)
        :return: ANSI escape sequence string for line navigation
        
        Example
        -------
        ```python
        >>> # Start new sections
        >>> print("Section 1")
        >>> print(Color.cursor_next_line(2) + "Section 2 (with gap)")
        ```
        """
    
    @staticmethod
    def cursor_prev_line(n: int = 1) -> str:
        """
        Move to beginning of line n rows up.
        
        Moves the cursor up n lines and positions it at column 1.
        Combines cursor_up(n) with cursor_col(1).
        
        :param n: Number of lines to move up (default: 1)
        :return: ANSI escape sequence string for line navigation
        
        Example
        -------
        ```python
        >>> # Update previous lines
        >>> print("Line 1")
        >>> print("Line 2")
        >>> print(Color.cursor_prev_line(1) + "Line 2 updated")
        ```
        """
    
    @staticmethod
    def erase_screen(mode: int = 2) -> str:
        """
        Erase screen content with different modes.
        
        Clears portions of the screen based on the mode parameter:
        - Mode 0: Clear from cursor to end of screen
        - Mode 1: Clear from start of screen to cursor
        - Mode 2: Clear entire screen (default)
        - Mode 3: Clear entire screen and scrollback buffer
        
        :param mode: Erase mode (0, 1, 2, or 3) - default is 2 (entire screen)
        :return: ANSI escape sequence string for screen erasure
        
        :raises ValueError: If mode is not 0, 1, 2, or 3
        
        Example
        -------
        ```python
        >>> # Clear everything
        >>> print(Color.erase_screen(2))
        >>> 
        >>> # Clear from cursor down (preserve header)
        >>> print_header()
        >>> print(Color.cursor_to(5, 1))
        >>> print(Color.erase_screen(0))  # Clear from row 5 downward
        >>> 
        >>> # Full reset including scrollback
        >>> print(Color.cursor_home() + Color.erase_screen(3))
        ```
        """
    
    @staticmethod
    def erase_line(mode: int = 2) -> str:
        """
        Erase line content with different modes.
        
        Clears portions of the current line based on the mode parameter:
        - Mode 0: Clear from cursor to end of line
        - Mode 1: Clear from start of line to cursor
        - Mode 2: Clear entire line (default)
        
        :param mode: Erase mode (0, 1, or 2) - default is 2 (entire line)
        :return: ANSI escape sequence string for line erasure
        
        :raises ValueError: If mode is not 0, 1, or 2
        
        Example
        -------
        ```python
        >>> # Clear entire line
        >>> print("Old content")
        >>> print(Color.cursor_up(1) + Color.erase_line() + "New content")
        >>> 
        >>> # Clear to end of line (status bar pattern)
        >>> print("Status: ", end="")
        >>> print("Loading..." + Color.erase_line(0))
        ```
        """
    
    @staticmethod
    def clear_screen() -> str:
        """
        Clear entire screen and move cursor to home position.
        
        Convenience method that combines erase_screen(2) with cursor_home().
        Clears all content and positions the cursor at the top-left corner.
        
        :return: ANSI escape sequence string to clear screen and reset cursor
        
        Example
        -------
        ```python
        >>> # Full screen reset
        >>> print(Color.clear_screen())
        >>> print("Fresh start")
        >>> 
        >>> # Application restart
        >>> def reset_ui():
        ...     print(Color.clear_screen())
        ...     draw_header()
        ...     draw_menu()
        ```
        """
    
    @staticmethod
    def clear_line() -> str:
        """
        Clear entire line and move cursor to beginning.
        
        Convenience method that combines erase_line(2) with cursor_col(1).
        Clears the entire current line and positions the cursor at column 1.
        
        :return: ANSI escape sequence string to clear line and reset cursor
        
        Example
        -------
        ```python
        >>> # Update status line
        >>> print("Processing...", end="", flush=True)
        >>> process_data()
        >>> print(Color.cursor_up(1) + Color.clear_line() + "Done!")
        >>> 
        >>> # Progress indicator
        >>> for i in range(100):
        ...     print(Color.clear_line() + f"Progress: {i+1}%", end="", flush=True)
        ...     time.sleep(0.1)
        ```
        """


class Canvas:
    """
    Ultra-lightweight ANSI Braille pixel rendering engine.
    
    Provides high-resolution terminal graphics using Unicode Braille characters,
    where each character represents a 2×4 pixel grid. This enables detailed
    graphics rendering in standard terminals with minimal overhead.
    
    The Canvas uses Braille patterns (Unicode U+2800-U+28FF) to achieve high
    pixel density. Each terminal character cell displays 2×4 pixels, providing
    effective resolution of (cols × 2) × (rows × 4) pixels.
    
    Key features:
    - Differential rendering: Only updates changed regions for efficiency
    - TrueColor (24-bit RGB) and 256-color palette support
    - Optional row downsampling for displays with limited height
    - Optimized with @micropython.viper decorators for performance
    - Automatic terminal buffer management (alternate screen)
    """
    
    cols: int
    """Number of terminal character columns."""
    
    rows: int
    """Number of terminal character rows."""
    
    default_rgb: tuple[int, int, int] | int
    """Default color for cleared pixels."""
    
    color_mode: str
    """Color mode: 'truecolor' (24-bit) or '256' (8-bit palette)."""

    def __init__(self, cols: int, rows: int,
                 default_rgb: tuple[int, int, int] | int = (220, 220, 220),
                 color_mode: str = 'truecolor',
                 term_rows_cap: int | None = None) -> None:
        """
        Initialize canvas and enter alternate screen buffer.
        
        Creates a new canvas with specified dimensions and automatically
        switches to the terminal's alternate screen buffer. The cursor
        is hidden during canvas operations.
        
        :param cols: Number of terminal character columns (width = cols × 2 pixels)
        :param rows: Number of terminal character rows (height = rows × 4 pixels)
        :param default_rgb: Default pixel color as (r, g, b) tuple or 0xRRGGBB int (default: (220,220,220))
        :param color_mode: Color rendering mode - 'truecolor' for 24-bit RGB or '256' for 8-bit palette (default: 'truecolor')
        :param term_rows_cap: Optional row limit for automatic downsampling when terminal height is constrained (default: None)
        
        Example
        -------
        ```python
        >>> # Basic canvas creation
        >>> cv = Canvas(40, 20)  # 80×80 pixel canvas
        >>> 
        >>> # Canvas with custom default color
        >>> cv = Canvas(30, 15, default_rgb=(50, 50, 50))  # Dark gray background
        >>> 
        >>> # Using 256-color mode for compatibility
        >>> cv = Canvas(40, 20, color_mode='256')
        >>> 
        >>> # With row downsampling for small terminals
        >>> cv = Canvas(40, 30, term_rows_cap=20)  # Render as 20 rows if needed
        ```
        """
    
    @property
    def width(self) -> int:
        """
        Canvas width in pixels.
        
        Returns the effective pixel width, which is twice the number of
        character columns since each Braille character represents 2 pixels
        horizontally.
        
        :return: Pixel width (cols × 2)
        
        Example
        -------
        ```python
        >>> cv = Canvas(40, 20)
        >>> print(cv.width)  # Output: 80
        >>> 
        >>> # Center pixel calculation
        >>> center_x = cv.width // 2
        >>> cv.set_px(center_x, cv.height // 2, 0xFF0000)
        ```
        """
    
    @property
    def height(self) -> int:
        """
        Canvas height in pixels.
        
        Returns the effective pixel height, which is four times the number of
        character rows since each Braille character represents 4 pixels
        vertically.
        
        :return: Pixel height (rows × 4)
        
        Example
        -------
        ```python
        >>> cv = Canvas(40, 20)
        >>> print(cv.height)  # Output: 80
        >>> 
        >>> # Draw horizontal line at center
        >>> y_center = cv.height // 2
        >>> for x in range(cv.width):
        ...     cv.set_px(x, y_center, 0x00FF00)
        ```
        """
    
    def begin(self) -> None:
        """
        Clear canvas to default state.
        
        Resets all pixels to the cleared state (using default_rgb color).
        Call this before starting a new frame or to clear the canvas.
        Does not automatically render - call render() to display changes.
        
        Example
        -------
        ```python
        >>> cv = Canvas(40, 20)
        >>> cv.begin()
        >>> 
        >>> # Draw something
        >>> for x in range(cv.width):
        ...     cv.set_px(x, cv.height // 2, 0xFF0000)
        >>> cv.render()
        >>> 
        >>> # Clear and draw new frame
        >>> cv.begin()  # Clear previous frame
        >>> for x in range(0, cv.width, 2):
        ...     cv.set_px(x, cv.height // 2, 0x00FF00)
        >>> cv.render()
        ```
        """
    
    def end(self) -> None:
        """
        Restore terminal state and exit alternate screen buffer.
        
        Switches back to the main screen buffer and makes the cursor visible
        again. Should always be called when finished with the canvas to
        properly restore terminal state.
        
        Example
        -------
        ```python
        >>> cv = Canvas(40, 20)
        >>> try:
        ...     cv.begin()
        ...     # Draw graphics
        ...     cv.render()
        ...     time.sleep(2)
        >>> finally:
        ...     cv.end()  # Always restore terminal
        >>> 
        >>> # Context manager pattern (if implemented)
        >>> cv = Canvas(40, 20)
        >>> cv.begin()
        >>> draw_graphics(cv)
        >>> cv.end()
        ```
        """
    
    @micropython.viper
    def set_px(self, x: int, y: int, rgb: int) -> None:
        """
        Set pixel at coordinates (x, y) with specified color.
        
        Turns on the pixel at the given coordinates and assigns it a color.
        The pixel will be visible after the next render() call. Coordinates
        are 0-indexed from the top-left corner.
        
        This method is optimized with @micropython.viper for high performance.
        Out-of-bounds coordinates are silently ignored.
        
        :param x: X coordinate (0 to width-1, increases rightward)
        :param y: Y coordinate (0 to height-1, increases downward)
        :param rgb: Packed 24-bit RGB color value (0xRRGGBB format)
        
        Example
        -------
        ```python
        >>> cv = Canvas(40, 20)
        >>> cv.begin()
        >>> 
        >>> # Set individual pixels
        >>> cv.set_px(10, 10, 0xFF0000)  # Red pixel at (10, 10)
        >>> cv.set_px(20, 15, 0x00FF00)  # Green pixel at (20, 15)
        >>> cv.set_px(30, 20, 0x0000FF)  # Blue pixel at (30, 20)
        >>> 
        >>> # Draw a line
        >>> for x in range(cv.width):
        ...     cv.set_px(x, cv.height // 2, 0xFFFFFF)  # White horizontal line
        >>> 
        >>> # Draw a gradient
        >>> for x in range(cv.width):
        ...     red = int(255 * x / cv.width)
        ...     color = (red << 16) | 0x0000FF  # Red to magenta
        ...     cv.set_px(x, 30, color)
        >>> 
        >>> cv.render()
        ```
        """
    
    @micropython.viper
    def clr_px(self, x: int, y: int) -> None:
        """
        Clear pixel at coordinates (x, y).
        
        Turns off the pixel at the given coordinates, making it display the
        default background color. Changes take effect after the next render() call.
        
        This method is optimized with @micropython.viper for high performance.
        Out-of-bounds coordinates are silently ignored.
        
        :param x: X coordinate (0 to width-1)
        :param y: Y coordinate (0 to height-1)
        
        Example
        -------
        ```python
        >>> cv = Canvas(40, 20)
        >>> cv.begin()
        >>> 
        >>> # Fill with pixels
        >>> for x in range(cv.width):
        ...     for y in range(cv.height):
        ...         cv.set_px(x, y, 0xFF0000)
        >>> 
        >>> # Erase some pixels to create pattern
        >>> for x in range(0, cv.width, 4):
        ...     for y in range(cv.height):
        ...         cv.clr_px(x, y)  # Create vertical stripes
        >>> 
        >>> cv.render()
        ```
        """
    
    @micropython.native
    def render(self, ox: int = 1, oy: int = 1) -> None:
        """
        Render canvas to terminal with differential updates.
        
        Outputs only the regions that have changed since the last render,
        minimizing terminal I/O for efficient updates. The rendering uses
        the alternate screen buffer to avoid scrolling.
        
        Coordinates ox and oy specify where the canvas appears in the terminal
        (1-indexed following terminal conventions, where 1,1 is top-left).
        
        This method is optimized with @micropython.native for performance.
        
        :param ox: Terminal column offset for canvas origin (1-indexed, default: 1)
        :param oy: Terminal row offset for canvas origin (1-indexed, default: 1)
        
        Example
        -------
        ```python
        >>> cv = Canvas(40, 20)
        >>> cv.begin()
        >>> 
        >>> # Render at default position (top-left)
        >>> cv.set_px(10, 10, 0xFF0000)
        >>> cv.render()  # Renders at (1, 1)
        >>> 
        >>> # Render with offset (e.g., leaving room for header)
        >>> cv.set_px(20, 15, 0x00FF00)
        >>> cv.render(ox=1, oy=3)  # Renders starting at row 3
        >>> 
        >>> # Animation loop with efficient differential updates
        >>> for frame in range(100):
        ...     # Only update changed pixels
        ...     x = frame % cv.width
        ...     cv.set_px(x, cv.height // 2, 0x0000FF)
        ...     cv.render()  # Only changed region is re-drawn
        ...     time.sleep(0.02)
        ```
        """
    
    def sgr(self, rgb: int | tuple[int, int, int] | None) -> str:
        """
        Generate ANSI SGR (Select Graphic Rendition) color sequence.
        
        Converts an RGB color value to the appropriate ANSI escape sequence
        based on the canvas color_mode ('truecolor' or '256').
        
        :param rgb: RGB color as packed int (0xRRGGBB), tuple (r,g,b), or None for default
        :return: ANSI escape sequence string for setting foreground color
        
        Example
        -------
        ```python
        >>> cv = Canvas(40, 20)
        >>> 
        >>> # Get color codes
        >>> red_seq = cv.sgr(0xFF0000)
        >>> print(red_seq + "This text is red" + Color.RESET)
        >>> 
        >>> # Using tuple format
        >>> green_seq = cv.sgr((0, 255, 0))
        >>> print(green_seq + "This text is green" + Color.RESET)
        ```
        """
    
    @staticmethod
    def pack_rgb(rgb: int | tuple[int, int, int]) -> int:
        """
        Pack RGB color into 24-bit integer format.
        
        Converts color from tuple (r, g, b) or validates integer format to
        ensure proper 24-bit RGB representation (0xRRGGBB).
        
        :param rgb: RGB color as tuple (r, g, b) or packed int
        :return: Packed 24-bit RGB value (0xRRGGBB)
        
        Example
        -------
        ```python
        >>> # Pack tuple to int
        >>> color = Canvas.pack_rgb((255, 128, 64))
        >>> print(hex(color))  # Output: 0xff8040
        >>> 
        >>> # Validate/normalize int
        >>> color = Canvas.pack_rgb(0xFF8040)
        >>> print(hex(color))  # Output: 0xff8040
        >>> 
        >>> # Use in drawing
        >>> cv = Canvas(40, 20)
        >>> cv.begin()
        >>> rgb_tuple = (200, 100, 50)
        >>> cv.set_px(10, 10, Canvas.pack_rgb(rgb_tuple))
        ```
        """


class Plot:
    """
    Matplotlib-compatible terminal plotting library.
    
    High-level plotting API for creating charts and visualizations in the terminal
    using a familiar matplotlib-style interface. Renders plots on a Canvas using
    Braille characters for high-resolution graphics.
    
    Features:
    - Line plots, scatter plots, bar charts, histograms
    - Geometric primitives (lines, circles)
    - Automatic axis scaling and labeling
    - Customizable grid, ticks, and legends
    - Color cycling for multiple datasets
    - Text annotations and labels
    
    The Plot class manages coordinate transformations between data space and
    pixel space, handles rendering of various plot types, and provides extensive
    customization options similar to matplotlib.
    
    """
    
    cv: Canvas
    """Reference to the underlying Canvas instance."""
    
    xmin: float
    """Minimum X-axis value."""
    
    xmax: float
    """Maximum X-axis value."""
    
    ymin: float
    """Minimum Y-axis value."""
    
    ymax: float
    """Maximum Y-axis value."""
    
    def __init__(self, canvas: Canvas,
                 region_px: tuple[int, int, int, int] | None = None,
                 xlim: tuple[float, float] = (0.0, 1.0),
                 ylim: tuple[float, float] = (0.0, 1.0),
                 color_cycle: list[tuple[int, int, int]] | None = None) -> None:
        """
        Initialize plot with canvas and configuration.
        
        Creates a plotting interface on the specified canvas with configurable
        viewport region and axis limits. The viewport defines the pixel region
        used for plotting, leaving room for labels and legends.
        
        :param canvas: Canvas instance for rendering graphics
        :param region_px: Plot region as (x, y, width, height) in pixels. If None, auto-calculated with margins (default: None)
        :param xlim: Initial X-axis range as (min, max) tuple (default: (0.0, 1.0))
        :param ylim: Initial Y-axis range as (min, max) tuple (default: (0.0, 1.0))
        :param color_cycle: List of RGB tuples for auto-coloring multiple datasets. If None, uses default palette (default: None)
        
        Example
        -------
        ```python
        >>> # Basic plot setup
        >>> cv = Canvas(60, 30)
        >>> plt = Plot(cv)
        >>> 
        >>> # Custom axis ranges
        >>> plt = Plot(cv, xlim=(0, 100), ylim=(-50, 50))
        >>> 
        >>> # Custom viewport (leave space for side panel)
        >>> plt = Plot(cv, region_px=(10, 5, 100, 100))
        >>> 
        >>> # Custom color palette
        >>> colors = [(255,0,0), (0,255,0), (0,0,255)]
        >>> plt = Plot(cv, color_cycle=colors)
        ```
        """
    
    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        """
        Set plot viewport region in pixel coordinates.
        
        Defines the rectangular region of the canvas used for plotting.
        Coordinates outside this region are clipped. The viewport is
        automatically constrained to fit within the canvas boundaries.
        
        :param x: Left edge of viewport in pixels (0-indexed)
        :param y: Top edge of viewport in pixels (0-indexed)
        :param width: Viewport width in pixels
        :param height: Viewport height in pixels
        
        Example
        -------
        ```python
        >>> cv = Canvas(80, 40)
        >>> plt = Plot(cv)
        >>> 
        >>> # Set custom viewport leaving margins
        >>> plt.set_viewport(10, 10, 140, 140)
        >>> 
        >>> # Create subplot-like layout
        >>> plt1 = Plot(cv, region_px=(5, 5, 70, 70))
        >>> plt2 = Plot(cv, region_px=(85, 5, 70, 70))
        ```
        """
    
    def set_xlim(self, xmin: float, xmax: float) -> None:
        """
        Set X-axis limits explicitly.
        
        Defines the range of X values displayed in the plot. Data outside
        this range will be clipped. Automatically updates internal scaling.
        
        :param xmin: Minimum X value
        :param xmax: Maximum X value
        
        Example
        -------
        ```python
        >>> plt = Plot(cv)
        >>> plt.set_xlim(0, 100)
        >>> 
        >>> # Zoom into specific region
        >>> plt.set_xlim(25, 75)
        ```
        """
    
    def set_ylim(self, ymin: float, ymax: float) -> None:
        """
        Set Y-axis limits explicitly.
        
        Defines the range of Y values displayed in the plot. Data outside
        this range will be clipped. Automatically updates internal scaling.
        
        :param ymin: Minimum Y value
        :param ymax: Maximum Y value
        
        Example
        -------
        ```python
        >>> plt = Plot(cv)
        >>> plt.set_ylim(-10, 10)
        >>> 
        >>> # Adjust range based on data
        >>> data_max = max(y_values)
        >>> plt.set_ylim(0, data_max * 1.1)  # 10% margin
        ```
        """
    
    def xlim(self, *args) -> tuple[float, float] | None:
        """
        Get or set X-axis limits (matplotlib-style interface).
        
        When called without arguments, returns current X limits.
        When called with arguments, sets new X limits.
        
        :param args: If empty, returns limits. If provided, sets limits as (xmin, xmax) or xmin, xmax
        :return: Current X-axis limits as (xmin, xmax) tuple when getting, None when setting
        
        Example
        -------
        ```python
        >>> plt = Plot(cv)
        >>> 
        >>> # Get current limits
        >>> xmin, xmax = plt.xlim()
        >>> 
        >>> # Set limits (tuple)
        >>> plt.xlim((0, 100))
        >>> 
        >>> # Set limits (separate args)
        >>> plt.xlim(0, 100)
        ```
        """
    
    def ylim(self, *args) -> tuple[float, float] | None:
        """
        Get or set Y-axis limits (matplotlib-style interface).
        
        When called without arguments, returns current Y limits.
        When called with arguments, sets new Y limits.
        
        :param args: If empty, returns limits. If provided, sets limits as (ymin, ymax) or ymin, ymax
        :return: Current Y-axis limits as (ymin, ymax) tuple when getting, None when setting
        
        Example
        -------
        ```python
        >>> plt = Plot(cv)
        >>> 
        >>> # Get current limits
        >>> ymin, ymax = plt.ylim()
        >>> 
        >>> # Set limits
        >>> plt.ylim(-1, 1)
        >>> 
        >>> # Auto-scale to data with margin
        >>> data_range = max(data) - min(data)
        >>> plt.ylim(min(data) - 0.1*data_range, max(data) + 0.1*data_range)
        ```
        """
    
    def title(self, s: str | None = None, color: tuple[int, int, int] = (230, 230, 230)) -> None:
        """
        Set plot title text and color.
        
        Displays centered title text above the plot area. The title is
        rendered during show() call.
        
        :param s: Title text string. If None, returns current title (default: None)
        :param color: Text color as RGB tuple (default: (230, 230, 230))
        
        Example
        -------
        ```python
        >>> plt = Plot(cv)
        >>> plt.title("Sensor Data Over Time")
        >>> 
        >>> # Custom color
        >>> plt.title("Temperature", color=(255, 100, 100))
        ```
        """
    
    def xlabel(self, s: str | None = None, color: tuple[int, int, int] = (210, 210, 210)) -> None:
        """
        Set X-axis label text and color.
        
        Displays centered label below the X-axis. The label is
        rendered during show() call.
        
        :param s: Label text string. If None, returns current label (default: None)
        :param color: Text color as RGB tuple (default: (210, 210, 210))
        
        Example
        -------
        ```python
        >>> plt = Plot(cv)
        >>> plt.xlabel("Time (seconds)")
        >>> 
        >>> # With custom color
        >>> plt.xlabel("Frequency (Hz)", color=(100, 200, 255))
        ```
        """
    
    def ylabel(self, s: str | None = None, color: tuple[int, int, int] = (210, 210, 210)) -> None:
        """
        Set Y-axis label text and color.
        
        Displays label to the left of the Y-axis. The label is
        rendered during show() call.
        
        :param s: Label text string. If None, returns current label (default: None)
        :param color: Text color as RGB tuple (default: (210, 210, 210))
        
        Example
        -------
        ```python
        >>> plt = Plot(cv)
        >>> plt.ylabel("Amplitude")
        >>> 
        >>> # With units
        >>> plt.ylabel("Temperature (°C)", color=(255, 128, 64))
        ```
        """
    
    def legend(self, loc: str | tuple[float, float] | None = None) -> None:
        """
        Enable and configure legend display.
        
        Shows legend with colored markers and labels for each dataset that
        has a label. Legend position can be specified as a named location
        or explicit (x, y) coordinates in data space.
        
        :param loc: Legend location as string or (x, y) tuple in data coordinates.
                   String options: 'upper right', 'upper left', 'lower left', 'lower right',
                   'upper center', 'lower center', 'center left', 'center right', 'center'.
                   If None, uses last set location or default 'upper right' (default: None)
        
        Example
        -------
        ```python
        >>> plt = Plot(cv)
        >>> plt.plot(x1, y1, label="Series 1")
        >>> plt.plot(x2, y2, label="Series 2")
        >>> plt.legend('upper left')
        >>> 
        >>> # Position at specific data coordinates
        >>> plt.legend((5.0, 0.8))
        ```
        """
    
    def set_legend_colors(self, colors: list[tuple[int, int, int]]) -> None:
        """
        Override automatic legend colors.
        
        Sets custom colors for legend entries, overriding the color cycle.
        Useful for matching legend to specific color schemes.
        
        :param colors: List of RGB tuples, one per legend entry
        
        Example
        -------
        ```python
        >>> plt = Plot(cv)
        >>> custom_colors = [(255,0,0), (0,255,0), (0,0,255)]
        >>> plt.set_legend_colors(custom_colors)
        ```
        """
    
    def clear_legend_items(self) -> None:
        """
        Clear all legend entries and reset colors.
        
        Removes all legend items and clears any custom colors set with
        set_legend_colors(). Useful for resetting legend state between plots.
        
        Example
        -------
        ```python
        >>> plt = Plot(cv)
        >>> # ... add some plots with labels ...
        >>> plt.clear_legend_items()  # Start fresh
        >>> plt.plot(new_data, label="New series")
        ```
        """
    
    def set_legend_items(self, names: list[str]) -> None:
        """
        Manually set legend items with names.
        
        Creates legend entries with specified names, using colors from
        the color cycle or custom colors if set with set_legend_colors().
        Replaces any existing legend items.
        
        :param names: List of legend entry names
        
        Example
        -------
        ```python
        >>> plt = Plot(cv)
        >>> plt.set_legend_items(["Temperature", "Humidity", "Pressure"])
        >>> plt.legend()
        ```
        """
    
    def grid(self, flag: bool | None = None) -> bool | None:
        """
        Enable or disable grid lines.
        
        When enabled, draws vertical lines at X-axis ticks and horizontal
        lines at Y-axis ticks. Grid is drawn in a subdued color to avoid
        interfering with data visualization.
        
        :param flag: If True, enable grid; if False, disable grid; if None, returns current state (default: None)
        :return: Current grid state when flag is None, otherwise None
        
        Example
        -------
        ```python
        >>> plt = Plot(cv)
        >>> plt.grid(True)  # Enable grid
        >>> 
        >>> # Toggle grid
        >>> current = plt.grid()
        >>> plt.grid(not current)
        ```
        """
    
    def xticks(self, ticks: list[float] | None = None, labels: list[str] | None = None) -> tuple[list[float], list[str]] | None:
        """
        Set X-axis tick positions and labels.
        
        Defines where tick marks appear on the X-axis and their labels.
        If grid is enabled, vertical grid lines are drawn at these positions.
        
        :param ticks: List of X values where ticks should appear. If None, returns current ticks (default: None)
        :param labels: Optional list of custom labels for ticks. If None, uses tick values as labels (default: None)
        :return: Tuple of (ticks, labels) when getting, None when setting
        
        Example
        -------
        ```python
        >>> plt = Plot(cv, xlim=(0, 10))
        >>> 
        >>> # Set ticks at regular intervals
        >>> plt.xticks([0, 2.5, 5, 7.5, 10])
        >>> 
        >>> # Custom labels
        >>> plt.xticks([0, 5, 10], ["Start", "Middle", "End"])
        >>> 
        >>> # Get current ticks
        >>> ticks, labels = plt.xticks()
        ```
        """
    
    def yticks(self, ticks: list[float] | None = None, labels: list[str] | None = None) -> tuple[list[float], list[str]] | None:
        """
        Set Y-axis tick positions and labels.
        
        Defines where tick marks appear on the Y-axis and their labels.
        If grid is enabled, horizontal grid lines are drawn at these positions.
        
        :param ticks: List of Y values where ticks should appear. If None, returns current ticks (default: None)
        :param labels: Optional list of custom labels for ticks. If None, uses tick values as labels (default: None)
        :return: Tuple of (ticks, labels) when getting, None when setting
        
        Example
        -------
        ```python
        >>> plt = Plot(cv, ylim=(-1, 1))
        >>> 
        >>> # Set ticks
        >>> plt.yticks([-1, -0.5, 0, 0.5, 1])
        >>> 
        >>> # Percentage labels
        >>> plt.yticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
        ```
        """
    
    def plot(self, *args, label: str | None = None, color: tuple[int, int, int] | None = None) -> None:
        """
        Create line plot connecting data points.
        
        Plots data as connected line segments. Accepts either a single Y data
        array (X values auto-generated) or explicit X and Y arrays. The line
        is drawn during the next show() call.
        
        :param args: Either (y_data,) for auto-generated X, or (x_data, y_data) for explicit coordinates
        :param label: Legend label for this series. If provided, adds entry to legend (default: None)
        :param color: Line color as RGB tuple. If None, uses next color from color cycle (default: None)
        
        Example
        -------
        ```python
        >>> import math
        >>> cv = Canvas(60, 30)
        >>> plt = Plot(cv, xlim=(0, 10), ylim=(-1, 1))
        >>> 
        >>> # Simple Y data (X auto-generated)
        >>> y = [math.sin(i * 0.1) for i in range(100)]
        >>> plt.plot(y, label="sin", color=(255, 0, 0))
        >>> 
        >>> # Explicit X and Y
        >>> x = [i * 0.1 for i in range(100)]
        >>> y = [math.cos(v) for v in x]
        >>> plt.plot(x, y, label="cos", color=(0, 255, 0))
        >>> 
        >>> plt.legend()
        >>> plt.show()
        ```
        """
    
    def scatter(self, x, y=None, s: int = 1, label: str | None = None,
                color: tuple[int, int, int] | None = None) -> None:
        """
        Create scatter plot with individual markers.
        
        Plots data as individual points without connecting lines. Each point
        is rendered as a single pixel. Useful for visualizing discrete data
        points or distributions.
        
        :param x: X coordinates as list, or Y coordinates if y is None
        :param y: Y coordinates as list. If None, x is treated as Y values with auto-generated X (default: None)
        :param s: Marker size (currently unused, reserved for future) (default: 1)
        :param label: Legend label for this series (default: None)
        :param color: Marker color as RGB tuple. If None, uses next color from color cycle (default: None)
        
        Example
        -------
        ```python
        >>> import random
        >>> cv = Canvas(60, 30)
        >>> plt = Plot(cv, xlim=(0, 100), ylim=(0, 100))
        >>> 
        >>> # Random scatter points
        >>> x = [random.uniform(0, 100) for _ in range(50)]
        >>> y = [random.uniform(0, 100) for _ in range(50)]
        >>> plt.scatter(x, y, label="Random", color=(255, 128, 0))
        >>> 
        >>> # Y-only (X auto-generated)
        >>> data = [random.gauss(50, 15) for _ in range(100)]
        >>> plt.scatter(data, label="Gaussian")
        >>> 
        >>> plt.show()
        ```
        """
    
    def bar(self, x, height, width: float = 0.8, label: str | None = None,
            color: tuple[int, int, int] | None = None) -> None:
        """
        Create vertical bar chart.
        
        Draws vertical bars from baseline (Y=0) to specified heights.
        Supports both single bar and multiple bars. Bars are filled
        rectangles rendered in data space.
        
        :param x: X position(s) of bar center(s). Can be single value or list
        :param height: Bar height(s). Can be single value or list matching x
        :param width: Bar width in data units (default: 0.8)
        :param label: Legend label. Only first bar in series uses label (default: None)
        :param color: Bar fill color as RGB tuple. If None, uses next color from color cycle (default: None)
        
        Example
        -------
        ```python
        >>> cv = Canvas(60, 30)
        >>> plt = Plot(cv, xlim=(0, 5), ylim=(0, 100))
        >>> 
        >>> # Single bars
        >>> categories = [1, 2, 3, 4]
        >>> values = [45, 72, 38, 91]
        >>> plt.bar(categories, values, width=0.6, label="Sales", color=(100, 200, 255))
        >>> 
        >>> # Multiple bars with list
        >>> x = [1, 2, 3]
        >>> heights = [50, 75, 25]
        >>> plt.bar(x, heights, width=0.5)
        >>> 
        >>> plt.xlabel("Category")
        >>> plt.ylabel("Value")
        >>> plt.show()
        ```
        """
    
    def hbar(self, y, width, height: float = 0.8, label: str | None = None,
             color: tuple[int, int, int] | None = None) -> None:
        """
        Create horizontal bar chart.
        
        Draws horizontal bars from baseline (X=0) to specified widths.
        Supports both single bar and multiple bars. Useful for displaying
        categorical data with long labels.
        
        :param y: Y position(s) of bar center(s). Can be single value or list
        :param width: Bar width(s) extending from X=0. Can be single value or list matching y
        :param height: Bar height (thickness) in data units (default: 0.8)
        :param label: Legend label. Only first bar in series uses label (default: None)
        :param color: Bar fill color as RGB tuple. If None, uses next color from color cycle (default: None)
        
        Example
        -------
        ```python
        >>> cv = Canvas(60, 30)
        >>> plt = Plot(cv, xlim=(0, 100), ylim=(0, 5))
        >>> 
        >>> # Horizontal bars for rankings
        >>> ranks = [1, 2, 3, 4]
        >>> scores = [85, 72, 91, 68]
        >>> plt.hbar(ranks, scores, height=0.6, label="Scores")
        >>> 
        >>> plt.xlabel("Score")
        >>> plt.ylabel("Rank")
        >>> plt.show()
        ```
        """
    
    def hist(self, data, bins: int = 10, range_: tuple[float, float] | None = None,
             density: bool = False, label: str | None = None,
             color: tuple[int, int, int] | None = None) -> None:
        """
        Create histogram from data distribution.
        
        Bins data into intervals and displays frequency counts or density
        as vertical bars. Automatically adjusts axis limits if needed to
        accommodate the data and histogram bars.
        
        :param data: Input data values to bin
        :param bins: Number of equal-width bins (default: 10)
        :param range_: Data range as (min, max) tuple. If None, uses min/max of data (default: None)
        :param density: If True, normalize to probability density; if False, show counts (default: False)
        :param label: Legend label for histogram series (default: None)
        :param color: Bar fill color as RGB tuple. If None, uses next color from color cycle (default: None)
        
        Example
        -------
        ```python
        >>> import random
        >>> cv = Canvas(60, 30)
        >>> plt = Plot(cv)
        >>> 
        >>> # Gaussian distribution
        >>> data = [random.gauss(50, 10) for _ in range(1000)]
        >>> plt.hist(data, bins=20, label="Distribution", color=(100, 200, 100))
        >>> 
        >>> plt.xlabel("Value")
        >>> plt.ylabel("Frequency")
        >>> plt.title("Histogram Example")
        >>> plt.show()
        >>> 
        >>> # Density histogram with range
        >>> plt.hist(data, bins=15, range_=(20, 80), density=True)
        ```
        """
    
    def text(self, x: float, y: float, s: str, color: tuple[int, int, int] = (220, 220, 220)) -> None:
        """
        Add text annotation at data coordinates.
        
        Places text label at specified position in data space. The text is
        rendered as terminal characters (not pixels) during show() call.
        Multiple text annotations can be added and will all be displayed.
        
        :param x: X coordinate in data space
        :param y: Y coordinate in data space
        :param s: Text string to display
        :param color: Text color as RGB tuple (default: (220, 220, 220))
        
        Example
        -------
        ```python
        >>> cv = Canvas(60, 30)
        >>> plt = Plot(cv, xlim=(0, 10), ylim=(0, 10))
        >>> 
        >>> # Mark specific points
        >>> plt.scatter([5], [5], color=(255, 0, 0))
        >>> plt.text(5.2, 5.2, "Peak", color=(255, 255, 0))
        >>> 
        >>> # Add annotations
        >>> plt.text(2, 8, "Start region", color=(128, 128, 255))
        >>> plt.text(8, 2, "End region", color=(255, 128, 128))
        >>> 
        >>> plt.show()
        ```
        """
    
    def line(self, x0: float, y0: float, x1: float, y1: float,
             color: tuple[int, int, int] | None = None, label: str | None = None,
             autoscale: bool = False) -> None:
        """
        Draw straight line between two points.
        
        Renders a line segment from (x0, y0) to (x1, y1) in data coordinates.
        Can optionally auto-adjust axis limits to ensure line is visible.
        
        :param x0: Starting X coordinate in data space
        :param y0: Starting Y coordinate in data space
        :param x1: Ending X coordinate in data space
        :param y1: Ending Y coordinate in data space
        :param color: Line color as RGB tuple. If None, uses next color from color cycle (default: None)
        :param label: Legend label for this line (default: None)
        :param autoscale: If True, automatically adjust axis limits to include line endpoints (default: False)
        
        Example
        -------
        ```python
        >>> cv = Canvas(60, 30)
        >>> plt = Plot(cv, xlim=(0, 10), ylim=(0, 10))
        >>> 
        >>> # Diagonal line
        >>> plt.line(0, 0, 10, 10, color=(255, 255, 0), label="y=x")
        >>> 
        >>> # Reference lines
        >>> plt.line(0, 5, 10, 5, color=(128, 128, 128))  # Horizontal
        >>> plt.line(5, 0, 5, 10, color=(128, 128, 128))  # Vertical
        >>> 
        >>> # Auto-scale to fit line
        >>> plt.line(-2, -2, 12, 12, autoscale=True, color=(0, 255, 255))
        >>> 
        >>> plt.show()
        ```
        """
    
    def circle(self, center: tuple[float, float], r: float,
               label: str | None = None, color: tuple[int, int, int] | None = None,
               fill: bool = False) -> None:
        """
        Draw circle at specified center with given radius.
        
        Renders a circle using Bresenham's algorithm. Can be drawn as outline
        or filled. Coordinates and radius are in data space.
        
        :param center: Circle center as (x, y) tuple in data coordinates
        :param r: Circle radius in data units
        :param label: Legend label for this circle (default: None)
        :param color: Circle color as RGB tuple. If None, uses next color from color cycle (default: None)
        :param fill: If True, draws filled circle; if False, draws outline only (default: False)
        
        Example
        -------
        ```python
        >>> cv = Canvas(60, 30)
        >>> plt = Plot(cv, xlim=(-2, 2), ylim=(-2, 2))
        >>> 
        >>> # Outline circles
        >>> plt.circle((0, 0), 1.0, color=(255, 0, 0), label="Inner")
        >>> plt.circle((0, 0), 1.5, color=(0, 255, 0), label="Outer")
        >>> 
        >>> # Filled circles
        >>> plt.circle((1, 1), 0.3, color=(255, 255, 0), fill=True)
        >>> plt.circle((-1, -1), 0.3, color=(0, 255, 255), fill=True)
        >>> 
        >>> plt.legend()
        >>> plt.show()
        ```
        """
    
    def show(self, clear_after: bool = False) -> None:
        """
        Render complete plot to terminal.
        
        Executes the full rendering pipeline: clears canvas, draws axes and grid,
        renders all queued plot elements (lines, points, bars, circles), displays
        labels, ticks, and legend, then outputs to terminal. This is the main
        method to call after adding all plot elements.
        
        :param clear_after: If True, clears plot series and text annotations after rendering,
                           useful for animated plots (default: False)
        
        Example
        -------
        ```python
        >>> cv = Canvas(60, 30)
        >>> plt = Plot(cv, xlim=(0, 10), ylim=(0, 100))
        >>> 
        >>> # Build plot
        >>> x = list(range(11))
        >>> y = [i**2 for i in x]
        >>> plt.plot(x, y, label="y=x²", color=(255, 128, 0))
        >>> plt.title("Quadratic Function")
        >>> plt.xlabel("X")
        >>> plt.ylabel("Y")
        >>> plt.grid(True)
        >>> plt.legend()
        >>> 
        >>> # Display
        >>> plt.show()
        >>> time.sleep(3)
        >>> cv.end()
        >>> 
        >>> # Animation with clear_after
        >>> for frame in range(100):
        ...     plt.scatter([frame], [random.randint(0, 100)])
        ...     plt.show(clear_after=True)  # Clear for next frame
        ...     time.sleep(0.05)
        ```
        """


class Scope:
    """
    Real-time oscilloscope-style scrolling display.
    
    Provides continuously updating waveform display optimized for streaming
    sensor data, similar to an oscilloscope or strip chart recorder. Features
    multi-channel support, automatic scrolling, preserved static overlays
    (grid, axes, labels), and efficient differential rendering.
    
    The Scope continuously plots incoming data points from left to right,
    automatically scrolling when reaching the right edge. It preserves
    background elements (axes, grid, zero line) during updates for maximum
    efficiency.
    
    Key features:
    - Real-time scrolling waveform display
    - Multi-channel support with auto-coloring
    - Line or dot rendering styles
    - Automatic legend generation
    - Configurable refresh rate
    - Zero reference line option
    - Preserved static overlays during scroll
    """
    
    ax: Plot
    """Plot instance used for coordinate transformations and rendering."""
    
    cv: Canvas
    """Canvas instance for direct pixel manipulation during scrolling."""
    
    vmin: float
    """Minimum Y-axis value for signal range."""
    
    vmax: float
    """Maximum Y-axis value for signal range."""
    
    def __init__(self, plot: Plot,
                 vmin: float = -2.0, vmax: float = 2.0,
                 colors: list[tuple[int, int, int]] | None = None,
                 show_zero: bool = True,
                 line: bool = True,
                 dot: bool = False,
                 flush_every: int = 2,
                 px_step: int = 2) -> None:
        """
        Initialize oscilloscope display with configuration.
        
        Creates a real-time scrolling display on the provided Plot instance.
        The scope immediately renders the initial state with axes, grid,
        and optional zero reference line.
        
        :param plot: Plot instance to use for rendering (its canvas and viewport)
        :param vmin: Minimum Y-axis value for signal range (default: -2.0)
        :param vmax: Maximum Y-axis value for signal range (default: 2.0)
        :param colors: Custom colors for channels as list of RGB tuples. If None, uses default palette (default: None)
        :param show_zero: If True, draws horizontal line at Y=0 as visual reference (default: True)
        :param line: If True, connects consecutive data points with lines (default: True)
        :param dot: If True, renders as individual pixels only (default: False)
        :param flush_every: Number of ticks between full canvas renders. Lower = smoother but slower (default: 2)
        :param px_step: Horizontal pixel advancement per tick. Higher = faster scroll (default: 2)
        
        Example
        -------
        ```python
        >>> import math
        >>> cv = Canvas(60, 30)
        >>> plt = Plot(cv, xlim=(0, 120), ylim=(-2, 2))
        >>> scope = Scope(plt, vmin=-2, vmax=2, show_zero=True, line=True)
        >>> 
        >>> # Stream single-channel data
        >>> for i in range(200):
        ...     value = math.sin(i * 0.1)
        ...     scope.tick(value)
        ...     time.sleep(0.02)
        >>> 
        >>> cv.end()
        >>> 
        >>> # Multi-channel oscilloscope
        >>> scope = Scope(plt, vmin=-1, vmax=1, colors=[(255,0,0), (0,255,0), (0,0,255)])
        >>> for i in range(500):
        ...     ch1 = math.sin(i * 0.05)
        ...     ch2 = math.cos(i * 0.05)
        ...     ch3 = math.sin(i * 0.1) * 0.5
        ...     scope.tick([ch1, ch2, ch3])
        ```
        """
    
    def reset(self) -> None:
        """
        Reset scope to initial state.
        
        Clears all waveform data, resets scroll position to the left edge,
        and redraws the static elements (axes, grid, labels, legend).
        Useful for starting a new measurement session without recreating
        the Scope instance.
        
        Example
        -------
        ```python
        >>> scope = Scope(plt, vmin=0, vmax=100)
        >>> 
        >>> # Collect first dataset
        >>> for value in sensor_data_1:
        ...     scope.tick(value)
        >>> 
        >>> # Clear and start new dataset
        >>> scope.reset()
        >>> for value in sensor_data_2:
        ...     scope.tick(value)
        ```
        """
    
    def set_range(self, vmin: float, vmax: float) -> None:
        """
        Change Y-axis value range and reset display.
        
        Updates the vertical scale of the oscilloscope and calls reset()
        to clear existing data. All subsequent data points will be plotted
        within the new range.
        
        :param vmin: New minimum Y value
        :param vmax: New maximum Y value
        
        Example
        -------
        ```python
        >>> scope = Scope(plt, vmin=0, vmax=5)
        >>> 
        >>> # Collect data
        >>> for i in range(100):
        ...     scope.tick(adc.read() * 0.01)
        >>> 
        >>> # Adjust range for higher resolution
        >>> scope.set_range(2.0, 3.5)
        >>> 
        >>> # Continue with new range
        >>> for i in range(100):
        ...     scope.tick(adc.read() * 0.01)
        ```
        """
    
    def set_channel_names(self, names: list[str]) -> None:
        """
        Set display names for channels.
        
        Updates the legend with custom names for each channel. The number
        of names should match the number of channels being plotted.
        
        :param names: List of channel name strings
        
        Example
        -------
        ```python
        >>> scope = Scope(plt)
        >>> scope.set_channel_names(["Temperature", "Humidity", "Pressure"])
        >>> 
        >>> # Now tick with 3 channels
        >>> scope.tick([temp, humidity, pressure])
        ```
        """
    
    def set_colors(self, colors: list[tuple[int, int, int]]) -> None:
        """
        Override channel colors.
        
        Sets custom colors for each channel, replacing the default color
        cycle. If there are more channels than colors, colors will be
        reused cyclically.
        
        :param colors: List of RGB color tuples, one per channel
        
        Example
        -------
        ```python
        >>> scope = Scope(plt)
        >>> 
        >>> # Set custom colors
        >>> scope.set_colors([
        ...     (255, 0, 0),    # Red for channel 1
        ...     (0, 255, 0),    # Green for channel 2
        ...     (0, 0, 255)     # Blue for channel 3
        ... ])
        ```
        """
    
    def text(self, x: float, y: float, s: str,
             color: tuple[int, int, int] = (200, 200, 200), align: str = 'left') -> None:
        """
        Add static text annotation at data coordinates.
        
        Places text that remains visible during scrolling. Unlike Plot.text(),
        this text is preserved when the waveform scrolls underneath it.
        Useful for labeling specific value ranges or adding persistent notes.
        
        :param x: X coordinate in data space
        :param y: Y coordinate in data space
        :param s: Text string to display
        :param color: Text color as RGB tuple (default: (200, 200, 200))
        :param align: Text alignment - 'left', 'center', or 'right' (default: 'left')
        
        Example
        -------
        ```python
        >>> scope = Scope(plt, vmin=-2, vmax=2)
        >>> 
        >>> # Add threshold markers
        >>> scope.text(5, 1.5, "High", color=(255, 100, 100))
        >>> scope.text(5, -1.5, "Low", color=(100, 100, 255))
        >>> scope.text(60, 0, "Zero", color=(200, 200, 200), align='center')
        >>> 
        >>> # Start plotting
        >>> for value in sensor_stream:
        ...     scope.tick(value)
        ```
        """
    
    def tick(self, values, names: list[str] | None = None, info_text: str | None = None) -> None:
        """
        Update display with new data point(s).
        
        The primary method for feeding data into the oscilloscope. Accepts
        single value for one channel, list/tuple for multiple channels, or
        dictionary with channel names as keys. Automatically creates new
        channels as needed and handles scrolling when reaching the right edge.
        
        :param values: Data value(s) - can be:
                      - Single number for one channel
                      - List/tuple of numbers for multiple channels
                      - Dictionary with channel names as keys and values as data
        :param names: Optional channel names (only used if values is not a dict and names not set before) (default: None)
        :param info_text: Optional text to display in upper-left corner, useful for frame counter or status (default: None)
        
        Example
        -------
        ```python
        >>> import math, random
        >>> scope = Scope(plt, vmin=-1, vmax=1)
        >>> 
        >>> # Single channel
        >>> for i in range(200):
        ...     value = math.sin(i * 0.1)
        ...     scope.tick(value)
        >>> 
        >>> # Multiple channels as list
        >>> for i in range(200):
        ...     ch1 = math.sin(i * 0.1)
        ...     ch2 = math.cos(i * 0.1)
        ...     scope.tick([ch1, ch2])
        >>> 
        >>> # Multiple channels as dict with names
        >>> for i in range(200):
        ...     scope.tick({
        ...         "Sensor A": random.gauss(0, 0.3),
        ...         "Sensor B": random.gauss(0, 0.5),
        ...         "Sensor C": random.gauss(0, 0.2)
        ...     })
        >>> 
        >>> # With info text
        >>> for i in range(200):
        ...     value = read_sensor()
        ...     scope.tick(value, info_text=f"Frame {i}")
        ```
        """
