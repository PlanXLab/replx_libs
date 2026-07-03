"""
Terminal Visualization Library for EFR32MG

Terminal graphics and formatting library for XBee3 MicroPython with ANSI escape codes.
Provides comprehensive terminal control capabilities including color formatting,
cursor manipulation, and screen management optimized for resource-constrained 
EFR32MG (Mighty Gecko) processors.

This is a simplified version of termviz designed for XBee3's limited memory
environment while maintaining essential functionality for terminal-based UIs.

Features:

- ANSI color support with TrueColor RGB and standard colors
- Cursor control and positioning
- Screen and line clearing operations  
- Text styling attributes (bold, italic, underline, etc.)
- Semantic color palettes for professional UIs
- Memory-efficient implementation for XBee3

"""

class Term:
    """
    ANSI escape code library with TrueColor RGB support and terminal control.
    
    Provides comprehensive terminal formatting capabilities including 24-bit RGB colors,
    cursor positioning, screen manipulation, and text styling attributes. All methods are
    static and return ANSI escape sequence strings ready for terminal output.
    
    The Term class supports both foreground and background coloring through:
    - Dynamic RGB Term generation (rgb, hex_color, gray methods)
    - Pre-defined semantic Term constants (FG and BG nested classes)
    - Terminal cursor control and positioning
    - Screen and line clearing operations
    - Text styling attributes (bold, italic, underline, etc.)
    
    Example
    -------
    ```python
    >>> # Using predefined foreground colors
    >>> print(Term.FG.RED + "Error message" + Term.RESET)
    >>> print(Term.FG.GREEN + "Success" + Term.RESET)
    >>> print(Term.FG.YELLOW + "Warning" + Term.RESET)
    >>> print(Term.FG.BLUE + "Information" + Term.RESET)
    >>> 
    >>> # Using predefined background colors
    >>> print(Term.BG.BLACK + Term.FG.WHITE + " Inverted text " + Term.RESET)
    >>> print(Term.BG.RED + Term.FG.BRIGHT_WHITE + " Alert! " + Term.RESET)
    >>> 
    >>> # Semantic colors for UI design
    >>> print(Term.FG.PRIMARY + "Primary action" + Term.RESET)
    >>> print(Term.FG.SUCCESS + "✓ Operation successful" + Term.RESET)
    >>> print(Term.FG.WARNING + "⚠ Check configuration" + Term.RESET)
    >>> print(Term.FG.DANGER + "✗ Critical error" + Term.RESET)
    >>> print(Term.FG.INFO + "ℹ Additional information" + Term.RESET)
    >>> print(Term.FG.MUTED + "Secondary text" + Term.RESET)
    >>> 
    >>> # Text styling attributes
    >>> print(Term.BOLD + "Bold text" + Term.RESET)
    >>> print(Term.ITALIC + "Italic text" + Term.RESET)
    >>> print(Term.UNDERLINE + "Underlined text" + Term.RESET)
    >>> print(Term.STRIKE + "Strikethrough text" + Term.RESET)
    >>> print(Term.DIM + "Dimmed text" + Term.RESET)
    >>> print(Term.REVERSE + "Reversed colors" + Term.RESET)
    >>> 
    >>> # Combining colors and styles
    >>> print(Term.BOLD + Term.FG.GREEN + "Bold green text" + Term.RESET)
    >>> print(Term.UNDERLINE + Term.FG.BLUE + "Underlined blue text" + Term.RESET)
    >>> print(Term.BG.YELLOW + Term.FG.BLACK + Term.BOLD + " Highlight " + Term.RESET)
    >>> 
    >>> # Building colored status indicators
    >>> status_ok = Term.FG.SUCCESS + "●" + Term.RESET + " Service running"
    >>> status_err = Term.FG.DANGER + "●" + Term.RESET + " Service stopped"
    >>> status_warn = Term.FG.WARNING + "●" + Term.RESET + " Service degraded"
    >>> print(status_ok)
    >>> print(status_err)
    >>> print(status_warn)
    >>> 
    >>> # Creating a colored progress bar
    >>> def progress_bar(percent, width=40):
    ...     filled = int(width * percent / 100)
    ...     bar = Term.FG.GREEN + "█" * filled + Term.RESET
    ...     bar += Term.FG.MUTED + "░" * (width - filled) + Term.RESET
    ...     return f"{bar} {percent}%"
    >>> print(progress_bar(75))
    >>> 
    >>> # Colored table output
    >>> header = Term.BOLD + Term.FG.CYAN
    >>> data = Term.FG.WHITE
    >>> print(header + "Name        Status      Value" + Term.RESET)
    >>> print(data + "Server-1    " + Term.FG.SUCCESS + "Running" + data + "     99.5%" + Term.RESET)
    >>> print(data + "Server-2    " + Term.FG.DANGER + "Stopped" + data + "     0.0%" + Term.RESET)
    ```
    """
    
    @staticmethod
    def rgb(r: int, g: int, b: int, fg: bool = True) -> str:
        """
        Generate TrueColor (24-bit) RGB ANSI escape sequence.
        
        Creates an ANSI escape code for true Term support in modern terminals.
        Each Term component can range from 0 (darkest) to 255 (brightest),
        providing 16.7 million possible colors.
        
        :param r: Red component intensity (0-255)
        :param g: Green component intensity (0-255)
        :param b: Blue component intensity (0-255)
        :param fg: If True, applies to foreground (text Term); if False, applies to background
        :return: ANSI escape sequence string for the specified RGB Term
        
        :raises ValueError: If any Term component is outside the valid 0-255 range
        
        Example
        -------
        ```python
        >>> # Basic Term usage
        >>> print(Term.rgb(255, 0, 0) + "Red text" + Term.RESET)
        >>> print(Term.rgb(0, 200, 100, fg=False) + "Green background" + Term.RESET)
        >>> 
        >>> # Creating custom Term schemes
        >>> brand_primary = Term.rgb(72, 133, 237)
        >>> brand_accent = Term.rgb(255, 171, 64)
        >>> print(brand_primary + "Logo" + Term.RESET + brand_accent + " Tagline" + Term.RESET)
        >>> 
        >>> # Gradient effect
        >>> for i in range(256):
        ...     print(Term.rgb(i, 0, 255-i) + "█", end="")
        >>> print(Term.RESET)
        ```
        """
    
    @staticmethod
    def hex_color(code: str, fg: bool = True) -> str:
        """
        Convert hexadecimal Term code to ANSI escape sequence.
        
        Accepts standard web hex Term formats and converts them to terminal
        TrueColor ANSI codes. Supports both short (#RGB) and full (#RRGGBB)
        notation, with or without the leading hash symbol.
        
        :param code: Hex Term code in format "#RGB", "#RRGGBB", "RGB", or "RRGGBB"
        :param fg: If True, applies to foreground (text Term); if False, applies to background
        :return: ANSI escape sequence string for the specified Term
        
        :raises ValueError: If hex format is invalid or contains non-hex characters
        
        Example
        -------
        ```python
        >>> # Web Term notation
        >>> print(Term.hex_color("#FF5733") + "Coral text" + Term.RESET)
        >>> print(Term.hex_color("3498DB", fg=False) + "Blue background" + Term.RESET)
        >>> 
        >>> # Short notation (expanded automatically)
        >>> print(Term.hex_color("#F00") + "Red" + Term.RESET)  # Expands to #FF0000
        >>> 
        >>> # Reading colors from configuration
        >>> theme_colors = {"primary": "#2C3E50", "accent": "#E74C3C"}
        >>> for name, hex_code in theme_colors.items():
        ...     print(Term.hex_color(hex_code) + name + Term.RESET)
        ```
        """
    
    @staticmethod
    def gray(level: int, fg: bool = True) -> str:
        """
        Generate grayscale ANSI escape sequence.
        
        Creates a gray Term by setting all RGB components to the same value.
        This is a convenience method for creating monochrome colors without
        specifying all three Term components separately.
        
        :param level: Gray intensity level where 0 is black, 255 is white, and values in between are shades of gray
        :param fg: If True, applies to foreground (text Term); if False, applies to background
        :return: ANSI escape sequence string for the specified gray level
        
        :raises ValueError: If level is outside the valid 0-255 range
        
        Example
        -------
        ```python
        >>> # Grayscale gradient
        >>> for level in range(0, 256, 16):
        ...     print(Term.gray(level) + "█" * 4, end="")
        >>> print(Term.RESET)
        >>> 
        >>> # Low-contrast UI elements
        >>> print(Term.gray(64, fg=False) + Term.gray(192) + " Subtle label " + Term.RESET)
        >>> 
        >>> # Creating disabled/muted text
        >>> enabled_text = Term.FG.WHITE + "Active item" + Term.RESET
        >>> disabled_text = Term.gray(128) + "Disabled item" + Term.RESET
        ```
        """
    
    class FG:
        """Foreground Term constants."""
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
        """Background Term constants."""
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
        >>> print(Term.cursor_up(1) + Term.clear_line() + "Line 2 replaced")
        >>> 
        >>> # Create simple progress indicator
        >>> for i in range(5):
        ...     print(f"Progress: {i*20}%")
        ...     time.sleep(0.5)
        ...     print(Term.cursor_up(1), end="")
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
        >>> print(Term.cursor_down(2))
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
        >>> print(Term.cursor_right(4) + "Indented text")
        >>> 
        >>> # Align columns manually
        >>> print("Name:" + Term.cursor_right(10) + "Value")
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
        >>> print(Term.cursor_left(5) + "There")
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
        >>> print(Term.cursor_to(5, 10) + "X")
        >>> print(Term.cursor_to(10, 20) + "O")
        >>> 
        >>> # Create simple menu
        >>> print(Term.cursor_to(1, 1) + "╔════ Menu ════╗")
        >>> print(Term.cursor_to(2, 1) + "║ 1. Option A ║")
        >>> print(Term.cursor_to(3, 1) + "║ 2. Option B ║")
        >>> print(Term.cursor_to(4, 1) + "╚══════════════╝")
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
        >>> print(Term.cursor_home() + "Back to top-left")
        >>> 
        >>> # Clear and restart display
        >>> print(Term.cursor_home() + Term.erase_screen())
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
        >>> print("Label:" + Term.cursor_col(20) + "Value")
        >>> print("Another:" + Term.cursor_col(20) + "123")
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
        >>> print("Original position" + Term.cursor_save())
        >>> print(Term.cursor_to(10, 1) + "Temporary message")
        >>> time.sleep(1)
        >>> print(Term.cursor_restore() + " continues here")
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
        >>> print(Term.cursor_save())
        >>> print(Term.cursor_to(1, 1) + "Status: Running...")
        >>> process_data()
        >>> print(Term.cursor_restore())
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
        >>> print(Term.cursor_hide())
        >>> for frame in animation_frames:
        ...     draw_frame(frame)
        ...     time.sleep(0.1)
        >>> print(Term.cursor_show())
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
        ...     print(Term.cursor_hide())
        ...     draw_complex_ui()
        >>> finally:
        ...     print(Term.cursor_show())
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
        >>> print(Term.cursor_next_line(2) + "Section 2 (with gap)")
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
        >>> print(Term.cursor_prev_line(1) + "Line 2 updated")
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
        >>> print(Term.erase_screen(2))
        >>> 
        >>> # Clear from cursor down (preserve header)
        >>> print_header()
        >>> print(Term.cursor_to(5, 1))
        >>> print(Term.erase_screen(0))  # Clear from row 5 downward
        >>> 
        >>> # Full reset including scrollback
        >>> print(Term.cursor_home() + Term.erase_screen(3))
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
        >>> print(Term.cursor_up(1) + Term.erase_line() + "New content")
        >>> 
        >>> # Clear to end of line (status bar pattern)
        >>> print("Status: ", end="")
        >>> print("Loading..." + Term.erase_line(0))
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
        >>> print(Term.clear_screen())
        >>> print("Fresh start")
        >>> 
        >>> # Application restart
        >>> def reset_ui():
        ...     print(Term.clear_screen())
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
        >>> print(Term.cursor_up(1) + Term.clear_line() + "Done!")
        >>> 
        >>> # Progress indicator
        >>> for i in range(100):
        ...     print(Term.clear_line() + f"Progress: {i+1}%", end="", flush=True)
        ...     time.sleep(0.1)
        ```
        """