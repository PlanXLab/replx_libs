"""
WS2812 Matrix Visual Effects
============================

Timer-driven visual effects for WS2812 LED matrices, running asynchronously
in the background using hardware timers and micropython.schedule().

Usage
-----
::

    from ws2812 import Matrix, Effect
    
    # Create matrix and effect controller
    matrix = Matrix([2], panel_width=8, panel_height=8)
    fx = Effect(matrix)
    
    # Start an effect
    fx.fireworks()
    
    # Stop effects
    fx.stop()

Effect Categories
-----------------

**Ambient Effects**
- `plasma`: Smooth flowing color waves
- `ripple`: Expanding rings from a center point
- `neon_checkerboard`: Pulsing colored tile grid

**Fire/Flame Effects**
- `campfire`: Realistic fire simulation with rising embers
- `fireworks`: Multi-rocket fireworks display
- `fire_horizontal`: Horizontal flames for signboards

**Particle Effects**
- `sparkle`: Twinkling stars with bloom effect
- `meteor_rain`: Colored trails flowing through the matrix
- `spark_stream`: Upward rising spark fountains
- `comet_horizontal`: Horizontal comets with trails

**Pattern Effects**
- `matrix_rain`: "Matrix" style falling green code
- `petal_vortex`: Rotating flower-like pattern
- `horizontal_wave`: Rainbow wave for wide displays
- `scrolling_gradient`: Smooth scrolling gradient
- `scanner`: Knight Rider style scanner beam
- `audio_bars`: Simulated audio visualizer

Notes
-----
- Only one effect runs at a time; starting a new effect stops the previous one.
- Effects use hardware Timer(-1), which is a virtual timer on RP2.
- Frame rate is automatically limited based on LED count to prevent data corruption.
- All effects are non-blocking and run in the background.
- Signboard effects (horizontal_wave, comet_horizontal, etc.) are optimized for
  wide aspect ratios like 160x16.
"""

from typing import Tuple, Optional, Sequence

Color = Tuple[int, int, int]

class Effect:
    """
    Timer-driven visual effect controller for Matrix.
    
    Provides various animated effects that run asynchronously using
    micropython.schedule() and hardware timers.
    
    :param ws: A Matrix instance to control
    
    Example
    -------
    ```python
        >>> from ws2812 import Matrix, Effect
        >>> 
        >>> matrix = Matrix([2], panel_width=8, panel_height=8)
        >>> fx = Effect(matrix)
        >>> 
        >>> # Run plasma effect
        >>> fx.plasma(speed=0.01, kx=4, ky=4)
        >>> 
        >>> # Later, stop
        >>> fx.stop()
    ```
    """
    
    def __init__(self, ws) -> None: ...
    
    def stop(self) -> None:
        """
        Stop the current running effect.
        
        Deinitializes the timer and clears the effect state.
        The LED matrix retains its last displayed state.
        """
        ...
    
    def sparkle(
        self,
        *,
        base: Color = (0, 0, 0),
        sparkle_color: Color = (230, 245, 255),
        spawn_per_tick: int = 10,
        decay_step: int = 28,
        max_active: int = 220,
        decay_budget_per_tick: int = 72,
        bloom_strength: int = 64,
        bloom_neighbors: int = 2,
        speed: float = 0.010
    ) -> None:
        """
        Twinkling sparkle effect with bloom.
        
        Creates randomly spawning bright points that fade with a twinkling
        animation and bloom effect to neighboring pixels.
        
        :param base: Background color (default: black)
        :param sparkle_color: Color of sparkle points
        :param spawn_per_tick: Number of new sparkles per frame
        :param decay_step: How much brightness decreases per frame
        :param max_active: Maximum simultaneous active sparkles
        :param decay_budget_per_tick: Number of sparkles to process per frame
        :param bloom_strength: Intensity of glow spread to neighbors (0-255)
        :param bloom_neighbors: Number of neighboring pixels to bloom to
        :param speed: Frame interval in seconds
        
        Example
        -------
        ```python
            >>> fx.sparkle(spawn_per_tick=15, bloom_strength=100)
        ```
        """
        ...
    
    def meteor_rain(
        self,
        *,
        colors: tuple = ((255, 80, 0), (0, 160, 255), (255, 0, 160)),
        count: int = 6,
        trail: int = 9,
        step: int = 2,
        glitter_prob: int = 32,
        speed: float = 0.010
    ) -> None:
        """
        Multi-colored meteor shower effect.

        Multiple meteors streak across the LED strip/matrix leaving
        fading trails, with optional random glitter sparkles.

        :param colors: Tuple of RGB colors for the meteors
        :param count: Number of simultaneous meteors
        :param trail: Trail length in pixels
        :param step: Pixels moved per frame
        :param glitter_prob: Probability of glitter pixels (0-255)
        :param speed: Frame interval in seconds

        Example
        -------
        ```python
            >>> fx.meteor_rain(count=8, trail=12, step=3)
        ```
        """
        ...
    
    def plasma(
        self,
        *,
        speed: float = 0.008,
        kx: int = 4,
        ky: int = 4,
        hue_step: int = 3
    ) -> None:
        """
        Smooth plasma color wave effect.
        
        Creates flowing, organic-looking color patterns using
        sine wave interference.
        
        :param speed: Frame interval in seconds
        :param kx: Horizontal frequency multiplier
        :param ky: Vertical frequency multiplier
        :param hue_step: Color cycling speed per frame
        
        Example
        -------
        ```python
            >>> fx.plasma(kx=6, ky=6, hue_step=5)
        ```
        """
        ...
    
    def fireworks(
        self,
        *,
        rockets: int = 3,
        tail_glow: int = 40,
        gravity: int = 10,
        drag_num: int = 255,
        drag_den: int = 260,
        sparks: int = 36,
        burst_speed: int = 220,
        life_decay: int = 12,
        speed: float = 0.012,
        stagger: int = 4
    ) -> None:
        """
        Multi-rocket fireworks display.
        
        Rockets launch from the bottom, rise, and explode into
        colorful particle bursts with physics simulation.
        
        :param rockets: Number of simultaneous rockets (1-5)
        :param tail_glow: Rocket trail fade factor (0-255)
        :param gravity: Downward acceleration on particles
        :param drag_num: Air drag numerator (with drag_den forms drag ratio)
        :param drag_den: Air drag denominator
        :param sparks: Total spark particles per explosion
        :param burst_speed: Initial velocity of explosion particles
        :param life_decay: How fast spark brightness fades
        :param speed: Frame interval in seconds
        :param stagger: Delay between rocket launches (in frames)
        
        Example
        -------
        ```python
            >>> fx.fireworks(rockets=4, sparks=48, burst_speed=250)
        ```
        """
        ...
    
    def campfire(
        self,
        *,
        cooling: int = 55,
        sparking: int = 120,
        speed: float = 0.010,
        ember_particles: int = 28,
        ember_decay: int = 18,
        base_rows: int = 2
    ) -> None:
        """
        Realistic campfire flame simulation.
        
        Uses a heat diffusion algorithm with rising embers to create
        a natural-looking fire effect.
        
        :param cooling: How quickly flames cool down (higher = cooler)
        :param sparking: Probability of new sparks at the base (0-255)
        :param speed: Frame interval in seconds
        :param ember_particles: Number of floating ember particles
        :param ember_decay: How fast embers fade as they rise
        :param base_rows: Height of the fire's base zone
        
        Example
        -------
        ```python
            >>> fx.campfire(cooling=45, sparking=150, ember_particles=35)
        ```
        """
        ...
    
    def ripple(
        self,
        *,
        speed: float = 0.010,
        wavelength: int = 10,
        phase_step: int = 3,
        center: Optional[Tuple[int, int]] = None
    ) -> None:
        """
        Expanding ripple rings from a center point.
        
        Creates concentric color rings that expand outward like
        ripples on water.
        
        :param speed: Frame interval in seconds
        :param wavelength: Distance between color bands (smaller = tighter rings)
        :param phase_step: Animation speed (color cycle per frame)
        :param center: Origin point (x, y), defaults to matrix center
        
        Example
        -------
        ```python
            >>> fx.ripple(wavelength=8, phase_step=5, center=(80, 8))
        ```
        """
        ...
    
    def matrix_rain(
        self,
        *,
        speed: float = 0.012,
        spawn_prob: int = 70,
        decay: int = 28,
        head_boost: int = 255,
        trail_boost: int = 120
    ) -> None:
        """
        "Matrix" style falling digital rain effect.
        
        Green vertical streams fall down the matrix with bright heads
        and fading trails, reminiscent of the Matrix movie.
        
        :param speed: Frame interval in seconds
        :param spawn_prob: Probability of spawning new drops (0-255)
        :param decay: How fast trails fade
        :param head_boost: Brightness of the leading pixel
        :param trail_boost: Brightness boost for pixels just behind the head
        
        Example
        -------
        ```python
            >>> fx.matrix_rain(spawn_prob=100, decay=20)
        ```
        """
        ...
    
    def neon_checkerboard(
        self,
        *,
        speed: float = 0.010,
        tile: int = 4,
        pulse_step: int = 3,
        hue_shift: int = 64,
        edge_boost: int = 80
    ) -> None:
        """
        Pulsing neon checkerboard pattern.
        
        A grid of alternating colored tiles that pulse with
        enhanced edges for a neon glow effect.
        
        :param speed: Frame interval in seconds
        :param tile: Size of each tile in pixels
        :param pulse_step: Animation speed per frame
        :param hue_shift: Color difference between alternating tiles
        :param edge_boost: Extra brightness at tile edges (0-255)
        
        Example
        -------
        ```python
            >>> fx.neon_checkerboard(tile=8, hue_shift=80)
        ```
        """
        ...
    
    def petal_vortex(
        self,
        *,
        speed: float = 0.010,
        petals: int = 6,
        spin_step: int = 3,
        radial: int = 3,
        contrast: int = 200
    ) -> None:
        """
        Rotating flower-like vortex pattern.
        
        Creates a spinning pattern with petal-like structures
        radiating from the center.
        
        :param speed: Frame interval in seconds
        :param petals: Number of petal structures (minimum 3)
        :param spin_step: Rotation speed per frame
        :param radial: Radial brightness gradient strength
        :param contrast: Pattern contrast level (0-255)
        
        Example
        -------
        ```python
            >>> fx.petal_vortex(petals=8, spin_step=5, contrast=220)
        ```
        """
        ...
    
    def spark_stream(
        self,
        *,
        speed: float = 0.010,
        emitters: int = 3,
        spawn_rate: int = 4,
        max_sparks: int = 48,
        base_hue: int = 150,
        hue_jitter: int = 20,
        fade: int = 220,
        gravity: int = 6,
        swirl: int = 10
    ) -> None:
        """
        Upward-rising spark fountain effect.
        
        Multiple emitter points shoot sparks upward with physics
        simulation including gravity and swirling motion.
        
        :param speed: Frame interval in seconds
        :param emitters: Number of spark emitter points (1-5)
        :param spawn_rate: Sparks spawned per frame
        :param max_sparks: Maximum simultaneous particles
        :param base_hue: Base color hue (0-255, cyan=150)
        :param hue_jitter: Random hue variation range
        :param fade: Background fade factor (0-255)
        :param gravity: Downward pull on particles
        :param swirl: Side-to-side oscillation strength
        
        Example
        -------
        ```python
            >>> fx.spark_stream(emitters=4, max_sparks=64, base_hue=200)
        ```
        """
        ...

    # ========== Signboard-Optimized Effects (for wide displays like 160x16) ==========

    def horizontal_wave(
        self,
        *,
        speed: float = 0.008,
        wavelength: int = 20,
        phase_step: int = 4,
        brightness_wave: bool = True
    ) -> None:
        """
        Horizontal rainbow wave optimized for wide signboards.
        
        Creates a smooth color wave flowing horizontally across the display,
        ideal for wide aspect ratios like 160x16.
        
        :param speed: Frame interval in seconds
        :param wavelength: Number of pixels for one full color cycle
        :param phase_step: How fast colors shift per frame (1-10)
        :param brightness_wave: If True, adds vertical brightness variation
            (center brighter than edges)
        
        Example
        -------
        ```python
            >>> fx.horizontal_wave(wavelength=30, phase_step=5)
        ```
        """
        ...

    def comet_horizontal(
        self,
        *,
        count: int = 3,
        speed: float = 0.008,
        trail: int = 25,
        direction: str = "left",
        colors: Optional[Sequence[Color]] = None,
        fade: int = 230
    ) -> None:
        """
        Horizontal comets with trails for signboards.
        
        Multiple comets streak across the display horizontally,
        leaving fading trails behind them.
        
        :param count: Number of comets (1-8)
        :param speed: Frame interval in seconds
        :param trail: Trail length in pixels
        :param direction: Movement direction, "left" or "right"
        :param colors: List of RGB colors for comets, if None uses rainbow distribution
        :param fade: Trail fade factor (200-255, higher = longer trails)
        
        Example
        -------
        ```python
            >>> fx.comet_horizontal(count=4, direction="right", fade=240)
        ```
        """
        ...

    def scrolling_gradient(
        self,
        *,
        speed: float = 0.006,
        colors: Optional[Sequence[Color]] = None,
        segment_width: int = 40
    ) -> None:
        """
        Smooth scrolling color gradient for signboards.
        
        Creates a continuous gradient that scrolls horizontally,
        blending smoothly between color stops.
        
        :param speed: Frame interval in seconds
        :param colors: List of RGB colors for gradient stops, if None uses a 7-color rainbow
        :param segment_width: Width of each color segment in pixels
        
        Example
        -------
        ```python
            >>> fx.scrolling_gradient(
            ...     colors=[(255,0,0), (0,255,0), (0,0,255)],
            ...     segment_width=50
            ... )
        ```
        """
        ...

    def audio_bars(
        self,
        *,
        speed: float = 0.015,
        bars: int = 16,
        decay: int = 25,
        attack: int = 80,
        color_mode: str = "gradient",
        base_color: Color = (0, 255, 128)
    ) -> None:
        """
        Simulated audio visualizer bars.
        
        Displays animated vertical bars that simulate an audio
        spectrum analyzer, with random movement.
        
        :param speed: Frame interval in seconds
        :param bars: Number of vertical bars
        :param decay: How fast bars fall (1-50)
        :param attack: Random jump probability (1-100)
        :param color_mode: "gradient" for height-based coloring (green→yellow→red),
            or "solid" for single color
        :param base_color: Color for solid mode
        
        Example
        -------
        ```python
            >>> fx.audio_bars(bars=16, color_mode="gradient")
        ```
        """
        ...

    def fire_horizontal(
        self,
        *,
        speed: float = 0.012,
        intensity: int = 150,
        cooling: int = 40,
        direction: str = "right"
    ) -> None:
        """
        Horizontal fire effect spreading across the signboard.
        
        Uses heat diffusion algorithm to create flames that
        spread horizontally from one edge.
        
        :param speed: Frame interval in seconds
        :param intensity: Fire intensity at the source edge (100-255)
        :param cooling: Cooling rate, higher = flames dissipate faster (20-80)
        :param direction: Fire spread direction, "left" or "right"
        
        Example
        -------
        ```python
            >>> fx.fire_horizontal(intensity=180, direction="left")
        ```
        """
        ...

    def scanner(
        self,
        *,
        speed: float = 0.006,
        width: int = 8,
        color: Color = (255, 0, 0),
        fade: int = 220,
        bounce: bool = True
    ) -> None:
        """
        Knight Rider style scanner effect.
        
        A bright beam sweeps back and forth across the display,
        leaving a fading trail.
        
        :param speed: Frame interval in seconds
        :param width: Scanner beam width in pixels
        :param color: Scanner beam color (RGB tuple)
        :param fade: Trail fade factor (200-255)
        :param bounce: If True, bounces at edges; if False, wraps around
        
        Example
        -------
        ```python
            >>> fx.scanner(width=12, color=(0, 0, 255), bounce=True)
        ```
        """
        ...
