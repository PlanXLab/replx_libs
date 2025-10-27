"""
Advanced WS2812 LED matrix controller with text rendering and visual effects.

This class provides comprehensive control of WS2812-based LED matrices with support for
multiple panels, text rendering with custom fonts, smooth animations, and pixel-level
manipulation. Features include hardware-accelerated updates via PIO/DMA, brightness
control, and extensive drawing capabilities for creating dynamic displays.

Matrix Configuration:

    - Single or multi-panel layouts with flexible grid arrangements
    - Configurable panel dimensions and zigzag wiring patterns
    - Multiple coordinate origins (top_left, top_right, bottom_left, bottom_right)
    - Brightness control with gamma correction lookup tables
    
Drawing Features:

    - Pixel-level color control with RGB/HSV color spaces
    - Vector graphics: lines, rectangles, ellipses, circles
    - Bitmap rendering for 1-bit and color images
    - Text rendering with custom fonts and spacing control
    - Smooth scrolling text with directional animation
    
Performance Optimizations:

    - Hardware-accelerated updates using RP2040 PIO and DMA
    - Efficient memory management with typed arrays
    - Configurable update frequencies for smooth animations
    - Non-blocking updates for real-time applications

"""
    
__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


class WS2812Matrix:
    DEFAULT_FONT: str = "lib/ticle/vga2_bold_16x16"

    def __init__(self, pin_sm_pairs: list[tuple[int, int]], *,
                 panel_width: int = 16, panel_height: int = 16,
                 grid_width: int = 1, grid_height: int = 1,
                 zigzag: bool = False, origin: str = "top_left",
                 brightness: float = 0.25, font: str = DEFAULT_FONT) -> None:
        """
        Initialize WS2812 LED matrix controller with hardware acceleration.
        
        Creates a high-performance LED matrix controller that manages multiple panels
        with DMA-based updates for smooth animations and precise timing control.
        
        :param pin_sm_pairs: List of (GPIO_pin, state_machine_id) tuples for LED control
                            Each pair controls one or more panels
        :param panel_width: Width of individual panel in pixels (default: 16)
        :param panel_height: Height of individual panel in pixels (default: 16)
        :param grid_width: Number of panels horizontally (default: 1)
        :param grid_height: Number of panels vertically (default: 1)
        :param zigzag: Enable zigzag wiring pattern for panels (default: False)
        :param origin: Coordinate system origin position (default: "top_left")
        
            - "top_left": (0,0) at top-left corner
            - "top_right": (0,0) at top-right corner  
            - "bottom_left": (0,0) at bottom-left corner
            - "bottom_right": (0,0) at bottom-right corner
            
        :param brightness: Global brightness level 0.0-1.0 (default: 0.25)
        :param font: Font module path for text rendering (default: DEFAULT_FONT)
        
        :raises ValueError: If origin is invalid or state machine IDs are out of range
        :raises OSError: If GPIO or PIO initialization fails
        
        Example
        -------
        ```python
            >>> # Single 16x16 panel
            >>> matrix = WS2812Matrix([(18, 0)], brightness=0.3)
            >>> 
            >>> # 2x2 grid of 16x16 panels with zigzag wiring
            >>> matrix = WS2812Matrix([(18, 0), (19, 1)], 
            ...                      grid_width=2, grid_height=2, 
            ...                      zigzag=True, brightness=0.5)
            >>> 
            >>> # Large single panel display
            >>> matrix = WS2812Matrix([(18, 0)], 
            ...                      panel_width=32, panel_height=8,
            ...                      origin="bottom_left")
        ```
        """
        
    class _PixelView:
        def __init__(self, parent, x, y):
            self._parent = parent
            self._x = x
            self._y = y

        @property
        def value(self):
            fb = self._parent._fb
            w = self._parent._fb_width
            packed = fb[self._y * w + self._x]
            g = (packed >> 24) & 0xFF
            r = (packed >> 16) & 0xFF
            b = (packed >> 8) & 0xFF
            return r, g, b

        @value.setter
        def value(self, color):
            self._parent._set_pixel(self._x, self._y, color)

    def __getitem__(self, pos: tuple[int, int]) -> "_PixelView":
        """
        Get a pixel view for reading and writing individual pixel colors.
        
        Provides direct access to pixel values with coordinate validation
        for precise pixel manipulation.
        
        :param pos: Pixel coordinates as (x, y) tuple
        :return: _PixelView object for pixel access
        
        :raises IndexError: If coordinates are out of bounds
        :raises TypeError: If pos is not a coordinate tuple
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> 
            >>> # Set individual pixels
            >>> matrix[5, 5].value = (255, 0, 0)    # Red pixel
            >>> matrix[6, 5].value = (0, 255, 0)    # Green pixel
            >>> matrix[7, 5].value = (0, 0, 255)    # Blue pixel
            >>> 
            >>> # Read pixel color
            >>> r, g, b = matrix[5, 5].value
            >>> print(f"Pixel color: RGB({r}, {g}, {b})")
            >>> 
            >>> matrix.update()
        ```
        """

    @property
    def width(self) -> int: 
        """
        Get the total matrix width in pixels.
        
        :return: Matrix width in pixels
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)], panel_width=16, grid_width=2)
            >>> print(matrix.width)  # Output: 32
        ```
        """

    @property
    def height(self) -> int: 
        """
        Get the total matrix height in pixels.
        
        :return: Matrix height in pixels
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)], panel_height=16, grid_height=2)
            >>> print(matrix.height)  # Output: 32
        ```
        """

    @property
    def brightness(self) -> float: 
        """
        Get the current brightness level.
        
        :return: Brightness level from 0.0 to 1.0
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)], brightness=0.5)
            >>> print(matrix.brightness)  # Output: 0.5
        ```
        """

    @brightness.setter
    def brightness(self, value: float) -> None:
        """
        Set the global brightness level for all LEDs.
        
        Updates the brightness and rebuilds the gamma correction lookup table
        for immediate effect on subsequent updates.
        
        :param value: Brightness level from 0.0 to 1.0
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> matrix.brightness = 0.8  # Bright
            >>> matrix.fill((255, 255, 255))
            >>> matrix.update()
            >>> 
            >>> matrix.brightness = 0.1  # Dim
            >>> matrix.update()  # Same colors, different brightness
        ```
        """

    def update(self, wait: bool = True) -> None:
        """
        Update the LED matrix display with current framebuffer content.
        
        Transfers the framebuffer to LEDs using hardware-accelerated DMA.
        Non-blocking mode allows for smooth animations without timing delays.
        
        :param wait: Wait for DMA transfer completion (default: True)
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> matrix.fill((255, 0, 0))  # Fill with red
            >>> matrix.update()           # Blocking update
            >>> 
            >>> # Non-blocking for animations
            >>> matrix.fill((0, 255, 0))
            >>> matrix.update(wait=False)  # Continue immediately
        ```
        """

    def clear(self) -> None:
        """
        Clear the matrix display and turn off all LEDs.
        
        Sets all pixels to black and immediately updates the display
        for instant clearing effect.
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> matrix.fill((255, 0, 0))  # Fill with red
            >>> matrix.update()
            >>> utime.sleep_ms(1000)
            >>> matrix.clear()            # Instant clear
        ```
        """
        self.fill(0)
        self.update(True)
    
    def fill(self, color: int | tuple[int, int, int]) -> None:
        """
        Fill the entire matrix with a single color.
        
        Sets all pixels to the specified color without updating the display.
        Call update() to apply changes to the LEDs.
        
        :param color: RGB color as tuple (r,g,b) or 24-bit integer
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> 
            >>> # Fill with red using tuple
            >>> matrix.fill((255, 0, 0))
            >>> matrix.update()
            >>> 
            >>> # Fill with blue using hex
            >>> matrix.fill(0x0000FF)
            >>> matrix.update()
        ```
        """

    def set_font(self, font_src: str | object) -> None:
        """
        Set the font for text rendering operations.
        
        Changes the current font used for all text drawing operations. Accepts
        either a font module path string or a font module object directly.
        
        :param font_src: Font module path string or font module object
        
        :raises ImportError: If font module cannot be imported
        :raises AttributeError: If font module lacks required attributes
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> 
            >>> # Load font by module path
            >>> matrix.set_font("lib/ticle/vga2_bold_16x16")
            >>> matrix.draw_text("Bold Text", x=0, y=0)
            >>> 
            >>> # Load different font
            >>> matrix.set_font("lib/ticle/arial_12x12")
            >>> matrix.draw_text("Arial Text", x=0, y=8)
            >>> matrix.update()
        ```
        """

    def deinit(self) -> None:
        """
        Safely deinitialize the matrix controller and release resources.
        
        Clears the display, stops all DMA operations, and releases GPIO/PIO
        resources for clean shutdown.
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> # ... use matrix ...
            >>> matrix.deinit()  # Clean shutdown
        ```
        """

    def draw_line(self, x0:int, y0:int, x1:int, y1:int, color):
        """
        Draw a line between two points using Bresenham's algorithm.
        
        Renders anti-aliased lines with pixel-perfect accuracy for
        geometric shapes and graphical elements.
        
        :param x0: Starting X coordinate
        :param y0: Starting Y coordinate  
        :param x1: Ending X coordinate
        :param y1: Ending Y coordinate
        :param color: Line color as RGB tuple or integer
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> 
            >>> # Draw diagonal line
            >>> matrix.draw_line(0, 0, 15, 15, (255, 255, 255))
            >>> 
            >>> # Draw border rectangle
            >>> matrix.draw_line(0, 0, 15, 0, (255, 0, 0))    # Top
            >>> matrix.draw_line(15, 0, 15, 15, (255, 0, 0))  # Right
            >>> matrix.draw_line(15, 15, 0, 15, (255, 0, 0))  # Bottom
            >>> matrix.draw_line(0, 15, 0, 0, (255, 0, 0))    # Left
            >>> matrix.update()
        ```
        """

    def draw_line_polar(self, cx:int, cy:int, length:int, angle_deg:int, color):
        """
        Draw a line using polar coordinates (center, length, angle).
        
        Renders a line from a center point with specified length and angle,
        useful for creating radial patterns, clock hands, and compass displays.
        
        :param cx: Center X coordinate
        :param cy: Center Y coordinate
        :param length: Line length in pixels
        :param angle_deg: Angle in degrees (0° = right, 90° = up)
        :param color: Line color as RGB tuple or integer
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> 
            >>> # Clock hand pointing up (12 o'clock)
            >>> matrix.draw_line_polar(8, 8, 6, 90, (255, 255, 255))
            >>> 
            >>> # Compass directions
            >>> matrix.draw_line_polar(8, 8, 5, 0, (255, 0, 0))    # East
            >>> matrix.draw_line_polar(8, 8, 5, 90, (0, 255, 0))   # North
            >>> matrix.draw_line_polar(8, 8, 5, 180, (0, 0, 255))  # West
            >>> matrix.draw_line_polar(8, 8, 5, 270, (255, 255, 0)) # South
            >>> 
            >>> # Radial pattern
            >>> for angle in range(0, 360, 30):
            ...     matrix.draw_line_polar(8, 8, 4, angle, (255, 255, 255))
            >>> matrix.update()
        ```
        """

    def draw_rect(self, x: int, y: int, w: int, h: int, outline: int | tuple[int, int, int], 
                  *, 
                  fill: int | tuple[int, int, int] = None) -> None:
        """
        Draw a rectangle with optional fill color.
        
        Renders rectangles with precise edge control for UI elements,
        borders, and geometric patterns.
        
        :param x: Top-left X coordinate
        :param y: Top-left Y coordinate
        :param w: Rectangle width
        :param h: Rectangle height
        :param outline: Border color
        :param fill: Fill color, None for outline only (default: None)
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> 
            >>> # Outlined rectangle
            >>> matrix.draw_rect(2, 2, 12, 8, (255, 255, 0))
            >>> 
            >>> # Filled rectangle with border
            >>> matrix.draw_rect(4, 4, 8, 6, (255, 0, 0), fill=(0, 255, 0))
            >>> matrix.update()
        ```
        """

    def draw_rect_polar(self, cx: int, cy: int, w: int, h: int, ngle_deg: float, outline, 
                        *, 
                        fill: int | tuple[int, int, int] = None) -> None:
        """
        Draw a rotated rectangle using polar coordinates.
        
        Renders a rectangle rotated around its center point, useful for
        creating oriented UI elements and dynamic geometric displays.
        
        :param cx: Center X coordinate
        :param cy: Center Y coordinate
        :param w: Rectangle width
        :param h: Rectangle height
        :param angle_deg: Rotation angle in degrees
        :param outline: Border color
        :param fill: Fill color, None for outline only (default: None)
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> 
            >>> # Rotated rectangles
            >>> matrix.draw_rect_polar(8, 8, 10, 6, 0, (255, 0, 0))    # Horizontal
            >>> matrix.draw_rect_polar(8, 8, 10, 6, 45, (0, 255, 0))   # 45° rotation
            >>> matrix.draw_rect_polar(8, 8, 10, 6, 90, (0, 0, 255))   # Vertical
            >>> 
            >>> # Filled rotated rectangle
            >>> matrix.draw_rect_polar(8, 8, 8, 4, 30, (255, 255, 255), 
            ...                      fill=(255, 0, 255))
            >>> matrix.update()
        ```
        """

    def draw_ellipse(self, cx: int, cy: int, rx: int, ry: int | None = None, outline=(255, 255, 255), 
                     *, 
                     fill: int | tuple[int, int, int] = None, 
                     angle_deg: float = 0.0):
        """
        Draw an ellipse with optional rotation and fill.
        
        Renders ellipses and circles with precise edge control, supporting
        rotation for dynamic geometric displays and decorative elements.
        
        :param cx: Center X coordinate
        :param cy: Center Y coordinate
        :param rx: Horizontal radius
        :param ry: Vertical radius, None for circle (default: None)
        :param outline: Border color (default: white)
        :param fill: Fill color, None for outline only (default: None)
        :param angle_deg: Rotation angle in degrees (default: 0.0)
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> 
            >>> # Simple circle
            >>> matrix.draw_ellipse(8, 8, 5, outline=(255, 0, 0))
            >>> 
            >>> # Ellipse with different radii
            >>> matrix.draw_ellipse(8, 8, 6, 3, outline=(0, 255, 0))
            >>> 
            >>> # Rotated ellipse
            >>> matrix.draw_ellipse(8, 8, 5, 2, outline=(0, 0, 255), angle_deg=45)
            >>> 
            >>> # Filled ellipse
            >>> matrix.draw_ellipse(8, 8, 4, 3, outline=(255, 255, 255), 
            ...                    fill=(255, 0, 255), angle_deg=30)
            >>> matrix.update()
        ```
        """

    def draw_circle(self, cx: int, cy: int, r: int, color: int | tuple[int, int, int], 
                    *, 
                    fill: int | tuple[int, int, int] = None) -> None:
        """
        Draw a circle with optional fill color.
        
        Renders smooth circles using optimized algorithms for
        decorative elements and geometric displays.
        
        :param cx: Center X coordinate
        :param cy: Center Y coordinate
        :param r: Circle radius
        :param color: Circle color
        :param fill: Fill color, None for outline only (default: None)
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> 
            >>> # Simple circle outline
            >>> matrix.draw_circle(8, 8, 6, (0, 255, 255))
            >>> 
            >>> # Filled circle
            >>> matrix.draw_circle(8, 8, 4, (255, 255, 255), fill=(255, 0, 255))
            >>> matrix.update()
        ```
        """

    def draw_bitmap_1bit(self, data:bytes|bytearray|memoryview, 
                         width:int, height:int, x:int=0, y:int=0, outline=(255,255,255)):
        """
        Draw a 1-bit bitmap with edge detection for outline rendering.
        
        Renders monochrome bitmaps with automatic edge detection to create
        clean outlined graphics, ideal for icons, logos, and simple graphics.
        
        :param data: Bitmap data as bytes/bytearray (1 bit per pixel, packed)
        :param width: Bitmap width in pixels
        :param height: Bitmap height in pixels
        :param x: Starting X coordinate (default: 0)
        :param y: Starting Y coordinate (default: 0)
        :param outline: Color for bitmap edges (default: white)
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> 
            >>> # Simple 8x8 bitmap (heart shape)
            >>> heart_data = bytes([
            ...     0b01100110,  # ..##..##
            ...     0b11111111,  # ########
            ...     0b11111111,  # ########
            ...     0b01111110,  # .######.
            ...     0b00111100,  # ..####..
            ...     0b00011000,  # ...##...
            ...     0b00000000,  # ........
            ...     0b00000000   # ........
            ... ])
            >>> matrix.draw_bitmap_1bit(heart_data, 8, 8, x=4, y=4, 
            ...                        outline=(255, 0, 0))
            >>> 
            >>> # Load bitmap from file
            >>> with open("icon.bin", "rb") as f:
            ...     icon_data = f.read()
            >>> matrix.draw_bitmap_1bit(icon_data, 16, 16, x=0, y=0)
            >>> matrix.update()
        ```
        """

    def draw_bitmap_color(self, data: bytes | bytearray | memoryview, 
                          width: int, height: int, x: int = 0, y: int = 0) -> None:
        """
        Draw a color bitmap with RGB pixel data.
        
        Renders full-color bitmaps with 24-bit RGB data, perfect for
        displaying photos, detailed graphics, and color icons.
        
        :param data: RGB bitmap data (3 bytes per pixel: R, G, B)
        :param width: Bitmap width in pixels
        :param height: Bitmap height in pixels
        :param x: Starting X coordinate (default: 0)
        :param y: Starting Y coordinate (default: 0)
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> 
            >>> # Simple 2x2 color bitmap
            >>> color_data = bytes([
            ...     255, 0, 0,    # Red pixel
            ...     0, 255, 0,    # Green pixel
            ...     0, 0, 255,    # Blue pixel
            ...     255, 255, 0   # Yellow pixel
            ... ])
            >>> matrix.draw_bitmap_color(color_data, 2, 2, x=7, y=7)
            >>> 
            >>> # Load color image
            >>> with open("photo.rgb", "rb") as f:
            ...     img_data = f.read()
            >>> matrix.draw_bitmap_color(img_data, 16, 16, x=0, y=0)
            >>> matrix.update()
        ```
        """

    def draw_text(self, text: str, 
                  *, 
                  x: int = 0, 
                  y: int = 0,
                  fg: int | tuple[int, int, int] = (255, 255, 255), 
                  bg: int | tuple[int, int, int] = (0, 0, 0),
                  space_scale: float = 0.3,
                  right_margin: int = 1, 
                  left_margin: int = 0) -> None:
        """
        Draw text on the matrix with customizable formatting.
        
        Renders text using the configured font with precise control over
        spacing, colors, and positioning for optimal display appearance.
        
        :param text: Text string to render
        :param x: Starting X coordinate (default: 0)
        :param y: Starting Y coordinate (default: 0)
        :param fg: Foreground color for text (default: white)
        :param bg: Background color, None for transparent (default: black)
        :param space_scale: Space character width as fraction of font width (default: 0.3)
        :param right_margin: Right margin pixels per character (default: 1)
        :param left_margin: Left margin pixels per character (default: 0)
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> 
            >>> # Simple text display
            >>> matrix.draw_text("Hello", x=2, y=4, fg=(255, 255, 0))
            >>> matrix.update()
            >>> 
            >>> # Colored text with spacing
            >>> matrix.draw_text("L E D", x=0, y=0, 
            ...                  fg=(0, 255, 0), bg=None,
            ...                  space_scale=0.5, right_margin=2)
            >>> matrix.update()
        ```
        """

    def draw_text_scroll(self, text: str, 
                         *, 
                         direction: str = "left", x: int = 0, y: int = 0,
                         fg: int | tuple[int, int, int] = (255, 255, 255),
                         bg: int | tuple[int, int, int] = (0, 0, 0),
                         step_px: int = 1, 
                         space_scale: float = 0.3,
                         right_margin: int = 1, 
                         left_margin: int = 0, 
                         up_margin: int = 1, 
                         down_margin: int = 0,
                         speed_ms: int = 0) -> None:
        """
        Display scrolling text animation across the matrix.
        
        Creates smooth scrolling text effects in four directions with configurable
        speed and spacing for eye-catching displays and information tickers.
        
        :param text: Text string to scroll
        :param direction: Scroll direction: "left", "right", "up", "down" (default: "left")
        :param x: Starting X coordinate (default: 0)
        :param y: Starting Y coordinate (default: 0)
        :param fg: Text color (default: white)
        :param bg: Background color (default: black)
        :param step_px: Pixels per scroll step (default: 1)
        :param space_scale: Space character width scaling (default: 0.3)
        :param right_margin: Character right margin (default: 1)
        :param left_margin: Character left margin (default: 0)
        :param up_margin: Vertical scroll top margin (default: 1)
        :param down_margin: Vertical scroll bottom margin (default: 0)
        :param speed_ms: Delay between scroll steps in milliseconds (default: 0)
        
        :raises ValueError: If direction is not valid
        
        Example
        -------
        ```python
            >>> matrix = WS2812Matrix([(18, 0)])
            >>> 
            >>> # Basic left scroll
            >>> matrix.draw_text_scroll("NEWS FLASH", direction="left", speed_ms=100)
            >>> 
            >>> # Fast right scroll with custom colors
            >>> matrix.draw_text_scroll("ALERT", direction="right", 
            ...                        fg=(255, 0, 0), speed_ms=50)
            >>> 
            >>> # Smooth vertical scroll
            >>> matrix.draw_text_scroll("INFO", direction="up", 
            ...                        step_px=1, speed_ms=150)
        ```
        """
