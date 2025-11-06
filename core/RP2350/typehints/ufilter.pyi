"""
Signal Processing Filter Library

Advanced signal processing filters for sensor data processing, noise reduction,
and real-time signal conditioning. Designed for MicroPython with performance
optimization and memory efficiency for embedded systems.

Features:

- Base filter interface for consistent API across all filter types
- Low-pass, high-pass, and band-pass filters with frequency specifications
- Kalman filter for optimal state estimation and noise reduction
- Moving average and median filters for robust signal smoothing
- Adaptive filters with automatic parameter adjustment
- Cascaded and parallel filter architectures for complex processing
- Memory-efficient implementations optimized for embedded systems
- Real-time performance with @micropython.native optimization
- Comprehensive error handling and parameter validation

Supported Filter Types:

- Alpha: Direct coefficient control for exponential smoothing
- LowPass/HighPass: Frequency-domain filtering with automatic design
- TauLowPass: Time-constant based low-pass filter with variable/fixed sampling
- SlewRateLimiter: Rate-of-change limiter with independent rise/fall rates
- MovingAverage: Linear phase smoothing with circular buffer
- Median: Non-linear outlier rejection and impulse noise removal
- RMS: Power estimation and signal amplitude monitoring
- Kalman: Optimal estimation with process and measurement noise modeling
- Adaptive: Self-adjusting smoothing based on signal dynamics
- Biquad: Second-order IIR filters with direct coefficient specification
- Butterworth: Maximally flat frequency response with automatic design
- FIR: Finite impulse response with custom tap coefficients
- AngleEMA: Exponential moving average for angular data with wrap-around
- PID: Full-featured PID controller with anti-windup and tracking
- FilterChain: Serial connection of multiple filters for complex processing

Performance:

- Optimized for low-power embedded devices with limited memory
- Configurable parameters for different noise levels and response times
- Efficient algorithms with O(1) or O(N) complexity per sample
- Minimal memory footprint with intelligent buffer management
- Non-blocking operation modes for real-time applications
- Automatic numerical stability protection and overflow handling

Applications:

- Sensor data smoothing and noise reduction
- Biomedical signal processing (EMG, ECG, EEG)
- Audio processing and digital signal conditioning
- Motion tracking and accelerometer filtering
- Environmental monitoring and data logging
- Industrial measurement and control systems
- Communication signal processing and detection
- Motor control and robotics with PID controllers
- IMU and compass heading filtering with angle wrap-around

Mathematical Foundation:

- Proven filter designs based on established signal processing theory
- Support for both IIR (Infinite Impulse Response) and FIR (Finite Impulse Response) structures
- Linear and non-linear filtering techniques for different noise characteristics
- Frequency-domain and time-domain filter specifications
- Optimal estimation theory implementation (Kalman filtering)
- Statistical signal processing methods for robust performance
- Control theory implementations (PID with anti-windup)
- Circular statistics for angular data processing

"""

import micropython

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


class FilterError(Exception):
    """Base exception for filter-related errors"""
    pass

class FilterConfigurationError(FilterError):
    """Raised when filter parameters are invalid"""
    pass

class FilterOperationError(FilterError):
    """Raised when filter operation fails"""
    pass


class Base:
    """
    Base class for all signal processing filters.
    
    This class provides a consistent interface for all filter implementations with
    standardized methods for processing, resetting, and configuration. All filter
    subclasses inherit from this base class to ensure consistent behavior and API
    across different filter types.
    
    The Base establishes the fundamental contract that all filters must follow:

    - Process samples one at a time through update()
    - Support batch processing for efficiency
    - Maintain internal state with reset capability
    - Track processing statistics
    - Provide parameter validation utilities
    
    Features:
    
        - Consistent interface for all filter implementations
        - Sample counting and processing statistics
        - Built-in parameter validation methods
        - Batch processing capabilities
        - Function call interface support (__call__)
        - Reset functionality for filter state management
        - Memory-efficient implementations
        - Real-time performance optimization
    
    Common Operations:

        - update(): Process single sample through filter
        - process_batch(): Process multiple samples efficiently
        - reset(): Reset filter to initial state
        - __call__(): Allow filter to be called as function
        - sample_count: Get number of processed samples
    
    Parameter Validation:

        - Numeric range validation with min/max bounds
        - Type checking with meaningful error messages
        - Configuration error reporting with detailed messages
        - Consistent error handling across all filter types
    
    Inheritance Pattern:
        All concrete filter classes should inherit from Base and implement
        the update() method. The base class provides common functionality while
        derived classes implement specific filtering algorithms.
    """
    
    def __init__(self) -> None:
        """
        Initialize base filter with default state.
        
        Sets up internal state tracking and prepares filter for operation.
        All filter implementations should call this base constructor to ensure
        proper initialization of common state variables.
        
        Initializes:
        
            - Sample counter to zero
            - Initialization flag to False
            - Internal state variables for tracking
        
        Example
        -------
        ```python
            >>> # Basic subclass implementation pattern
            >>> class CustomFilter(Base):
            ...     def __init__(self, custom_param):
            ...         super().__init__()  # Call base constructor first
            ...         self.custom_param = custom_param
            ...         self.internal_state = 0.0
            ...     
            ...     def update(self, x):
            ...         self._sample_count += 1  # Track sample count
            ...         self.internal_state = self.internal_state * 0.9 + x * 0.1
            ...         return self.internal_state
            >>> 
            >>> # Create filter instance
            >>> my_filter = CustomFilter(custom_param=5.0)
            >>> print(f"Initial sample count: {my_filter.sample_count}")  # 0
        ```
        """

    @micropython.native
    def update(self, x: float) -> float:
        """
        Process a single sample through the filter.
        
        This is the core method that all filter subclasses must implement.
        It takes an input sample and returns the filtered output sample.
        The method should update internal filter state and increment the
        sample counter for proper statistics tracking.
        
        :param x: Input sample value (numeric type, will be converted to float)
        :return: Filtered output sample as float
        
        :raises NotImplementedError: This base method must be overridden by subclasses
        
        Implementation Guidelines:
            - Always increment self._sample_count
            - Convert input to float for consistency
            - Update internal filter state
            - Return filtered result as float
            - Handle edge cases (NaN, infinity) appropriately
        
        Example
        -------
        ```python
            >>> # Real-time processing example
            >>> filter_obj = LowPass(fc=1.0, fs=10.0)
            >>> 
            >>> # Read sensor data (simulated here)
            >>> raw_value = 32768  # Simulated ADC reading
            >>> voltage = raw_value * 3.3 / 65535  # Convert to voltage
            >>> 
            >>> # Filter the signal
            >>> filtered_voltage = filter_obj.update(voltage)
            >>> print(f"Raw: {voltage:.3f}V → Filtered: {filtered_voltage:.3f}V")
            >>> 
            >>> # Process a sequence of samples
            >>> sequence = [1.0, 2.0, 1.5, 0.5, 1.0]
            >>> results = []
            >>> for value in sequence:
            ...     results.append(filter_obj.update(value))
            >>> print(f"Processed {filter_obj.sample_count} samples")
        ```
        """
    
    def reset(self) -> None:
        """
        Reset filter to initial state.
        
        Clears all internal state and prepares the filter for fresh processing.
        This method resets the sample counter and initialization flag, and
        subclasses should override this method to reset their specific state
        while calling the base implementation.
        
        Base Reset Operations:
            - Resets sample counter to zero
            - Clears initialization flag
            - Prepares filter for new data stream
        
        Subclass Override Pattern:
            Subclasses should call super().reset() first, then reset their
            own internal state variables to initial values.
        
        Example
        -------
        ```python
            >>> # Reset behavior demonstration
            >>> filter_obj = MovingAverage(window_size=5)
            >>> 
            >>> # Process a few samples
            >>> for i in range(10):
            ...     filter_obj.update(i)
            >>> 
            >>> print(f"Before reset: {filter_obj.sample_count} samples processed")
            >>> 
            >>> # Reset the filter
            >>> filter_obj.reset()
            >>> print(f"After reset: {filter_obj.sample_count} samples processed")
            >>> 
            >>> # Start fresh processing
            >>> new_result = filter_obj.update(20.0)
            >>> print(f"First new sample result: {new_result}")
        ```
        """
    
    def __call__(self, x: float) -> float:
        """
        Allow filter to be called as a function.
        
        This enables convenient functional-style usage of filters by making
        the filter object callable. It's equivalent to calling the update()
        method directly but provides a more concise syntax for functional
        programming patterns.
        
        :param x: Input sample value (numeric type)
        :return: Filtered output sample as float
        
        Functional Programming Benefits:
        
            - Cleaner syntax for single-sample processing
            - Compatible with higher-order functions
            - Enables filter chaining and composition
            - Supports lambda-like usage patterns
        
        Example
        -------
        ```python
            >>> filter_obj = LowPass(fc=1.0, fs=10.0)
            >>> 
            >>> # These are equivalent:
            >>> result1 = filter_obj.update(5.0)
            >>> result2 = filter_obj(5.0)
            >>> print(f"update(): {result1:.3f}, __call__(): {result2:.3f}")
            >>> 
            >>> # Functional programming style
            >>> data = [1.0, 2.0, 3.0, 4.0, 5.0]
            >>> filtered_data = [filter_obj(x) for x in data]
            >>> print(f"Filtered: {[f'{x:.2f}' for x in filtered_data]}")
            >>> 
            >>> # Filter composition
            >>> def create_filter_pipeline(data):
            ...     noise_filter = Median(window_size=3)
            ...     smooth_filter = LowPass(fc=2.0, fs=20.0)
            ...     
            ...     # Chain filters using __call__
            ...     return [smooth_filter(noise_filter(x)) for x in data]
        ```
        """
    
    def process_batch(self, samples: list) -> list:
        """
        Process multiple samples efficiently.
        
        Processes a list or sequence of input samples and returns a list of
        filtered outputs. This method provides a convenient way to process
        multiple samples at once and can be overridden by subclasses for
        more efficient batch processing if the filter algorithm allows it.
        
        :param samples: Iterable of input sample values (list, tuple, etc.)
        :return: List of filtered output samples in the same order
        
        :raises TypeError: If samples is not iterable
        
        Batch Processing Benefits:
        
            - Convenient for processing stored data
            - Can be optimized by subclasses for better performance
            - Maintains sample order (FIFO processing)
            - Reduces function call overhead for large datasets
            - Suitable for offline processing and analysis
        
        Example
        -------
        ```python
            >>> filter_obj = MovingAverage(window_size=3)
            >>> 
            >>> # Process batch of samples
            >>> input_data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
            >>> output_data = filter_obj.process_batch(input_data)
            >>> 
            >>> print("Input: ", input_data)
            >>> print("Output:", [f"{x:.2f}" for x in output_data])
            >>> # Output: ['1.00', '1.50', '2.00', '3.00', '4.00', '5.00']
            >>> 
            >>> # File processing example
            >>> def process_data_file(filename, filter_obj):
            ...     # Read data from file (simulated)
            ...     raw_data = [1.2, 1.5, 1.1, 1.8, 1.3]  # Simulated file data
            ...     
            ...     # Process entire dataset at once
            ...     filtered_data = filter_obj.process_batch(raw_data)
            ...     
            ...     print(f"Processed {len(filtered_data)} samples")
            ...     return filtered_data
        ```
        """
    
    @property
    def sample_count(self) -> int:
        """
        Get number of samples processed since reset.
        
        Returns the total count of samples that have been processed through
        this filter instance since the last reset() call. This provides
        useful statistics for monitoring filter usage and performance.
        
        :return: Number of samples processed (non-negative integer)
        
        Statistics and Monitoring:
        
            - Tracks total throughput since last reset
            - Useful for performance analysis and debugging
            - Enables periodic operations based on sample count
            - Helps with filter state management
        
        Example
        -------
        ```python
            >>> filter_obj = Median(window_size=5)
            >>> 
            >>> print(f"Initial count: {filter_obj.sample_count}")  # 0
            >>> 
            >>> # Process some samples
            >>> for i in range(10):
            ...     result = filter_obj.update(i)
            >>> 
            >>> print(f"Processed {filter_obj.sample_count} samples")  # 10
            >>> 
            >>> # Periodic logging based on sample count
            >>> def process_with_logging(filter_obj, input_data, log_interval=5):
            ...     for sample in input_data:
            ...         result = filter_obj.update(sample)
            ...         
            ...         # Log periodically based on sample count
            ...         if filter_obj.sample_count % log_interval == 0:
            ...             print(f"Processed {filter_obj.sample_count} samples")
        ```
        """
    
    def _validate_numeric(self, value: float, name: str, min_val: float = None, max_val: float = None) -> float:
        """
        Validate numeric parameters with optional range checking.
        
        Ensures that a parameter is numeric and optionally within specified bounds.
        Used internally by filter implementations for parameter validation during
        initialization and configuration updates.
        
        :param value: Value to validate (will be converted to float)
        :param name: Parameter name for error messages (descriptive string)
        :param min_val: Minimum allowed value (inclusive, optional)
        :param max_val: Maximum allowed value (inclusive, optional)
        :return: Validated numeric value as float
        
        :raises FilterConfigurationError: If value is invalid or out of range
        :raises TypeError: If value cannot be converted to float
        
        Validation Rules:
            - Value must be convertible to float
            - If min_val specified, value must be >= min_val
            - If max_val specified, value must be <= max_val
            - Provides clear error messages with parameter names
        
        Example
        -------
        ```python
            >>> # In a filter subclass implementation
            >>> class LowPass(Base):
            ...     def __init__(self, fc, fs):
            ...         super().__init__()
            ...         
            ...         # Validate sampling frequency
            ...         self.fs = self._validate_numeric(fs, "sampling frequency", min_val=0.0)
            ...         
            ...         # Validate cutoff frequency with both min and max bounds
            ...         self.fc = self._validate_numeric(
            ...             fc, "cutoff frequency", min_val=0.0, max_val=self.fs/2
            ...         )
            ...         
            ...         # Calculate filter coefficient
            ...         self.alpha = 1.0 - exp(-2.0 * pi * self.fc / self.fs)
            >>> 
            >>> # Valid parameter usage
            >>> filter1 = LowPass(fc=10.0, fs=100.0)
            >>> print(f"Valid filter created: fc={filter1.fc}, fs={filter1.fs}")
            >>> 
            >>> # Invalid parameter usage (will raise error)
            >>> try:
            ...     filter2 = LowPass(fc=60.0, fs=100.0)  # fc >= fs/2 (Nyquist violation)
            >>> except FilterConfigurationError as e:
            ...     print(f"Configuration error: {e}")
            >>> # Output: "cutoff frequency must be <= 50.0, got 60.0"
        ```
        """


class Alpha(Base):
    """
    Single-pole IIR filter with direct alpha coefficient specification.
    
    A simple first-order infinite impulse response (IIR) filter that implements
    exponential smoothing with a user-specified alpha coefficient. This filter
    provides direct control over the filtering strength without requiring frequency
    domain calculations, making it ideal for rapid prototyping, real-time tuning,
    and applications where simplicity is preferred over frequency-domain precision.
    
    The filter implements the classic exponential smoothing equation:
        y[n] = α·x[n] + (1-α)·y[n-1]
    
    Where:
    
        - α (alpha) is the smoothing factor (0 < α ≤ 1)
        - Higher α values → faster response, less smoothing
        - Lower α values → slower response, more smoothing
    
    Key Characteristics:
    
        - Direct coefficient control without frequency calculations
        - Real-time adjustable alpha parameter
        - Memory-efficient single-delay implementation
        - Predictable exponential decay response
        - Always stable for valid alpha range
        - Zero-phase initialization capability
    
    Applications:
    
        - Sensor data smoothing with adjustable responsiveness
        - Real-time signal conditioning with dynamic tuning
        - Rapid prototyping and algorithm development
        - Educational demonstrations of IIR filtering
        - Simple noise reduction for embedded systems
        - Adaptive filtering with coefficient modulation
    
    Mathematical Properties:
    
        - Impulse response: h[n] = α·(1-α)ⁿ for n ≥ 0
        - Step response: y[n] = 1 - (1-α)ⁿ⁺¹ for unit step
        - Time constant: τ = -1/ln(1-α) samples
        - 3dB frequency: f₃dB ≈ -fs·ln(1-α)/(2π) Hz
        - DC gain: 0dB (unity gain)
        - Stability: Always stable for 0 < α ≤ 1
    
    Alpha Selection Guidelines:
    
        - α = 0.1: Heavy smoothing, slow response (τ ≈ 9.5 samples)
        - α = 0.2: Moderate smoothing (τ ≈ 4.5 samples)
        - α = 0.5: Balanced response (τ ≈ 1.4 samples)
        - α = 0.8: Light smoothing, fast response (τ ≈ 0.7 samples)
        - α = 1.0: No filtering (pass-through)
    
    """
    
    def __init__(self, alpha: float, initial: float = 0.0) -> None:
        """
        Initialize alpha filter with specified smoothing coefficient.
        
        Creates a first-order IIR filter with direct alpha coefficient control,
        providing exponential smoothing without requiring frequency domain
        calculations. The alpha parameter directly controls the trade-off
        between responsiveness and smoothing strength.
        
        :param alpha: Smoothing coefficient in range (0, 1]

            - Higher values (→1.0): Less smoothing, faster response
            - Lower values (→0.0): More smoothing, slower response
            - Typical range: 0.01 to 0.9 for practical applications

        :param initial: Initial output value for filter state (default: 0.0)
                       Useful for avoiding startup transients when expected
                       signal level is known
        
        :raises ValueError: If alpha is not in valid range (0, 1]
        :raises TypeError: If parameters cannot be converted to numeric types
        
        Alpha Selection Guidelines:
            Choose alpha based on your application requirements:
            
            Conservative Filtering (α = 0.01 to 0.1):

                - Heavy noise suppression
                - Slow response to signal changes
                - Good for: Temperature monitoring, battery voltage
                - Time constant: ~10-100 samples
            
            Moderate Filtering (α = 0.1 to 0.3):

                - Balanced noise reduction and responsiveness
                - General-purpose applications
                - Good for: Sensor smoothing, control systems
                - Time constant: ~3-10 samples
            
            Light Filtering (α = 0.3 to 0.7):

                - Minimal smoothing, fast response
                - Preserves signal dynamics
                - Good for: Audio processing, vibration monitoring
                - Time constant: ~0.5-3 samples
            
            Minimal Filtering (α = 0.7 to 1.0):

                - Very light smoothing
                - Near real-time response
                - Good for: Control feedback, rapid prototyping
                - Time constant: <1 sample
        
        Mathematical Relationships:
            Time Constant: τ = -1/ln(1-α) samples
            3dB Frequency: f₃dB ≈ -fs·ln(1-α)/(2π) Hz (approximate)
            Step Response: y[n] = initial + (target-initial)·(1-(1-α)ⁿ⁺¹)
            Settling Time (95%): n₉₅% ≈ 3·τ = -3/ln(1-α) samples
        
        Example
        -------
        ```python
            >>> # Creating filters for different applications
            >>> # Conservative filtering for temperature sensor
            >>> temp_filter = Alpha(alpha=0.05, initial=25.0)
            >>> print(f"Time constant: {-1/log(1-0.05):.1f} samples")  # ~19.5
            >>> 
            >>> # Moderate filtering for general sensor data
            >>> sensor_filter = Alpha(alpha=0.2, initial=0.0)
            >>> print(f"Time constant: {-1/log(1-0.2):.1f} samples")  # ~4.5
            >>> 
            >>> # Light filtering for responsive control
            >>> control_filter = Alpha(alpha=0.6, initial=5.0)
            >>> print(f"Time constant: {-1/log(1-0.6):.1f} samples")  # ~1.1
            >>> 
            >>> # Parameter validation examples
            >>> try:
            ...     invalid_filter = Alpha(alpha=0.0)  # Too low
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     invalid_filter = Alpha(alpha=1.5)  # Too high
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
        ```
        """

    @property
    def alpha(self) -> float:
        """
        Get current alpha coefficient.
        
        Returns the current smoothing coefficient value. This property
        allows runtime inspection of the filter's responsiveness setting.
        
        :return: Current alpha value (0 < α ≤ 1)
        
        The alpha value determines the filter's behavior:
            
            - α → 1.0: Minimal filtering, maximum responsiveness
            - α → 0.0: Maximum filtering, minimal responsiveness
        
        Example
        -------
        ```python
            >>> # Inspecting and analyzing filter characteristics
            >>> filter_obj = Alpha(alpha=0.3)
            >>> print(f"Current alpha: {filter_obj.alpha}")  # 0.3
            >>> 
            >>> # Check filter characteristics
            >>> time_constant = -1 / log(1 - filter_obj.alpha)
            >>> print(f"Time constant: {time_constant:.2f} samples")
            >>> 
            >>> # Calculate settling time
            >>> settling_time = -3 / log(1 - filter_obj.alpha)
            >>> print(f"95% settling time: {settling_time:.2f} samples")
            >>> 
            >>> # Estimate frequency response (with 100 Hz sampling)
            >>> fs = 100.0  # Hz
            >>> cutoff_freq = -fs * log(1 - filter_obj.alpha) / (2 * pi)
            >>> print(f"Approximate 3dB cutoff: {cutoff_freq:.2f} Hz")
        ```
        """

    @alpha.setter
    def alpha(self, value: float) -> None:
        """
        Set alpha coefficient with validation.
        
        Updates the smoothing coefficient while ensuring it remains within
        the valid range. This allows real-time adjustment of filter
        characteristics without recreating the filter object.
        
        :param value: New alpha value (0 < α ≤ 1)
        
        :raises ValueError: If value is not in valid range (0, 1]
        :raises TypeError: If value cannot be converted to float
        
        Real-time Tuning Applications:
            
            - Adaptive filtering based on signal conditions
            - User-adjustable smoothing controls
            - Automatic noise level compensation
            - Dynamic system response optimization
        
        Example
        -------
        ```python
            >>> # Real-time filter adjustment based on conditions
            >>> filter_obj = Alpha(alpha=0.2)
            >>> 
            >>> # Adjust filtering strength in real-time
            >>> for noise_level in [0.1, 0.5, 0.9, 0.3]:
            ...     if noise_level > 0.7:
            ...         filter_obj.alpha = 0.05  # Heavy filtering for high noise
            ...     elif noise_level < 0.2:
            ...         filter_obj.alpha = 0.6   # Light filtering for low noise
            ...     else:
            ...         filter_obj.alpha = 0.2   # Moderate filtering
            ...     
            ...     print(f"Noise: {noise_level:.1f} → Alpha: {filter_obj.alpha:.2f}")
            >>> # Noise: 0.1 → Alpha: 0.60
            >>> # Noise: 0.5 → Alpha: 0.20
            >>> # Noise: 0.9 → Alpha: 0.05
            >>> # Noise: 0.3 → Alpha: 0.20
            >>> 
            >>> # User interface for smoothing adjustment
            >>> def set_smoothing_level(filter_obj, level):
            ...     '''Set smoothing from user-friendly 1-10 scale.'''
            ...     if not (1 <= level <= 10):
            ...         raise ValueError("Smoothing level must be 1-10")
            ...     
            ...     # Convert 1-10 scale to alpha (1=heavy smoothing, 10=light)
            ...     filter_obj.alpha = 0.02 + (level - 1) * 0.1
            ...     print(f"Smoothing level {level} → α={filter_obj.alpha:.3f}")
            >>> 
            >>> user_filter = Alpha(alpha=0.2)
            >>> set_smoothing_level(user_filter, 3)  # Smoothing level 3 → α=0.220
            >>> set_smoothing_level(user_filter, 8)  # Smoothing level 8 → α=0.720
        ```
        """

    @micropython.native
    def update(self, x: float) -> float:
        """
        Update filter with new sample and return filtered output.
        
        Applies exponential smoothing to the input sample using the current
        alpha coefficient. This is the core filtering operation that implements
        the first-order IIR difference equation.
        
        :param x: Input sample value (any numeric type, converted to float)
        :return: Filtered output sample as float
        
        :raises TypeError: If input cannot be converted to float
        
        Algorithm Details:
            The filter implements: y[n] = α·x[n] + (1-α)·y[n-1]
            
            Where:
            
            - y[n] is the current output
            - x[n] is the current input
            - y[n-1] is the previous output (stored in self.y)
            - α is the smoothing coefficient (self._alpha)
        
        Performance Characteristics:
            
            - O(1) computational complexity
            - Single multiply-accumulate operation
            - Minimal memory usage (one float for previous output)
            - Optimized with @micropython.native decorator
            - Suitable for high-frequency real-time processing
        
        Numerical Properties:
            
            - Always stable for 0 < α ≤ 1
            - No risk of overflow for finite inputs
            - Maintains precision for typical signal ranges
            - Graceful handling of extreme input values
        
        Example
        -------
        ```python
            >>> # Processing samples through the filter
            >>> filter_obj = Alpha(alpha=0.3, initial=0.0)
            >>> 
            >>> # Process a sequence of samples
            >>> test_sequence = [1.0, 2.0, 1.5, 3.0, 2.5, 1.0, 0.5]
            >>> 
            >>> print("Input  | Output | Change")
            >>> print("-" * 25)
            >>> 
            >>> for i, sample in enumerate(test_sequence):
            ...     previous_output = filter_obj.y
            ...     current_output = filter_obj.update(sample)
            ...     change = current_output - previous_output
            ...     
            ...     print(f"{sample:5.1f} | {current_output:6.3f} | {change:+6.3f}")
            >>> # Input  | Output | Change
            >>> # -------------------------
            >>> #   1.0 |  0.300 | +0.300
            >>> #   2.0 |  0.810 | +0.510
            >>> #   1.5 |  1.017 | +0.207
            >>> #   3.0 |  1.612 | +0.595
            >>> #   2.5 |  1.878 | +0.267
            >>> #   1.0 |  1.615 | -0.263
            >>> #   0.5 |  1.330 | -0.285
            >>> 
            >>> # Real-time filtering for sensor data
            >>> def process_sensor_data():
            ...     accel_filter = Alpha(alpha=0.1)  # Heavy smoothing
            ...     
            ...     # Simulate 10 sensor readings with noise
            ...     true_values = [1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 3.0, 3.0, 3.0, 3.0]
            ...     noise = [0.2, -0.3, 0.1, 0.4, -0.2, 0.3, -0.4, 0.2, -0.1, 0.3]
            ...     
            ...     print("Raw    | Filtered | Error")
            ...     print("-" * 30)
            ...     
            ...     for i, (true, n) in enumerate(zip(true_values, noise)):
            ...         raw = true + n  # Simulated noisy reading
            ...         filtered = accel_filter.update(raw)
            ...         error = abs(filtered - true)
            ...         
            ...         print(f"{raw:6.2f} | {filtered:8.2f} | {error:5.2f}")
        ```
        """
    
    def reset(self) -> None:
        """
        Reset filter to initial state while preserving configuration.
        
        Clears the filter's internal state (previous output value) and resets
        the sample counter, but maintains the alpha coefficient and initial
        value settings. This allows the filter to be reused for new data
        streams without reconfiguration.
        
        Reset Operations:
           
            - Restores output value to initial setting
            - Resets sample counter to zero
            - Preserves alpha coefficient
            - Preserves initial value setting
            - Prepares filter for new input sequence
        
        Use Cases:
           
            - Starting new measurement session
            - Switching between different signal sources
            - Clearing filter memory after transient events
            - Batch processing of multiple datasets
            - A/B testing with consistent initial conditions
        
        Example
        -------
        ```python
            >>> # Demonstrating filter reset for batch processing
            >>> filter_obj = Alpha(alpha=0.3, initial=5.0)
            >>> 
            >>> # Process first batch of data
            >>> first_batch = [6.0, 7.0, 8.0, 6.5, 7.5]
            >>> first_results = []
            >>> 
            >>> for sample in first_batch:
            ...     result = filter_obj.update(sample)
            ...     first_results.append(result)
            >>> 
            >>> print("First batch results:", [f"{x:.2f}" for x in first_results])
            >>> print(f"Final state: {filter_obj.y:.2f}, Samples: {filter_obj.sample_count}")
            >>> 
            >>> # Reset filter for second batch
            >>> filter_obj.reset()
            >>> print(f"After reset: {filter_obj.y:.2f}, Samples: {filter_obj.sample_count}")
            >>> 
            >>> # Process second batch with same filter
            >>> second_batch = [10.0, 9.5, 11.0, 10.5, 9.0]
            >>> second_results = []
            >>> 
            >>> for sample in second_batch:
            ...     result = filter_obj.update(sample)
            ...     second_results.append(result)
            >>> 
            >>> print("Second batch results:", [f"{x:.2f}" for x in second_results])
            >>> 
            >>> # Compare how each batch started from the same initial conditions
            >>> print(f"First sample: Batch 1={first_results[0]:.2f}, Batch 2={second_results[0]:.2f}")
        ```
        """


class LowPass(Base):
    """
    First-order low-pass filter with cutoff frequency specification.
    
    A digital low-pass filter that allows low-frequency components to pass through
    while attenuating high-frequency components above the cutoff frequency. This
    implementation uses a first-order IIR (Infinite Impulse Response) structure
    with exponential decay characteristics, making it ideal for noise reduction
    and signal smoothing applications.
    
    The filter implements the difference equation:
        
        y[n] = α·x[n] + (1-α)·y[n-1]
    
    Where α (alpha) is automatically calculated from the cutoff and sampling frequencies:
        
        α = 1 - exp(-2π·fc/fs)
    
    Features:
        
        - Automatic coefficient calculation from frequency specifications
        - Standard first-order low-pass response (-20dB/decade rolloff)
        - Configurable cutoff frequency and sampling rate
        - Memory-efficient single-delay implementation
        - Real-time processing with minimal computational overhead
        - Numerical stability through proper coefficient bounds
    
    Applications:
        
        - Sensor data smoothing and noise reduction
        - Anti-aliasing before downsampling
        - Signal conditioning for control systems
        - EMG/ECG signal preprocessing
        - Audio processing and equalization
        - Vibration analysis and filtering
    
    Mathematical Properties:
        
        - 3dB cutoff at specified frequency fc
        - Phase lag increases with frequency
        - Group delay: τ = (1-α)/(2π·fc·α)
        - Stability: Always stable for 0 < α ≤ 1
        - DC gain: 0dB (unity)
        - High-frequency attenuation: -20dB/decade
    
    """
    
    def __init__(self, fc: float, fs: float, initial: float = 0.0) -> None:
        """
        Initialize low-pass filter with frequency specifications.
        
        Creates a first-order digital low-pass filter by calculating the appropriate
        filter coefficient (alpha) from the specified cutoff and sampling frequencies.
        The filter uses bilinear transform equivalent for first-order analog prototype.
        
        :param fc: Cutoff frequency in Hz (3dB point, must be > 0 and < fs/2)
        :param fs: Sampling frequency in Hz (must be > 0 and > 2*fc)
        :param initial: Initial output value for filter state (default: 0.0)
        
        :raises ValueError: If frequencies are invalid or violate Nyquist criterion
        :raises TypeError: If parameters cannot be converted to float
        
        Filter Coefficient Calculation:
            The alpha coefficient is calculated using the formula:
        
            α = 1 - exp(-2π·fc/fs)
            
            This ensures:
        
            - Correct 3dB cutoff frequency at fc
            - Proper frequency response characteristics  
            - Numerical stability for all valid frequency ratios
            - Smooth transition between passband and stopband
        
        Frequency Constraints:
        
            - fc must be positive (fc > 0)
            - fc must be less than Nyquist frequency (fc < fs/2)
            - fs must be positive (fs > 0)
            - Recommended: fc should be at least 10x smaller than fs for good approximation
        
        Example
        -------
        ```python
            >>> # Audio processing filter
            >>> audio_filter = LowPass(fc=5000.0, fs=44100.0, initial=0.0)
            >>> print(f"Filter alpha: {audio_filter._alpha:.6f}")
            >>> 
            >>> # Sensor data filter  
            >>> sensor_filter = LowPass(fc=2.0, fs=100.0)
            >>> print(f"Cutoff: {sensor_filter.fc} Hz, Sampling: {sensor_filter.fs} Hz")
            >>> 
            >>> # Control system filter
            >>> control_filter = LowPass(fc=0.1, fs=10.0, initial=5.0)
            >>> print(f"Initial output: {control_filter.y}")
            >>> 
            >>> # Invalid configurations (will raise ValueError)
            >>> try:
            ...     invalid_filter = LowPass(fc=60.0, fs=100.0)  # fc >= fs/2
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     invalid_filter = LowPass(fc=-5.0, fs=100.0)  # Negative fc
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> # Coefficient analysis
            >>> def analyze_coefficients():
            ...     fs = 100.0
            ...     cutoffs = [0.1, 0.5, 1.0, 5.0, 10.0, 20.0, 40.0]
            ...     
            ...     print("Cutoff (Hz) | Alpha     | -3dB Freq | Time Const")
            ...     print("-" * 50)
            ...     
            ...     for fc in cutoffs:
            ...         if fc < fs / 2:
            ...             filter_obj = LowPass(fc=fc, fs=fs)
            ...             alpha = filter_obj._alpha
            ...             time_constant = (1 - alpha) / (2 * pi * fc * alpha)
            ...             
            ...             print(f"{fc:10.1f} | {alpha:8.6f} | {fc:8.1f} | {time_constant:9.3f}")
        ```
        """

    @micropython.native
    def update(self, x: float) -> float:
        """
        Update filter with new sample and return filtered output.
        
        Processes a single input sample through the first-order IIR low-pass filter
        using the difference equation: y[n] = α·x[n] + (1-α)·y[n-1]
        
        This method applies exponential smoothing to the input signal, where the
        filter coefficient α determines the balance between responsiveness to new
        samples and smoothness of the output.
        
        :param x: Input sample value (any numeric type, converted to float)
        :return: Filtered output sample as float
        
        :raises TypeError: If input cannot be converted to float
        
        Performance Characteristics:

            - O(1) computational complexity
            - Single multiply-add operation per sample
            - Minimal memory usage (single delay element)
            - Optimized with @micropython.native decorator
            - Suitable for real-time applications
        
        Signal Processing Properties:

            - Amplitude response: |H(f)| = α / sqrt((α²) + (1-α)²)
            - Phase response: φ(f) = -arctan((1-α)/α * sin(2πf/fs) / (1 + (1-α)cos(2πf/fs)))
            - Group delay: τ = (1-α)/(2πfc·α) at low frequencies
            - Step response: y(n) = α·(1-(1-α)ⁿ) for unit step input
        
        Example
        -------
        ```python
            >>> # Basic filtering operation
            >>> filter_obj = LowPass(fc=5.0, fs=50.0)
            >>> 
            >>> # Process single sample
            >>> output = filter_obj.update(10.0)
            >>> print(f"First sample: {output:.4f}")  # Shows initial response
            >>> 
            >>> # Process sequence of samples
            >>> input_sequence = [1.0, 2.0, 1.5, 3.0, 2.5, 1.0, 0.5]
            >>> output_sequence = []
            >>> 
            >>> for i, sample in enumerate(input_sequence):
            ...     filtered = filter_obj.update(sample)
            ...     output_sequence.append(filtered)
            ...     print(f"Sample {i}: {sample:4.1f} → {filtered:6.4f}")
            >>> 
            >>> # Analyze step response
            >>> def step_response_analysis():
            ...     step_filter = LowPass(fc=2.0, fs=20.0)
            ...     
            ...     print("Step Response Analysis:")
            ...     print("Sample | Input | Output | Error")
            ...     print("-" * 35)
            ...     
            ...     for n in range(20):
            ...         step_input = 1.0  # Unit step
            ...         output = step_filter.update(step_input)
            ...         
            ...         # Theoretical step response: 1 - (1-α)^n
            ...         alpha = step_filter._alpha
            ...         theoretical = 1.0 - (1.0 - alpha) ** (n + 1)
            ...         error = abs(output - theoretical)
            ...         
            ...         print(f"{n:6d} | {step_input:5.1f} | {output:6.4f} | {error:6.5f}")
            ...         
            ...         if output > 0.95:  # 95% of final value
            ...             print(f"95% settling time: {n} samples ({n/20:.2f} seconds)")
            ...             break
            >>> 
            >>> # Frequency response visualization
            >>> def visualize_frequency_response():
            ...     filter_obj = LowPass(fc=10.0, fs=100.0)
            ...     
            ...     # Test at various frequencies
            ...     test_freqs = [1, 2, 5, 10, 15, 20, 30, 40]
            ...     
            ...     print("Frequency Response:")
            ...     print("Freq (Hz) | Gain (dB) | Phase (deg)")
            ...     print("-" * 40)
            ...     
            ...     for freq in test_freqs:
            ...         # Calculate theoretical response
            ...         alpha = filter_obj._alpha
            ...         w = 2 * pi * freq / filter_obj.fs
            ...         
            ...         # Magnitude response
            ...         numerator = alpha
            ...         denominator = sqrt(alpha**2 + (1-alpha)**2 - 2*alpha*(1-alpha)*cos(w))
            ...         gain = numerator / denominator if denominator > 0 else 1.0
            ...         gain_db = 20 * log10(gain) if gain > 0 else -60
            ...         
            ...         # Phase response (simplified)
            ...         phase_rad = -atan2((1-alpha) * sin(w), alpha + (1-alpha) * cos(w))
            ...         phase_deg = phase_rad * 180 / pi
            ...         
            ...         print(f"{freq:8.1f} | {gain_db:9.2f} | {phase_deg:11.1f}")
        ```
        """
    
    def reset(self) -> None:
        """
        Reset filter to initial state while preserving configuration.
        
        Clears the filter's internal state (output history) and resets the sample
        counter, but maintains all configuration parameters like cutoff frequency,
        sampling frequency, and calculated coefficients. This allows the filter
        to be reused for new data streams without reconfiguration.
        
        Reset Operations:
        
            - Clears output history (y[n-1])
            - Resets sample counter to zero
            - Preserves filter coefficients and parameters
            - Restores initial output value
            - Prepares filter for new input sequence
        
        Use Cases:
        
            - Starting new measurement session
            - Switching between different signal sources
            - Clearing filter memory after transient events
            - Periodic reset to prevent numerical drift
            - Batch processing of multiple datasets
        
        Example
        -------
        ```python
            >>> filter_obj = LowPass(fc=5.0, fs=50.0, initial=2.0)
            >>> 
            >>> # Process some data
            >>> for i in range(10):
            ...     result = filter_obj.update(i)
            ...     print(f"Sample {i}: {result:.3f}")
            >>> 
            >>> print(f"Samples processed: {filter_obj.sample_count}")  # 10
            >>> print(f"Current output: {filter_obj.y:.3f}")
            >>> 
            >>> # Reset filter
            >>> filter_obj.reset()
            >>> print(f"After reset - Samples: {filter_obj.sample_count}")  # 0
            >>> print(f"After reset - Output: {filter_obj.y:.3f}")  # 2.0 (initial value)
            >>> 
            >>> # Filter is ready for new data with same configuration
            >>> result = filter_obj.update(100.0)
            >>> print(f"First new sample: {result:.3f}")
            >>> 
            >>> # Batch processing example
            >>> def process_multiple_datasets():
            ...     data_filter = LowPass(fc=2.0, fs=20.0)
            ...     
            ...     datasets = [
            ...         [1, 2, 3, 4, 5],
            ...         [10, 20, 30, 40, 50],
            ...         [0.1, 0.2, 0.3, 0.4, 0.5]
            ...     ]
            ...     
            ...     for i, dataset in enumerate(datasets):
            ...         print(f"Processing dataset {i+1}:")
            ...         
            ...         # Reset filter for each new dataset
            ...         data_filter.reset()
            ...         
            ...         for sample in dataset:
            ...             filtered = data_filter.update(sample)
            ...             print(f"  {sample:4.1f} → {filtered:6.3f}")
            ...         
            ...         print(f"  Dataset complete: {data_filter.sample_count} samples\n")
        ```
        """


class HighPass(Base):
    """
    First-order high-pass filter with cutoff frequency specification.
    
    A digital high-pass filter that allows high-frequency components to pass through
    while attenuating low-frequency components below the cutoff frequency. This
    implementation uses a first-order IIR (Infinite Impulse Response) structure
    with exponential decay characteristics, making it ideal for DC removal,
    baseline correction, and extracting dynamic signal components.
    
    The filter implements the difference equation:
    
        y[n] = a·(y[n-1] + x[n] - x[n-1])
    
    Where the coefficient 'a' is automatically calculated from the cutoff and sampling frequencies:
    
        a = exp(-2π·fc/fs)
    
    Features:
    
        - Automatic coefficient calculation from frequency specifications
        - Standard first-order high-pass response (+20dB/decade rolloff)
        - Configurable cutoff frequency and sampling rate
        - Memory-efficient dual-delay implementation (input and output)
        - Real-time processing with minimal computational overhead
        - Numerical stability through proper coefficient bounds
        - DC blocking with zero steady-state response to constant inputs
    
    Applications:
    
        - DC offset removal from sensor signals
        - Baseline drift correction in biomedical signals
        - Edge detection in signal processing
        - Motion detection in accelerometer data
        - Audio coupling (removing DC bias)
        - Derivative-like signal enhancement
        - Trend removal from time series data
        - EMG/ECG baseline correction
        - Vibration monitoring (isolating dynamic components)
    
    Mathematical Properties:
    
        - 3dB cutoff at specified frequency fc
        - Phase lead increases with frequency
        - High-frequency gain: 0dB (unity)
        - Low-frequency attenuation: -20dB/decade
        - DC gain: -∞dB (complete DC rejection)
        - Stability: Always stable for 0 < a < 1
        - Group delay: varies with frequency
    
    Signal Characteristics:
    
        - Removes slow-varying components (trends, drift)
        - Emphasizes rapid changes and edges
        - Introduces phase lead at low frequencies
        - Preserves high-frequency content
        - Zero response to constant (DC) inputs
        - Differentiation-like behavior at low frequencies
    """
    
    def __init__(self, fc: float, fs: float, initial: float = 0.0) -> None:
        """
        Initialize high-pass filter with frequency specifications.
        
        Creates a first-order digital high-pass filter by calculating the appropriate
        filter coefficient from the specified cutoff and sampling frequencies.
        The filter removes low-frequency components while preserving high-frequency
        content, making it ideal for DC removal and baseline correction.
        
        :param fc: Cutoff frequency in Hz (3dB point, must be > 0 and < fs/2)
        :param fs: Sampling frequency in Hz (must be > 0 and > 2*fc)
        :param initial: Initial state value for both input and output delays (default: 0.0)
                       Should typically be 0.0 for high-pass filters to avoid startup transients
        
        :raises ValueError: If frequencies are invalid or violate Nyquist criterion
        :raises TypeError: If parameters cannot be converted to float
        
        Filter Coefficient Calculation:
            The coefficient 'a' is calculated using the formula:
    
            a = exp(-2π·fc/fs)
            
            This ensures:
    
            - Correct 3dB cutoff frequency at fc
            - Proper high-pass frequency response characteristics
            - Numerical stability for all valid frequency ratios
            - Zero steady-state response to DC inputs
        
        Frequency Constraints:
    
            - fc must be positive (fc > 0)
            - fc must be less than Nyquist frequency (fc < fs/2)
            - fs must be positive (fs > 0)
            - Recommended: fc should be significantly smaller than fs for good performance
        
        Example
        -------
        ```python
            >>> # DC removal from sensor data
            >>> dc_filter = HighPass(fc=0.1, fs=100.0, initial=0.0)
            >>> print(f"Filter coefficient a: {dc_filter.a:.6f}")
            >>> 
            >>> # Audio DC blocking
            >>> audio_filter = HighPass(fc=20.0, fs=44100.0)
            >>> print(f"Cutoff: {audio_filter.fc} Hz, Sampling: {audio_filter.fs} Hz")
            >>> 
            >>> # Motion detection (remove gravity)
            >>> motion_filter = HighPass(fc=0.5, fs=100.0, initial=0.0)
            >>> print(f"Initial states: y={motion_filter.y}, x_prev={motion_filter.x_prev}")
            >>> 
            >>> # Invalid configurations (will raise ValueError)
            >>> try:
            ...     invalid_filter = HighPass(fc=60.0, fs=100.0)  # fc >= fs/2
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> # Application-specific filter design
            >>> def design_application_filters():
            ...     '''Design filters for specific applications.'''
            ...     
            ...     # EMG baseline correction (remove drift < 5 Hz)
            ...     emg_filter = HighPass(fc=5.0, fs=1000.0)
            ...     print(f"EMG filter: fc={emg_filter.fc} Hz, a={emg_filter.a:.4f}")
            ...     
            ...     # ECG baseline wander removal (remove < 0.5 Hz)
            ...     ecg_filter = HighPass(fc=0.5, fs=250.0)
            ...     print(f"ECG filter: fc={ecg_filter.fc} Hz, a={ecg_filter.a:.4f}")
            ...     
            ...     # Accelerometer motion detection (remove gravity)
            ...     motion_filter = HighPass(fc=0.1, fs=100.0)
            ...     print(f"Motion filter: fc={motion_filter.fc} Hz, a={motion_filter.a:.4f}")
            ...     
            ...     # Audio DC blocking (remove < 20 Hz)
            ...     audio_filter = HighPass(fc=20.0, fs=44100.0)
            ...     print(f"Audio filter: fc={audio_filter.fc} Hz, a={audio_filter.a:.4f}")
        ```
        """

    @micropython.native
    def update(self, x: float) -> float:
        """
        Update filter with new sample and return filtered output.
        
        Processes a single input sample through the first-order IIR high-pass filter
        using the difference equation: y[n] = a·(y[n-1] + x[n] - x[n-1])
        
        This method implements high-pass filtering by maintaining both input and output
        history. The filter emphasizes changes in the input signal while suppressing
        constant (DC) components.
        
        :param x: Input sample value (any numeric type, converted to float)
        :return: Filtered output sample as float
        
        :raises TypeError: If input cannot be converted to float
        
        Algorithm Details:
            The filter implements: y[n] = a·(y[n-1] + x[n] - x[n-1])
            
            Where:
        
            - y[n] is the current output
            - y[n-1] is the previous output (stored in self.y)
            - x[n] is the current input
            - x[n-1] is the previous input (stored in self.x_prev)
            - a is the filter coefficient (self.a)
        
        Performance Characteristics:
        
            - O(1) computational complexity
            - Two multiply-add operations per sample
            - Minimal memory usage (two float values for state)
            - Optimized with @micropython.native decorator
            - Suitable for real-time applications
        
        Signal Processing Properties:
        
            - High-frequency gain: 0dB (unity gain at high frequencies)
            - Low-frequency attenuation: -20dB/decade below cutoff
            - DC gain: -∞dB (complete DC rejection)
            - Phase response: +90° at low frequencies, 0° at high frequencies
            - Steady-state response to constants: 0.0
        
        Example
        -------
        ```python
            >>> # Basic high-pass filtering
            >>> filter_obj = HighPass(fc=1.0, fs=10.0)
            >>> 
            >>> # Test with DC + AC signal
            >>> test_signal = [5.0, 5.1, 5.0, 4.9, 5.0, 5.2, 5.0, 4.8]  # DC=5, AC varies
            >>> 
            >>> print("Input | Output | Description")
            >>> print("-" * 35)
            >>> 
            >>> for i, sample in enumerate(test_signal):
            ...     output = filter_obj.update(sample)
            ...     
            ...     if i == 0:
            ...         desc = "First sample"
            ...     elif sample == 5.0:
            ...         desc = "DC component"
            ...     else:
            ...         desc = f"AC: {sample-5.0:+.1f}"
            ...     
            ...     print(f"{sample:5.1f} | {output:+6.3f} | {desc}")
            >>> # Input | Output | Description
            >>> # -------------------------
            >>> #   5.0 | +0.000 | First sample
            >>> #   5.1 | +0.095 | AC: +0.1
            >>> #   5.0 | -0.005 | DC component
            >>> #   4.9 | -0.095 | AC: -0.1
            >>> #   5.0 | +0.005 | DC component
            >>> #   5.2 | +0.190 | AC: +0.2
            >>> #   5.0 | -0.010 | DC component
            >>> #   4.8 | -0.191 | AC: -0.2
            >>> 
            >>> # DC rejection demonstration
            >>> def demonstrate_dc_rejection():
            ...     dc_filter = HighPass(fc=0.1, fs=10.0)
            ...     
            ...     print("DC Rejection Test:")
            ...     print("Sample | Input | Output | Running Avg")
            ...     print("-" * 40)
            ...     
            ...     dc_value = 3.0
            ...     running_sum = 0.0
            ...     
            ...     for n in range(50):
            ...         # Constant DC input
            ...         output = dc_filter.update(dc_value)
            ...         running_sum += output
            ...         running_avg = running_sum / (n + 1)
            ...         
            ...         if n % 10 == 0:  # Print every 10th sample
            ...             print(f"{n:6d} | {dc_value:5.1f} | {output:+6.4f} | {running_avg:+8.5f}")
            ...     
            ...     print(f"Final average output: {running_avg:+.6f} (should approach 0)")
            >>> 
            >>> # Edge detection example
            >>> def edge_detection_example():
            ...     edge_detector = HighPass(fc=2.0, fs=20.0)
            ...     
            ...     # Create signal with step changes
            ...     signal = [1.0]*10 + [2.0]*10 + [1.5]*10 + [3.0]*10
            ...     
            ...     print("Edge Detection Example:")
            ...     print("Sample | Input | Edge Signal | Event")
            ...     print("-" * 45)
            ...     
            ...     threshold = 0.1
            ...     
            ...     for i, sample in enumerate(signal):
            ...         edge_signal = edge_detector.update(sample)
            ...         
            ...         # Detect edges
            ...         if abs(edge_signal) > threshold:
            ...             if edge_signal > 0:
            ...                 event = "Rising edge"
            ...             else:
            ...                 event = "Falling edge"
            ...         else:
            ...             event = "-"
            ...         
            ...         if i % 5 == 0 or event != "-":  # Print on events or periodically
            ...             print(f"{i:6d} | {sample:5.1f} | {edge_signal:+10.4f} | {event}")
        ```
        """
    
    def reset(self) -> None:
        """
        Reset filter to initial state while preserving configuration.
        
        Clears the filter's internal state (both input and output history) and resets
        the sample counter, but maintains all configuration parameters like cutoff
        frequency, sampling frequency, and calculated coefficients. This allows the
        filter to be reused for new data streams without reconfiguration.
        
        Reset Operations:
        
            - Clears output history (y[n-1])
            - Clears input history (x[n-1])
            - Resets sample counter to zero
            - Preserves filter coefficients and parameters
            - Restores initial state values
            - Prepares filter for new input sequence
        
        State Variables Reset:
        
            - self.y (output history) → initial value
            - self.x_prev (input history) → initial value
            - self._sample_count → 0
            - Filter coefficients (a, fc, fs) preserved
        
        Example
        -------
        ```python
            >>> filter_obj = HighPass(fc=1.0, fs=10.0, initial=0.0)
            >>> 
            >>> # Process some data with DC offset
            >>> test_data = [5.0, 5.1, 5.0, 4.9, 5.0]
            >>> for sample in test_data:
            ...     result = filter_obj.update(sample)
            ...     print(f"Sample: {sample:.1f} → Output: {result:+.4f}")
            >>> # Sample: 5.0 → Output: +0.0000
            >>> # Sample: 5.1 → Output: +0.0905
            >>> # Sample: 5.0 → Output: -0.0082
            >>> # Sample: 4.9 → Output: -0.0905
            >>> # Sample: 5.0 → Output: +0.0082
            >>> 
            >>> print(f"Before reset: samples={filter_obj.sample_count}, "
            ...       f"y={filter_obj.y:.4f}, x_prev={filter_obj.x_prev:.1f}")
            >>> # Before reset: samples=5, y=0.0082, x_prev=5.0
            >>> 
            >>> # Reset filter
            >>> filter_obj.reset()
            >>> print(f"After reset: samples={filter_obj.sample_count}, "
            ...       f"y={filter_obj.y:.4f}, x_prev={filter_obj.x_prev:.1f}")
            >>> # After reset: samples=0, y=0.0000, x_prev=0.0
            >>> 
            >>> # Verify coefficients preserved
            >>> print(f"Coefficients preserved: fc={filter_obj.fc} Hz, a={filter_obj.a:.6f}")
            >>> 
            >>> # Multi-channel processing with synchronized reset
            >>> def synchronized_multichannel():
            ...     # Create filters for 3-axis accelerometer
            ...     accel_x = HighPass(fc=0.5, fs=100.0)
            ...     accel_y = HighPass(fc=0.5, fs=100.0)
            ...     accel_z = HighPass(fc=0.5, fs=100.0)
            ...     
            ...     # Process first batch of data
            ...     batch1 = [(1.0, 0.1, 9.8), (0.9, 0.2, 9.7), (1.1, 0.0, 9.9)]
            ...     
            ...     print("Batch 1 processing:")
            ...     for i, (x, y, z) in enumerate(batch1):
            ...         x_filt = accel_x.update(x)
            ...         y_filt = accel_y.update(y)
            ...         z_filt = accel_z.update(z)
            ...         print(f"Sample {i+1}: Gravity removed - X:{x_filt:.3f} Y:{y_filt:.3f} Z:{z_filt:.3f}")
            ...     
            ...     # Reset all filters simultaneously for new session
            ...     for filter_obj in [accel_x, accel_y, accel_z]:
            ...         filter_obj.reset()
            ...     
            ...     print("\nAfter reset - all filters ready for new data")
            ...     
            ...     # Process second batch with fresh state
            ...     batch2 = [(0.5, -0.1, 9.7), (0.6, -0.2, 9.8)]
            ...     
            ...     print("\nBatch 2 processing:")
            ...     for i, (x, y, z) in enumerate(batch2):
            ...         x_filt = accel_x.update(x)
            ...         y_filt = accel_y.update(y)
            ...         z_filt = accel_z.update(z)
            ...         print(f"Sample {i+1}: Gravity removed - X:{x_filt:.3f} Y:{y_filt:.3f} Z:{z_filt:.3f}")
        ```
        """



class TauLowPass(Base):
    """
    Time-constant based low-pass filter with variable or fixed sampling rate.
    
    A first-order exponential smoothing filter characterized by its time constant
    tau (in seconds) rather than alpha coefficient. This provides more intuitive
    tuning based on physical time scales and desired settling time, making it ideal
    for applications where response time specifications are given in seconds rather
    than abstract smoothing coefficients.
    
    The filter implements exponential smoothing with dynamic coefficient calculation:
        
        α = dt / (tau + dt)
        y[n] = α·x[n] + (1-α)·y[n-1]
    
    Where:
        
        - tau is the time constant in seconds
        - dt is the time step (sampling interval) in seconds
        - α is automatically calculated based on tau and dt
    
    Key Features:
        
        - Intuitive time-based parameter specification
        - Supports both variable and fixed sampling rates
        - Automatic coefficient calculation per update
        - Predictable settling time based on tau
        - Easy conversion from cutoff frequency
        - Consistent response regardless of sampling rate
        - Real-time adjustable time constant
    
    Applications:
        
        - Sensor smoothing with time-based specifications
        - Control systems with settling time requirements
        - Variable-rate data acquisition systems
        - Audio processing with physical time constants
        - IMU sensor fusion and filtering
        - Temperature monitoring with thermal time constants
        - Real-time signal conditioning
    
    Mathematical Properties:
        
        - Time constant: τ (user-specified)
        - Step response: y(t) ≈ (1 - e^(-t/τ))·A for step of amplitude A
        - 63.2% settling time: τ seconds
        - 95% settling time: ≈ 3τ seconds
        - 99% settling time: ≈ 5τ seconds
        - Cutoff frequency: fc ≈ 1/(2π·τ) Hz
        - Always stable for τ > 0
    
    Time Constant Selection Guidelines:
        
        - τ = 0.01s: Very fast response (100 Hz cutoff)
        - τ = 0.1s: Fast response (1.6 Hz cutoff)
        - τ = 0.5s: Moderate smoothing (0.3 Hz cutoff)
        - τ = 1.0s: Heavy smoothing (0.16 Hz cutoff)
        - τ = 5.0s: Very slow response (0.03 Hz cutoff)
    """
    def __init__(self, tau_s: float, initial: float = 0.0, fs: float | None = None) -> None:
        """
        Initialize time-constant based low-pass filter.
        
        Creates a first-order low-pass filter specified by its time constant in
        seconds. The filter can operate in either fixed sampling rate mode (when
        fs is provided) or variable sampling rate mode (when fs is None).
        
        :param tau_s: Time constant in seconds (must be > 0)
                     Determines the filter's response speed. Larger values provide
                     more smoothing but slower response. Smaller values give faster
                     response but less noise reduction.
        :param initial: Initial output value for filter state (default: 0.0)
                       Use expected signal level to minimize startup transients
        :param fs: Optional fixed sampling rate in Hz (default: None)
                  If provided, use update(x) with automatic dt calculation.
                  If None, must use update_with_dt(x, dt) with explicit dt.
        
        :raises FilterConfigurationError: If tau_s <= 0 or fs <= 0
        :raises TypeError: If parameters cannot be converted to numeric types
        
        Time Constant Specification:
            The time constant tau represents the time for the filter output to
            reach 63.2% of a step input. This provides intuitive tuning:
            
            - Response speed: Smaller tau = faster response
            - Smoothing amount: Larger tau = more smoothing
            - Settling time (95%): approximately 3×tau
            - Settling time (99%): approximately 5×tau
        
        Sampling Rate Modes:
            
            Fixed Sampling Rate (fs provided):
                
                - Use update(x) method
                - Time step dt = 1/fs is constant
                - More efficient (no dt parameter needed)
                - Suitable for periodic sampling systems
                - Example: 100 Hz control loop
            
            Variable Sampling Rate (fs = None):
                
                - Use update_with_dt(x, dt) method
                - Time step dt varies per sample
                - Handles irregular sampling
                - Adapts to actual timing
                - Example: Event-driven measurements
        
        Relationship to Cutoff Frequency:
            If you have a desired cutoff frequency fc:
            
            tau = 1 / (2π·fc)
            
            Example: fc = 10 Hz → tau ≈ 0.0159s
        
        Example
        -------
        ```python
            >>> # Fixed sampling rate configuration
            >>> temp_filter = TauLowPass(tau_s=0.5, initial=25.0, fs=10.0)
            >>> print(f"Time constant: {temp_filter.tau}s")
            >>> print(f"95% settling time: {3 * temp_filter.tau:.2f}s")
            >>> # Time constant: 0.5s
            >>> # 95% settling time: 1.50s
            >>> 
            >>> # Variable sampling rate configuration
            >>> accel_filter = TauLowPass(tau_s=0.05, initial=0.0)
            >>> print(f"Cutoff frequency: {1/(2*pi*accel_filter.tau):.2f} Hz")
            >>> # Cutoff frequency: 3.18 Hz
            >>> 
            >>> # Configure from cutoff frequency
            >>> desired_fc = 5.0  # Hz
            >>> tau_for_fc = 1.0 / (2 * pi * desired_fc)
            >>> signal_filter = TauLowPass(tau_s=tau_for_fc, initial=0.0, fs=100.0)
            >>> print(f"Configured for {desired_fc} Hz cutoff")
            >>> 
            >>> # Application-specific configurations
            >>> def design_application_filters():
            ...     '''Design filters for various applications.'''
            ...     
            ...     # Temperature sensor (slow thermal response)
            ...     temp = TauLowPass(tau_s=2.0, initial=22.0, fs=1.0)
            ...     print(f"Temp: tau={temp.tau}s, settling ~{5*temp.tau}s")
            ...     
            ...     # IMU accelerometer (fast response needed)
            ...     imu = TauLowPass(tau_s=0.02, initial=0.0, fs=200.0)
            ...     print(f"IMU: tau={imu.tau}s, settling ~{5*imu.tau}s")
            ...     
            ...     # Audio envelope follower
            ...     audio = TauLowPass(tau_s=0.01, initial=0.0, fs=44100.0)
            ...     print(f"Audio: tau={audio.tau}s, settling ~{5*audio.tau}s")
            ...     
            ...     # Battery voltage monitor (very slow)
            ...     battery = TauLowPass(tau_s=10.0, initial=3.7, fs=0.1)
            ...     print(f"Battery: tau={battery.tau}s, settling ~{5*battery.tau}s")
            >>> 
            >>> # Invalid configurations
            >>> try:
            ...     bad_filter = TauLowPass(tau_s=0.0, initial=0.0)  # Zero tau
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     bad_filter = TauLowPass(tau_s=-0.1, initial=0.0)  # Negative tau
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
        ```
        """
        ...
    
    @property
    def tau(self) -> float:
        """
        Get time constant in seconds.
        
        Returns the current time constant value that characterizes the filter's
        response speed. The time constant represents the time for the filter to
        reach approximately 63.2% of a step input.
        
        :return: Time constant in seconds (always positive)
        
        Time Constant Interpretation:
            
            - τ = 0.01s: Very fast response (fc ≈ 16 Hz)
            - τ = 0.1s: Fast response (fc ≈ 1.6 Hz)
            - τ = 0.5s: Moderate response (fc ≈ 0.3 Hz)
            - τ = 1.0s: Slow response (fc ≈ 0.16 Hz)
            - τ = 5.0s: Very slow response (fc ≈ 0.03 Hz)
        
        Relationship to Settling Time:
            
            - 63.2% settling: τ seconds
            - 95% settling: ≈ 3τ seconds
            - 99% settling: ≈ 5τ seconds
            - 99.9% settling: ≈ 7τ seconds
        
        Example
        -------
        ```python
            >>> from ufilter import TauLowPass
            >>> 
            >>> # Create filter and check tau
            >>> filt = TauLowPass(tau_s=0.5, fs=100.0)
            >>> print(f"Time constant: {filt.tau}s")
            >>> # Time constant: 0.5s
            >>> 
            >>> # Calculate settling times
            >>> print(f"95% settling: {3 * filt.tau:.2f}s")
            >>> print(f"99% settling: {5 * filt.tau:.2f}s")
            >>> # 95% settling: 1.50s
            >>> # 99% settling: 2.50s
            >>> 
            >>> # Calculate equivalent cutoff frequency
            >>> import math
            >>> fc = 1.0 / (2 * math.pi * filt.tau)
            >>> print(f"Equivalent cutoff: {fc:.2f} Hz")
            >>> # Equivalent cutoff: 0.32 Hz
        ```
        """
        ...
    
    @tau.setter
    def tau(self, value: float) -> None:
        """
        Set time constant in seconds.
        
        Updates the filter's time constant, changing its response speed. The new
        time constant takes effect immediately and will be used for all subsequent
        update() calls. For fixed sampling rate mode, the alpha coefficient is
        automatically recalculated.
        
        :param value: New time constant in seconds (must be > 0)
        
        :raises FilterConfigurationError: If value <= 0
        :raises TypeError: If value cannot be converted to float
        
        Effects of Changing Tau:
            
            Increasing tau (slower response):
                
                - More smoothing, less noise
                - Longer settling time
                - Lower cutoff frequency
                - More phase lag
            
            Decreasing tau (faster response):
                
                - Less smoothing, more noise
                - Shorter settling time
                - Higher cutoff frequency
                - Less phase lag
        
        Real-Time Adjustment Use Cases:
            
            - Adaptive filtering based on noise level
            - Speed-dependent smoothing (faster movement = less smoothing)
            - User-adjustable responsiveness
            - Automatic tuning based on signal characteristics
        
        Example
        -------
        ```python
            >>> from ufilter import TauLowPass
            >>> 
            >>> # Create filter with initial tau
            >>> filt = TauLowPass(tau_s=0.5, initial=0.0, fs=100.0)
            >>> print(f"Initial tau: {filt.tau}s")
            >>> # Initial tau: 0.5s
            >>> 
            >>> # Process some samples
            >>> for i in range(5):
            ...     output = filt.update(float(i))
            ...     print(f"Sample {i}: {output:.3f}")
            >>> 
            >>> # Change tau for different response
            >>> filt.tau = 0.1  # Faster response
            >>> print(f"\nNew tau: {filt.tau}s")
            >>> # New tau: 0.1s
            >>> 
            >>> # Continue processing with new tau
            >>> for i in range(5, 10):
            ...     output = filt.update(float(i))
            ...     print(f"Sample {i}: {output:.3f}")
            >>> 
            >>> # Adaptive filtering example
            >>> def adaptive_smoothing():
            ...     sensor_filter = TauLowPass(tau_s=0.2, fs=100.0)
            ...     
            ...     for sample in sensor_data:
            ...         # Measure noise level (example: from variance)
            ...         noise_level = estimate_noise_level()
            ...         
            ...         # Adjust tau based on noise
            ...         if noise_level > 0.5:
            ...             sensor_filter.tau = 0.5  # Heavy smoothing
            ...         elif noise_level > 0.2:
            ...             sensor_filter.tau = 0.2  # Moderate
            ...         else:
            ...             sensor_filter.tau = 0.05  # Light smoothing
            ...         
            ...         filtered = sensor_filter.update(sample)
            >>> 
            >>> # Speed-dependent filtering
            >>> def speed_dependent_filter():
            ...     position_filter = TauLowPass(tau_s=0.1, fs=50.0)
            ...     
            ...     for position, velocity in motion_data:
            ...         # More smoothing at low speeds
            ...         if abs(velocity) < 1.0:
            ...             position_filter.tau = 0.3
            ...         elif abs(velocity) < 5.0:
            ...             position_filter.tau = 0.1
            ...         else:
            ...             position_filter.tau = 0.03  # Fast motion
            ...         
            ...         filtered_pos = position_filter.update(position)
            >>> 
            >>> # Invalid values
            >>> try:
            ...     filt.tau = 0.0  # Zero not allowed
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     filt.tau = -0.1  # Negative not allowed
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
        ```
        """
        ...
    
    def set_cutoff(self, fc_hz: float) -> None:
        """
        Set time constant from cutoff frequency.
        
        Converts a desired cutoff frequency (3dB point) to the corresponding time
        constant and updates the filter. This provides an intuitive way to configure
        the filter when the frequency domain specification is more natural than
        time constant.
        
        :param fc_hz: Desired cutoff frequency in Hz (must be > 0)
        
        :raises FilterConfigurationError: If fc_hz <= 0
        :raises TypeError: If fc_hz cannot be converted to float
        
        Conversion Formula:
            The relationship between cutoff frequency and time constant:
            
            tau = 1 / (2π × fc)
            
            Or equivalently:
            
            fc = 1 / (2π × tau)
            
            This ensures the filter has -3dB attenuation at the specified frequency.
        
        Typical Cutoff Frequencies:
            
            - fc = 0.1 Hz: Very low frequency (tau ≈ 1.59s)
            - fc = 1 Hz: Low frequency (tau ≈ 0.159s)
            - fc = 10 Hz: Moderate frequency (tau ≈ 0.0159s)
            - fc = 100 Hz: High frequency (tau ≈ 0.00159s)
        
        Application Examples:
            
            - Audio: 20 Hz - 20 kHz
            - Vibration: 1 Hz - 1 kHz
            - Temperature: 0.01 Hz - 1 Hz
            - Servo control: 1 Hz - 100 Hz
        
        Example
        -------
        ```python
            >>> from ufilter import TauLowPass
            >>> import math
            >>> 
            >>> # Create filter with initial tau
            >>> filt = TauLowPass(tau_s=0.1, initial=0.0, fs=1000.0)
            >>> print(f"Initial tau: {filt.tau:.4f}s")
            >>> # Initial tau: 0.1000s
            >>> 
            >>> # Calculate initial cutoff
            >>> fc_initial = 1.0 / (2 * math.pi * filt.tau)
            >>> print(f"Initial cutoff: {fc_initial:.2f} Hz")
            >>> # Initial cutoff: 1.59 Hz
            >>> 
            >>> # Set new cutoff frequency
            >>> filt.set_cutoff(10.0)  # 10 Hz cutoff
            >>> print(f"New tau: {filt.tau:.4f}s")
            >>> # New tau: 0.0159s
            >>> 
            >>> # Verify cutoff
            >>> fc_new = 1.0 / (2 * math.pi * filt.tau)
            >>> print(f"New cutoff: {fc_new:.2f} Hz")
            >>> # New cutoff: 10.00 Hz
            >>> 
            >>> # Design filters for specific applications
            >>> def design_by_frequency():
            ...     # Audio envelope follower (20 Hz cutoff)
            ...     audio_filt = TauLowPass(tau_s=0.1, fs=44100.0)
            ...     audio_filt.set_cutoff(20.0)
            ...     print(f"Audio: fc=20Hz, tau={audio_filt.tau:.4f}s")
            ...     
            ...     # Vibration sensor (100 Hz cutoff)
            ...     vib_filt = TauLowPass(tau_s=0.1, fs=1000.0)
            ...     vib_filt.set_cutoff(100.0)
            ...     print(f"Vibration: fc=100Hz, tau={vib_filt.tau:.5f}s")
            ...     
            ...     # Temperature sensor (0.1 Hz cutoff)
            ...     temp_filt = TauLowPass(tau_s=1.0, fs=10.0)
            ...     temp_filt.set_cutoff(0.1)
            ...     print(f"Temperature: fc=0.1Hz, tau={temp_filt.tau:.2f}s")
            >>> 
            >>> # Interactive tuning
            >>> def interactive_cutoff_tuning():
            ...     signal_filt = TauLowPass(tau_s=0.1, fs=100.0)
            ...     
            ...     # User adjusts cutoff in Hz (more intuitive than tau)
            ...     cutoff_settings = [1.0, 2.0, 5.0, 10.0, 20.0]
            ...     
            ...     for fc in cutoff_settings:
            ...         signal_filt.set_cutoff(fc)
            ...         print(f"Cutoff: {fc:5.1f} Hz → tau: {signal_filt.tau:.4f}s "
            ...               f"→ 95% settling: {3*signal_filt.tau:.3f}s")
            >>> 
            >>> # Frequency sweep testing
            >>> def frequency_sweep():
            ...     test_filt = TauLowPass(tau_s=0.1, fs=1000.0)
            ...     
            ...     print("Frequency | Tau     | Alpha (fs=1kHz)")
            ...     print("-" * 40)
            ...     
            ...     for fc in [0.1, 1, 5, 10, 50, 100]:
            ...         test_filt.set_cutoff(fc)
            ...         alpha = (1.0/1000.0) / (test_filt.tau + 1.0/1000.0)
            ...         print(f"{fc:9.1f} | {test_filt.tau:7.4f} | {alpha:.6f}")
            >>> 
            >>> # Invalid cutoff
            >>> try:
            ...     filt.set_cutoff(0.0)  # Zero not allowed
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     filt.set_cutoff(-5.0)  # Negative not allowed
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
        ```
        """
        ...
    
    def update_with_dt(self, x: float, dt_s: float) -> float:
        """
        Update filter with variable time step.
        
        Processes a single input sample through the filter using an explicitly
        provided time step. The filter coefficient alpha is calculated dynamically
        based on the actual elapsed time, allowing the filter to adapt to irregular
        or variable sampling rates while maintaining consistent time-based response.
        
        :param x: Input sample value (any numeric type, converted to float)
        :param dt_s: Time elapsed since last update in seconds (must be > 0)
        :return: Filtered output sample as float
        
        :raises FilterOperationError: If dt_s <= 0
        :raises TypeError: If parameters cannot be converted to float
        
        Algorithm Details:
            The filter implements: y[n] = α·x[n] + (1-α)·y[n-1]
            
            Where α is dynamically calculated per sample:
            
            α = dt / (tau + dt)
            
            This ensures:
            
            - Consistent response regardless of sampling irregularity
            - Proper time-constant behavior with variable dt
            - Automatic adaptation to actual timing
            - Predictable settling time in wall-clock seconds
        
        Performance Characteristics:
            
            - O(1) computational complexity
            - Three floating-point operations per sample
            - Minimal memory usage (single output state)
            - Suitable for real-time variable-rate systems
            - No accumulation of timing errors
        
        Timing Considerations:
            
            - Accurate dt is critical for correct filtering
            - Use high-resolution timers when available
            - Account for processing delays if timing is tight
            - Very small dt (<< tau) is safe but inefficient
            - Very large dt (>> tau) causes step-like behavior
        
        Example
        -------
        ```python
            >>> import time
            >>> from ufilter import TauLowPass
            >>> 
            >>> # Variable-rate sensor filtering
            >>> sensor_filter = TauLowPass(tau_s=0.1, initial=0.0)
            >>> 
            >>> # Simulate variable sampling intervals
            >>> last_time = time.ticks_ms()
            >>> test_intervals = [0.01, 0.015, 0.008, 0.012, 0.01]  # seconds
            >>> test_values = [1.0, 1.5, 2.0, 1.8, 2.2]
            >>> 
            >>> print("dt (s) | Input | Output | Alpha")
            >>> print("-" * 40)
            >>> 
            >>> for dt, value in zip(test_intervals, test_values):
            ...     output = sensor_filter.update_with_dt(value, dt)
            ...     alpha = dt / (sensor_filter.tau + dt)
            ...     print(f"{dt:6.3f} | {value:5.1f} | {output:6.3f} | {alpha:.4f}")
            >>> # dt (s) | Input | Output | Alpha
            >>> # ----------------------------------------
            >>> # 0.010  |   1.0 |  0.091 | 0.0909
            >>> # 0.015  |   1.5 |  0.302 | 0.1304
            >>> # 0.008  |   2.0 |  0.428 | 0.0741
            >>> # 0.012  |   1.8 |  0.592 | 0.1071
            >>> # 0.010  |   2.2 |  0.738 | 0.0909
            >>> 
            >>> # Real-world application with timing
            >>> def variable_rate_application():
            ...     filter_obj = TauLowPass(tau_s=0.2)
            ...     
            ...     last_time = time.ticks_ms()
            ...     sample_count = 0
            ...     
            ...     while sample_count < 100:
            ...         # Variable timing due to sensor/processing delays
            ...         sensor_value = read_sensor()  # May have variable latency
            ...         
            ...         current_time = time.ticks_ms()
            ...         dt = time.ticks_diff(current_time, last_time) / 1000.0
            ...         last_time = current_time
            ...         
            ...         # Filter adapts to actual timing
            ...         filtered = filter_obj.update_with_dt(sensor_value, dt)
            ...         
            ...         print(f"dt={dt*1000:.1f}ms, filtered={filtered:.3f}")
            ...         
            ...         sample_count += 1
            ...         time.sleep(0.01)  # Nominal 100 Hz, but actual varies
            >>> 
            >>> # Handling timing edge cases
            >>> def demonstrate_timing_effects():
            ...     filt = TauLowPass(tau_s=0.1)
            ...     
            ...     # Normal sampling
            ...     result1 = filt.update_with_dt(1.0, 0.01)
            ...     print(f"Normal dt: {result1:.4f}")
            ...     
            ...     # Very small dt (inefficient but safe)
            ...     result2 = filt.update_with_dt(1.0, 0.0001)
            ...     print(f"Tiny dt: {result2:.4f} (minimal change)")
            ...     
            ...     # Large dt (approaches step)
            ...     result3 = filt.update_with_dt(2.0, 1.0)
            ...     print(f"Large dt: {result3:.4f} (large step)")
        ```
        """
        ...
    
    def update(self, x: float) -> float:
        """
        Update filter with fixed time step.
        
        Processes a single input sample through the filter using the fixed sampling
        rate specified in the constructor. The filter coefficient alpha is pre-calculated
        from the time constant and fixed sampling period, providing efficient operation
        for periodic sampling systems.
        
        :param x: Input sample value (any numeric type, converted to float)
        :return: Filtered output sample as float
        
        :raises FilterOperationError: If fs was not provided in constructor
        :raises TypeError: If input cannot be converted to float
        
        Algorithm Details:
            The filter implements: y[n] = α·x[n] + (1-α)·y[n-1]
            
            Where α is pre-calculated once from fs and tau:
            
            α = (1/fs) / (tau + 1/fs)
            
            This provides:
            
            - Efficient filtering with no per-sample coefficient calculation
            - Consistent response at fixed sampling rate
            - Predictable computational load
            - Optimal for periodic control loops
        
        Performance Characteristics:
            
            - O(1) computational complexity
            - Two floating-point operations per sample (multiply-add)
            - Pre-calculated coefficient for efficiency
            - Minimal memory usage (single output state)
            - Ideal for deterministic real-time systems
        
        Usage Requirements:
            
            - Sampling rate fs must be provided in constructor
            - Samples must arrive at approximately fs rate
            - For irregular sampling, use update_with_dt() instead
            - Calling this without fs raises FilterOperationError
        
        Example
        -------
        ```python
            >>> from ufilter import TauLowPass
            >>> 
            >>> # Temperature sensor at 10 Hz
            >>> temp_filter = TauLowPass(tau_s=0.5, initial=25.0, fs=10.0)
            >>> 
            >>> # Process samples (simple interface, no dt needed)
            >>> test_temps = [25.2, 25.8, 26.1, 25.9, 26.3, 25.7, 25.5]
            >>> 
            >>> print("Sample | Input | Output | Change")
            >>> print("-" * 35)
            >>> 
            >>> for i, temp in enumerate(test_temps):
            ...     prev_output = temp_filter.y if i > 0 else temp_filter.y
            ...     output = temp_filter.update(temp)
            ...     change = output - prev_output
            ...     print(f"{i:6d} | {temp:5.1f} | {output:6.3f} | {change:+6.3f}")
            >>> # Sample | Input | Output | Change
            >>> # -----------------------------------
            >>> #      0 |  25.2 |  25.039 | +0.039
            >>> #      1 |  25.8 |  25.188 | +0.149
            >>> #      2 |  26.1 |  25.366 | +0.178
            >>> #      3 |  25.9 |  25.470 | +0.104
            >>> #      4 |  26.3 |  25.631 | +0.161
            >>> #      5 |  25.7 |  25.644 | +0.013
            >>> #      6 |  25.5 |  25.616 | -0.028
            >>> 
            >>> # High-frequency control loop
            >>> def control_loop_example():
            ...     # 100 Hz control loop with tau = 0.02s
            ...     controller_filter = TauLowPass(tau_s=0.02, initial=0.0, fs=100.0)
            ...     
            ...     print("Control Loop Filtering (100 Hz)")
            ...     print("Sample | Input | Filtered")
            ...     print("-" * 30)
            ...     
            ...     # Simulate noisy sensor with step input
            ...     for n in range(20):
            ...         # Step from 0 to 10 at sample 10 with noise
            ...         true_value = 10.0 if n >= 10 else 0.0
            ...         noise = (hash(n) % 100 - 50) / 500.0  # ±0.1
            ...         sensor = true_value + noise
            ...         
            ...         filtered = controller_filter.update(sensor)
            ...         
            ...         if n % 5 == 0 or n == 10:  # Print periodically and at step
            ...             print(f"{n:6d} | {sensor:5.2f} | {filtered:8.3f}")
            >>> 
            >>> # Error handling - missing fs
            >>> try:
            ...     no_fs_filter = TauLowPass(tau_s=0.1)  # No fs provided
            ...     result = no_fs_filter.update(1.0)  # Will raise error
            >>> except FilterOperationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> # Batch processing with fixed rate
            >>> def batch_process_data():
            ...     data = [0.1, 0.3, 0.2, 0.5, 0.4, 0.6, 0.5, 0.7]
            ...     
            ...     # Process at 50 Hz with tau = 0.05s
            ...     processor = TauLowPass(tau_s=0.05, fs=50.0)
            ...     
            ...     filtered_data = []
            ...     for sample in data:
            ...         filtered = processor.update(sample)
            ...         filtered_data.append(filtered)
            ...     
            ...     return filtered_data
        ```
        """
        ...
    
    def reset(self) -> None:
        """
        Reset filter to initial state while preserving configuration.
        
        Clears the filter's internal state (output value) and resets the sample
        counter, but maintains all configuration parameters like time constant,
        sampling frequency, and initial value setting. This allows the filter
        to be reused for new data streams without reconfiguration.
        
        Reset Operations:
            
            - Restores output value to initial setting
            - Resets sample counter to zero
            - Preserves time constant (tau)
            - Preserves sampling frequency (fs)
            - Preserves initial value setting
            - Prepares filter for new input sequence
        
        Use Cases:
            
            - Starting new measurement session
            - Switching between different signal sources
            - Clearing filter memory after transient events
            - Batch processing of multiple datasets
            - Periodic reset to prevent numerical drift
            - A/B testing with consistent initial conditions
        
        Example
        -------
        ```python
            >>> from ufilter import TauLowPass
            >>> 
            >>> # Create filter and process some data
            >>> sensor_filter = TauLowPass(tau_s=0.1, initial=0.0, fs=100.0)
            >>> 
            >>> print("First dataset:")
            >>> for i in range(5):
            ...     result = sensor_filter.update(float(i))
            ...     print(f"  Sample {i}: {result:.3f}")
            >>> # First dataset:
            >>> #   Sample 0: 0.000
            >>> #   Sample 1: 0.091
            >>> #   Sample 2: 0.264
            >>> #   Sample 3: 0.512
            >>> #   Sample 4: 0.830
            >>> 
            >>> print(f"After processing: output={sensor_filter.y:.3f}, samples={sensor_filter.sample_count}")
            >>> # After processing: output=0.830, samples=5
            >>> 
            >>> # Reset for new dataset
            >>> sensor_filter.reset()
            >>> print(f"After reset: output={sensor_filter.y:.3f}, samples={sensor_filter.sample_count}")
            >>> # After reset: output=0.000, samples=0
            >>> 
            >>> # Verify configuration preserved
            >>> print(f"Configuration: tau={sensor_filter.tau}s, fs={sensor_filter.fs} Hz")
            >>> # Configuration: tau=0.1s, fs=100.0 Hz
            >>> 
            >>> # Process second dataset with same filter
            >>> print("\nSecond dataset:")
            >>> for i in range(5):
            ...     result = sensor_filter.update(float(i) * 2)
            ...     print(f"  Sample {i}: {result:.3f}")
            >>> 
            >>> # Multi-sensor application with synchronized reset
            >>> def synchronized_multichannel_filtering():
            ...     # Create filters for 3-axis accelerometer
            ...     tau = 0.05
            ...     fs = 200.0
            ...     
            ...     accel_x = TauLowPass(tau_s=tau, initial=0.0, fs=fs)
            ...     accel_y = TauLowPass(tau_s=tau, initial=0.0, fs=fs)
            ...     accel_z = TauLowPass(tau_s=tau, initial=9.8, fs=fs)
            ...     
            ...     filters = [accel_x, accel_y, accel_z]
            ...     
            ...     # Process first batch
            ...     batch1 = [(0.1, 0.2, 9.7), (0.2, 0.1, 9.8), (0.0, 0.3, 9.9)]
            ...     
            ...     print("Batch 1:")
            ...     for i, (x, y, z) in enumerate(batch1):
            ...         fx = accel_x.update(x)
            ...         fy = accel_y.update(y)
            ...         fz = accel_z.update(z)
            ...         print(f"  Sample {i}: X={fx:.3f}, Y={fy:.3f}, Z={fz:.3f}")
            ...     
            ...     # Reset all filters for new batch
            ...     for filt in filters:
            ...         filt.reset()
            ...     
            ...     print("\nAfter reset - ready for Batch 2")
            ...     
            ...     # Process second batch starting from same initial conditions
            ...     batch2 = [(0.5, -0.1, 9.6), (0.3, 0.0, 9.7)]
            ...     
            ...     print("Batch 2:")
            ...     for i, (x, y, z) in enumerate(batch2):
            ...         fx = accel_x.update(x)
            ...         fy = accel_y.update(y)
            ...         fz = accel_z.update(z)
            ...         print(f"  Sample {i}: X={fx:.3f}, Y={fy:.3f}, Z={fz:.3f}")
        ```
        """
        ...



class SlewRateLimiter(Base):
    """
    Slew rate limiter with independent rise/fall rates and optional deadband.
    
    A signal conditioning filter that constrains the rate of change of a signal to
    specified maximum rates. Provides independent control of rising and falling edge
    rates, making it ideal for protecting mechanical systems, smoothing control commands,
    and preventing abrupt transitions that could cause overshoot or instability.
    
    The limiter implements rate-of-change constraints:
        
        Δy/Δt ≤ rise_rate (when input > output)
        Δy/Δt ≥ -fall_rate (when input < output)
    
    Where:
        
        - rise_rate: Maximum allowed positive rate (units/second)
        - fall_rate: Maximum allowed negative rate (units/second)
        - Output tracks input but changes no faster than specified rates
    
    Key Features:
        
        - Independent rise and fall rate limits (asymmetric control)
        - Optional deadband for noise immunity
        - Supports variable and fixed sampling rates
        - Protects mechanical systems from excessive acceleration
        - Smooths step changes in control commands
        - Real-time adjustable rate limits
        - No phase distortion (non-frequency-dependent)
    
    Applications:
        
        - Motor speed command smoothing
        - Servo position control with rate limiting
        - Setpoint ramping in process control
        - Mechanical system protection
        - Audio volume fade in/out
        - LED brightness transitions
        - Temperature setpoint ramping
        - Valve opening/closing rate control
    
    Mathematical Properties:
        
        - Linear phase response (simple delay)
        - No frequency-dependent attenuation
        - Deterministic worst-case delay
        - Ramp time: Δ / rate for step of size Δ
        - Asymmetric response for rise vs. fall
        - Deadband provides hysteresis
    
    Rate Selection Guidelines:
        
        - Motor acceleration: Typically 50-500 RPM/s
        - Servo positioning: 10-100 degrees/s
        - Temperature ramping: 0.5-5 °C/min
        - Audio volume: 10-50 dB/s
        - LED brightness: 100-1000 units/s
    """
    def __init__(self, rise_per_s: float, fall_per_s: float | None = None, 
                 initial: float = 0.0, fs: float | None = None, 
                 deadband: float = 0.0) -> None:
        """
        Initialize slew rate limiter with specified rate constraints.
        
        Creates a rate-of-change limiter that constrains how quickly the output
        can track changes in the input. Separate limits for rising and falling
        edges allow asymmetric control suitable for systems with different
        acceleration and deceleration characteristics.
        
        :param rise_per_s: Maximum rising rate in units/second (must be > 0)
                          Controls how fast output can increase when tracking
                          an increasing input signal.
        :param fall_per_s: Maximum falling rate in units/second (must be > 0)
                          Controls how fast output can decrease when tracking
                          a decreasing input signal. If None, uses rise_per_s
                          value for symmetric rate limiting.
        :param initial: Initial output value (default: 0.0)
                       Starting point for the limiter. Use expected initial
                       signal level to avoid unnecessary ramping at startup.
        :param fs: Optional fixed sampling rate in Hz (default: None)
                  If provided, use update(x) with automatic dt calculation.
                  If None, must use update_with_dt(x, dt) with explicit dt.
        :param deadband: Deadband threshold in signal units (default: 0.0)
                        Changes smaller than this are ignored, providing
                        immunity to noise and small jitter.
        
        :raises FilterConfigurationError: If rise_per_s <= 0, fall_per_s <= 0,
                                         fs <= 0, or deadband < 0
        :raises TypeError: If parameters cannot be converted to numeric types
        
        Rate Specification:
            Rates are specified in signal units per second. For example:
            
            - Motor speed: RPM per second (e.g., 100.0 → 100 RPM/s)
            - Position: degrees per second (e.g., 45.0 → 45°/s)
            - Temperature: °C per second (e.g., 0.5 → 0.5°C/s)
            - Volume: dB per second (e.g., 20.0 → 20dB/s)
        
        Asymmetric Rates:
            
            When rise_per_s ≠ fall_per_s:
            
            - Useful for systems with different dynamics in each direction
            - Example: Motor can brake faster than it can accelerate
            - Example: Heater cools slower than it heats
            - Example: Audio fade-out faster than fade-in
        
        Deadband Feature:
            
            - Prevents output changes for inputs within ±deadband
            - Reduces output jitter from noisy inputs
            - Particularly useful with variable sampling rates
            - Set to ~1-5% of signal range for typical applications
        
        Example
        -------
        ```python
            >>> from ufilter import SlewRateLimiter
            >>> 
            >>> # Motor control with asymmetric rates
            >>> motor_limiter = SlewRateLimiter(
            ...     rise_per_s=100.0,    # Accelerate at 100 RPM/s
            ...     fall_per_s=200.0,     # Decelerate at 200 RPM/s (brake faster)
            ...     initial=0.0,
            ...     fs=50.0               # 50 Hz control loop
            ... )
            >>> print(f"Rise rate: {motor_limiter.rise_per_s} RPM/s")
            >>> print(f"Fall rate: {motor_limiter.fall_per_s} RPM/s")
            >>> # Rise rate: 100.0 RPM/s
            >>> # Fall rate: 200.0 RPM/s
            >>> 
            >>> # Symmetric rate limiting with deadband
            >>> servo_limiter = SlewRateLimiter(
            ...     rise_per_s=45.0,      # 45 degrees/second both directions
            ...     fall_per_s=None,      # Same as rise_per_s
            ...     initial=90.0,         # Start at 90 degrees
            ...     fs=100.0,
            ...     deadband=0.5          # Ignore changes < 0.5 degrees
            ... )
            >>> print(f"Rate limit: ±{servo_limiter.rise_per_s} deg/s")
            >>> print(f"Deadband: ±{servo_limiter.deadband} degrees")
            >>> 
            >>> # Variable sampling rate configuration
            >>> temp_limiter = SlewRateLimiter(
            ...     rise_per_s=1.0,       # Heat at 1°C/s
            ...     fall_per_s=0.3,       # Cool at 0.3°C/s (slower)
            ...     initial=20.0          # Room temperature
            ... )  # No fs - must use update_with_dt()
            >>> 
            >>> # Calculate required time for step change
            >>> def calculate_ramp_time(limiter, target_change):
            ...     '''Calculate time required to reach target change.'''
            ...     if target_change > 0:
            ...         time_s = target_change / limiter.rise_per_s
            ...         print(f"Rise time: {time_s:.2f}s for +{target_change} units")
            ...     else:
            ...         time_s = abs(target_change) / limiter.fall_per_s
            ...         print(f"Fall time: {time_s:.2f}s for {target_change} units")
            ...     return time_s
            >>> 
            >>> # Example: Motor accelerating 1000 RPM
            >>> calculate_ramp_time(motor_limiter, 1000.0)  # 10.0s
            >>> # Rise time: 10.00s for +1000.0 units
            >>> 
            >>> # Example: Motor decelerating 1000 RPM
            >>> calculate_ramp_time(motor_limiter, -1000.0)  # 5.0s
            >>> # Fall time: 5.00s for -1000.0 units
            >>> 
            >>> # Invalid configurations
            >>> try:
            ...     bad_limiter = SlewRateLimiter(rise_per_s=0.0)  # Zero rate
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     bad_limiter = SlewRateLimiter(rise_per_s=10.0, deadband=-1.0)
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")  # Negative deadband
        ```
        """
        ...
    
    @property
    def rise_per_s(self) -> float:
        """
        Get maximum rising rate in units/second.
        
        Returns the current rate limit for positive (rising) changes. This represents
        the maximum speed at which the output can increase when tracking an increasing
        input signal.
        
        :return: Maximum rising rate in signal units per second (always positive)
        
        Rate Interpretation:
            
            - Motor speed: RPM per second (e.g., 100.0 = 100 RPM/s)
            - Servo position: degrees per second (e.g., 45.0 = 45°/s)
            - Temperature: °C per second (e.g., 1.0 = 1°C/s)
            - Audio volume: dB per second (e.g., 20.0 = 20dB/s)
        
        Example
        -------
        ```python
            >>> from ufilter import SlewRateLimiter
            >>> 
            >>> limiter = SlewRateLimiter(rise_per_s=100.0, fall_per_s=200.0, fs=50.0)
            >>> print(f"Rise rate: {limiter.rise_per_s} units/s")
            >>> # Rise rate: 100.0 units/s
            >>> 
            >>> # Calculate time to reach target
            >>> target_change = 500.0  # units
            >>> time_to_target = target_change / limiter.rise_per_s
            >>> print(f"Time to rise {target_change}: {time_to_target:.1f}s")
            >>> # Time to rise 500.0: 5.0s
        ```
        """
        ...
    
    @rise_per_s.setter
    def rise_per_s(self, value: float) -> None:
        """
        Set maximum rising rate in units/second.
        
        Updates the rate limit for positive (rising) changes. The new rate takes
        effect immediately for subsequent update calls. For fixed sampling rate mode,
        the maximum step size per sample is automatically recalculated.
        
        :param value: New maximum rising rate (must be > 0)
        
        :raises FilterConfigurationError: If value <= 0
        :raises TypeError: If value cannot be converted to float
        
        Effects of Changing Rise Rate:
            
            Increasing rise rate (faster acceleration):
                
                - Output tracks increasing inputs more quickly
                - Shorter rise time to reach target
                - Less protection against overshoot
                - More responsive system
            
            Decreasing rise rate (slower acceleration):
                
                - Output tracks increasing inputs more slowly
                - Longer rise time to reach target
                - Better mechanical protection
                - Smoother acceleration
        
        Real-Time Adjustment Use Cases:
            
            - Load-dependent acceleration (heavy load = slower rate)
            - Temperature-dependent ramping (cold = slower rate)
            - User-selectable speed modes (eco/normal/sport)
            - Safety-critical situations (emergency = fast rate)
        
        Example
        -------
        ```python
            >>> from ufilter import SlewRateLimiter
            >>> 
            >>> # Create limiter
            >>> motor_limiter = SlewRateLimiter(
            ...     rise_per_s=100.0,
            ...     fall_per_s=200.0,
            ...     fs=50.0
            ... )
            >>> 
            >>> # Run in normal mode
            >>> print(f"Normal mode: {motor_limiter.rise_per_s} RPM/s")
            >>> for i in range(5):
            ...     output = motor_limiter.update(1000.0)
            ...     print(f"  t={i*20}ms: {output:.0f} RPM")
            >>> 
            >>> # Switch to sport mode (faster acceleration)
            >>> motor_limiter.rise_per_s = 300.0
            >>> motor_limiter.reset()  # Start fresh
            >>> print(f"\nSport mode: {motor_limiter.rise_per_s} RPM/s")
            >>> for i in range(5):
            ...     output = motor_limiter.update(1000.0)
            ...     print(f"  t={i*20}ms: {output:.0f} RPM")
            >>> 
            >>> # Switch to eco mode (slower acceleration)
            >>> motor_limiter.rise_per_s = 50.0
            >>> motor_limiter.reset()
            >>> print(f"\nEco mode: {motor_limiter.rise_per_s} RPM/s")
            >>> 
            >>> # Load-dependent acceleration
            >>> def load_dependent_control():
            ...     limiter = SlewRateLimiter(rise_per_s=100.0, fs=50.0)
            ...     
            ...     for load_kg in [0, 50, 100, 200]:
            ...         # Reduce acceleration rate as load increases
            ...         max_accel = 100.0 * (1.0 - load_kg / 250.0)
            ...         limiter.rise_per_s = max(max_accel, 20.0)  # Min 20 RPM/s
            ...         
            ...         print(f"Load {load_kg}kg: rise rate = {limiter.rise_per_s:.1f} RPM/s")
        ```
        """
        ...
    
    @property
    def fall_per_s(self) -> float:
        """
        Get maximum falling rate in units/second.
        
        Returns the current rate limit for negative (falling) changes. This represents
        the maximum speed at which the output can decrease when tracking a decreasing
        input signal.
        
        :return: Maximum falling rate in signal units per second (always positive)
        
        Note: The value is stored as positive, representing the magnitude of the
        maximum negative rate of change.
        
        Example
        -------
        ```python
            >>> from ufilter import SlewRateLimiter
            >>> 
            >>> limiter = SlewRateLimiter(rise_per_s=100.0, fall_per_s=200.0, fs=50.0)
            >>> print(f"Fall rate: {limiter.fall_per_s} units/s")
            >>> # Fall rate: 200.0 units/s
            >>> 
            >>> # Calculate time to decrease
            >>> target_change = -500.0  # units (negative)
            >>> time_to_fall = abs(target_change) / limiter.fall_per_s
            >>> print(f"Time to fall {abs(target_change)}: {time_to_fall:.1f}s")
            >>> # Time to fall 500.0: 2.5s
        ```
        """
        ...
    
    @fall_per_s.setter
    def fall_per_s(self, value: float) -> None:
        """
        Set maximum falling rate in units/second.
        
        Updates the rate limit for negative (falling) changes. The new rate takes
        effect immediately for subsequent update calls. For fixed sampling rate mode,
        the maximum step size per sample is automatically recalculated.
        
        :param value: New maximum falling rate (must be > 0, represents magnitude)
        
        :raises FilterConfigurationError: If value <= 0
        :raises TypeError: If value cannot be converted to float
        
        Effects of Changing Fall Rate:
            
            Increasing fall rate (faster deceleration):
                
                - Output tracks decreasing inputs more quickly
                - Shorter fall time to reach target
                - Faster braking/stopping
                - More responsive system
            
            Decreasing fall rate (slower deceleration):
                
                - Output tracks decreasing inputs more slowly
                - Longer fall time to reach target
                - Gentler braking/stopping
                - Smoother deceleration
        
        Asymmetric Rate Applications:
            
            - Motors: Often brake faster than they accelerate
            - Heating: Heat quickly, cool slowly (thermal inertia)
            - Audio: Fade out faster than fade in (perceptual)
            - Safety: Emergency stop faster than normal slowdown
        
        Example
        -------
        ```python
            >>> from ufilter import SlewRateLimiter
            >>> 
            >>> # Motor with adjustable braking
            >>> motor_limiter = SlewRateLimiter(
            ...     rise_per_s=100.0,
            ...     fall_per_s=200.0,
            ...     initial=1000.0,  # Running at 1000 RPM
            ...     fs=50.0
            ... )
            >>> 
            >>> # Normal braking
            >>> print(f"Normal braking: {motor_limiter.fall_per_s} RPM/s")
            >>> for i in range(5):
            ...     output = motor_limiter.update(0.0)
            ...     print(f"  t={i*20}ms: {output:.0f} RPM")
            >>> 
            >>> # Emergency stop (faster braking)
            >>> motor_limiter.reset(1000.0)  # Reset to running
            >>> motor_limiter.fall_per_s = 500.0  # Much faster braking
            >>> print(f"\nEmergency stop: {motor_limiter.fall_per_s} RPM/s")
            >>> for i in range(5):
            ...     output = motor_limiter.update(0.0)
            ...     print(f"  t={i*20}ms: {output:.0f} RPM")
            >>> 
            >>> # Gentle deceleration for comfort
            >>> motor_limiter.reset(1000.0)
            >>> motor_limiter.fall_per_s = 50.0  # Gentle
            >>> print(f"\nGentle stop: {motor_limiter.fall_per_s} RPM/s")
        ```
        """
        ...
    
    @property
    def deadband(self) -> float:
        """
        Get deadband threshold in signal units.
        
        Returns the current deadband value. Changes in the input smaller than this
        threshold are ignored, providing noise immunity and reducing output jitter.
        
        :return: Deadband threshold in signal units (always non-negative)
        
        Deadband Behavior:
            
            - If |input - output| ≤ deadband: output unchanged
            - If |input - output| > deadband: apply rate limiting
            - Creates hysteresis around current output value
            - Prevents chatter from noisy inputs
        
        Example
        -------
        ```python
            >>> from ufilter import SlewRateLimiter
            >>> 
            >>> limiter = SlewRateLimiter(
            ...     rise_per_s=100.0,
            ...     fall_per_s=100.0,
            ...     initial=50.0,
            ...     fs=100.0,
            ...     deadband=2.0
            ... )
            >>> 
            >>> print(f"Deadband: ±{limiter.deadband} units")
            >>> # Deadband: ±2.0 units
            >>> 
            >>> # Test deadband effect
            >>> print("\nInput | Output | Action")
            >>> print("-" * 30)
            >>> 
            >>> # Small change - ignored
            >>> out1 = limiter.update(51.5)
            >>> print(f"51.5  | {out1:.1f}    | Ignored (< 2.0)")
            >>> 
            >>> # Large change - tracked
            >>> out2 = limiter.update(55.0)
            >>> print(f"55.0  | {out2:.1f}    | Tracking (> 2.0)")
        ```
        """
        ...
    
    @deadband.setter
    def deadband(self, value: float) -> None:
        """
        Set deadband threshold in signal units.
        
        Updates the deadband value that determines the minimum input change required
        to produce an output change. This provides adjustable noise immunity.
        
        :param value: New deadband threshold (must be >= 0)
        
        :raises FilterConfigurationError: If value < 0
        :raises TypeError: If value cannot be converted to float
        
        Effects of Changing Deadband:
            
            Increasing deadband:
                
                - More noise immunity
                - Larger changes ignored
                - Reduces output updates
                - May miss small legitimate changes
            
            Decreasing deadband:
                
                - Less noise immunity
                - Smaller changes tracked
                - More output updates
                - Better tracking of small changes
            
            Zero deadband:
                
                - No noise filtering
                - All changes tracked (within rate limits)
                - Maximum responsiveness
                - Susceptible to noise
        
        Deadband Selection Guidelines:
            
            - Set to 1-2× expected noise amplitude
            - Typically 1-5% of signal range
            - Too large: misses real changes
            - Too small: unnecessary updates from noise
        
        Example
        -------
        ```python
            >>> from ufilter import SlewRateLimiter
            >>> 
            >>> # Start with no deadband
            >>> limiter = SlewRateLimiter(
            ...     rise_per_s=50.0,
            ...     fall_per_s=50.0,
            ...     initial=100.0,
            ...     fs=100.0,
            ...     deadband=0.0
            ... )
            >>> 
            >>> # Noisy input
            >>> noisy_inputs = [100.0, 100.5, 99.8, 100.3, 99.5, 100.2]
            >>> 
            >>> print("No deadband:")
            >>> for inp in noisy_inputs:
            ...     out = limiter.update(inp)
            ...     print(f"  {inp:5.1f} → {out:5.2f}")
            >>> 
            >>> # Add deadband to reduce jitter
            >>> limiter.reset(100.0)
            >>> limiter.deadband = 1.0
            >>> 
            >>> print(f"\nWith deadband = {limiter.deadband}:")
            >>> for inp in noisy_inputs:
            ...     out = limiter.update(inp)
            ...     print(f"  {inp:5.1f} → {out:5.2f}")
            >>> 
            >>> # Adaptive deadband based on signal quality
            >>> def adaptive_deadband():
            ...     position_limiter = SlewRateLimiter(
            ...         rise_per_s=100.0,
            ...         fs=50.0,
            ...         deadband=1.0
            ...     )
            ...     
            ...     for position, snr in sensor_data:
            ...         # Adjust deadband based on signal-to-noise ratio
            ...         if snr > 20:  # Good signal
            ...             position_limiter.deadband = 0.5
            ...         elif snr > 10:  # Moderate signal
            ...             position_limiter.deadband = 2.0
            ...         else:  # Noisy signal
            ...             position_limiter.deadband = 5.0
            ...         
            ...         filtered = position_limiter.update(position)
        ```
        """
        ...
    
    def set_fs(self, fs: float) -> None:
        """
        Set fixed sampling rate and recompute step sizes.
        
        Updates the limiter to use a fixed sampling rate and recalculates the
        maximum step sizes per sample based on the new rate and the current
        rise/fall rate limits. This allows switching from variable to fixed
        sampling mode or changing the sampling rate.
        
        :param fs: Sampling rate in Hz (must be > 0)
        
        :raises FilterConfigurationError: If fs <= 0
        :raises TypeError: If fs cannot be converted to float
        
        Effect of Sampling Rate:
            The maximum change per sample is calculated as:
            
            rise_step = rise_per_s / fs
            fall_step = fall_per_s / fs
            
            Higher fs → smaller steps per sample (same rate/second)
            Lower fs → larger steps per sample (same rate/second)
        
        Use Cases:
            
            - Converting from variable to fixed rate operation
            - Changing control loop frequency
            - Adapting to different timing requirements
            - Synchronizing with other system components
        
        Example
        -------
        ```python
            >>> from ufilter import SlewRateLimiter
            >>> 
            >>> # Create with variable rate
            >>> limiter = SlewRateLimiter(rise_per_s=100.0, fall_per_s=200.0)
            >>> print(f"Initial fs: {limiter.fs}")
            >>> # Initial fs: None
            >>> 
            >>> # Switch to fixed rate at 50 Hz
            >>> limiter.set_fs(50.0)
            >>> print(f"New fs: {limiter.fs} Hz")
            >>> # New fs: 50.0 Hz
            >>> 
            >>> # Calculate step sizes
            >>> rise_step = limiter.rise_per_s / 50.0
            >>> fall_step = limiter.fall_per_s / 50.0
            >>> print(f"Rise step: {rise_step:.2f} units/sample")
            >>> print(f"Fall step: {fall_step:.2f} units/sample")
            >>> # Rise step: 2.00 units/sample
            >>> # Fall step: 4.00 units/sample
            >>> 
            >>> # Now use simple update() instead of update_with_dt()
            >>> for i in range(10):
            ...     output = limiter.update(500.0)
            ...     if i % 2 == 0:
            ...         print(f"Sample {i}: {output:.1f}")
            >>> 
            >>> # Change sampling rate
            >>> limiter.set_fs(100.0)
            >>> print(f"\nUpdated fs: {limiter.fs} Hz")
            >>> rise_step_new = limiter.rise_per_s / 100.0
            >>> print(f"New rise step: {rise_step_new:.2f} units/sample")
            >>> # Updated fs: 100.0 Hz
            >>> # New rise step: 1.00 units/sample
            >>> 
            >>> # Adaptive sampling rate example
            >>> def adaptive_sampling():
            ...     ctrl = SlewRateLimiter(rise_per_s=100.0, fall_per_s=100.0)
            ...     
            ...     # Start with slow sampling
            ...     ctrl.set_fs(10.0)
            ...     print(f"Low precision mode: {ctrl.fs} Hz")
            ...     
            ...     # Switch to fast sampling for critical operation
            ...     ctrl.set_fs(100.0)
            ...     print(f"High precision mode: {ctrl.fs} Hz")
            ...     
            ...     # Return to slow sampling
            ...     ctrl.set_fs(10.0)
            ...     print(f"Power save mode: {ctrl.fs} Hz")
            >>> 
            >>> # Invalid sampling rate
            >>> try:
            ...     limiter.set_fs(0.0)
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     limiter.set_fs(-10.0)
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
        ```
        """
        ...
    
    def update_with_dt(self, x: float, dt_s: float) -> float:
        """
        Update limiter with variable time step.
        
        Processes a single input value and constrains the rate of change based on
        the actual elapsed time since the last update. The maximum allowed change
        is calculated from the rate limits and actual dt, making it suitable for
        systems with irregular or variable sampling intervals.
        
        :param x: Input value (any numeric type, converted to float)
        :param dt_s: Time elapsed since last update in seconds (must be > 0)
        :return: Rate-limited output value as float
        
        :raises FilterOperationError: If dt_s <= 0
        :raises TypeError: If parameters cannot be converted to float
        
        Algorithm Details:
            The limiter implements rate-of-change constraints:
            
            error = input - output
            
            If |error| <= deadband:
                output unchanged (noise immunity)
            Else if error > 0:
                max_step = rise_per_s × dt_s
                output = output + min(error, max_step)
            Else if error < 0:
                max_step = fall_per_s × dt_s
                output = output + max(error, -max_step)
        
        Performance Characteristics:
            
            - O(1) computational complexity
            - Four floating-point comparisons per sample
            - Two floating-point operations (multiply, add)
            - Suitable for real-time variable-rate systems
            - Adapts to actual timing automatically
        
        Deadband Behavior:
            
            - Changes smaller than deadband are ignored
            - Prevents output jitter from noisy inputs
            - Provides hysteresis around current output
            - Particularly useful with variable dt
            - Set to 1-5% of signal range typically
        
        Example
        -------
        ```python
            >>> import time
            >>> from ufilter import SlewRateLimiter
            >>> 
            >>> # Variable-rate motor control
            >>> motor_limiter = SlewRateLimiter(
            ...     rise_per_s=100.0,    # 100 RPM/s acceleration
            ...     fall_per_s=200.0,     # 200 RPM/s deceleration
            ...     initial=0.0,
            ...     deadband=5.0          # Ignore < 5 RPM changes
            ... )
            >>> 
            >>> # Simulate variable timing
            >>> last_time = time.ticks_ms()
            >>> target_speed = 500.0
            >>> 
            >>> print("Time(ms) | dt(ms) | Target | Output | Limited?")
            >>> print("-" * 50)
            >>> 
            >>> for i in range(10):
            ...     # Variable delays (8-12ms)
            ...     time.sleep(0.008 + (i % 5) * 0.001)
            ...     
            ...     current_time = time.ticks_ms()
            ...     dt = time.ticks_diff(current_time, last_time) / 1000.0
            ...     last_time = current_time
            ...     
            ...     output = motor_limiter.update_with_dt(target_speed, dt)
            ...     
            ...     # Calculate if limited
            ...     max_change = motor_limiter.rise_per_s * dt
            ...     is_limited = (target_speed - output) > 0.1
            ...     
            ...     print(f"{current_time:8d} | {dt*1000:6.1f} | {target_speed:6.1f} | "
            ...           f"{output:6.1f} | {'YES' if is_limited else 'NO'}")
            >>> 
            >>> # Demonstrating deadband with noise
            >>> def demonstrate_deadband():
            ...     limiter = SlewRateLimiter(
            ...         rise_per_s=50.0,
            ...         fall_per_s=50.0,
            ...         initial=100.0,
            ...         deadband=3.0  # Ignore < 3 unit changes
            ...     )
            ...     
            ...     # Noisy input around 100
            ...     noisy_inputs = [100.0, 101.5, 99.8, 100.2, 98.5, 100.1, 104.5]
            ...     dt = 0.01  # 10ms updates
            ...     
            ...     print("Input  | Output | Changed | Reason")
            ...     print("-" * 45)
            ...     
            ...     for inp in noisy_inputs:
            ...         prev_output = limiter.y
            ...         output = limiter.update_with_dt(inp, dt)
            ...         changed = abs(output - prev_output) > 0.001
            ...         
            ...         error = abs(inp - prev_output)
            ...         if error <= limiter.deadband:
            ...             reason = f"Deadband (Δ={error:.1f})"
            ...         elif changed:
            ...             reason = f"Tracking (Δ={error:.1f})"
            ...         else:
            ...             reason = "Reached target"
            ...         
            ...         print(f"{inp:6.1f} | {output:6.2f} | {'Yes' if changed else 'No ':3s} | {reason}")
            >>> 
            >>> # Asymmetric rate limiting
            >>> def demonstrate_asymmetric_rates():
            ...     limiter = SlewRateLimiter(
            ...         rise_per_s=100.0,  # Slow rise
            ...         fall_per_s=500.0,  # Fast fall
            ...         initial=0.0
            ...     )
            ...     
            ...     dt = 0.01  # 10ms
            ...     
            ...     print("Rising phase (target = 100):")
            ...     target = 100.0
            ...     for i in range(15):
            ...         output = limiter.update_with_dt(target, dt)
            ...         if i % 5 == 0:
            ...             print(f"  t={i*10:3d}ms: {output:5.1f}")
            ...     
            ...     print(f"\nFalling phase (target = 0):")
            ...     target = 0.0
            ...     for i in range(15):
            ...         output = limiter.update_with_dt(target, dt)
            ...         if i % 5 == 0:
            ...             print(f"  t={i*10:3d}ms: {output:5.1f}")
        ```
        """
        ...
    
    def update(self, x: float) -> float:
        """
        Update limiter with fixed time step.
        
        Processes a single input value with the fixed sampling rate specified in the
        constructor. The maximum allowed change per sample is pre-calculated from
        the rate limits and sampling period, providing efficient operation for
        periodic control systems.
        
        :param x: Input value (any numeric type, converted to float)
        :return: Rate-limited output value as float
        
        :raises FilterOperationError: If fs was not provided in constructor
        :raises TypeError: If input cannot be converted to float
        
        Algorithm Details:
            The limiter uses pre-calculated maximum step sizes:
            
            rise_step = rise_per_s / fs
            fall_step = fall_per_s / fs
            
            Then applies constraints:
            
            error = input - output
            
            If |error| <= deadband:
                output unchanged
            Else if error > 0:
                output = output + min(error, rise_step)
            Else:
                output = output + max(error, -fall_step)
        
        Performance Characteristics:
            
            - O(1) computational complexity
            - Three floating-point comparisons per sample
            - One floating-point addition per sample
            - Pre-calculated step sizes for efficiency
            - Deterministic execution time
            - Ideal for periodic control loops
        
        Ramp Time Calculation:
            For a step input of size Δ:
            
            Rise time: Δ / rise_per_s seconds
            Fall time: |Δ| / fall_per_s seconds
            Samples required: time × fs
        
        Example
        -------
        ```python
            >>> from ufilter import SlewRateLimiter
            >>> 
            >>> # Motor speed control at 50 Hz
            >>> motor_limiter = SlewRateLimiter(
            ...     rise_per_s=100.0,    # 100 RPM/s
            ...     fall_per_s=200.0,     # 200 RPM/s
            ...     initial=0.0,
            ...     fs=50.0              # 50 Hz control
            ... )
            >>> 
            >>> # Calculate step sizes
            >>> rise_step = motor_limiter.rise_per_s / 50.0
            >>> fall_step = motor_limiter.fall_per_s / 50.0
            >>> print(f"Rise step: {rise_step:.2f} RPM/sample")
            >>> print(f"Fall step: {fall_step:.2f} RPM/sample")
            >>> # Rise step: 2.00 RPM/sample
            >>> # Fall step: 4.00 RPM/sample
            >>> 
            >>> # Step response demonstration
            >>> target = 500.0  # Step to 500 RPM
            >>> 
            >>> print("\nRise phase:")
            >>> print("Sample | Output | Change | Progress")
            >>> print("-" * 40)
            >>> 
            >>> for i in range(0, 300, 50):  # Every 50th sample (1 second intervals)
            ...     output = motor_limiter.update(target)
            ...     change_per_sec = rise_step * 50.0
            ...     progress = (output / target) * 100
            ...     print(f"{i:6d} | {output:6.1f} | {change_per_sec:+6.1f} | {progress:5.1f}%")
            >>> 
            >>> # Verify at target
            >>> print(f"\nFinal output: {motor_limiter.y:.1f} RPM")
            >>> 
            >>> # Fall phase
            >>> target = 0.0
            >>> print("\nFall phase:")
            >>> print("Sample | Output | Change/s")
            >>> print("-" * 30)
            >>> 
            >>> for i in range(0, 150, 25):  # Faster deceleration
            ...     output = motor_limiter.update(target)
            ...     if i % 25 == 0:
            ...         print(f"{i:6d} | {output:6.1f} | {-fall_step*50.0:+7.1f}")
            >>> 
            >>> # Production control loop example
            >>> def motor_control_loop():
            ...     limiter = SlewRateLimiter(
            ...         rise_per_s=150.0,
            ...         fall_per_s=300.0,
            ...         initial=0.0,
            ...         fs=100.0  # 100 Hz
            ...     )
            ...     
            ...     user_setpoint = 0.0
            ...     
            ...     while True:
            ...         # Get user command (could be from GUI, joystick, etc.)
            ...         user_setpoint = get_user_setpoint()  # May change abruptly
            ...         
            ...         # Limit rate of change
            ...         safe_setpoint = limiter.update(user_setpoint)
            ...         
            ...         # Apply to motor
            ...         set_motor_speed(safe_setpoint)
            ...         
            ...         # 100 Hz timing
            ...         time.sleep(0.01)
            >>> 
            >>> # Error handling
            >>> try:
            ...     # No fs provided in constructor
            ...     bad_limiter = SlewRateLimiter(rise_per_s=100.0)
            ...     result = bad_limiter.update(10.0)  # Will raise error
            >>> except FilterOperationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> # Multi-axis control
            >>> def three_axis_position_control():
            ...     # Create limiters for X, Y, Z axes
            ...     limiters = [
            ...         SlewRateLimiter(rise_per_s=100.0, fall_per_s=100.0, fs=50.0),
            ...         SlewRateLimiter(rise_per_s=100.0, fall_per_s=100.0, fs=50.0),
            ...         SlewRateLimiter(rise_per_s=80.0, fall_per_s=80.0, fs=50.0)
            ...     ]
            ...     
            ...     target_pos = [100.0, 50.0, 30.0]  # Target X, Y, Z
            ...     
            ...     # Control loop
            ...     for step in range(100):
            ...         smooth_pos = [lim.update(tgt) for lim, tgt in zip(limiters, target_pos)]
            ...         
            ...         if step % 10 == 0:
            ...             print(f"Step {step}: X={smooth_pos[0]:.1f}, Y={smooth_pos[1]:.1f}, Z={smooth_pos[2]:.1f}")
            ...         
            ...         # Apply to motors
            ...         set_xyz_position(smooth_pos)
            ...         time.sleep(0.02)  # 50 Hz
        ```
        """
        ...
    
    def reset(self) -> None:
        """
        Reset limiter to initial state while preserving configuration.
        
        Clears the limiter's internal state (current output value) and resets the
        sample counter, but maintains all configuration parameters like rate limits,
        sampling frequency, deadband, and initial value setting. This allows the
        limiter to be reused for new command sequences without reconfiguration.
        
        Reset Operations:
            
            - Restores output value to initial setting
            - Resets sample counter to zero
            - Preserves rise and fall rate limits
            - Preserves sampling frequency (fs)
            - Preserves deadband threshold
            - Preserves initial value setting
            - Prepares limiter for new input sequence
        
        Use Cases:
            
            - Starting new motion sequence
            - Emergency stop and restart
            - Switching between different control modes
            - Batch processing of command sequences
            - Coordinated multi-axis reset
            - System initialization after power-up
        
        Example
        -------
        ```python
            >>> from ufilter import SlewRateLimiter
            >>> 
            >>> # Create limiter and ramp up
            >>> limiter = SlewRateLimiter(
            ...     rise_per_s=100.0,
            ...     fall_per_s=200.0,
            ...     initial=0.0,
            ...     fs=50.0
            ... )
            >>> 
            >>> print("First sequence - ramp to 500:")
            >>> for i in range(0, 250, 50):
            ...     output = limiter.update(500.0)
            ...     print(f"  Sample {i}: {output:.1f}")
            >>> 
            >>> print(f"\nAfter sequence: output={limiter.y:.1f}, samples={limiter.sample_count}")
            >>> 
            >>> # Reset for new sequence
            >>> limiter.reset()
            >>> print(f"After reset: output={limiter.y:.1f}, samples={limiter.sample_count}")
            >>> 
            >>> # Verify configuration preserved
            >>> print(f"Config: rise={limiter.rise_per_s}, fall={limiter.fall_per_s}, fs={limiter.fs}")
            >>> 
            >>> print("\nSecond sequence - ramp to 300:")
            >>> for i in range(0, 150, 50):
            ...     output = limiter.update(300.0)
            ...     print(f"  Sample {i}: {output:.1f}")
            >>> 
            >>> # Emergency stop scenario
            >>> def emergency_stop_example():
            ...     motor_limiter = SlewRateLimiter(
            ...         rise_per_s=100.0,
            ...         fall_per_s=500.0,  # Fast emergency stop
            ...         initial=0.0,
            ...         fs=100.0
            ...     )
            ...     
            ...     # Normal operation - ramp to speed
            ...     print("Normal operation:")
            ...     for i in range(100):
            ...         speed = motor_limiter.update(1000.0)
            ...         if i % 25 == 0:
            ...             print(f"  t={i*10}ms: {speed:.0f} RPM")
            ...     
            ...     print(f"\nRunning at: {motor_limiter.y:.0f} RPM")
            ...     
            ...     # Emergency stop detected
            ...     print("\nEMERGENCY STOP!")
            ...     limiter.reset()  # Immediate reset to 0
            ...     print(f"Output reset to: {motor_limiter.y:.0f} RPM")
            ...     
            ...     # System can now restart safely
            ...     print("\nRestarting:")
            ...     for i in range(50):
            ...         speed = motor_limiter.update(500.0)
            ...         if i % 10 == 0:
            ...             print(f"  t={i*10}ms: {speed:.0f} RPM")
            >>> 
            >>> # Multi-axis synchronized reset
            >>> def synchronized_multiaxis_reset():
            ...     # Create limiters for robot arm joints
            ...     joint_limiters = [
            ...         SlewRateLimiter(rise_per_s=90.0, fall_per_s=90.0, fs=50.0),   # Joint 1
            ...         SlewRateLimiter(rise_per_s=120.0, fall_per_s=120.0, fs=50.0), # Joint 2
            ...         SlewRateLimiter(rise_per_s=180.0, fall_per_s=180.0, fs=50.0)  # Joint 3
            ...     ]
            ...     
            ...     # Execute motion sequence
            ...     targets = [45.0, 90.0, -30.0]
            ...     print("Executing motion:")
            ...     for i in range(100):
            ...         positions = [lim.update(tgt) for lim, tgt in zip(joint_limiters, targets)]
            ...         if i % 20 == 0:
            ...             print(f"  Step {i}: J1={positions[0]:.1f}° J2={positions[1]:.1f}° J3={positions[2]:.1f}°")
            ...     
            ...     print("\nMotion complete")
            ...     
            ...     # Reset all joints simultaneously for new motion
            ...     for limiter in joint_limiters:
            ...         limiter.reset()
            ...     
            ...     print("All joints reset to home position")
            ...     print("Ready for new motion sequence")
        ```
        """
        ...


class MovingAverage(Base):
    """
    Moving average filter with efficient circular buffer implementation.
    
    A finite impulse response (FIR) filter that computes the arithmetic mean of
    the most recent N samples using a memory-efficient circular buffer. This
    filter provides excellent noise reduction while preserving signal trends,
    making it ideal for smoothing noisy sensor data and extracting signal baselines.
    
    The filter implements the moving average equation:
        
        y[n] = (1/N) * Σ(x[n-k]) for k = 0 to N-1
    
    Key Features:
        
        - O(1) computational complexity per sample (constant time updates)
        - Memory-efficient circular buffer implementation
        - Optimized with @micropython.viper decorator
        - Linear phase response (no phase distortion)
        - Excellent for noise reduction and baseline extraction
        - Configurable window size for different smoothing levels
    
    Performance Characteristics:
        
        - Zero phase delay for centered implementation
        - Group delay: (N-1)/2 samples
        - Frequency response: sinc function with nulls at fs/N, 2*fs/N, etc.
        - DC gain: 0dB (unity gain)
        - Noise reduction: ~10*log10(N) dB for white noise
    
    Applications:
        
        - Sensor data smoothing and noise reduction
        - Signal baseline estimation
        - Trend extraction from noisy measurements
        - Data preprocessing for control systems
        - Real-time signal conditioning
        - Peak detection preprocessing
    
    Mathematical Properties:
        
        - Linear phase response (symmetric impulse response)
        - First null at frequency fs/N
        - Stopband attenuation: -13.3dB at fs/N for rectangular window
        - Transition bandwidth inversely proportional to window size
        - Always stable (FIR filter)
    
    """
    
    def __init__(self, window_size: int, initial: float = 0.0) -> None:
        """
        Initialize moving average filter with specified window size.
        
        Creates a moving average filter using an efficient circular buffer
        implementation. The filter maintains a rolling average of the most
        recent window_size samples, providing smooth output with minimal
        computational overhead.
        
        :param window_size: Number of samples to include in moving average
                           Must be a positive integer. Larger values provide
                           more smoothing but increase delay.
        :param initial: Initial value for all buffer positions (default: 0.0)
                       Use expected signal level to minimize startup transients
        
        :raises ValueError: If window_size is not a positive integer
        :raises TypeError: If initial cannot be converted to float
        
        Window Size Selection Guidelines:
            Small windows (3-10 samples):
        
                - Fast response to signal changes
                - Minimal delay (good for control systems)
                - Less noise reduction
                - Good for: Real-time control, peak detection
            
            Medium windows (10-50 samples):
        
                - Balanced smoothing and responsiveness
                - Moderate delay
                - Good noise reduction
                - Good for: General sensor smoothing, trend detection
            
            Large windows (50+ samples):
        
                - Heavy smoothing, excellent noise reduction
                - Significant delay (not suitable for fast control)
                - Stable baseline estimation
                - Good for: Baseline estimation, very noisy signals
        
        Memory Usage:
        
            - Buffer memory: window_size × 4 bytes (float array)
            - Additional overhead: ~32 bytes for object structure
            - Total memory: approximately (window_size × 4) + 32 bytes
        
        Example
        -------
        ```python
            >>> # Temperature sensor with moderate smoothing
            >>> temp_filter = MovingAverage(window_size=10, initial=22.0)
            >>> print(f"Memory usage: ~{10*4 + 32} bytes")
            >>> 
            >>> # Pressure sensor with heavy smoothing
            >>> pressure_filter = MovingAverage(window_size=100, initial=1013.25)
            >>> 
            >>> # Very responsive filter for control applications
            >>> control_filter = MovingAverage(window_size=3, initial=0.0)
            >>> 
            >>> # Invalid configurations
            >>> try:
            ...     bad_filter = MovingAverage(window_size=0)
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> # Performance consideration for large windows
            >>> def choose_window_size_for_application():
            ...     # For 1 kHz sampling rate
            ...     fs = 1000  # Hz
            ...     
            ...     # Different applications
            ...     applications = {
            ...         'Motor control': 5,      # 5ms delay, fast response
            ...         'Temperature': 60,       # 60ms delay, good smoothing
            ...         'Baseline estimation': 500  # 500ms delay, heavy smoothing
            ...     }
            ...     
            ...     for app, window_size in applications.items():
            ...         delay_ms = window_size / fs * 1000
            ...         memory_bytes = window_size * 4 + 32
            ...         print(f"{app}: {window_size} samples, {delay_ms:.1f}ms delay, {memory_bytes} bytes")
        ```
        """

    @micropython.native
    def update(self, x: float) -> float:
        """
        Update filter with new sample and return moving average.
        
        Efficiently computes the moving average using a circular buffer
        implementation. This method updates the internal state and returns
        the current average of the most recent samples.
        
        :param x: Input sample value (any numeric type, converted to float)
        :return: Current moving average as float
        
        :raises TypeError: If input cannot be converted to float
        
        Algorithm Details:
        
            1. Replace oldest sample in circular buffer with new sample
            2. Update running sum (subtract old value, add new value)
            3. Advance circular buffer index
            4. Return sum divided by number of samples
        
        Performance Characteristics:
        
            - O(1) time complexity (constant time per sample)
            - Single division operation per sample
            - Optimized with @micropython.viper decorator
            - Memory efficient (no data copying)
            - Suitable for high-frequency real-time processing
        
        Circular Buffer Behavior:
        
            - Initial phase: Buffer fills gradually (average of 1, 2, ..., N samples)
            - Steady state: Always averages exactly N most recent samples
            - No memory allocation during operation (fixed buffer size)
            - Automatic wraparound when buffer is full
        
        Example
        -------
        ```python
            >>> # Demonstrate circular buffer behavior
            >>> filter_obj = MovingAverage(window_size=4, initial=0.0)
            >>> 
            >>> test_sequence = [1, 2, 3, 4, 5, 6, 7, 8]
            >>> 
            >>> print("Sample | Input | Buffer State | Average | Samples Used")
            >>> print("-" * 55)
            >>> 
            >>> for i, sample in enumerate(test_sequence):
            ...     avg = filter_obj.update(sample)
            ...     
            ...     # Show internal buffer state (for illustration)
            ...     buffer_contents = list(filter_obj._buf)
            ...     samples_used = min(i + 1, filter_obj.window_size)
            ...     
            ...     print(f"{i+1:6d} | {sample:5d} | {buffer_contents} | {avg:7.2f} | {samples_used:11d}")
            >>> # Sample | Input | Buffer State | Average | Samples Used
            >>> # -------------------------------------------------------
            >>> #      1 |     1 | [1.0, 0.0, 0.0, 0.0] |    1.00 |           1
            >>> #      2 |     2 | [1.0, 2.0, 0.0, 0.0] |    1.50 |           2
            >>> #      3 |     3 | [1.0, 2.0, 3.0, 0.0] |    2.00 |           3
            >>> #      4 |     4 | [1.0, 2.0, 3.0, 4.0] |    2.50 |           4
            >>> #      5 |     5 | [5.0, 2.0, 3.0, 4.0] |    3.50 |           4
            >>> #      6 |     6 | [5.0, 6.0, 3.0, 4.0] |    4.50 |           4
            >>> #      7 |     7 | [5.0, 6.0, 7.0, 4.0] |    5.50 |           4
            >>> #      8 |     8 | [5.0, 6.0, 7.0, 8.0] |    6.50 |           4
            >>> 
            >>> # Noise reduction measurement
            >>> def measure_noise_reduction():
            ...     import random
            ...     
            ...     # Generate noisy signal
            ...     true_signal = 5.0
            ...     noise_level = 0.5
            ...     window_sizes = [1, 5, 10, 20, 50]
            ...     
            ...     print("Noise Reduction Analysis:")
            ...     print("Window Size | Output Std Dev | Noise Reduction (dB)")
            ...     print("-" * 50)
            ...     
            ...     for window_size in window_sizes:
            ...         filter_obj = MovingAverage(window_size=window_size, initial=true_signal)
            ...         
            ...         # Process 1000 noisy samples
            ...         outputs = []
            ...         for _ in range(1000):
            ...             noisy_sample = true_signal + random.uniform(-noise_level, noise_level)
            ...             filtered = filter_obj.update(noisy_sample)
            ...             outputs.append(filtered)
            ...         
            ...         # Calculate output noise level
            ...         mean_output = sum(outputs) / len(outputs)
            ...         variance = sum((x - mean_output)**2 for x in outputs) / len(outputs)
            ...         std_dev = variance ** 0.5
            ...         
            ...         # Theoretical noise reduction for white noise
            ...         theoretical_reduction_db = 10 * log10(window_size)
            ...         actual_reduction_db = 20 * log10(noise_level / std_dev) if std_dev > 0 else 60
            ...         
            ...         print(f"{window_size:11d} | {std_dev:14.4f} | {actual_reduction_db:17.1f}")
        ```
        """

    def reset(self) -> None:
        """
        Reset filter to initial state while preserving configuration.
        
        Clears all samples from the circular buffer and resets internal state
        variables, but maintains the window size and initial value settings.
        This allows the filter to be reused for new data streams without
        reconfiguration.
        
        Reset Operations:
        
            - Fills buffer with initial values
            - Resets sum to initial_value × window_size
            - Resets buffer index to 0
            - Resets sample count to 0
            - Preserves window_size and initial_value settings
        
        Use Cases:
        
            - Starting new measurement session
            - Switching between different signal sources
            - Clearing filter memory after transient events
            - Batch processing of multiple datasets
            - Removing effects of outliers or bad data
        
        Example
        -------
        ```python
            >>> filter_obj = MovingAverage(window_size=5, initial=10.0)
            >>> 
            >>> # Process some data
            >>> test_data = [12, 14, 11, 13, 15, 16, 12, 14]
            >>> for sample in test_data:
            ...     result = filter_obj.update(sample)
            ...     print(f"Sample: {sample:2d} → Average: {result:5.2f}")
            >>> 
            >>> print(f"Before reset: {filter_obj.sample_count} samples processed")
            >>> print(f"Current average: {filter_obj._sum / filter_obj._count:.2f}")
            >>> 
            >>> # Reset filter
            >>> filter_obj.reset()
            >>> print(f"After reset: {filter_obj.sample_count} samples processed")
            >>> print(f"Buffer restored to initial value: {filter_obj._initial_value}")
            >>> 
            >>> # Filter ready for new data
            >>> first_new_result = filter_obj.update(20.0)
            >>> print(f"First new sample result: {first_new_result:.2f}")
            >>> 
            >>> # Error recovery with reset
            >>> def robust_data_processing():
            ...     signal_filter = MovingAverage(window_size=10, initial=5.0)
            ...     error_count = 0
            ...     max_errors = 5
            ...     
            ...     while True:
            ...         try:
            ...             sensor_reading = read_sensor()
            ...             
            ...             # Validate reading
            ...             if not (0 <= sensor_reading <= 100):
            ...                 raise ValueError(f"Sensor reading out of range: {sensor_reading}")
            ...             
            ...             # Process valid reading
            ...             filtered_value = signal_filter.update(sensor_reading)
            ...             error_count = 0  # Reset error count on success
            ...             
            ...             use_filtered_value(filtered_value)
            ...             
            ...         except Exception as e:
            ...             error_count += 1
            ...             print(f"Error {error_count}: {e}")
            ...             
            ...             if error_count >= max_errors:
            ...                 print("Too many errors, resetting filter")
            ...                 signal_filter.reset()
            ...                 error_count = 0
            ...         
            ...         utime.sleep_ms(100)
        ```
        """


class Median(Base):
    """
    Median filter for impulse noise removal and outlier rejection.
    
    A non-linear filter that computes the median value of the most recent N samples
    using a sliding window approach. This filter excels at removing impulse noise,
    spikes, and outliers while preserving signal edges and sharp transitions,
    making it ideal for robust signal conditioning in noisy environments.
    
    The filter implements the median operation:
    
        y[n] = median(x[n], x[n-1], ..., x[n-N+1])
    
    Key Features:
    
        - Excellent impulse noise and spike removal
        - Preserves edges and sharp signal transitions
        - Non-linear operation (order statistics)
        - Robust against outliers and artifacts
        - No overshoot or undershoot in step responses
        - Effective for salt-and-pepper type noise
    
    Performance Characteristics:
    
        - Computational complexity: O(N log N) per sample (sorting)
        - Memory usage: N samples in circular buffer
        - Group delay: (N-1)/2 samples
        - Non-linear phase response
        - DC preservation for constant signals
        - Edge-preserving properties
    
    Applications:
    
        - Sensor spike removal (ADC glitches, EMI)
        - Image processing (salt-and-pepper noise)
        - Biomedical signal preprocessing
        - Industrial measurement outlier rejection
        - Communication system impulse noise removal
        - Robust baseline estimation
    
    Mathematical Properties:
    
        - Output always within input range (no overshoot)
        - Preserves monotonic signal trends
        - Robust breakdown point: 50% for odd window sizes
        - Non-linear operation (not amenable to frequency analysis)
        - Idempotent: median(median(x)) = median(x)
    
    """
    
    def __init__(self, window_size: int, initial: float = 0.0) -> None:
        """
        Initialize median filter with specified window size.
        
        Creates a median filter using a circular buffer to maintain the most
        recent samples. The filter computes the median of these samples to
        provide robust outlier rejection and impulse noise removal.
        
        :param window_size: Number of samples in sliding window (positive integer)
                           Larger windows provide stronger outlier rejection but
                           increase delay and computational cost. Odd values
                           recommended for symmetric median operation.
        :param initial: Initial value for all buffer positions (default: 0.0)
                       Should be set to expected signal level to minimize
                       startup transients.
        
        :raises ValueError: If window_size is not a positive integer
        :raises TypeError: If initial value cannot be converted to float
        
        Window Size Selection Guidelines:
            Small windows (3-5 samples):
    
                - Fast response, minimal delay
                - Light outlier rejection
                - Preserves rapid signal changes
                - Good for: Real-time control, low-latency applications
            
            Medium windows (5-15 samples):
    
                - Balanced performance
                - Good outlier rejection
                - Moderate delay
                - Good for: General sensor conditioning, measurement systems
            
            Large windows (15+ samples):
    
                - Strong outlier rejection
                - High delay (not suitable for fast control)
                - May blur rapid signal changes
                - Good for: Offline processing, heavy noise environments
        
        Computational Considerations:
    
            - CPU usage: O(N log N) per sample due to sorting
            - Memory usage: N × 4 bytes for buffer storage
            - Real-time suitability decreases with window size
            - Consider MovingAverage for lower CPU usage
        
        Example
        -------
        ```python
            >>> # Light filtering for control applications
            >>> control_filter = Median(window_size=3, initial=0.0)
            >>> 
            >>> # Moderate filtering for sensor data
            >>> sensor_filter = Median(window_size=7, initial=25.0)
            >>> 
            >>> # Heavy filtering for noisy environments
            >>> noise_filter = Median(window_size=15, initial=0.0)
            >>> 
            >>> # Invalid configurations
            >>> try:
            ...     bad_filter = Median(window_size=0)
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     bad_filter = Median(window_size=-3)
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> # Performance analysis for different window sizes
            >>> def analyze_performance():
            ...     import utime
            ...     
            ...     window_sizes = [3, 5, 7, 11, 15]
            ...     test_samples = 1000
            ...     
            ...     print("Performance Analysis:")
            ...     print("Window Size | Processing Time (ms) | CPU Usage")
            ...     print("-" * 50)
            ...     
            ...     for size in window_sizes:
            ...         filter_obj = Median(window_size=size)
            ...         
            ...         start_time = utime.ticks_ms()
            ...         for i in range(test_samples):
            ...             filter_obj.update(i * 0.1)
            ...         end_time = utime.ticks_ms()
            ...         
            ...         duration = utime.ticks_diff(end_time, start_time)
            ...         cpu_usage = "Low" if duration < 50 else "Medium" if duration < 200 else "High"
            ...         
            ...         print(f"{size:11d} | {duration:19d} | {cpu_usage}")
        ```
        """

    @micropython.native
    def update(self, x: float) -> float:
        """
        Update filter with new sample and return median value.
        
        Adds the new sample to the circular buffer and computes the median
        of all samples currently in the buffer. This provides robust
        outlier rejection while preserving signal characteristics.
        
        :param x: Input sample value (any numeric type, converted to float)
        :return: Median of current window samples as float
        
        :raises TypeError: If input cannot be converted to float
        
        Algorithm Details:
        
            1. Add new sample to circular buffer (replacing oldest)
            2. Create sorted copy of active buffer contents
            3. Return middle value (or average of two middle values)
            4. Advance buffer index for next sample
        
        Performance Characteristics:
        
            - Time complexity: O(N log N) due to sorting operation
            - Space complexity: O(N) for buffer and temporary sort array
            - Optimized with @micropython.native decorator
            - CPU usage scales with window size
        
        Median Calculation:
        
            - Odd window size: Returns middle element of sorted array
            - Even window size: Returns average of two middle elements
            - Always returns value within input data range
            - Robust against outliers (up to 50% contamination)
        
        Example
        -------
        ```python
            >>> # Basic median filtering
            >>> filter_obj = Median(window_size=5, initial=0.0)
            >>> 
            >>> # Process sequence with outliers
            >>> test_sequence = [1.0, 1.1, 10.0, 1.2, 0.9, 1.0, 15.0, 1.1]
            >>> 
            >>> print("Sample | Input | Median | Buffer Contents")
            >>> print("-" * 45)
            >>> 
            >>> for i, sample in enumerate(test_sequence):
            ...     median_val = filter_obj.update(sample)
            ...     # Show buffer state (first few samples)
            ...     active_samples = min(i + 1, filter_obj.window_size)
            ...     buffer_contents = list(filter_obj._buffer[:active_samples])
            ...     
            ...     print(f"{i+1:6d} | {sample:5.1f} | {median_val:6.1f} | {buffer_contents}")
            >>> # Sample | Input | Median | Buffer Contents
            >>> # ---------------------------------------------
            >>> #      1 |   1.0 |    1.0 | [1.0]
            >>> #      2 |   1.1 |    1.0 | [1.0, 1.1]
            >>> #      3 |  10.0 |    1.1 | [1.0, 1.1, 10.0]
            >>> #      4 |   1.2 |    1.1 | [1.0, 1.1, 10.0, 1.2]
            >>> #      5 |   0.9 |    1.1 | [1.0, 1.1, 10.0, 1.2, 0.9]
            >>> #      6 |   1.0 |    1.0 | [1.0, 1.1, 1.0, 1.2, 0.9]
            >>> #      7 |  15.0 |    1.0 | [1.0, 1.1, 15.0, 1.2, 0.9]
            >>> #      8 |   1.1 |    1.1 | [1.0, 1.1, 15.0, 1.1, 0.9]
            >>> 
            >>> # Comparing median with average for outlier rejection
            >>> def compare_median_vs_average():
            ...     data = [5.0, 5.2, 4.8, 5.3, 20.0, 5.1, 4.9]
            ...     
            ...     # Calculate standard average
            ...     avg = sum(data) / len(data)
            ...     
            ...     # Calculate median
            ...     sorted_data = sorted(data)
            ...     if len(data) % 2 == 1:
            ...         median = sorted_data[len(data) // 2]
            ...     else:
            ...         median = (sorted_data[len(data) // 2 - 1] + sorted_data[len(data) // 2]) / 2
            ...     
            ...     print(f"Data: {data}")
            ...     print(f"Average: {avg:.2f}")
            ...     print(f"Median: {median:.2f}")
            ...     print(f"Outlier effect: {avg - median:.2f} units")
        ```
        """

    def reset(self) -> None:
        """
        Reset filter to initial state while preserving configuration.
        
        Clears all samples from the buffer and resets internal state variables,
        but maintains the window size and initial value settings. This allows
        the filter to be reused for new data streams without reconfiguration.
        
        Reset Operations:
        
            - Fills buffer with initial values
            - Resets buffer index to 0
            - Resets sample count to 0
            - Preserves window_size and initial_value settings
            - Prepares filter for new input sequence
        
        Use Cases:
        
            - Starting new measurement session
            - Switching between different signal sources
            - Clearing filter memory after data corruption
            - Batch processing of multiple datasets
            - Removing effects of previous outliers
        
        Example
        -------
        ```python
            >>> filter_obj = Median(window_size=5, initial=10.0)
            >>> 
            >>> # Process some data with outliers
            >>> test_data = [12, 11, 50, 13, 10, 100, 12, 11]
            >>> for sample in test_data:
            ...     result = filter_obj.update(sample)
            ...     print(f"Sample: {sample:3d} → Median: {result:5.1f}")
            >>> 
            >>> print(f"Before reset: {filter_obj.sample_count} samples processed")
            >>> print(f"Buffer contents: {list(filter_obj._buffer)}")
            >>> 
            >>> # Reset filter
            >>> filter_obj.reset()
            >>> print(f"After reset: {filter_obj.sample_count} samples processed")
            >>> print(f"Buffer restored: {list(filter_obj._buffer)}")
            >>> 
            >>> # Filter ready for new data
            >>> first_new_result = filter_obj.update(20.0)
            >>> print(f"First new sample: {first_new_result:.1f}")
            >>> 
            >>> # Segmented data processing
            >>> def process_segmented_data():
            ...     '''Process multiple data segments with clean filter state.'''
            ...     segments = [
            ...         [1.0, 1.2, 5.0, 1.1, 0.9],  # Normal data with outlier
            ...         [5.0, 5.2, 5.1, 20.0, 4.9],  # Different baseline with outlier
            ...         [10.0, 9.8, 10.2, 10.1, 9.9]  # Third segment
            ...     ]
            ...     
            ...     outlier_filter = Median(window_size=3, initial=0.0)
            ...     
            ...     for i, segment in enumerate(segments):
            ...         print(f"Processing segment {i+1}:")
            ...         
            ...         # Reset filter for clean start on each segment
            ...         outlier_filter.reset()
            ...         
            ...         # Process segment data
            ...         segment_results = []
            ...         for sample in segment:
            ...             clean_value = outlier_filter.update(sample)
            ...             segment_results.append(clean_value)
            ...         
            ...         # Report segment statistics
            ...         avg_raw = sum(segment) / len(segment)
            ...         avg_clean = sum(segment_results) / len(segment_results)
            ...         
            ...         print(f"  Raw data: {segment}")
            ...         print(f"  Filtered: {[f'{x:.1f}' for x in segment_results]}")
            ...         print(f"  Raw average: {avg_raw:.2f}, Clean average: {avg_clean:.2f}")
            ...         print()
        ```
        """


class RMS(Base):
    """
    Root Mean Square (RMS) filter for signal power estimation and analysis.
    
    A specialized filter that computes the RMS (Root Mean Square) value of the most
    recent N samples using an efficient circular buffer implementation. This filter
    is essential for power analysis, signal level monitoring, and amplitude detection
    in real-time applications where understanding signal strength is critical.
    
    The filter implements the RMS equation:
        
        RMS[n] = sqrt((1/N) * Σ(x[n-k]²)) for k = 0 to N-1
    
    Key Features:
        
        - O(1) computational complexity per sample (constant time updates)
        - Efficient circular buffer with running sum of squares
        - Optimized with @micropython.viper decorator
        - Real-time power and amplitude monitoring
        - Suitable for audio, vibration, and signal analysis
        - Automatic numerical stability protection
    
    Performance Characteristics:
        
        - Time complexity: O(1) per sample (no sorting required)
        - Memory usage: N × 4 bytes for sample buffer
        - Group delay: (N-1)/2 samples
        - Always positive output (magnitude only)
        - Responsive to both positive and negative signal changes
        - Excellent for detecting signal presence and amplitude variations
    
    Applications:
        
        - Audio level monitoring and AGC (Automatic Gain Control)
        - Vibration analysis and machinery monitoring
        - Signal quality assessment and SNR estimation
        - Power consumption monitoring in RF systems
        - Biomedical signal amplitude detection (EMG, ECG)
        - Motor current monitoring and load detection
        - Environmental noise level measurement
        - Communication signal strength indication
    
    Mathematical Properties:
        
        - Output represents signal power (energy per sample)
        - Sensitive to outliers and spikes (squared terms amplify)
        - Linear response to signal amplitude changes
        - Zero output for zero-mean noise approaches sqrt(variance)
        - Suitable for detecting both AC and DC signal components
        - Natural integration with power-based signal processing
    
    """
    
    def __init__(self, window_size: int) -> None:
        """
        Initialize RMS filter with specified window size.
        
        Creates an RMS filter using an efficient circular buffer implementation
        that maintains a running sum of squares for constant-time RMS calculation.
        The filter provides real-time power estimation suitable for signal
        monitoring and analysis applications.
        
        :param window_size: Number of samples to include in RMS calculation
                           Must be a positive integer. Larger values provide
                           more stable readings but increase response delay.
        
        :raises ValueError: If window_size is not a positive integer
        
        Window Size Selection Guidelines:
            Short windows (10-100 samples):
        
                - Fast response to amplitude changes
                - Good for transient detection
                - Higher variability in readings
                - Good for: Real-time level meters, AGC systems
            
            Medium windows (100-1000 samples):
        
                - Balanced stability and responsiveness
                - Suitable for most monitoring applications
                - Good for: Audio processing, vibration analysis
            
            Long windows (1000+ samples):
        
                - Very stable readings
                - Slow response to changes
                - Good for: Long-term trending, baseline estimation
        
        Memory and Performance:
        
            - Memory usage: window_size × 4 bytes (float array)
            - Computational cost: O(1) per sample
            - Suitable for high-frequency real-time processing
        
        Example
        -------
        ```python
            >>> # Audio level meter (fast response)
            >>> audio_meter = RMS(window_size=256)  # ~6ms at 44.1kHz
            >>> print(f"Audio meter window: {audio_meter.window_size} samples")
            >>> 
            >>> # Vibration monitor (medium response)
            >>> vibration_monitor = RMS(window_size=500)  # 5s at 100Hz
            >>> print(f"Vibration monitor delay: {500/100:.1f}s at 100Hz")
            >>> 
            >>> # Power trend analysis (slow response)
            >>> power_trend = RMS(window_size=5000)  # 50s at 100Hz
            >>> print(f"Power trend memory usage: ~{5000*4} bytes")
            >>> 
            >>> # Invalid configurations
            >>> try:
            ...     bad_filter = RMS(window_size=0)
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> # Memory consideration for embedded systems
            >>> def estimate_memory_requirements(sample_rate, response_time):
            ...     '''Calculate window size and memory needs for target response.'''
            ...     window_size = int(sample_rate * response_time)
            ...     memory_bytes = window_size * 4
            ...     
            ...     print(f"For {response_time:.1f}s response at {sample_rate}Hz:")
            ...     print(f"  Window size: {window_size} samples")
            ...     print(f"  Memory usage: {memory_bytes} bytes")
            ...     
            ...     return window_size
            >>> 
            >>> # Example calculations for different applications
            >>> audio_window = estimate_memory_requirements(44100, 0.1)  # 100ms audio
            >>> vibration_window = estimate_memory_requirements(100, 2.0)  # 2s vibration
        ```
        """

    @micropython.native
    def update(self, x: float) -> float:
        """
        Update filter with new sample and return current RMS value.
        
        Efficiently computes the RMS value using a circular buffer and running
        sum of squares. This method provides constant-time RMS calculation
        regardless of window size, making it suitable for real-time applications.
        
        :param x: Input sample value (any numeric type, converted to float)
        :return: Current RMS value as float (always non-negative)
        
        :raises TypeError: If input cannot be converted to float
        
        Algorithm Details:
        
            1. Square the new input sample
            2. Add new squared value to running sum
            3. Subtract old squared value from running sum
            4. Update circular buffer with new sample
            5. Return sqrt(sum_of_squares / sample_count)
        
        Performance Characteristics:
        
            - O(1) computational complexity per sample
            - Single square root operation per sample
            - Optimized with @micropython.viper decorator
            - Numerically stable with automatic bounds checking
            - Suitable for high-frequency processing
        
        RMS Properties:
        
            - Always returns non-negative values
            - Sensitive to signal amplitude (linear response)
            - Emphasizes outliers due to squaring operation
            - Provides power-based signal characterization
            - Zero output only for all-zero input window
        
        Example
        -------
        ```python
            >>> # Basic RMS calculation demonstration
            >>> rms_filter = RMS(window_size=4)
            >>> 
            >>> # Test with sine wave samples
            >>> import math
            >>> test_samples = [math.sin(2 * math.pi * i / 8) for i in range(12)]
            >>> 
            >>> print("Sample | Input  | RMS    | Comment")
            >>> print("-" * 35)
            >>> 
            >>> # Process samples and show progression toward true RMS
            >>> for i, sample in enumerate(test_samples):
            ...     rms_value = rms_filter.update(sample)
            ...     # For sine wave, RMS approaches 1/sqrt(2) ≈ 0.707
            ...     comment = "Building" if i < 4 else "Steady state"
            ...     print(f"{i+1:6d} | {sample:+6.3f} | {rms_value:6.3f} | {comment}")
            >>> 
            >>> # Simple audio level calculation
            >>> def analyze_audio_levels():
            ...     '''Demonstrate RMS for audio level analysis.'''
            ...     # Create sine wave at different amplitudes
            ...     level_filter = RMS(window_size=100)
            ...     
            ...     amplitudes = [0.1, 0.5, 1.0, 0.2]
            ...     sample_count = 200
            ...     
            ...     print("\nAudio Level Analysis:")
            ...     print("Amplitude | RMS Level | dB FS")
            ...     print("-" * 35)
            ...     
            ...     for amplitude in amplitudes:
            ...         # Generate sine wave at this amplitude
            ...         level_filter.reset()
            ...         
            ...         # Process full sine wave cycle
            ...         for i in range(sample_count):
            ...             angle = 2 * math.pi * i / 50  # 50 samples per cycle
            ...             sample = amplitude * math.sin(angle)
            ...             level = level_filter.update(sample)
            ...         
            ...         # Calculate dB relative to full scale
            ...         true_rms = amplitude / math.sqrt(2)
            ...         db_level = 20 * math.log10(level) if level > 0 else -100
            ...         
            ...         print(f"{amplitude:9.2f} | {level:9.4f} | {db_level:6.1f}")
        ```
        """

    def reset(self) -> None:
        """
        Reset filter to initial state while preserving configuration.
        
        Clears all samples from the circular buffer and resets internal state
        variables, but maintains the window size setting. This allows the filter
        to be reused for new data streams without reconfiguration.
        
        Reset Operations:
        
            - Clears all buffer samples to zero
            - Resets sum of squares to zero
            - Resets buffer index to zero
            - Resets sample count to zero
            - Preserves window_size setting
        
        Use Cases:
        
            - Starting new measurement session
            - Switching between different signal sources
            - Clearing filter memory after data corruption
            - Initializing for baseline measurements
            - Removing effects of previous transients
        
        Example
        -------
        ```python
            >>> # Demonstrate reset functionality
            >>> rms_filter = RMS(window_size=100)
            >>> 
            >>> # Process some test data
            >>> test_data = [1.0, -2.0, 1.5, -1.8, 2.2, -1.2, 0.8]
            >>> for sample in test_data:
            ...     rms_value = rms_filter.update(sample)
            >>> 
            >>> # Check state before reset
            >>> print(f"Before reset: {rms_filter.sample_count} samples processed")
            >>> current_rms = sqrt(max(0.0, rms_filter._sum_of_squares / rms_filter._count))
            >>> print(f"Current RMS value: {current_rms:.4f}")
            >>> 
            >>> # Reset filter
            >>> rms_filter.reset()
            >>> print(f"After reset: {rms_filter.sample_count} samples processed")
            >>> print(f"Buffer sum of squares: {rms_filter._sum_of_squares:.4f}")
            >>> 
            >>> # Process new data after reset
            >>> rms_filter.update(5.0)
            >>> print(f"After first new sample: {rms_filter.sample_count} sample processed")
            >>> new_rms = sqrt(max(0.0, rms_filter._sum_of_squares / rms_filter._count))
            >>> print(f"New RMS value: {new_rms:.4f}")  # Should be 5.0
            >>> 
            >>> # Real-world Example: Calibration and monitoring sequence
            >>> def calibration_sequence():
            ...     '''Demonstrate reset in a calibration workflow.'''
            ...     # Create vibration monitor
            ...     vibration_filter = RMS(window_size=200)
            ...     
            ...     # Step 1: Measure baseline noise floor
            ...     print("\nStep 1: Measuring system noise floor (motor off)")
            ...     # Simulate measuring ambient noise for 2 seconds
            ...     for _ in range(200):  # 200 samples
            ...         noise_sample = 0.05 * (random() - 0.5)  # Small random noise
            ...         vibration_filter.update(noise_sample)
            ...     
            ...     noise_floor = sqrt(vibration_filter._sum_of_squares / vibration_filter._count)
            ...     print(f"Noise floor: {noise_floor:.4f}g RMS")
            ...     
            ...     # Step 2: Reset and measure with motor running
            ...     vibration_filter.reset()
            ...     print("\nStep 2: Measuring normal operation (motor on)")
            ...     
            ...     # Simulate motor vibration for 2 seconds
            ...     for _ in range(200):  # 200 samples
            ...         # Vibration signal: 0.5g base + harmonics + noise
            ...         vibration = 0.5 * sin(2*pi*random()) + 0.05 * (random() - 0.5)
            ...         vibration_filter.update(vibration)
            ...     
            ...     normal_level = sqrt(vibration_filter._sum_of_squares / vibration_filter._count)
            ...     print(f"Normal operation: {normal_level:.4f}g RMS")
            ...     
            ...     # Step 3: Reset and measure with simulated fault
            ...     vibration_filter.reset()
            ...     print("\nStep 3: Measuring fault condition (bearing wear)")
            ...     
            ...     # Simulate faulty bearing for 2 seconds
            ...     for _ in range(200):  # 200 samples
            ...         # Fault adds high peaks and increased baseline
            ...         fault = 0.8 * sin(2*pi*random()) + 0.2 * sin(8*pi*random()) + 0.1 * random()
            ...         vibration_filter.update(fault)
            ...     
            ...     fault_level = sqrt(vibration_filter._sum_of_squares / vibration_filter._count)
            ...     print(f"Fault condition: {fault_level:.4f}g RMS")
            ...     
            ...     # Compare results
            ...     print("\nResults Summary:")
            ...     print(f"Signal-to-noise ratio: {20*log10(normal_level/noise_floor):.1f} dB")
            ...     print(f"Fault vs normal ratio: {fault_level/normal_level:.2f}x")
            ...     
            ...     # Make maintenance decision
            ...     if fault_level > 1.5 * normal_level:
            ...         print("ALERT: Maintenance required - abnormal vibration detected")
        ```
        """


class Kalman(Base):
    """
    One-dimensional Kalman filter for optimal state estimation.
    
    A recursive optimal estimator that produces statistically optimal estimates of
    noisy signals by combining measurements with predictions from a system model.
    This implementation uses a simplified scalar (1D) Kalman filter suitable for
    tracking a single variable in the presence of both measurement noise and
    process dynamics.
    
    The filter implements the standard Kalman filter equations simplified for
    the one-dimensional case:
        Prediction:
        
            x_pred = x
            p_pred = p + q
        
        Update:
        
            k = p_pred / (p_pred + r)
            x = x_pred + k * (z - x_pred)
            p = (1 - k) * p_pred
    
    Key Features:
        
        - Recursive Bayesian estimation for optimal tracking
        - Handles both process and measurement uncertainty
        - Automatic adaptation to noise characteristics
        - Outlier rejection with innovation-based gain adjustment
        - Numerically stable implementation with safeguards
        - Optimized with @micropython.viper decorator
        - Minimal memory footprint with efficient state representation
    
    Performance Characteristics:
        
        - O(1) computational complexity (constant time updates)
        - Optimal for Gaussian noise distributions
        - Automatic gain adjustment based on uncertainty
        - Graceful handling of temporary measurement failures
        - Self-stabilizing error covariance
        - Responsive to changing signal dynamics
    
    Applications:
        
        - Sensor fusion and data integration
        - Noisy sensor reading stabilization
        - Position and velocity estimation
        - Signal tracking with varying noise levels
        - Predictive filtering for control systems
        - Motion prediction and smoothing
        - Financial time series estimation
    
    Mathematical Properties:
        
        - Optimal for linear systems with Gaussian noise
        - Minimizes mean squared error
        - Combines prior knowledge with new measurements
        - Automatically balances smoothing vs. responsiveness
        - Uses uncertainty (covariance) for optimal weighting
        - Converges to steady-state behavior for constant systems
    
    """
    
    def __init__(self, process_noise: float = 0.01, measurement_noise: float = 0.1, 
                 initial_estimate: float = 0.0, initial_error: float = 1.0) -> None:
        """
        Initialize one-dimensional Kalman filter.
        
        Creates a Kalman filter for tracking a single variable with specified
        noise characteristics and initial state. The filter provides optimal
        estimation by balancing between system model predictions and measurements.
        
        :param process_noise: Process noise variance (q) - how quickly the true state can change
                             Higher values make filter more responsive to measurements
                             Lower values make filter rely more on its internal model
                             Must be non-negative (default: 0.01)
        :param measurement_noise: Measurement noise variance (r) - how noisy the measurements are
                                 Higher values make filter more skeptical of measurements
                                 Lower values make filter follow measurements more closely
                                 Must be positive (default: 0.1)
        :param initial_estimate: Initial state estimate (x) - starting value for the filter
                                (default: 0.0)
        :param initial_error: Initial error covariance (p) - starting uncertainty
                             Higher values make filter adapt more quickly at start
                             Lower values indicate confidence in initial estimate
                             Must be positive (default: 1.0)
        
        :raises ValueError: If process_noise is negative or measurement_noise is not positive
        
        Parameter Selection Guidelines:
            Process Noise (q):
        
                - Low (0.0001-0.001): For very stable variables (temperature, pressure)
                - Medium (0.01-0.1): For moderately changing variables (position)
                - High (0.1-1.0): For rapidly changing variables (acceleration)
            
            Measurement Noise (r):
        
                - Low (0.01-0.1): For precise sensors (high-end IMUs, calibrated instruments)
                - Medium (0.1-1.0): For typical sensors (consumer-grade sensors)
                - High (1.0-10.0): For very noisy sensors (low-cost or compromised sensors)
            
            Initial Error (p):
        
                - Low (0.1): High confidence in initial estimate
                - Medium (1.0): Moderate confidence
                - High (10.0): Low confidence, adapt quickly
        
        Filter Behavior:
        
            - q/r ratio determines filter responsiveness vs. smoothness
            - q/r >> 1: Very responsive, follows measurements closely
            - q/r << 1: Very smooth, rejects measurement noise but responds slowly
        
        Example
        -------
        ```python
            >>> # Position tracking with moderate noise
            >>> position_filter = Kalman(
            ...     process_noise=0.01,      # Position can change moderately
            ...     measurement_noise=0.5,   # Moderate sensor noise
            ...     initial_estimate=0.0,    # Start at origin
            ...     initial_error=1.0        # Moderate initial uncertainty
            ... )
            >>> 
            >>> # Temperature monitoring with high stability
            >>> temp_filter = Kalman(
            ...     process_noise=0.0001,    # Temperature changes very slowly
            ...     measurement_noise=0.2,   # Moderate sensor noise
            ...     initial_estimate=22.0,   # Start at room temperature
            ...     initial_error=5.0        # High initial uncertainty
            ... )
            >>> 
            >>> # Parameter validation
            >>> try:
            ...     invalid_filter = Kalman(process_noise=-0.5)  # Negative value
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
        ```
        """

    @micropython.native
    def update(self, measurement: float) -> float:
        """
        Update filter with new measurement and return optimal estimate.
        
        Processes a single measurement through the Kalman filter using the
        prediction-update cycle. This method produces an optimal estimate
        that balances between the system model and the new measurement.
        
        :param measurement: New measurement value (any numeric type, converted to float)
        :return: Current optimal state estimate as float
        
        :raises TypeError: If measurement cannot be converted to float
        
        Algorithm Steps:
        
            1. Prediction step: Project state and error covariance forward
        
               - x_pred = x (assumes constant state)
               - p_pred = p + q (state uncertainty grows by process noise)
            
            2. Update step: Incorporate new measurement
        
               - Calculate Kalman gain: k = p_pred / (p_pred + r)
               - Update state: x = x_pred + k * (z - x_pred)
               - Update error covariance: p = (1 - k) * p_pred
            
            3. Outlier detection: Reduce gain for measurements far from prediction
        
               - If |z - x_pred| > 3*sqrt(p_pred), reduce Kalman gain by 90%
        
        Performance Characteristics:
        
            - O(1) computational complexity
            - Optimized with @micropython.viper decorator
            - Minimal memory usage (four float values for state)
            - Automatic stability protection for covariance
            - Outlier rejection for large innovations
        
        Example
        -------
        ```python
            >>> # Basic filtering demonstration
            >>> filter_obj = Kalman(process_noise=0.01, measurement_noise=1.0)
            >>> 
            >>> # Process a series of noisy measurements
            >>> true_value = 10.0
            >>> noisy_measurements = [10.2, 9.7, 10.3, 9.9, 11.2, 9.8, 10.1, 9.6]
            >>> 
            >>> print("Measurement | Estimate | Error")
            >>> print("-" * 35)
            >>> 
            >>> for i, measurement in enumerate(noisy_measurements):
            ...     estimate = filter_obj.update(measurement)
            ...     error = abs(estimate - true_value)
            ...     
            ...     print(f"{measurement:11.2f} | {estimate:8.2f} | {error:5.2f}")
            >>> 
            >>> # Outlier rejection demonstration
            >>> def demonstrate_outlier_rejection():
            ...     '''Show how the filter handles outliers.'''
            ...     robust_filter = Kalman(process_noise=0.01, measurement_noise=0.1)
            ...     
            ...     # Normal measurements with outliers
            ...     data = [5.1, 5.0, 5.2, 15.0, 5.1, 4.9, 5.0, -5.0, 5.2, 5.0]
            ...     
            ...     print("\nOutlier Rejection Test:")
            ...     print("Measurement | Estimate | Innovation | Kalman Gain")
            ...     print("-" * 55)
            ...     
            ...     for i, measurement in enumerate(data):
            ...         # Store state before update
            ...         x_prev = robust_filter.x
            ...         p_pred = robust_filter.p + robust_filter.q
            ...         
            ...         # Calculate theoretical Kalman gain
            ...         k_normal = p_pred / (p_pred + robust_filter.r)
            ...         
            ...         # Innovation (measurement residual)
            ...         innovation = measurement - x_prev
            ...         
            ...         # Update filter
            ...         estimate = robust_filter.update(measurement)
            ...         
            ...         # Calculate actual Kalman gain from results
            ...         if abs(innovation) > 0.001:  # Avoid division by zero
            ...             k_actual = (estimate - x_prev) / innovation
            ...         else:
            ...             k_actual = k_normal
            ...         
            ...         # Determine if this was detected as an outlier
            ...         is_outlier = abs(innovation) > 3.0 * sqrt(p_pred)
            ...         
            ...         print(f"{measurement:11.1f} | {estimate:8.2f} | {innovation:+10.2f} | {k_actual:.4f}" +
            ...               (" (outlier)" if is_outlier else ""))
        ```
        """

    def reset(self) -> None:
        """
        Reset filter to initial state while preserving configuration.
        
        Clears the filter's internal state (estimate and error covariance) and
        resets the sample counter, but maintains the noise parameters. This allows
        the filter to be reused for new data streams without reconfiguration.
        
        Reset Operations:
        
            - Restores state estimate to initial value
            - Restores error covariance to initial value
            - Resets sample counter to zero
            - Preserves process and measurement noise settings
            - Prepares filter for new input sequence
        
        Use Cases:
        
            - Starting new measurement session
            - Switching between different signal sources
            - Recovering from divergence or numerical issues
            - Batch processing of multiple datasets
            - Reinitializing after system mode changes
        
        Example
        -------
        ```python
            >>> # Demonstrate filter reset for multiple data sessions
            >>> filter_obj = Kalman(
            ...     process_noise=0.01, 
            ...     measurement_noise=0.5,
            ...     initial_estimate=0.0,
            ...     initial_error=1.0
            ... )
            >>> 
            >>> # First data session (tracking position)
            >>> position_data = [0.1, 0.3, 0.6, 0.9, 1.2, 1.5, 1.7, 2.0]
            >>> position_estimates = []
            >>> 
            >>> for measurement in position_data:
            ...     estimate = filter_obj.update(measurement)
            ...     position_estimates.append(estimate)
            >>> 
            >>> print("Position tracking results:")
            >>> print(f"Final estimate: {filter_obj.x:.2f}")
            >>> print(f"Final uncertainty: {filter_obj.p:.4f}")
            >>> print(f"Samples processed: {filter_obj.sample_count}")
            >>> 
            >>> # Reset filter for new data session
            >>> filter_obj.reset()
            >>> print("\nAfter reset:")
            >>> print(f"State estimate: {filter_obj.x:.2f}")
            >>> print(f"Error covariance: {filter_obj.p:.4f}")
            >>> print(f"Samples processed: {filter_obj.sample_count}")
            >>> 
            >>> # Multiple sensor fusion with reset
            >>> def sensor_fusion_example():
            ...     '''Demonstrate switching between sensors with reset.'''
            ...     kalman = Kalman(process_noise=0.01, measurement_noise=0.5)
            ...     
            ...     # Simulate primary sensor data (accurate but occasional dropouts)
            ...     primary_data = [10.1, 10.2, None, 10.0, 9.9, None, None, 10.1]
            ...     
            ...     # Simulate backup sensor data (less accurate but always available)
            ...     backup_data = [10.5, 9.8, 10.4, 9.7, 9.5, 10.3, 9.6, 10.2]
            ...     
            ...     print("\nSensor Fusion with Primary/Backup:")
            ...     print("Sample | Primary | Backup | Selected | Estimate")
            ...     print("-" * 55)
            ...     
            ...     for i, (primary, backup) in enumerate(zip(primary_data, backup_data)):
            ...         if primary is not None:
            ...             # Use primary sensor with regular noise model
            ...             kalman.r = 0.5  # Lower noise for primary sensor
            ...             selected = primary
            ...             sensor = "Primary"
            ...         else:
            ...             # Primary sensor dropout, switch to backup
            ...             kalman.r = 2.0  # Higher noise for backup sensor
            ...             selected = backup
            ...             sensor = "Backup"
            ...         
            ...         estimate = kalman.update(selected)
            ...         
            ...         primary_val = f"{primary:.1f}" if primary is not None else "---"
            ...         print(f"{i:6d} | {primary_val:7s} | {backup:6.1f} | {sensor:8s} | {estimate:8.2f}")
        ```
        """


class Adaptive(Base):
    """
    Adaptive alpha filter that automatically adjusts response based on signal dynamics.
    
    A smart first-order IIR filter that dynamically changes its alpha coefficient
    based on detected signal changes. The filter transitions between slow response
    (for steady signals) and fast response (for rapidly changing signals) by monitoring
    signal deltas between consecutive samples and comparing against a threshold.
    
    The filter implements a variable alpha smoothing equation:
        
        y[n] = α(n)·x[n] + (1-α(n))·y[n-1]
    
    Where α(n) is dynamically calculated based on input signal changes:
        
        α(n) = α_min + ratio·(α_max - α_min)
        ratio = min(|x[n] - x[n-1]| / threshold, 1.0)
    
    Key Features:
        
        - Self-adjusting smoothing coefficient for optimal response
        - Balances noise rejection and transient response automatically
        - Configurable sensitivity through threshold parameter
        - Customizable response range via alpha_min and alpha_max
        - Memory-efficient implementation with minimal state variables
        - Adaptive to changing signal characteristics in real-time
        - No prior signal statistics required for operation
    
    Performance Characteristics:
        
        - O(1) computational complexity per sample
        - Preserves sharp transitions while smoothing steady regions
        - Fast convergence on signal changes
        - Gradual smoothing on stable signals
        - Continuous adaptation without mode switching
        - No overshoot during transition between coefficients
    
    Applications:
        
        - Sensor fusion with varying noise conditions
        - Motion tracking with rapid direction changes
        - User interface input smoothing
        - Biomedical signal processing
        - Embedded systems with limited processing power
        - Signal conditioning for event detection
        - Mixed steady-state and transient monitoring
    
    Mathematical Properties:
        
        - Time constant varies with signal dynamics
        - Automatic adjustment between first-order response modes
        - Continuous operation without discontinuities
        - Self-stabilizing for both steady and changing signals
        - Noise rejection proportional to signal stability
        - Step response speed proportional to step magnitude
    
    """
    
    def __init__(self, alpha_min: float = 0.01, alpha_max: float = 0.9, 
                 threshold: float = 0.1, initial: float = 0.0) -> None:
        """
        Initialize adaptive filter with customizable response range.
        
        Creates an adaptive filter that automatically adjusts its smoothing coefficient
        based on detected signal changes. The filter provides variable smoothing that
        adapts to both steady-state and transient signal conditions.
        
        :param alpha_min: Minimum alpha value for steady signals (0 < alpha_min < 1)
                         Lower values provide stronger smoothing for stable signals
                         (default: 0.01)
        :param alpha_max: Maximum alpha value for rapidly changing signals (0 < alpha_max ≤ 1)
                         Higher values provide faster response to signal changes
                         (default: 0.9)
        :param threshold: Signal change threshold that triggers maximum response
                         Changes larger than this trigger alpha_max response
                         Changes smaller than this scale alpha proportionally
                         Must be non-negative (default: 0.1)
        :param initial: Initial output value for filter state (default: 0.0)
                       Used to minimize startup transients when expected signal 
                       level is known
        
        :raises ValueError: If alpha_min, alpha_max are outside valid ranges or if
                           alpha_min ≥ alpha_max, or if threshold is negative
        
        Parameter Selection Guidelines:
        
            alpha_min:
        
                - Very low (0.001-0.01): Heavy smoothing for steady signals
                - Low (0.01-0.05): Moderate smoothing
                - Medium (0.05-0.2): Light smoothing for noisy environments
            
            alpha_max:
        
                - Medium (0.5-0.7): Balanced transient response
                - High (0.7-0.9): Fast transient response
                - Maximum (1.0): Immediate response to changes above threshold
            
            threshold:
        
                - Low (< 0.1): Very sensitive to small changes
                - Medium (0.1-1.0): Moderate sensitivity
                - High (> 1.0): Only responds to large signal transitions
        
        Example
        -------
        ```python
            >>> # Create adaptive filter for sensor fusion
            >>> sensor_filter = Adaptive(
            ...     alpha_min=0.02,   # Strong smoothing for steady signals
            ...     alpha_max=0.8,    # Fast response to changes
            ...     threshold=0.5,    # Transition threshold
            ...     initial=0.0       # Start at zero
            ... )
            >>> 
            >>> # Parameter validation examples
            >>> try:
            ...     # Invalid: alpha_min must be > 0
            ...     invalid_filter = Adaptive(alpha_min=0, alpha_max=0.9)
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     # Invalid: alpha_min must be < alpha_max
            ...     invalid_filter = Adaptive(alpha_min=0.5, alpha_max=0.3)
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
        ```
        """

    @micropython.native
    def update(self, x: float) -> float:
        """
        Update filter with new sample using adaptive coefficient.
        
        Processes a single input sample through the adaptive filter, dynamically
        adjusting the alpha coefficient based on detected signal changes. This
        provides optimal smoothing that adapts to signal dynamics.
        
        :param x: Input sample value (any numeric type, converted to float)
        :return: Filtered output sample as float
        
        :raises TypeError: If input cannot be converted to float
        
        Adaptation Algorithm:
        
            1. Calculate absolute change between current and previous input
            2. If change > threshold: Use alpha_max (fast response)
            3. If change ≤ threshold: Scale alpha proportionally between
               alpha_min and alpha_max
            4. Apply standard first-order filter with calculated alpha
            5. Store current input for next comparison
        
        Performance Characteristics:
        
            - O(1) computational complexity per sample
            - Adaptive smoothing with no parameter tuning needed
            - Optimized with @micropython.native decorator
            - Suitable for real-time applications
        
        Example
        -------
        ```python
            >>> # Basic adaptive filtering demonstration
            >>> filter_obj = Adaptive(alpha_min=0.1, alpha_max=0.9, threshold=0.5)
            >>> 
            >>> # Test with steady signal followed by step change
            >>> test_sequence = [5.0, 5.1, 5.0, 5.2, 5.0, 8.0, 8.1, 8.0, 7.9]
            >>> 
            >>> print("Input | Output | Change | Alpha")
            >>> print("-" * 40)
            >>> 
            >>> for i, sample in enumerate(test_sequence):
            ...     # Store previous output for comparison
            ...     prev_output = filter_obj.y if i > 0 else 0
            ...     
            ...     # Calculate change for alpha selection
            ...     change = abs(sample - filter_obj.prev_x) if i > 0 else 0
            ...     
            ...     # Calculate what alpha will be used
            ...     if change > filter_obj.threshold:
            ...         alpha = filter_obj.alpha_max
            ...     else:
            ...         ratio = change / filter_obj.threshold
            ...         alpha = filter_obj.alpha_min + ratio * (filter_obj.alpha_max - filter_obj.alpha_min)
            ...     
            ...     # Update filter
            ...     output = filter_obj.update(sample)
            ...     
            ...     print(f"{sample:5.1f} | {output:6.3f} | {change:6.3f} | {alpha:.3f}")
        ```
        """

    def reset(self) -> None:
        """
        Reset filter to initial state while preserving configuration.
        
        Clears the filter's internal state (output and previous input) and resets
        the sample counter, but maintains all configuration parameters. This allows
        the filter to be reused for new data streams without reconfiguration.
        
        Reset Operations:
        
            - Restores output value to initial value
            - Restores previous input to initial value
            - Resets sample counter to zero
            - Preserves alpha_min, alpha_max, and threshold parameters
            - Prepares filter for new input sequence
        
        Use Cases:
        
            - Starting new measurement session
            - Switching between different signal sources
            - Recovering from signal glitches or dropouts
            - Batch processing of multiple datasets
        
        Example
        -------
        ```python
            >>> # Demonstrate filter reset
            >>> filter_obj = Adaptive(alpha_min=0.1, alpha_max=0.9, threshold=0.5, initial=1.0)
            >>> 
            >>> # Process some data
            >>> for sample in [1.2, 1.5, 3.0, 3.2, 3.1]:
            ...     result = filter_obj.update(sample)
            >>> 
            >>> print(f"Before reset: output={filter_obj.y:.2f}, prev_x={filter_obj.prev_x:.2f}")
            >>> 
            >>> # Reset filter
            >>> filter_obj.reset()
            >>> print(f"After reset: output={filter_obj.y:.2f}, prev_x={filter_obj.prev_x:.2f}")
            >>> 
            >>> # Process new data with reset filter
            >>> new_result = filter_obj.update(10.0)
            >>> print(f"First new result: {new_result:.2f}")
        ```
        """


class Biquad(Base):
    """
    Generic biquad (second-order IIR) filter with configurable coefficients.
    
    A versatile second-order Infinite Impulse Response (IIR) filter that directly
    implements the biquadratic transfer function with configurable coefficients.
    This filter provides a flexible building block for creating various filter types
    including lowpass, highpass, bandpass, notch, and peaking filters, offering
    superior frequency response control compared to first-order filters.
    
    The filter implements the difference equation:
        
        y[n] = b0·x[n] + b1·x[n-1] + b2·x[n-2] - a1·y[n-1] - a2·y[n-2]
    
    Where:
        
        - b0, b1, b2: Feedforward (numerator) coefficients
        - a1, a2: Feedback (denominator) coefficients
        - x[n]: Current and previous input samples
        - y[n]: Current and previous output samples
    
    Key Features:
        
        - Flexible second-order transfer function implementation
        - Direct coefficient specification for custom responses
        - Memory-efficient four-delay implementation
        - Configurable for all standard filter types
        - -40dB/decade roll-off for lowpass/highpass configurations
        - Optimized with @micropython.viper decorator
        - High precision with minimal computational overhead
    
    Performance Characteristics:
        
        - O(1) computational complexity (constant time updates)
        - Steeper roll-off than first-order filters
        - Better frequency selectivity than first-order filters
        - Capability for resonance and peaked responses
        - Efficient implementation for embedded systems
        - Low memory footprint (6 float values)
    
    Applications:
        
        - Audio equalizers and crossovers
        - Precise sensor data filtering
        - Scientific signal analysis
        - Anti-aliasing and reconstruction filters
        - Biomedical signal processing
        - Frequency-selective noise reduction
        - Communication systems filtering
        - Resonator and oscillator implementation
    
    Mathematical Properties:
        
        - Second-order transfer function: H(z) = (b0 + b1·z⁻¹ + b2·z⁻²)/(1 + a1·z⁻¹ + a2·z⁻²)
        - Two poles and two zeros in z-plane
        - Roll-off: -40dB/decade for lowpass/highpass
        - Q factor controls resonance/bandwidth
        - Stability requires poles inside unit circle (care needed with coefficients)
        - Amplitude and phase can be independently controlled
        - Can implement complex-conjugate pole pairs
    """
    
    def __init__(self, b0: float, b1: float, b2: float, a1: float, a2: float) -> None:
        """
        Initialize biquad filter with direct coefficient specification.
        
        Creates a second-order IIR filter with explicitly specified coefficients,
        providing complete control over the filter's transfer function. The 
        coefficients directly determine the filter's frequency response, stability,
        and time-domain characteristics.
        
        :param b0: Feedforward coefficient for current input x[n]
        :param b1: Feedforward coefficient for first delayed input x[n-1]
        :param b2: Feedforward coefficient for second delayed input x[n-2]
        :param a1: Feedback coefficient for first delayed output y[n-1] (negative in equation)
        :param a2: Feedback coefficient for second delayed output y[n-2] (negative in equation)
        
        :raises TypeError: If coefficients cannot be converted to float
        
        Coefficient Guidelines:
        
            - Stability requires: |a2| < 1, |a1| < 1+a2
            - Unity DC gain (lowpass): b0 + b1 + b2 = 1 + a1 + a2
            - Unity Nyquist gain (highpass): b0 - b1 + b2 = 1 - a1 + a2
            - For coefficient design, consider using derived classes like 
              Butterworth or NotchFilter instead of manual calculation
        
        Transfer Function:
        
            H(z) = (b0 + b1·z⁻¹ + b2·z⁻²)/(1 + a1·z⁻¹ + a2·z⁻²)
        
        Example
        -------
        ```python
            >>> # Create a simple lowpass biquad filter (manually calculated coefficients)
            >>> # Cutoff: 100Hz, Sampling: 1000Hz, Q: 0.7071
            >>> lowpass = Biquad(
            ...     b0=0.0718, b1=0.1436, b2=0.0718, 
            ...     a1=-1.1430, a2=0.4304
            ... )
            >>> 
            >>> # Create a notch filter (manually calculated coefficients)
            >>> # Notch at 60Hz, Sampling: 1000Hz, Q: 10
            >>> notch = Biquad(
            ...     b0=0.9889, b1=-1.9558, b2=0.9889,
            ...     a1=-1.9558, a2=0.9778
            ... )
            >>> 
            >>> # Coefficient validation (stability check)
            >>> def check_stability(a1, a2):
            ...     '''Check if filter is stable based on feedback coefficients.'''
            ...     if abs(a2) >= 1:
            ...         return False  # Unstable
            ...     if abs(a1) >= 1 + a2:
            ...         return False  # Unstable
            ...     return True
            >>> 
            >>> # Check our filter stability
            >>> check_stability(-1.1430, 0.4304)  # Should be True
        ```
        """

    def set_coefficients(self, b0: float, b1: float, b2: float, a1: float, a2: float) -> None:
        """
        Set filter coefficients to new values.
        
        Updates the biquad filter coefficients without needing to create a new filter
        instance. This allows dynamic modification of the filter's frequency response
        characteristics during operation.
        
        :param b0: Feedforward coefficient for current input x[n]
        :param b1: Feedforward coefficient for first delayed input x[n-1]
        :param b2: Feedforward coefficient for second delayed input x[n-2]
        :param a1: Feedback coefficient for first delayed output y[n-1] (negative in equation)
        :param a2: Feedback coefficient for second delayed output y[n-2] (negative in equation)
        
        :raises TypeError: If coefficients cannot be converted to float
        
        Dynamic Configuration Applications:
        
            - Real-time filter tuning for adaptive filtering
            - Parameter sweeping for filter design
            - Frequency response morphing between different filter types
            - User-adjustable filter characteristics
        
        Example
        -------
        ```python
            >>> # Create a filter and then modify it
            >>> filter_obj = Biquad(1.0, 0.0, 0.0, 0.0, 0.0)  # Initially a pass-through
            >>> 
            >>> # Convert to lowpass filter (manually calculated coefficients)
            >>> filter_obj.set_coefficients(
            ...     b0=0.0718, b1=0.1436, b2=0.0718, 
            ...     a1=-1.1430, a2=0.4304
            ... )
            >>> 
            >>> # Dynamic frequency adjustment
            >>> def change_filter_frequency(fc, fs, Q=0.7071):
            ...     '''Calculate and set coefficients for a lowpass filter.'''
            ...     w0 = 2 * pi * fc / fs
            ...     alpha = sin(w0) / (2 * Q)
            ...     cosw0 = cos(w0)
            ...     
            ...     # Calculate normalized coefficients
            ...     b0 = (1 - cosw0) / 2
            ...     b1 = 1 - cosw0
            ...     b2 = (1 - cosw0) / 2
            ...     a0 = 1 + alpha
            ...     a1 = -2 * cosw0
            ...     a2 = 1 - alpha
            ...     
            ...     # Normalize by a0
            ...     filter_obj.set_coefficients(
            ...         b0/a0, b1/a0, b2/a0, 
            ...         a1/a0, a2/a0
            ...     )
            ...     
            ...     print(f"Updated to {fc}Hz lowpass filter")
            >>> 
            >>> # Change filter cutoff frequency
            >>> change_filter_frequency(fc=200, fs=1000)  # 200Hz cutoff
            >>> change_filter_frequency(fc=500, fs=1000)  # 500Hz cutoff
        ```
        """

    @micropython.native
    def update(self, x: float) -> float:
        """
        Update filter with new sample and return filtered output.
        
        Processes a single input sample through the second-order IIR biquad filter
        using the direct form I structure. This method implements the difference equation:
        y[n] = b0·x[n] + b1·x[n-1] + b2·x[n-2] - a1·y[n-1] - a2·y[n-2]
        
        :param x: Input sample value (any numeric type, converted to float)
        :return: Filtered output sample as float
        
        :raises TypeError: If input cannot be converted to float
        
        Algorithm Details:
        
            - Direct Form I implementation (separate input and output delays)
            - Updates internal state with new input and output values
            - Maintains two input (x1, x2) and two output (y1, y2) delay elements
            - Optimized with @micropython.viper decorator for maximum performance
        
        Performance Characteristics:
        
            - O(1) computational complexity
            - Five multiply-add operations per sample
            - Minimal memory usage (four float values for delay elements)
            - Suitable for real-time processing of high-frequency signals
        
        Example
        -------
        ```python
            >>> # Basic biquad filtering operation
            >>> # Create a simple lowpass filter (fc=0.1*fs)
            >>> filter_obj = Biquad(
            ...     b0=0.0201, b1=0.0402, b2=0.0201,
            ...     a1=-1.5610, a2=0.6414
            ... )
            >>> 
            >>> # Process a simple step input
            >>> output_sequence = []
            >>> for i in range(10):
            ...     # Input is 0 for i<5, then jumps to 1.0
            ...     input_value = 0.0 if i < 5 else 1.0
            ...     output = filter_obj.update(input_value)
            ...     output_sequence.append(output)
            ...     print(f"Sample {i}: Input={input_value:.1f}, Output={output:.6f}")
            >>> 
            >>> # Verify the filter's step response is as expected:
            >>> # - Initially zero
            >>> # - After step, gradually approaches 1.0
            >>> # - Smooth transition without excessive ringing
            >>> print(f"Final output: {output_sequence[-1]:.6f}")
        ```
        """

    def reset(self) -> None:
        """
        Reset filter to initial state while preserving coefficients.
        
        Clears the filter's internal delay line (both input and output history)
        and resets the sample counter, but maintains all coefficient settings.
        This allows the filter to be reused for new data streams without
        reconfiguration.
        
        Reset Operations:
        
            - Clears input history (x1, x2) to zero
            - Clears output history (y1, y2) to zero
            - Resets sample counter to zero
            - Preserves all filter coefficients (b0, b1, b2, a1, a2)
        
        Use Cases:
        
            - Starting new filtering session
            - Switching between different signal sources
            - Clearing filter memory after transient events
            - Preventing startup transients when processing new signals
            - Batch processing of multiple datasets
        
        Example
        -------
        ```python
            >>> # Demonstrate filter reset for batch processing
            >>> filter_obj = Biquad(
            ...     b0=0.0201, b1=0.0402, b2=0.0201,
            ...     a1=-1.5610, a2=0.6414
            ... )
            >>> 
            >>> # Process first batch (step response)
            >>> for i in range(10):
            ...     input_value = 0.0 if i < 5 else 1.0
            ...     output = filter_obj.update(input_value)
            >>> 
            >>> print(f"Before reset: Output={filter_obj.y1:.4f}, Count={filter_obj.sample_count}")
            >>> 
            >>> # Reset filter for second batch
            >>> filter_obj.reset()
            >>> print(f"After reset: Output={filter_obj.y1:.4f}, Count={filter_obj.sample_count}")
            >>> 
            >>> # Process second batch (sine wave)
            >>> import math
            >>> for i in range(10):
            ...     # Create sine wave input
            ...     input_value = math.sin(2 * math.pi * i / 10)
            ...     output = filter_obj.update(input_value)
            ...     print(f"Sample {i}: Input={input_value:.4f}, Output={output:.4f}")
            >>> 
            >>> # Verify filter starts with fresh state for each batch
            >>> print(f"Final count: {filter_obj.sample_count}")  # Should be 10
        ```
        """


class Butterworth(Biquad):
    """
    Second-order Butterworth filter with maximally flat frequency response.
    
    A specialized biquad filter implementation that provides a Butterworth response
    characteristic, known for its maximally flat magnitude response in the passband.
    This filter offers an optimal balance between time and frequency domain performance,
    with no ripple in the passband and a -40dB/decade (12dB/octave) roll-off in the
    stopband, making it a popular choice for general filtering applications.
    
    The filter supports both lowpass and highpass configurations with automatic
    coefficient calculation from basic frequency specifications, eliminating the need
    for manual coefficient design.
    
    Key Features:
        
        - Maximally flat magnitude response in passband (no ripple)
        - Smooth rolloff transition (-40dB/decade)
        - Automatic coefficient calculation from frequency specifications
        - Both lowpass and highpass configurations
        - Excellent general-purpose filter characteristics
        - Inherited efficiency from Biquad implementation
        - Optimal phase response for given magnitude constraint
    
    Performance Characteristics:
        
        - Standard second-order response (-40dB/decade)
        - Slightly less steep rolloff than Chebyshev filters
        - Slightly better stopband attenuation than Bessel filters
        - Moderate group delay variation near cutoff
        - No passband ripple (unlike Chebyshev filters)
        - Phase response optimized for given constraints
    
    Applications:
        
        - General-purpose noise filtering
        - Anti-aliasing before sampling
        - Audio processing and crossovers
        - Biomedical signal preprocessing
        - Sensor data conditioning
        - Baseline removal (highpass mode)
        - Communication systems
        - Smooth signal reconstruction
    
    Mathematical Properties:
        
        - Magnitude squared response: |H(ω)|² = 1/(1 + (ω/ωc)²ⁿ)
          where n is the filter order (2 for this implementation)
        - Maximally flat at ω = 0 (all derivatives zero)
        - No ripple in passband or stopband
        - -3dB attenuation exactly at the cutoff frequency
        - Monotonically decreasing magnitude response
        - Optimal phase response for given magnitude constraint
   
    """
    
    def __init__(self, fc: float, fs: float, filter_type: str = 'lowpass') -> None:
        """
        Initialize second-order Butterworth filter with frequency specifications.
        
        Creates a Butterworth filter with automatic coefficient calculation from
        cutoff frequency, sampling frequency, and filter type. The coefficients are
        calculated to provide the characteristic maximally flat response.
        
        :param fc: Cutoff frequency in Hz (3dB point, must be > 0 and < fs/2)
        :param fs: Sampling frequency in Hz (must be > 0 and > 2*fc)
        :param filter_type: Filter mode - 'lowpass' or 'highpass' (default: 'lowpass')
                          'lowpass': Passes frequencies below fc, attenuates above
                          'highpass': Passes frequencies above fc, attenuates below
        
        :raises ValueError: If frequencies are invalid, violate Nyquist criterion,
                          or if filter_type is not recognized
        :raises TypeError: If parameters cannot be converted to appropriate types
        
        Filter Design:
        
            The filter implements a second-order Butterworth response with:
        
            - Maximally flat passband (binomial coefficients)
            - -40dB/decade rolloff rate
            - -3dB attenuation exactly at fc
            - Optimal phase response for given magnitude constraints
        
        Example
        -------
        ```python
            >>> # Create lowpass Butterworth filter at 100Hz (sampled at 1kHz)
            >>> lowpass = Butterworth(fc=100.0, fs=1000.0, filter_type='lowpass')
            >>> print(f"Lowpass cutoff: {lowpass.fc} Hz")
            >>> 
            >>> # Create highpass Butterworth filter (DC blocker)
            >>> highpass = Butterworth(fc=20.0, fs=1000.0, filter_type='highpass')
            >>> print(f"Highpass cutoff: {highpass.fc} Hz")
            >>> 
            >>> # Invalid configuration
            >>> try:
            ...     # Cutoff too high (violates Nyquist)
            ...     invalid = Butterworth(fc=600.0, fs=1000.0)
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
        ```
        """
    
    @micropython.native
    def update(self, x: float) -> float:
        """
        Update filter with new sample and return filtered output.
        
        Processes a single input sample through the second-order Butterworth filter.
        This method inherits the efficient implementation from the Biquad parent class.
        
        :param x: Input sample value (any numeric type, converted to float)
        :return: Filtered output sample as float
        
        :raises TypeError: If input cannot be converted to float
        
        Example
        -------
        ```python
            >>> # Process a simple step response
            >>> filter_obj = Butterworth(fc=10.0, fs=100.0, filter_type='lowpass')
            >>> 
            >>> # Create and process a step input
            >>> outputs = []
            >>> for i in range(20):
            ...     # Step occurs at i=10
            ...     input_value = 0.0 if i < 10 else 1.0
            ...     output = filter_obj.update(input_value)
            ...     outputs.append(output)
            >>> 
            >>> # Print key points in the response
            >>> print(f"Step applied at sample 10")
            >>> print(f"Initial output (0): {outputs[0]:.6f}")
            >>> print(f"At step (10): {outputs[10]:.6f}")
            >>> print(f"Final value (19): {outputs[19]:.6f}")
        ```
        """
    
    def reset(self) -> None:
        """
        Reset filter to initial state while preserving configuration.
        
        Clears the filter's internal state (delay line) and resets the sample counter,
        but maintains all configuration parameters and coefficients. This method
        inherits its implementation from the Biquad parent class.
        
        Example
        -------
        ```python
            >>> # Create filter and process some data
            >>> filter_obj = Butterworth(fc=30.0, fs=1000.0, filter_type='lowpass')
            >>> 
            >>> # Process first dataset
            >>> for x in [1.0, 0.5, 0.2, 0.7, 0.9]:
            ...     y = filter_obj.update(x)
            >>> 
            >>> print(f"Before reset: {filter_obj.sample_count} samples processed")
            >>> 
            >>> # Reset filter for new dataset
            >>> filter_obj.reset()
            >>> print(f"After reset: {filter_obj.sample_count} samples processed")
            >>> 
            >>> # Filter is now ready for new dataset with same configuration
            >>> new_output = filter_obj.update(1.0)
            >>> print(f"First output after reset: {new_output:.6f}")
        ```
        """



class FIR(Base):
    """
    Finite Impulse Response (FIR) filter with configurable tap coefficients.
    
    A versatile FIR filter implementation that processes signals using a direct
    convolution structure with user-specified tap coefficients. This filter offers
    linear phase response, guaranteed stability, and precise frequency response
    control at the cost of higher memory usage compared to IIR filters.
    
    The filter implements the standard FIR convolution equation:
        
        y[n] = Σ(h[k]·x[n-k]) for k = 0 to N-1
    
    Where:
        
        - h[k]: Tap coefficients (impulse response)
        - x[n-k]: Delayed input samples
        - N: Filter order (number of taps)
    
    Key Features:
        
        - Linear phase response (when using symmetric coefficients)
        - Guaranteed stability (no feedback paths)
        - Precise frequency response control
        - Efficient circular buffer implementation
        - Customizable impulse response via tap coefficients
        - Zero phase distortion for symmetric coefficients
        - Runtime coefficient adjustment capability
    
    Performance Characteristics:

        - Computational complexity: O(N) per sample
        - Memory usage: 2N float values (taps + buffer)
        - Group delay: (N-1)/2 samples for symmetric coefficients
        - Frequency response exactly matches coefficient design
        - Steeper roll-off requires more taps (memory/CPU tradeoff)
        - Optimized with @micropython.native decorator
    
    Applications:

        - Custom frequency response filtering
        - Linear phase signal processing
        - Matched filtering and correlation
        - Hilbert transformers
        - Pulse shaping filters
        - Audio equalization with minimal phase distortion
        - Communication system filters
        - Signal detection and extraction
    
    Mathematical Properties:
        - Linear phase when taps are symmetric
        - Frequency response is Fourier transform of tap coefficients
        - Always stable (no feedback, no poles)
        - Finite response duration equal to tap count
        - No recursive behavior (output always settles)
        - Adjustable frequency selectivity based on tap count
    
    """
    
    def __init__(self, taps: list) -> None:
        """
        Initialize FIR filter with specified tap coefficients.
        
        Creates a Finite Impulse Response filter with user-supplied tap coefficients.
        The coefficients directly determine the filter's impulse response and
        frequency characteristics.
        
        :param taps: List or sequence of filter coefficients (must be non-empty)
                    These define the impulse response of the filter
                    Length of taps determines filter order
        
        :raises ValueError: If taps list is empty
        :raises TypeError: If taps cannot be converted to float values
        
        Coefficient Design Guidelines:
        
            - Symmetric coefficients (h[i] = h[N-1-i]) → Linear phase
            - Number of taps determines frequency selectivity
            - More taps → Steeper roll-off, narrower transition band
            - Window functions reduce Gibbs phenomenon (ripple)
            - For specific responses, use windowed-sinc or filter design software
        
        Common FIR Types:
        
            - Lowpass: Central coefficient largest, decaying symmetrically
            - Highpass: Alternating signs, central region strongest
            - Bandpass: Sinusoidal envelope modulated by lowpass shape
            - Bandstop: Lowpass with subtracted bandpass component
        
        Example
        -------
        ```python
            >>> # Simple 5-tap moving average filter (symmetric)
            >>> moving_avg = FIR(taps=[0.2, 0.2, 0.2, 0.2, 0.2])
            >>> print(f"Filter order: {len(moving_avg.taps)-1}")
            >>> print(f"Group delay: {(len(moving_avg.taps)-1)/2} samples")
            >>> 
            >>> # Highpass filter (symmetric with alternating signs)
            >>> highpass = FIR(taps=[-0.1, 0.2, -0.5, 0.2, -0.1])
            >>> 
            >>> # Parameter validation
            >>> try:
            ...     invalid_filter = FIR(taps=[])  # Empty taps list
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
        ```
        """

    @property
    def taps(self) -> list:
        """
        Get current tap coefficients.
        
        Returns a copy of the current filter coefficients as a list.
        This allows inspection of the filter configuration without
        modifying internal state.
        
        :return: List of current tap coefficients
        
        Example
        -------
        ```python
            >>> # Inspect filter taps
            >>> filter_obj = FIR(taps=[0.1, 0.2, 0.4, 0.2, 0.1])
            >>> 
            >>> # Get current taps
            >>> current_taps = filter_obj.taps
            >>> print(f"Filter taps: {current_taps}")
            >>> 
            >>> # Verify if filter is symmetric (linear phase)
            >>> def is_symmetric(taps):
            ...     n = len(taps)
            ...     for i in range(n // 2):
            ...         if abs(taps[i] - taps[n-i-1]) > 1e-6:
            ...             return False
            ...     return True
            >>> 
            >>> print(f"Linear phase: {is_symmetric(filter_obj.taps)}")
        ```
        """

    @taps.setter
    def taps(self, taps: list) -> None:
        """
        Set filter tap coefficients.
        
        Updates the filter's tap coefficients without creating a new filter instance.
        This allows dynamic modification of the filter's frequency response during
        operation.
        
        :param taps: List or sequence of filter coefficients (must be non-empty)
        
        :raises ValueError: If taps list is empty
        :raises TypeError: If taps cannot be converted to float values
        
        Dynamic Configuration Applications:
        
            - Adaptive filtering based on signal conditions
            - Filter morphing between different responses
            - Real-time frequency response adjustment
            - A/B testing of different coefficient sets
        
        Example
        -------
        ```python
            >>> # Create filter with initial coefficients
            >>> filter_obj = FIR(taps=[1.0, 0.0, 0.0, 0.0, 0.0])  # Unit impulse
            >>> 
            >>> # Later update to moving average coefficients
            >>> filter_obj.taps = [0.2, 0.2, 0.2, 0.2, 0.2]
            >>> print(f"New taps: {filter_obj.taps}")
            >>> 
            >>> # Dynamic coefficient switching
            >>> def switch_filter_mode(filter_obj, mode='lowpass'):
            ...     '''Switch between different filter responses.'''
            ...     if mode == 'lowpass':
            ...         filter_obj.taps = [0.2, 0.2, 0.2, 0.2, 0.2]
            ...     elif mode == 'highpass':
            ...         filter_obj.taps = [-0.1, 0.2, -0.5, 0.2, -0.1]
            ...     else:
            ...         filter_obj.taps = [0.0, 0.0, 1.0, 0.0, 0.0]  # All-pass
            ...     
            ...     print(f"Switched to {mode} mode, filter length: {len(filter_obj.taps)}")
        ```
        """

    @micropython.native
    def update(self, x: float) -> float:
        """
        Update filter with new sample and return filtered output.
        
        Processes a single input sample through the FIR filter using
        direct convolution with the tap coefficients. This implements
        the standard FIR filtering operation.
        
        :param x: Input sample value (any numeric type, converted to float)
        :return: Filtered output sample as float
        
        :raises TypeError: If input cannot be converted to float
        
        Algorithm Details:
        
            1. Store new input in circular buffer
            2. Compute dot product of buffer and tap coefficients
            3. Advance circular buffer index
            4. Return computed result
        
        Performance Characteristics:
        
            - Computational complexity: O(N) operations per sample
            - Memory access: 2N reads, 1 write per sample
            - Optimized with @micropython.native decorator
            - Linear scaling with number of taps
        
        Example
        -------
        ```python
            >>> # Basic FIR filtering operation
            >>> # 5-tap moving average filter
            >>> filter_obj = FIR(taps=[0.2, 0.2, 0.2, 0.2, 0.2])
            >>> 
            >>> # Process a simple impulse input
            >>> inputs = [0, 0, 1, 0, 0, 0, 0, 0]
            >>> outputs = []
            >>> 
            >>> for sample in inputs:
            ...     output = filter_obj.update(sample)
            ...     outputs.append(output)
            >>> 
            >>> print("Impulse Response:")
            >>> for i, out in enumerate(outputs):
            ...     print(f"Sample {i}: {out:.1f}")
            >>> 
            >>> # Response should match tap coefficients as impulse propagates
            >>> # through the filter's delay line
        ```
        """

    def reset(self) -> None:
        """
        Reset filter to initial state while preserving coefficients.
        
        Clears the filter's delay line (buffer) and resets the sample counter,
        but maintains the tap coefficients. This allows the filter to be reused
        for new data streams without reconfiguration.
        
        Reset Operations:
        
            - Clears input buffer (delay line) to zeros
            - Resets buffer index to 0
            - Resets sample counter to 0
            - Preserves tap coefficients
        
        Use Cases:
        
            - Starting new filtering session
            - Removing previous signal history
            - Batch processing of multiple signals
            - Clearing filter state after transients
        
        Example
        -------
        ```python
            >>> # Demonstrate filter reset
            >>> filter_obj = FIR(taps=[0.1, 0.2, 0.4, 0.2, 0.1])
            >>> 
            >>> # Process some data
            >>> for sample in [1.0, 2.0, 3.0, 4.0, 5.0]:
            ...     result = filter_obj.update(sample)
            >>> 
            >>> print(f"Before reset: {filter_obj.sample_count} samples processed")
            >>> 
            >>> # Reset filter
            >>> filter_obj.reset()
            >>> print(f"After reset: {filter_obj.sample_count} samples processed")
            >>> 
            >>> # Process new data with clean state
            >>> new_result = filter_obj.update(10.0)
            >>> print(f"First result after reset: {new_result:.1f}")
        ```
        """



class AngleEMA(Base):
    """
    Exponential Moving Average filter for angular data with wrap-around handling.
    
    A specialized exponential smoothing filter designed for circular/angular quantities
    such as compass headings, phase angles, or rotation measurements. Unlike standard
    filters that average linearly, this filter properly handles the discontinuity at
    ±π radians (±180°) using circular statistics, preventing averaging errors when
    angles wrap around the circle boundary.
    
    The filter implements exponential smoothing in angular difference space:
        
        θ_out[n] = θ_out[n-1] + α · angle_diff(θ_in[n], θ_out[n-1])
    
    Where:
        
        - θ_in[n]: Current input angle in radians
        - θ_out[n]: Current output angle in radians
        - α: Smoothing factor (0 < α ≤ 1)
        - angle_diff: Circular difference function (wraps at ±π)
    
    Key Features:
        
        - Circular statistics for proper angular averaging
        - Automatic wrap-around handling at ±π boundary
        - Configurable smoothing strength via alpha parameter
        - Optional lazy initialization on first update
        - Memory-efficient single-value state
        - Real-time adjustable smoothing factor
        - Output always normalized to [-π, π]
    
    Applications:
        
        - IMU compass heading smoothing
        - GPS course over ground filtering
        - Motor encoder angle smoothing
        - Phase tracking in signal processing
        - Robot orientation estimation
        - Wind direction averaging
        - Satellite antenna pointing
        - Gimbal stabilization
    
    Mathematical Properties:
        
        - Uses circular (modulo 2π) distance metric
        - Prevents 0°/360° boundary artifacts
        - Correctly handles angle sequences like: 350°, 355°, 0°, 5°, 10°
        - Standard EMA behavior in angular difference space
        - Step response: approaches target via shortest circular path
        - Impulse response: exponential decay in angular space
    
    Alpha Selection Guidelines:
        
        - α = 0.1: Heavy smoothing, slow response (IMU drift correction)
        - α = 0.2: Moderate smoothing (compass heading)
        - α = 0.3-0.5: Balanced (general orientation tracking)
        - α = 0.6-0.8: Light smoothing (responsive control)
        - α = 1.0: No filtering (pass-through)
    
    Circular Averaging Example:
        
        Consider angles 170° and -170° (190° in 0-360 notation):
        
        - Linear average: (170° + -170°) / 2 = 0° ❌ WRONG
        - Circular average: ±180° ✓ CORRECT
        
        This filter correctly computes ±180° by recognizing the angles
        are only 20° apart on the circle, not 340° apart.
    """
    def __init__(self, alpha: float = 0.25, initial: float | None = None) -> None:
        """
        Initialize angle EMA filter with smoothing factor.
        
        Creates an exponential moving average filter specifically designed for
        angular data that properly handles wrap-around at the ±π boundary.
        The filter can be initialized with a starting angle or left uninitialized
        to automatically set its initial state from the first measurement.
        
        :param alpha: Smoothing factor in range (0, 1] (default: 0.25)
                     Higher values = less smoothing, faster response
                     Lower values = more smoothing, slower response
                     - α = 1.0: No filtering (output = input)
                     - α = 0.1: Heavy smoothing (tau ≈ 9 samples)
                     - α = 0.5: Moderate smoothing (tau ≈ 1 sample)
        :param initial: Optional initial angle in radians (default: None)
                       If provided, must be in [-π, π] range.
                       If None, filter initializes on first update() call.
        
        :raises FilterConfigurationError: If alpha not in range (0, 1]
        :raises TypeError: If parameters cannot be converted to numeric types
        
        Alpha Parameter Guidelines:
            The smoothing factor α controls the trade-off between noise
            reduction and responsiveness:
            
            Heavy Smoothing (α = 0.05 to 0.15):
                
                - Strong noise suppression
                - Slow tracking of true angle changes
                - Good for: Drifting IMUs, very noisy compass
                - Time constant: ~10-20 samples
            
            Moderate Smoothing (α = 0.15 to 0.4):
                
                - Balanced noise reduction and tracking
                - Suitable for most applications
                - Good for: General compass/heading filtering
                - Time constant: ~2-6 samples
            
            Light Smoothing (α = 0.4 to 0.8):
                
                - Minimal delay, fast response
                - Light noise reduction only
                - Good for: Control feedback, responsive steering
                - Time constant: ~0.5-2 samples
        
        Initialization Strategies:
            
            With Initial Value (initial provided):
                
                - Filter starts at specified angle
                - Useful when approximate starting angle is known
                - Reduces initial transient
                - Example: GPS last known heading, saved state
            
            Lazy Initialization (initial = None):
                
                - Filter starts on first update()
                - First measurement becomes initial state
                - Useful when starting angle is unknown
                - No artificial bias from wrong initial guess
        
        Example
        -------
        ```python
            >>> from ufilter import AngleEMA
            >>> import math
            >>> 
            >>> # Compass heading filter with known initial direction
            >>> compass_filter = AngleEMA(alpha=0.3, initial=0.0)  # North
            >>> print(f"Alpha: {compass_filter.alpha}")
            >>> print(f"Initial: {math.degrees(compass_filter.value):.1f}°")
            >>> # Alpha: 0.3
            >>> # Initial: 0.0°
            >>> 
            >>> # IMU orientation filter with lazy initialization
            >>> orientation_filter = AngleEMA(alpha=0.2, initial=None)
            >>> print(f"Initialized: {orientation_filter.value is not None}")
            >>> # Initialized: False
            >>> 
            >>> # Motor encoder angle filter
            >>> encoder_filter = AngleEMA(alpha=0.5, initial=math.radians(90))
            >>> print(f"Starting angle: {math.degrees(encoder_filter.value):.1f}°")
            >>> # Starting angle: 90.0°
            >>> 
            >>> # Application-specific alpha values
            >>> def design_angle_filters():
            ...     '''Design filters for various applications.'''
            ...     
            ...     # GPS course over ground (slow changes expected)
            ...     gps_course = AngleEMA(alpha=0.1)
            ...     print(f"GPS: alpha={gps_course.alpha}, tau≈{(1/gps_course.alpha):.0f} samples")
            ...     
            ...     # Compass heading (moderate noise)
            ...     compass = AngleEMA(alpha=0.25)
            ...     print(f"Compass: alpha={compass.alpha}, tau≈{(1/compass.alpha):.0f} samples")
            ...     
            ...     # Robot heading control (fast response needed)
            ...     robot = AngleEMA(alpha=0.6, initial=0.0)
            ...     print(f"Robot: alpha={robot.alpha}, tau≈{(1/robot.alpha):.1f} samples")
            ...     
            ...     # Wind vane (very noisy, needs heavy smoothing)
            ...     wind = AngleEMA(alpha=0.05)
            ...     print(f"Wind: alpha={wind.alpha}, tau≈{(1/wind.alpha):.0f} samples")
            >>> 
            >>> # Invalid configurations
            >>> try:
            ...     bad_filter = AngleEMA(alpha=0.0)  # Zero alpha
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     bad_filter = AngleEMA(alpha=1.5)  # Alpha > 1
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> # Angle normalization demonstration
            >>> def demonstrate_angle_normalization():
            ...     # Initial values outside [-π, π] are normalized
            ...     import math
            ...     
            ...     # 270° = -90° in [-π, π] range
            ...     filt1 = AngleEMA(alpha=0.5, initial=math.radians(270))
            ...     print(f"Input 270° → Stored: {math.degrees(filt1.value):.1f}°")
            ...     
            ...     # 450° = 90° in [-π, π] range
            ...     filt2 = AngleEMA(alpha=0.5, initial=math.radians(450))
            ...     print(f"Input 450° → Stored: {math.degrees(filt2.value):.1f}°")
        ```
        """
        ...
    
    @property
    def alpha(self) -> float:
        """
        Get smoothing factor.
        
        Returns the current alpha (smoothing factor) value that controls the
        trade-off between noise reduction and responsiveness. Higher alpha values
        provide faster response with less smoothing, while lower values provide
        more smoothing with slower response.
        
        :return: Smoothing factor in range (0, 1]
        
        Alpha Interpretation:
            
            - α = 1.0: No filtering (output = input)
            - α = 0.5: Moderate smoothing (tau ≈ 1 sample)
            - α = 0.2: Heavy smoothing (tau ≈ 4 samples)
            - α = 0.1: Very heavy smoothing (tau ≈ 9 samples)
        
        Relationship to Time Constant:
            
            For approximate time constant in samples:
            
            tau ≈ (1 - α) / α
            
            Example: α = 0.2 → tau ≈ 4 samples
        
        Example
        -------
        ```python
            >>> from ufilter import AngleEMA
            >>> import math
            >>> 
            >>> # Check current alpha
            >>> heading_filter = AngleEMA(alpha=0.3, initial=0.0)
            >>> print(f"Alpha: {heading_filter.alpha}")
            >>> # Alpha: 0.3
            >>> 
            >>> # Calculate time constant
            >>> tau_samples = (1 - heading_filter.alpha) / heading_filter.alpha
            >>> print(f"Approximate tau: {tau_samples:.1f} samples")
            >>> # Approximate tau: 2.3 samples
            >>> 
            >>> # Calculate 95% settling time
            >>> settling_95 = 3 * tau_samples
            >>> print(f"95% settling: {settling_95:.1f} samples")
            >>> # 95% settling: 7.0 samples
        ```
        """
        ...
    
    @alpha.setter
    def alpha(self, value: float) -> None:
        """
        Set smoothing factor.
        
        Updates the filter's alpha (smoothing factor), changing the balance between
        noise reduction and responsiveness. The new alpha takes effect immediately
        for all subsequent update() calls.
        
        :param value: New smoothing factor in range (0, 1]
        
        :raises FilterConfigurationError: If value not in range (0, 1]
        :raises TypeError: If value cannot be converted to float
        
        Effects of Changing Alpha:
            
            Increasing alpha (toward 1.0):
                
                - Faster response to angle changes
                - Less smoothing, more noise
                - Shorter settling time
                - Better tracking of rapid rotation
            
            Decreasing alpha (toward 0.0):
                
                - Slower response to angle changes
                - More smoothing, less noise
                - Longer settling time
                - Better for drifting or noisy sensors
        
        Real-Time Adjustment Use Cases:
            
            - Motion-adaptive smoothing (stationary = heavy, moving = light)
            - SNR-based smoothing (noisy = heavy, clean = light)
            - User-adjustable responsiveness
            - Mode-dependent filtering (calibration vs operation)
        
        Example
        -------
        ```python
            >>> from ufilter import AngleEMA
            >>> import math
            >>> 
            >>> # Create filter
            >>> compass = AngleEMA(alpha=0.2, initial=0.0)
            >>> print(f"Initial alpha: {compass.alpha}")
            >>> # Initial alpha: 0.2
            >>> 
            >>> # Test with one setting
            >>> for angle in [10, 20, 30]:
            ...     result = compass.update(math.radians(angle))
            ...     print(f"  {angle}° → {math.degrees(result):.1f}°")
            >>> 
            >>> # Adjust for faster response
            >>> compass.alpha = 0.5
            >>> compass.reset(math.radians(30))  # Reset to last angle
            >>> print(f"\nFaster response (alpha={compass.alpha}):")
            >>> for angle in [40, 50, 60]:
            ...     result = compass.update(math.radians(angle))
            ...     print(f"  {angle}° → {math.degrees(result):.1f}°")
            >>> 
            >>> # Motion-adaptive filtering
            >>> def motion_adaptive_compass():
            ...     heading_filter = AngleEMA(alpha=0.2)
            ...     
            ...     for heading, angular_velocity in imu_data:
            ...         # Adjust smoothing based on rotation rate
            ...         if abs(angular_velocity) < 5:  # deg/s, nearly stationary
            ...             heading_filter.alpha = 0.1  # Heavy smoothing
            ...         elif abs(angular_velocity) < 30:  # deg/s, moderate motion
            ...             heading_filter.alpha = 0.3  # Moderate smoothing
            ...         else:  # Fast rotation
            ...             heading_filter.alpha = 0.7  # Light smoothing
            ...         
            ...         filtered = heading_filter.update(heading)
            >>> 
            >>> # SNR-based adaptive filtering
            >>> def snr_adaptive_filtering():
            ...     orientation_filter = AngleEMA(alpha=0.25)
            ...     
            ...     for angle, signal_quality in sensor_stream:
            ...         # Adjust based on signal quality
            ...         if signal_quality > 0.8:  # High quality
            ...             orientation_filter.alpha = 0.5
            ...         elif signal_quality > 0.5:  # Medium quality
            ...             orientation_filter.alpha = 0.25
            ...         else:  # Low quality
            ...             orientation_filter.alpha = 0.1
            ...         
            ...         filtered = orientation_filter.update(angle)
            >>> 
            >>> # User-adjustable smoothing
            >>> def user_adjustable_smoothing(smoothing_level):
            ...     '''Set smoothing from 1 (heavy) to 10 (light).'''
            ...     gyro_filter = AngleEMA(alpha=0.25)
            ...     
            ...     # Map 1-10 to alpha 0.05-0.95
            ...     alpha_value = 0.05 + (smoothing_level - 1) * 0.1
            ...     gyro_filter.alpha = alpha_value
            ...     
            ...     print(f"Smoothing level {smoothing_level} → alpha={alpha_value:.2f}")
            ...     return gyro_filter
            >>> 
            >>> # Invalid values
            >>> try:
            ...     compass.alpha = 0.0  # Zero not allowed
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     compass.alpha = 1.5  # Greater than 1 not allowed
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
        ```
        """
        ...
    
    @property
    def value(self) -> float:
        """
        Get current filtered angle in radians.
        
        Returns the most recent filtered angle output. The angle is always
        normalized to the range [-π, π] radians (±180°).
        
        :return: Current filtered angle in radians, range [-π, π]
                Returns None if filter is uninitialized
        
        Angle Range:
            
            - Minimum: -π radians (-180°)
            - Maximum: +π radians (+180°)
            - Wraps around at boundaries
            - Example: π + 0.1 → -π + 0.1
        
        Use Cases:
            
            - Getting current heading estimate
            - Checking filter state before reset
            - Logging filtered orientation
            - Feeding to control algorithms
        
        Example
        -------
        ```python
            >>> from ufilter import AngleEMA
            >>> import math
            >>> 
            >>> # Create and check initial value
            >>> compass = AngleEMA(alpha=0.3, initial=math.radians(45))
            >>> print(f"Initial value: {math.degrees(compass.value):.1f}°")
            >>> # Initial value: 45.0°
            >>> 
            >>> # Update and check new value
            >>> compass.update(math.radians(50))
            >>> print(f"After update: {math.degrees(compass.value):.1f}°")
            >>> # After update: 46.5°
            >>> 
            >>> # Uninitialized filter
            >>> new_filter = AngleEMA(alpha=0.3, initial=None)
            >>> print(f"Uninitialized: {new_filter.value}")
            >>> # Uninitialized: None
            >>> 
            >>> # After first update, becomes initialized
            >>> new_filter.update(math.radians(30))
            >>> print(f"Now initialized: {math.degrees(new_filter.value):.1f}°")
            >>> # Now initialized: 30.0°
            >>> 
            >>> # Using value in control loop
            >>> def heading_control():
            ...     heading_filter = AngleEMA(alpha=0.25, initial=0.0)
            ...     target_heading = math.radians(90)  # 90° target
            ...     
            ...     for raw_heading in sensor_readings:
            ...         # Filter heading
            ...         filtered_heading = heading_filter.update(raw_heading)
            ...         
            ...         # Calculate error (circular difference)
            ...         current = heading_filter.value
            ...         error = math.atan2(
            ...             math.sin(target_heading - current),
            ...             math.cos(target_heading - current)
            ...         )
            ...         
            ...         # Apply control
            ...         control_output = kp * error
            >>> 
            >>> # Checking angle normalization
            >>> def demonstrate_normalization():
            ...     filt = AngleEMA(alpha=0.5, initial=math.radians(170))
            ...     
            ...     print("Testing angle normalization:")
            ...     test_angles = [170, 175, -175, -170, 180, -180]
            ...     
            ...     for angle in test_angles:
            ...         filt.update(math.radians(angle))
            ...         result_deg = math.degrees(filt.value)
            ...         print(f"  Input: {angle:4d}° → Stored: {result_deg:6.1f}°")
        ```
        """
        ...
    
    def reset(self, rad: float | None = None) -> None:
        """
        Reset filter state while preserving configuration.
        
        Clears the filter's internal state (filtered angle value) and resets the
        sample counter, but maintains the alpha smoothing factor. The filter can
        be reset to a specific angle or left uninitialized to automatically set
        its state from the next measurement.
        
        :param rad: Optional angle in radians to reset to (default: None)
                   If provided, filter state set to this angle (normalized to [-π, π])
                   If None, filter becomes uninitialized until next update() call
        
        :raises TypeError: If rad cannot be converted to float
        
        Reset Operations:
            
            - Clears current filtered angle value
            - Resets sample counter to zero
            - Preserves alpha smoothing factor
            - Option 1 (rad provided): Set to specific angle
            - Option 2 (rad=None): Lazy initialization on next update
        
        Use Cases:
            
            - Starting new measurement session
            - Known position change (e.g., robot repositioned)
            - Recovering from sensor glitch
            - Switching between different angle sources
            - Batch processing of multiple datasets
            - Calibration or re-initialization sequences
        
        Example
        -------
        ```python
            >>> from ufilter import AngleEMA
            >>> import math
            >>> 
            >>> # Create and use filter
            >>> heading_filter = AngleEMA(alpha=0.3, initial=0.0)
            >>> 
            >>> print("First session:")
            >>> angles = [0, 5, 10, 15, 20]
            >>> for angle_deg in angles:
            ...     angle_rad = math.radians(angle_deg)
            ...     filtered_rad = heading_filter.update(angle_rad)
            ...     print(f"  Input: {angle_deg:3.0f}° → Filtered: {math.degrees(filtered_rad):5.1f}°")
            >>> # First session:
            >>> #   Input:   0° → Filtered:   0.0°
            >>> #   Input:   5° → Filtered:   1.5°
            >>> #   Input:  10° → Filtered:   4.1°
            >>> #   Input:  15° → Filtered:   7.3°
            >>> #   Input:  20° → Filtered:  11.1°
            >>> 
            >>> print(f"After session: angle={math.degrees(heading_filter.value):.1f}°, "
            ...       f"samples={heading_filter.sample_count}")
            >>> # After session: angle=11.1°, samples=5
            >>> 
            >>> # Reset to known angle (e.g., robot repositioned)
            >>> heading_filter.reset(math.radians(90))
            >>> print(f"After reset: angle={math.degrees(heading_filter.value):.1f}°, "
            ...       f"samples={heading_filter.sample_count}")
            >>> # After reset: angle=90.0°, samples=0
            >>> 
            >>> # Verify alpha preserved
            >>> print(f"Alpha preserved: {heading_filter.alpha}")
            >>> # Alpha preserved: 0.3
            >>> 
            >>> print("\nSecond session (from 90°):")
            >>> angles2 = [95, 100, 105, 110]
            >>> for angle_deg in angles2:
            ...     angle_rad = math.radians(angle_deg)
            ...     filtered_rad = heading_filter.update(angle_rad)
            ...     print(f"  Input: {angle_deg:3.0f}° → Filtered: {math.degrees(filtered_rad):5.1f}°")
            >>> 
            >>> # Reset to uninitialized state
            >>> heading_filter.reset()  # rad=None
            >>> print(f"\nAfter reset (None): initialized={heading_filter.value is not None}")
            >>> # After reset (None): initialized=False
            >>> 
            >>> # First update initializes
            >>> first_angle = heading_filter.update(math.radians(45))
            >>> print(f"After first update: angle={math.degrees(first_angle):.1f}°")
            >>> # After first update: angle=45.0°
            >>> 
            >>> # Multi-sensor application with synchronized reset
            >>> def multiaxis_orientation_tracking():
            ...     # IMU with roll, pitch, yaw filtering
            ...     roll_filter = AngleEMA(alpha=0.25, initial=0.0)
            ...     pitch_filter = AngleEMA(alpha=0.25, initial=0.0)
            ...     yaw_filter = AngleEMA(alpha=0.25, initial=0.0)
            ...     
            ...     filters = [roll_filter, pitch_filter, yaw_filter]
            ...     names = ['Roll', 'Pitch', 'Yaw']
            ...     
            ...     # Process first set of measurements
            ...     measurements1 = [
            ...         (5, 10, 45),    # roll, pitch, yaw in degrees
            ...         (8, 12, 50),
            ...         (6, 9, 48)
            ...     ]
            ...     
            ...     print("Session 1:")
            ...     for roll, pitch, yaw in measurements1:
            ...         angles_rad = [math.radians(a) for a in [roll, pitch, yaw]]
            ...         filtered = [f.update(r) for f, r in zip(filters, angles_rad)]
            ...         filtered_deg = [math.degrees(f) for f in filtered]
            ...         print(f"  R:{filtered_deg[0]:5.1f}° P:{filtered_deg[1]:5.1f}° Y:{filtered_deg[2]:5.1f}°")
            ...     
            ...     # Reset all axes to known calibration position
            ...     print("\nCalibration reset to (0°, 0°, 0°)")
            ...     for filt in filters:
            ...         filt.reset(0.0)
            ...     
            ...     # Process second set from calibrated position
            ...     measurements2 = [(-2, 1, 5), (-1, 2, 8)]
            ...     
            ...     print("\nSession 2 (after calibration):")
            ...     for roll, pitch, yaw in measurements2:
            ...         angles_rad = [math.radians(a) for a in [roll, pitch, yaw]]
            ...         filtered = [f.update(r) for f, r in zip(filters, angles_rad)]
            ...         filtered_deg = [math.degrees(f) for f in filtered]
            ...         print(f"  R:{filtered_deg[0]:5.1f}° P:{filtered_deg[1]:5.1f}° Y:{filtered_deg[2]:5.1f}°")
            >>> 
            >>> # Sensor glitch recovery
            >>> def glitch_recovery_example():
            ...     compass = AngleEMA(alpha=0.2, initial=math.radians(45))
            ...     
            ...     # Normal readings
            ...     readings = [45, 47, 46, 48, 999, 47, 49]  # 999 is glitch
            ...     
            ...     print("Glitch Recovery:")
            ...     print("Reading | Valid? | Filtered")
            ...     print("-" * 35)
            ...     
            ...     for reading in readings:
            ...         # Detect glitch (unreasonable value)
            ...         if reading > 360 or reading < -180:
            ...             print(f"{reading:7d} | NO     | <skipped, reset>")
            ...             # Reset to last known good value
            ...             compass.reset(compass.value)
            ...         else:
            ...             filtered = compass.update(math.radians(reading))
            ...             filtered_deg = math.degrees(filtered)
            ...             print(f"{reading:7d} | YES    | {filtered_deg:7.1f}°")
        ```
        """
        ...
    
    @micropython.native
    def update(self, rad: float) -> float:
        """
        Update filter with new angle measurement.
        
        Processes a single angular input through the exponential moving average filter
        using circular statistics. The filter automatically handles wrap-around at the
        ±π boundary, ensuring correct averaging even when angles cross 0°/360°.
        
        :param rad: Input angle in radians (any value, will be normalized to [-π, π])
        :return: Filtered angle in radians, guaranteed to be in [-π, π] range
        
        :raises TypeError: If input cannot be converted to float
        
        Algorithm Details:
            The filter implements circular exponential smoothing:
            
            1. Normalize input: θ_in = atan2(sin(rad), cos(rad))  → [-π, π]
            2. If uninitialized: θ_out = θ_in (first sample)
            3. Calculate circular difference: Δθ = atan2(sin(θ_in - θ_out), cos(θ_in - θ_out))
            4. Update: θ_out = θ_out + α · Δθ
            5. Normalize output: θ_out = atan2(sin(θ_out), cos(θ_out))  → [-π, π]
            
            Where:
            
            - Circular difference finds shortest path around circle
            - atan2 ensures proper quadrant and wrapping
            - Output is always in [-π, π] range
        
        Performance Characteristics:
            
            - O(1) computational complexity
            - Involves trigonometric functions (sin, cos, atan2)
            - More expensive than linear EMA due to circular math
            - Optimized with @micropython.native decorator
            - Suitable for typical IMU/compass rates (10-100 Hz)
        
        Wrap-Around Handling:
            
            The filter correctly handles discontinuity at ±π:
            
            Example 1: Crossing from positive to negative
                - Current: +170° (2.967 rad)
                - Input: -170° (-2.967 rad)
                - Linear difference: -340° ❌ WRONG
                - Circular difference: +20° ✓ CORRECT
                - Filter smoothly tracks via short path
            
            Example 2: Crossing from negative to positive
                - Current: -175° (-3.054 rad)
                - Input: +175° (+3.054 rad)
                - Linear difference: +350° ❌ WRONG
                - Circular difference: -10° ✓ CORRECT
                - Filter smoothly tracks via short path
        
        Example
        -------
        ```python
            >>> from ufilter import AngleEMA
            >>> import math
            >>> 
            >>> # Demonstrating wrap-around behavior
            >>> heading_filter = AngleEMA(alpha=0.4, initial=math.radians(170))
            >>> 
            >>> print("Wrap-around test:")
            >>> print("Input (°) | Output (°) | Description")
            >>> print("-" * 45)
            >>> 
            >>> # Sequence that crosses ±180° boundary
            >>> test_angles_deg = [170, 175, -175, -170, -165, -175, 180, 175]
            >>> 
            >>> for angle_deg in test_angles_deg:
            ...     angle_rad = math.radians(angle_deg)
            ...     filtered_rad = heading_filter.update(angle_rad)
            ...     filtered_deg = math.degrees(filtered_rad)
            ...     
            ...     # Describe what's happening
            ...     if abs(angle_deg) > 160:
            ...         desc = "Near ±180°"
            ...     elif angle_deg > 0:
            ...         desc = "Positive side"
            ...     else:
            ...         desc = "Negative side"
            ...     
            ...     print(f"{angle_deg:9.0f} | {filtered_deg:10.1f} | {desc}")
            >>> # Input (°) | Output (°) | Description
            >>> # ---------------------------------------------
            >>> #       170 |      170.0 | Near ±180°
            >>> #       175 |      172.0 | Near ±180°
            >>> #      -175 |      176.2 | Near ±180° (wrapped)
            >>> #      -170 |      173.7 | Near ±180°
            >>> #      -165 |      170.2 | Near ±180°
            >>> 
            >>> # Compass heading smoothing
            >>> def compass_heading_example():
            ...     compass = AngleEMA(alpha=0.25)
            ...     
            ...     # Simulate noisy compass readings around North (0°)
            ...     noisy_readings = [
            ...         (0, 0.3), (5, 0.2), (358, -0.4), (2, 0.1),
            ...         (355, -0.3), (1, 0.2), (359, -0.1), (3, 0.3)
            ...     ]
            ...     
            ...     print("\nNoisy Compass Filtering:")
            ...     print("Raw (°) | Noise | Filtered (°) | Error (°)")
            ...     print("-" * 50)
            ...     
            ...     for true_heading, noise_deg in noisy_readings:
            ...         noisy_rad = math.radians(true_heading + noise_deg)
            ...         filtered_rad = compass.update(noisy_rad)
            ...         filtered_deg = math.degrees(filtered_rad)
            ...         
            ...         # Calculate circular error
            ...         error = ((filtered_deg - true_heading + 180) % 360) - 180
            ...         
            ...         print(f"{true_heading:7.0f} | {noise_deg:+5.1f} | {filtered_deg:12.1f} | {error:+8.2f}")
            >>> 
            >>> # Motor position tracking with wrap-around
            >>> def motor_position_tracking():
            ...     position_filter = AngleEMA(alpha=0.5, initial=0.0)
            ...     
            ...     # Simulate continuous rotation through multiple revolutions
            ...     print("\nContinuous Rotation Tracking:")
            ...     print("Time | Raw Position | Filtered | Revolutions")
            ...     print("-" * 50)
            ...     
            ...     for t in range(0, 360, 30):
            ...         # Motor position wraps at ±180°
            ...         raw_position_deg = (t * 3) % 360
            ...         if raw_position_deg > 180:
            ...             raw_position_deg -= 360
            ...         
            ...         raw_rad = math.radians(raw_position_deg)
            ...         filtered_rad = position_filter.update(raw_rad)
            ...         filtered_deg = math.degrees(filtered_rad)
            ...         
            ...         revolutions = t * 3 / 360
            ...         
            ...         print(f"{t:4d} | {raw_position_deg:12.0f}° | {filtered_deg:8.1f}° | {revolutions:5.1f}")
            >>> 
            >>> # Phase tracking in signal processing
            >>> def phase_tracking_example():
            ...     import cmath
            ...     
            ...     phase_filter = AngleEMA(alpha=0.3)
            ...     
            ...     print("\nPhase Tracking:")
            ...     print("Sample | Raw Phase | Filtered Phase | Phase Noise")
            ...     print("-" * 55)
            ...     
            ...     base_freq = 10  # Hz
            ...     sample_rate = 1000  # Hz
            ...     
            ...     for n in range(0, 100, 10):
            ...         # Generate signal with phase noise
            ...         t = n / sample_rate
            ...         phase = 2 * math.pi * base_freq * t
            ...         phase_noise = 0.2 * math.sin(2 * math.pi * 50 * t)  # Noise
            ...         
            ...         noisy_phase = phase + phase_noise
            ...         
            ...         # Normalize and filter
            ...         normalized = math.atan2(math.sin(noisy_phase), math.cos(noisy_phase))
            ...         filtered = phase_filter.update(normalized)
            ...         
            ...         print(f"{n:6d} | {math.degrees(normalized):9.1f}° | "
            ...               f"{math.degrees(filtered):14.1f}° | {math.degrees(phase_noise):11.2f}°")
        ```
        """
        ...



class PID(Base):
    """
    Full-featured PID controller with anti-windup, derivative filtering, and tracking.
    
    Implements a discrete-time PID controller with numerous advanced features
    including proportional-on-measurement to reduce overshoot, derivative-on-
    measurement to avoid derivative kick, configurable derivative filtering,
    multiple anti-windup strategies, integrator tracking for bumpless transfer,
    and support for both fixed and variable sampling rates.
    
    Control Law:
        
        u(t) = Kp×e_p(t) + Ki×∫e_i(t)dt + Kd×de/dt
        
        Where:
            
            - e_p = beta×setpoint - measurement (proportional error with weighting)
            - e_i = setpoint - measurement (integral error, full setpoint)
            - de/dt = -(measurement - measurement_prev)/dt (derivative on measurement)
    
    Key Features:
        
        - Proportional-on-Measurement (adjustable via beta parameter)
        - Derivative-on-Measurement (no derivative kick on setpoint changes)
        - Configurable derivative low-pass filtering
        - Three anti-windup strategies: None, Clamping, Back-calculation
        - Integrator tracking mode for bumpless manual-to-auto transfer
        - Independent integrator and output limits
        - Fixed or variable sampling rate support
    
    Anti-Windup Modes:
        
        - AW_NONE (0): No anti-windup (integrator can grow unbounded)
        - AW_CLAMP (1): Conditional integration (stop when saturated) [default]
        - AW_BACKCALC (2): Back-calculation with configurable gain k_aw
    
    Applications:
        
        - Temperature control (ovens, heaters, chillers)
        - Motor speed and position control
        - Process control (level, flow, pressure)
        - HVAC systems
        - Battery management
        - Any closed-loop control application
    
    Performance Characteristics:
        
        - Execution time: ~50-100 µs per update (platform dependent)
        - Memory: ~100 bytes per instance
        - Deterministic execution (suitable for real-time control)
        - Optimized with @micropython.native decorator
    
    Attributes:
        
        kp, ki, kd: PID gains (read/write)
        setpoint: Current setpoint (read/write via set_setpoint())
        u: Most recent controller output
        fs: Fixed sampling rate (None if variable)
        out_min, out_max: Output limits
        i_min, i_max: Integrator limits
        beta: Setpoint weighting [0, 1]
        tau_d: Derivative filter time constant
        aw_mode: Anti-windup mode (AW_NONE, AW_CLAMP, AW_BACKCALC)
        k_aw: Back-calculation gain
    
    Constants:
        
        AW_NONE = 0: No anti-windup
        AW_CLAMP = 1: Conditional integration (stop when saturated)
        AW_BACKCALC = 2: Back-calculation method
    
    Methods:
        
        update(meas, dt_s): Compute control output
        set_setpoint(sp, keep_output): Change setpoint with optional bumpless transfer
        set_gains(kp, ki, kd): Update PID gains
        set_output_limits(out_min, out_max, clamp_i): Change output limits
        set_beta(beta): Set setpoint weighting [0, 1]
        set_tau_d(tau): Set derivative filter time constant
        set_aw(mode, k_aw): Configure anti-windup
        preload_integrator(i0): Manually set integrator state
        start_tracking(u_manual): Enable tracking mode (follow external output)
        stop_tracking(): Disable tracking mode
        reset(): Reset controller state
    
    Notes:
        
        - Derivative acts on measurement (not error) to avoid derivative kick
        - Proportional term uses beta×setpoint to reduce overshoot
        - Integral term always uses full setpoint for zero steady-state error
        - Integrator limits should generally be ≤ output limits
        - tau_d_filter recommended when derivative noise is an issue
        - Back-calculation anti-windup generally preferred over clamping
        - Tracking mode enables bumpless manual-to-auto transfer
    """
    
    AW_NONE: int = 0
    AW_CLAMP: int = 1
    AW_BACKCALC: int = 2
    
    def __init__(self, kp: float, ki: float, kd: float, *,
                 fs: float | None = None,
                 out_min: float = -1.0, out_max: float = 1.0,
                 i_min: float | None = None, i_max: float | None = None,
                 beta: float = 1.0,
                 tau_d_filter: float = 0.0,
                 aw_mode: int = 1, k_aw: float = 1.0) -> None:
        """
        Initialize PID controller with gains and configuration parameters.
        
        Creates a new PID controller instance with the specified gains and
        configuration. The controller starts in an uninitialized state (no
        previous measurement) and must be given a setpoint before use.
        
        :param kp: Proportional gain (must be >= 0)
        :param ki: Integral gain (must be >= 0)
        :param kd: Derivative gain (must be >= 0)
        :param fs: Fixed sampling rate in Hz. If provided, dt is calculated as 1/fs
                   and update() is called without dt parameter. If None, dt_s must
                   be provided to each update() call. (default: None)
        :param out_min: Minimum output limit (default: -1.0)
        :param out_max: Maximum output limit (must be > out_min, default: 1.0)
        :param i_min: Minimum integrator limit. If None, uses out_min (default: None)
        :param i_max: Maximum integrator limit. If None, uses out_max (default: None)
        :param beta: Setpoint weighting for proportional term, range [0, 1]
                     - 1.0: Full proportional action (may overshoot, default)
                     - 0.0: Proportional-on-measurement only (no overshoot)
                     (default: 1.0)
        :param tau_d_filter: Derivative filter time constant in seconds
                             - 0.0: No filtering (default)
                             - 0.01-0.5: Typical filtering range
                             (default: 0.0)
        :param aw_mode: Anti-windup mode
                        - PID.AW_NONE (0): No anti-windup
                        - PID.AW_CLAMP (1): Conditional integration (default)
                        - PID.AW_BACKCALC (2): Back-calculation
                        (default: 1)
        :param k_aw: Back-calculation gain for AW_BACKCALC mode (>= 0)
                     Typical range: 0.5 to 2.0 (default: 1.0)
        
        :raises FilterConfigurationError: If kp, ki, or kd < 0, or if out_max <= out_min,
                                         or if beta not in [0, 1], or if tau_d_filter < 0,
                                         or if k_aw < 0
        :raises TypeError: If parameters cannot be converted to appropriate types
        
        Gain Selection Guidelines:
            
            Proportional Gain (kp):
                
                - Primary factor for speed of response
                - Too high: Overshoot, oscillation, instability
                - Too low: Slow response, large steady-state error
                - Typical starting point: 1.0 to 5.0
            
            Integral Gain (ki):
                
                - Eliminates steady-state error
                - Too high: Overshoot, oscillation, slow settling
                - Too low: Slow elimination of steady-state error
                - Typical starting point: 0.1 to 2.0
            
            Derivative Gain (kd):
                
                - Improves stability, reduces overshoot
                - Too high: Noise amplification, high-frequency oscillation
                - Too low: Excessive overshoot, longer settling time
                - Typical starting point: 0.0 to 0.5
        
        Sampling Rate Configuration:
            
            Fixed sampling rate (fs provided):
                
                - Controller assumes constant update rate
                - dt calculated as 1/fs
                - Call update(measurement) without dt parameter
                - Recommended for periodic control loops
                - Example: fs=10.0 → dt=0.1s → 10 Hz control
            
            Variable sampling rate (fs=None):
                
                - Controller adapts to actual timing
                - Must provide dt_s to each update() call
                - Useful for event-driven or irregular sampling
                - Example: update(measurement, dt_s=measured_dt)
        
        Output Limit Configuration:
            
            Output limits (out_min, out_max):
                
                - Define actuator saturation bounds
                - All control outputs clamped to [out_min, out_max]
                - Must satisfy: out_max > out_min
                - Example: Heater 0-100% → out_min=0.0, out_max=100.0
            
            Integrator limits (i_min, i_max):
                
                - Define integrator saturation bounds
                - If None, default to output limits
                - Should generally be ≤ output limits
                - Helps prevent integrator windup
                - Example: Limit integrator to ±50 → i_min=-50.0, i_max=50.0
        
        Beta Parameter (Setpoint Weighting):
            
            - Controls proportional response to setpoint changes
            - beta = 1.0: Standard PID (fast response, may overshoot)
            - beta = 0.5: Moderate weighting (balanced)
            - beta = 0.0: P-on-M only (no overshoot on setpoint step)
            - Recommended: 0.0 for temperature, 1.0 for position
        
        Derivative Filtering:
            
            - Reduces noise amplification in derivative term
            - tau_d = 0: No filter (maximum noise sensitivity)
            - tau_d = 0.05-0.2s: Typical filtering
            - Cutoff frequency: fc ≈ 1/(2π×tau_d)
            - Example: tau_d=0.1s → fc≈1.6Hz
        
        Anti-Windup Configuration:
            
            AW_NONE: No protection (use only if saturation never occurs)
            
            AW_CLAMP: Stops integration when saturated (simple, effective)
            
            AW_BACKCALC: Actively reduces integrator when saturated
                         - Requires k_aw tuning
                         - k_aw=1.0: Standard rate
                         - k_aw>1.0: Faster reduction
                         - k_aw<1.0: Slower reduction
        
        Example
        -------
        ```python
            >>> from ufilter import PID
            >>> 
            >>> # Basic temperature controller
            >>> temp_pid = PID(
            ...     kp=2.0, ki=0.5, kd=0.1,
            ...     fs=10.0,  # 10 Hz sampling
            ...     out_min=0.0, out_max=100.0  # 0-100% heater power
            ... )
            >>> 
            >>> # Motor controller with reduced overshoot
            >>> motor_pid = PID(
            ...     kp=5.0, ki=2.0, kd=0.5,
            ...     fs=50.0,  # 50 Hz sampling
            ...     out_min=-100.0, out_max=100.0,  # ±100% PWM
            ...     beta=0.3,  # Reduce overshoot
            ...     tau_d_filter=0.05  # Light derivative filtering
            ... )
            >>> 
            >>> # Pressure controller with back-calculation anti-windup
            >>> pressure_pid = PID(
            ...     kp=1.5, ki=0.3, kd=0.2,
            ...     fs=20.0,  # 20 Hz sampling
            ...     out_min=0.0, out_max=100.0,  # 0-100% valve position
            ...     aw_mode=PID.AW_BACKCALC,  # Back-calculation
            ...     k_aw=1.5  # Aggressive anti-windup
            ... )
            >>> 
            >>> # Variable sampling rate controller
            >>> variable_pid = PID(
            ...     kp=2.0, ki=0.5, kd=0.1,
            ...     fs=None,  # Variable rate
            ...     out_min=0.0, out_max=100.0
            ... )
            >>> # Must provide dt_s to update()
            >>> output = variable_pid.update(measurement, dt_s=0.105)
            >>> 
            >>> # P-only controller (no integral or derivative)
            >>> p_only = PID(
            ...     kp=3.0, ki=0.0, kd=0.0,  # P-only
            ...     fs=10.0,
            ...     out_min=0.0, out_max=100.0
            ... )
            >>> 
            >>> # PI controller (no derivative)
            >>> pi_controller = PID(
            ...     kp=2.0, ki=0.5, kd=0.0,  # No derivative
            ...     fs=10.0,
            ...     out_min=0.0, out_max=100.0
            ... )
            >>> 
            >>> # Proportional-on-measurement for overshoot-free control
            >>> pom_pid = PID(
            ...     kp=3.0, ki=1.0, kd=0.2,
            ...     fs=10.0,
            ...     out_min=0.0, out_max=100.0,
            ...     beta=0.0  # P-on-M: no overshoot
            ... )
            >>> 
            >>> # Heavy derivative filtering for noisy sensor
            >>> filtered_pid = PID(
            ...     kp=2.0, ki=0.5, kd=0.5,
            ...     fs=10.0,
            ...     out_min=0.0, out_max=100.0,
            ...     tau_d_filter=0.2  # Heavy filtering
            ... )
            >>> 
            >>> # Asymmetric integrator limits
            >>> asymmetric_pid = PID(
            ...     kp=2.0, ki=0.5, kd=0.1,
            ...     fs=10.0,
            ...     out_min=-100.0, out_max=100.0,
            ...     i_min=-50.0, i_max=80.0  # Asymmetric integrator
            ... )
            >>> 
            >>> # Ziegler-Nichols tuned controller
            >>> def create_zn_tuned_pid(ku, tu):
            ...     '''Create PID with Ziegler-Nichols tuning.
            ...     
            ...     ku: Ultimate gain from relay test
            ...     tu: Ultimate period from relay test
            ...     '''
            ...     kp = 0.6 * ku
            ...     ki = 1.2 * ku / tu
            ...     kd = 0.075 * ku * tu
            ...     
            ...     return PID(kp=kp, ki=ki, kd=kd, fs=10.0,
            ...                out_min=0.0, out_max=100.0)
            >>> 
            >>> # Invalid configurations
            >>> try:
            ...     bad_pid = PID(kp=-1.0, ki=0.5, kd=0.1, fs=10.0)  # Negative gain
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     bad_pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                   out_min=100.0, out_max=0.0)  # Invalid limits
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     bad_pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                   beta=1.5)  # Beta out of range
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
        ```
        
        Notes:
            
            - Controller initialized in reset state (no history)
            - Must call set_setpoint() before use
            - First update() will have zero derivative
            - Gains and parameters can be changed after construction
            - Use set_gains(), set_beta(), etc. for runtime adjustments
        """
        ...
    
    def set_output_limits(self, out_min: float, out_max: float, clamp_i: bool = True) -> None:
        """
        Change output and integrator limits.
        
        Updates the controller's output saturation limits and optionally clamps
        the integrator state to the new limits. This is useful when the controlled
        system's actuator limits change (e.g., reduced motor power available,
        changed valve position range) or when switching between operating modes
        with different constraints.
        
        :param out_min: New minimum output limit
        :param out_max: New maximum output limit (must be > out_min)
        :param clamp_i: If True, also clamp current integrator value to new limits
        
        :raises FilterConfigurationError: If out_max <= out_min
        :raises TypeError: If limits cannot be converted to float
        
        Effects of Limit Changes:
            
            With clamp_i=True (default):
                
                - Output clamped to [out_min, out_max] on next update()
                - Integrator immediately clamped to [i_min, i_max]
                - Prevents output jumps when limits expand
                - Recommended for most applications
            
            With clamp_i=False:
                
                - Output clamped to [out_min, out_max] on next update()
                - Integrator not modified immediately
                - May cause output jump when limits expand
                - Use only when integrator state must be preserved
        
        Integrator Limits:
            
            The integrator limits (i_min, i_max) track the output limits unless
            explicitly set differently. When output limits change:
                
                - If i_min/i_max were not explicitly set, they follow out_min/out_max
                - If i_min/i_max were explicitly set, they remain unchanged
                - Integrator limits should generally be ≤ output limits
        
        Use Cases:
            
            - Actuator constraint changes (motor derating, valve repositioning)
            - Operating mode switching (eco mode, sport mode)
            - Safety limit adjustments (temperature limits, speed limits)
            - Battery-aware control (limit output based on charge level)
            - Load-dependent limiting (heavy load = reduced acceleration)
        
        Example
        -------
        ```python
            >>> from ufilter import PID
            >>> 
            >>> # Temperature controller
            >>> pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...           out_min=0.0, out_max=100.0)  # 0-100% heater power
            >>> pid.set_setpoint(25.0)
            >>> 
            >>> # Normal operation
            >>> temp = 20.0
            >>> power = pid.update(temp)
            >>> print(f"Power: {power:.1f}%")
            >>> # Power: 85.0%
            >>> 
            >>> # Reduce limits due to low battery
            >>> battery_level = 0.5  # 50% charge
            >>> max_power = 100.0 * battery_level
            >>> pid.set_output_limits(0.0, max_power, clamp_i=True)
            >>> print(f"New max power: {max_power:.1f}%")
            >>> # New max power: 50.0%
            >>> 
            >>> # Next update respects new limits
            >>> power = pid.update(20.0)
            >>> print(f"Limited power: {power:.1f}%")
            >>> # Limited power: 50.0% (clamped)
            >>> 
            >>> # Operating mode switching
            >>> def mode_based_limiting():
            ...     motor_pid = PID(kp=1.5, ki=0.8, kd=0.05, fs=50.0,
            ...                     out_min=-100.0, out_max=100.0)
            ...     
            ...     mode = "eco"  # eco, normal, sport
            ...     
            ...     if mode == "eco":
            ...         motor_pid.set_output_limits(-50.0, 50.0, clamp_i=True)
            ...     elif mode == "normal":
            ...         motor_pid.set_output_limits(-80.0, 80.0, clamp_i=True)
            ...     else:  # sport
            ...         motor_pid.set_output_limits(-100.0, 100.0, clamp_i=True)
            ...     
            ...     return motor_pid
            >>> 
            >>> # Battery-aware control
            >>> def battery_aware_control():
            ...     pid = PID(kp=2.0, ki=1.0, kd=0.0, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     while True:
            ...         battery_voltage = read_battery()
            ...         
            ...         # Scale max output based on battery
            ...         if battery_voltage > 11.0:  # Full power
            ...             pid.set_output_limits(0.0, 100.0, clamp_i=True)
            ...         elif battery_voltage > 10.0:  # Reduced power
            ...             pid.set_output_limits(0.0, 70.0, clamp_i=True)
            ...         else:  # Low battery
            ...             pid.set_output_limits(0.0, 40.0, clamp_i=True)
            ...         
            ...         measurement = read_sensor()
            ...         output = pid.update(measurement)
            >>> 
            >>> # Load-dependent limiting
            >>> def load_adaptive_limits():
            ...     pid = PID(kp=1.5, ki=0.8, kd=0.05, fs=50.0,
            ...               out_min=-100.0, out_max=100.0)
            ...     
            ...     current_load = measure_load()
            ...     
            ...     # Reduce acceleration limit with heavy loads
            ...     if current_load > 80:  # Heavy load (kg)
            ...         pid.set_output_limits(-60.0, 60.0, clamp_i=True)
            ...     elif current_load > 50:  # Medium load
            ...         pid.set_output_limits(-80.0, 80.0, clamp_i=True)
            ...     else:  # Light load
            ...         pid.set_output_limits(-100.0, 100.0, clamp_i=True)
            >>> 
            >>> # Emergency limit reduction
            >>> def emergency_derate():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     temperature = read_controller_temp()
            ...     
            ...     if temperature > 85:  # Overheating
            ...         # Reduce to 30% immediately
            ...         pid.set_output_limits(0.0, 30.0, clamp_i=True)
            ...         print("Emergency derate activated")
            ...     elif temperature > 75:  # Hot
            ...         # Reduce to 60%
            ...         pid.set_output_limits(0.0, 60.0, clamp_i=True)
            >>> 
            >>> # Invalid configuration
            >>> try:
            ...     pid.set_output_limits(100.0, 0.0)  # max < min
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     pid.set_output_limits(50.0, 50.0)  # max == min
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
        ```
        """
        ...
    
    def set_gains(self, kp: float | None = None, ki: float | None = None, 
                  kd: float | None = None) -> None:
        """
        Update PID gains. Only provided gains are changed.
        
        Allows runtime adjustment of PID gains for adaptive control, gain
        scheduling, or online tuning. Unchanged gains retain their current values.
        The controller state (integrator, derivative filter) is preserved, enabling
        smooth gain transitions without output discontinuities.
        
        :param kp: New proportional gain (must be >= 0), or None to leave unchanged
        :param ki: New integral gain (must be >= 0), or None to leave unchanged
        :param kd: New derivative gain (must be >= 0), or None to leave unchanged
        
        :raises FilterConfigurationError: If any provided gain < 0
        :raises TypeError: If gain values cannot be converted to float
        
        Gain Effects:
            
            Proportional Gain (kp):
                
                - Increasing: Faster response, reduced steady-state error,
                             potential overshoot, reduced stability margin
                - Decreasing: Slower response, increased steady-state error,
                             reduced overshoot, improved stability
                - Zero: No immediate response to error (P action disabled)
            
            Integral Gain (ki):
                
                - Increasing: Faster elimination of steady-state error,
                             increased overshoot, potential oscillation
                - Decreasing: Slower elimination of steady-state error,
                             reduced overshoot, improved stability
                - Zero: Steady-state error not eliminated (I action disabled)
            
            Derivative Gain (kd):
                
                - Increasing: Faster damping of oscillations, improved stability,
                             increased noise amplification
                - Decreasing: Slower damping, reduced stability margin,
                             reduced noise sensitivity
                - Zero: No anticipatory action (D action disabled)
        
        Use Cases:
            
            - Gain scheduling based on operating point
            - Adaptive control based on system identification
            - Online tuning (manual or auto-tuning algorithms)
            - Mode-dependent gains (startup, normal, emergency)
            - Load-dependent gain adjustments
            - Performance vs stability trade-offs
        
        Example
        -------
        ```python
            >>> from ufilter import PID
            >>> 
            >>> # Create controller with initial gains
            >>> pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...           out_min=0.0, out_max=100.0)
            >>> pid.set_setpoint(25.0)
            >>> 
            >>> # Update only kp
            >>> pid.set_gains(kp=3.0)  # ki, kd unchanged
            >>> 
            >>> # Update ki and kd, leave kp unchanged
            >>> pid.set_gains(ki=0.8, kd=0.15)
            >>> 
            >>> # Update all gains
            >>> pid.set_gains(kp=2.5, ki=0.6, kd=0.12)
            >>> 
            >>> # Gain scheduling based on error magnitude
            >>> def gain_scheduling_controller():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     pid.set_setpoint(25.0)
            ...     
            ...     while True:
            ...         temp = read_sensor()
            ...         error = abs(25.0 - temp)
            ...         
            ...         # Adjust gains based on error
            ...         if error > 10.0:  # Far from setpoint
            ...             pid.set_gains(kp=3.0, ki=1.0, kd=0.2)
            ...         elif error > 2.0:  # Moderate error
            ...             pid.set_gains(kp=2.0, ki=0.5, kd=0.1)
            ...         else:  # Near setpoint
            ...             pid.set_gains(kp=1.0, ki=0.3, kd=0.05)
            ...         
            ...         output = pid.update(temp)
            >>> 
            >>> # Mode-dependent gains
            >>> def mode_adaptive_gains():
            ...     motor_pid = PID(kp=1.5, ki=0.8, kd=0.05, fs=50.0,
            ...                     out_min=-100.0, out_max=100.0)
            ...     
            ...     mode = "normal"  # startup, normal, precision
            ...     
            ...     if mode == "startup":
            ...         motor_pid.set_gains(kp=2.5, ki=1.5, kd=0.1)
            ...     elif mode == "normal":
            ...         motor_pid.set_gains(kp=1.5, ki=0.8, kd=0.05)
            ...     else:  # precision
            ...         motor_pid.set_gains(kp=0.8, ki=0.3, kd=0.02)
            >>> 
            >>> # Load-dependent gain adjustment
            >>> def load_adaptive_gains():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     load = measure_load()
            ...     scale_factor = 1.0 / (1.0 + load/100.0)
            ...     
            ...     pid.set_gains(
            ...         kp=2.0 * scale_factor,
            ...         ki=0.5 * scale_factor,
            ...         kd=0.1 * scale_factor
            ...     )
            >>> 
            >>> # Invalid gain values
            >>> try:
            ...     pid.set_gains(kp=-1.0)  # Negative gain
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
        ```
        
        Notes:
            
            - Gain changes take effect on the next update() call
            - Controller state (integrator, derivative filter) is preserved
            - No output discontinuity when gains change
            - For aggressive tuning, consider resetting controller after gain change
            - Use gain scheduling carefully to avoid instability
        """
        ...
    
    def set_beta(self, beta: float) -> None:
        """
        Set setpoint weighting for proportional term.
        
        Configures the proportional term's response to setpoint changes, enabling
        control over overshoot behavior. Beta = 0 implements proportional-on-
        measurement (P-on-M), eliminating derivative kick and reducing overshoot
        on setpoint steps. Beta = 1 provides full proportional action for fastest
        response but may cause overshoot.
        
        :param beta: Setpoint weighting in range [0, 1]
                     - 0.0: Proportional-on-measurement only (no overshoot on SP change)
                     - 0.5: Partial setpoint weighting (reduced overshoot)
                     - 1.0: Full proportional action (fastest response, may overshoot)
        
        :raises FilterConfigurationError: If beta not in [0, 1]
        :raises TypeError: If beta cannot be converted to float
        
        Control Law with Beta:
            
            Proportional term: P = Kp × (beta × setpoint - measurement)
            
            When beta = 0:
                
                - P = -Kp × measurement (proportional-on-measurement)
                - No immediate response to setpoint changes
                - Eliminates overshoot on setpoint steps
                - Slower rise time
            
            When beta = 1:
                
                - P = Kp × (setpoint - measurement) (standard P term)
                - Immediate response to setpoint changes
                - May cause overshoot on setpoint steps
                - Faster rise time
        
        Beta Selection Guidelines:
            
            Use beta = 0.0 when:
                
                - Overshoot is unacceptable (safety, quality)
                - Setpoint changes frequently
                - System is highly responsive
                - Example: Temperature ovens, level control
            
            Use beta = 0.3-0.7 when:
                
                - Moderate overshoot acceptable
                - Balance between speed and overshoot
                - General-purpose applications
                - Example: HVAC, motor positioning
            
            Use beta = 1.0 when:
                
                - Fast response is critical
                - Overshoot acceptable or desired
                - Setpoint changes rarely
                - Example: Fast servo systems, tracking control
        
        Example
        -------
        ```python
            >>> from ufilter import PID
            >>> import time
            >>> 
            >>> # Temperature controller - no overshoot allowed
            >>> oven_pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                out_min=0.0, out_max=100.0,
            ...                beta=0.0)  # No overshoot
            >>> oven_pid.set_setpoint(180.0)  # 180°C target
            >>> 
            >>> # Motor position - fast response desired
            >>> servo_pid = PID(kp=5.0, ki=2.0, kd=0.5, fs=100.0,
            ...                 out_min=-100.0, out_max=100.0,
            ...                 beta=1.0)  # Full proportional action
            >>> 
            >>> # HVAC - balanced performance
            >>> hvac_pid = PID(kp=1.5, ki=0.3, kd=0.05, fs=1.0,
            ...                out_min=0.0, out_max=100.0,
            ...                beta=0.5)  # Moderate overshoot
            >>> 
            >>> # Demonstrating beta effect on setpoint step
            >>> def compare_beta_response():
            ...     # Two identical controllers, different beta
            ...     pid_standard = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                        out_min=0.0, out_max=100.0, beta=1.0)
            ...     pid_no_overshoot = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                            out_min=0.0, out_max=100.0, beta=0.0)
            ...     
            ...     # Setpoint step from 0 to 100
            ...     pid_standard.set_setpoint(100.0)
            ...     pid_no_overshoot.set_setpoint(100.0)
            ...     
            ...     # Simulate response
            ...     measurement = 0.0
            ...     for i in range(100):
            ...         out1 = pid_standard.update(measurement)
            ...         out2 = pid_no_overshoot.update(measurement)
            ...         
            ...         # beta=1.0 will show larger initial output
            ...         # beta=0.0 will show gradual increase
            ...         if i < 5:
            ...             print(f"Step {i}: beta=1.0 → {out1:.1f}, beta=0.0 → {out2:.1f}")
            >>> 
            >>> # Application-specific beta selection
            >>> def application_beta_selection():
            ...     # Medical device - zero overshoot
            ...     drug_pump = PID(kp=1.0, ki=0.2, kd=0.05, fs=10.0,
            ...                     out_min=0.0, out_max=100.0)
            ...     drug_pump.set_beta(0.0)  # Safety critical
            ...     
            ...     # 3D printer extruder - minimal overshoot
            ...     extruder = PID(kp=3.0, ki=1.0, kd=0.2, fs=10.0,
            ...                    out_min=0.0, out_max=100.0)
            ...     extruder.set_beta(0.2)  # Quality critical
            ...     
            ...     # Robot joint - fast response
            ...     robot_joint = PID(kp=5.0, ki=2.0, kd=0.5, fs=100.0,
            ...                       out_min=-100.0, out_max=100.0)
            ...     robot_joint.set_beta(0.8)  # Speed critical
            >>> 
            >>> # Adaptive beta based on setpoint change magnitude
            >>> def adaptive_beta():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0, beta=0.5)
            ...     
            ...     prev_setpoint = 50.0
            ...     pid.set_setpoint(prev_setpoint)
            ...     
            ...     while True:
            ...         new_setpoint = get_new_setpoint()
            ...         sp_change = abs(new_setpoint - prev_setpoint)
            ...         
            ...         # Adjust beta based on setpoint change size
            ...         if sp_change > 20:  # Large change
            ...             pid.set_beta(0.0)  # Avoid overshoot
            ...         elif sp_change > 5:  # Medium change
            ...             pid.set_beta(0.3)  # Small overshoot OK
            ...         else:  # Small change
            ...             pid.set_beta(0.8)  # Fast response
            ...         
            ...         pid.set_setpoint(new_setpoint)
            ...         prev_setpoint = new_setpoint
            >>> 
            >>> # Invalid beta values
            >>> try:
            ...     oven_pid.set_beta(-0.1)  # Below 0
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
            >>> 
            >>> try:
            ...     oven_pid.set_beta(1.5)  # Above 1
            >>> except FilterConfigurationError as e:
            ...     print(f"Error: {e}")
        ```
        
        Notes:
            
            - Beta change takes effect on next update() call
            - Does not affect integral or derivative terms
            - Does not cause output discontinuity
            - Commonly set to 0.0 for temperature control
            - Commonly set to 1.0 for position/velocity control
            - Consider adaptive beta for varying setpoint dynamics
        """
        ...
    
    def set_tau_d(self, tau: float) -> None:
        """
        Set derivative filter time constant.
        
        Configures first-order low-pass filtering of the derivative term to reduce
        high-frequency noise amplification. The derivative term is naturally
        sensitive to measurement noise; filtering improves stability and reduces
        control output jitter at the cost of slightly reduced derivative action.
        
        :param tau: Time constant in seconds (> 0 enables filter, 0 disables)
        
        :raises FilterConfigurationError: If tau < 0
        :raises TypeError: If tau cannot be converted to float
        
        Filter Characteristics:
            
            Derivative filter equation:
                
                D_filtered = alpha × D_raw + (1 - alpha) × D_filtered_prev
                
                where alpha = dt / (tau + dt)
            
            Effect of tau:
                
                - tau = 0: No filtering (maximum noise amplification)
                - tau = 0.01-0.05s: Light filtering (responsive, some noise)
                - tau = 0.1-0.5s: Moderate filtering (balanced)
                - tau > 0.5s: Heavy filtering (smooth, reduced D action)
            
            Cutoff frequency:
                
                f_cutoff ≈ 1 / (2π × tau)
                
                Example: tau = 0.1s → fc ≈ 1.6 Hz
        
        Tau Selection Guidelines:
            
            Use tau = 0 when:
                
                - Measurement is very clean (low noise)
                - Maximum derivative action needed
                - Sampling rate is low relative to system dynamics
            
            Use tau = 0.01-0.1s when:
                
                - Moderate measurement noise
                - General-purpose applications
                - Sampling rate 10-100 Hz
            
            Use tau > 0.1s when:
                
                - High measurement noise
                - Derivative term causing output jitter
                - Need smooth control output
        
        Example
        -------
        ```python
            >>> from ufilter import PID
            >>> 
            >>> # No filtering - clean measurement
            >>> position_pid = PID(kp=5.0, ki=2.0, kd=0.5, fs=100.0,
            ...                    out_min=-100.0, out_max=100.0,
            ...                    tau_d_filter=0.0)  # No filter
            >>> 
            >>> # Light filtering - some noise
            >>> temp_pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                out_min=0.0, out_max=100.0,
            ...                tau_d_filter=0.05)  # fc ≈ 3 Hz
            >>> 
            >>> # Heavy filtering - noisy sensor
            >>> pressure_pid = PID(kp=1.5, ki=0.3, kd=0.2, fs=10.0,
            ...                    out_min=0.0, out_max=100.0,
            ...                    tau_d_filter=0.2)  # fc ≈ 0.8 Hz
            >>> 
            >>> # Adjust filtering at runtime
            >>> def adaptive_derivative_filtering():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0, tau_d_filter=0.05)
            ...     
            ...     # Measure noise level
            ...     noise_std = measure_noise_std()
            ...     
            ...     # Adjust filter based on noise
            ...     if noise_std > 0.5:  # High noise
            ...         pid.set_tau_d(0.2)  # Heavy filtering
            ...     elif noise_std > 0.1:  # Moderate noise
            ...         pid.set_tau_d(0.1)  # Moderate filtering
            ...     else:  # Low noise
            ...         pid.set_tau_d(0.02)  # Light filtering
            >>> 
            >>> # Demonstrating filter effect
            >>> def compare_filtering():
            ...     # Two controllers, different filtering
            ...     pid_unfiltered = PID(kp=2.0, ki=0.5, kd=0.5, fs=10.0,
            ...                          out_min=0.0, out_max=100.0, tau_d_filter=0.0)
            ...     pid_filtered = PID(kp=2.0, ki=0.5, kd=0.5, fs=10.0,
            ...                        out_min=0.0, out_max=100.0, tau_d_filter=0.1)
            ...     
            ...     # Add noise to measurement
            ...     import random
            ...     clean_signal = 50.0
            ...     
            ...     for i in range(50):
            ...         noisy_meas = clean_signal + random.gauss(0, 2.0)
            ...         
            ...         out1 = pid_unfiltered.update(noisy_meas)
            ...         out2 = pid_filtered.update(noisy_meas)
            ...         
            ...         # Unfiltered will show more output variation
            ...         if i % 10 == 0:
            ...             print(f"Unfiltered: {out1:.2f}, Filtered: {out2:.2f}")
            >>> 
            >>> # Calculate appropriate tau from cutoff frequency
            >>> def tau_from_cutoff_frequency(fc_hz):
            ...     '''Convert desired cutoff frequency to tau.'''
            ...     import math
            ...     tau = 1.0 / (2.0 * math.pi * fc_hz)
            ...     return tau
            >>> 
            >>> # Example: Want 2 Hz cutoff
            >>> tau_value = tau_from_cutoff_frequency(2.0)
            >>> temp_pid.set_tau_d(tau_value)  # tau ≈ 0.08s
            >>> 
            >>> # Mode-dependent filtering
            >>> def mode_based_filtering():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     mode = "normal"  # startup, normal, precision
            ...     
            ...     if mode == "startup":
            ...         # Fast response, less filtering
            ...         pid.set_tau_d(0.02)
            ...     elif mode == "normal":
            ...         # Balanced
            ...         pid.set_tau_d(0.1)
            ...     else:  # precision
            ...         # Smooth output, heavy filtering
            ...         pid.set_tau_d(0.3)
            >>> 
            >>> # Disable filtering
            >>> temp_pid.set_tau_d(0.0)  # No derivative filter
        ```
        
        Notes:
            
            - Tau change takes effect on next update() call
            - Does not affect proportional or integral terms
            - Larger tau = smoother derivative, more lag
            - Smaller tau = noisier derivative, less lag
            - Typical range: 0.0 to 0.5 seconds
            - Consider tau = 1/(10×fs) as starting point
        """
        ...
    
    def set_aw(self, mode: int | None = None, k_aw: float | None = None) -> None:
        """
        Configure anti-windup settings.
        
        Adjusts the controller's anti-windup strategy to prevent integrator buildup
        when the output saturates. Anti-windup is critical for systems with actuator
        limits to avoid excessive overshoot and long settling times when returning
        from saturation. Three modes are available: no anti-windup, conditional
        integration (clamping), and back-calculation.
        
        :param mode: Anti-windup mode (AW_NONE, AW_CLAMP, or AW_BACKCALC), or None to leave unchanged
        :param k_aw: Back-calculation gain for AW_BACKCALC mode (>= 0), or None to leave unchanged
        
        :raises FilterConfigurationError: If mode is invalid or k_aw < 0
        :raises TypeError: If parameters cannot be converted to appropriate types
        
        Anti-Windup Modes:
            
            AW_NONE (0): No anti-windup
                
                - Integrator continues to accumulate when saturated
                - Can lead to large overshoot when constraint is removed
                - Use only if output never saturates or for testing
            
            AW_CLAMP (1): Conditional integration (default)
                
                - Stops integration when output is saturated
                - Simple and effective for most applications
                - Minimal computational overhead
                - Recommended for general use
            
            AW_BACKCALC (2): Back-calculation with gain k_aw
                
                - Drives integrator back when saturated
                - More aggressive than clamping
                - Requires tuning of k_aw gain
                - Better performance for systems with large saturation
        
        Back-Calculation Gain (k_aw):
            
            Used only in AW_BACKCALC mode:
                
                - k_aw = 0: No back-calculation (equivalent to AW_CLAMP)
                - k_aw = 1: Standard back-calculation rate
                - k_aw > 1: Faster integrator reduction (aggressive)
                - k_aw < 1: Slower integrator reduction (conservative)
            
            Typical values: 0.5 to 2.0
            
            Selection guidelines:
                
                - Start with k_aw = 1.0
                - Increase if overshoot after saturation is excessive
                - Decrease if integrator resets too quickly
        
        Example
        -------
        ```python
            >>> from ufilter import PID
            >>> 
            >>> # Default: clamping anti-windup
            >>> pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...           out_min=0.0, out_max=100.0,
            ...           aw_mode=PID.AW_CLAMP)  # Default
            >>> 
            >>> # Back-calculation anti-windup
            >>> motor_pid = PID(kp=1.5, ki=0.8, kd=0.05, fs=50.0,
            ...                 out_min=-100.0, out_max=100.0,
            ...                 aw_mode=PID.AW_BACKCALC,
            ...                 k_aw=1.0)
            >>> 
            >>> # Change anti-windup mode at runtime
            >>> pid.set_aw(mode=PID.AW_BACKCALC, k_aw=1.5)
            >>> 
            >>> # Demonstrating anti-windup necessity
            >>> def demonstrate_windup():
            ...     # Two controllers, with and without anti-windup
            ...     pid_no_aw = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                     out_min=0.0, out_max=100.0,
            ...                     aw_mode=PID.AW_NONE)
            ...     
            ...     pid_with_aw = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                       out_min=0.0, out_max=100.0,
            ...                       aw_mode=PID.AW_CLAMP)
            ...     
            ...     # Large setpoint step with slow system
            ...     pid_no_aw.set_setpoint(100.0)
            ...     pid_with_aw.set_setpoint(100.0)
            ...     
            ...     # Simulate: output saturates, integrator builds up
            ...     for i in range(100):
            ...         measurement = i * 0.5  # Slow system
            ...         
            ...         out1 = pid_no_aw.update(measurement)
            ...         out2 = pid_with_aw.update(measurement)
            ...         
            ...         # pid_no_aw will show larger overshoot later
            >>> 
            >>> # Application-specific anti-windup selection
            >>> def select_antiwindup_strategy():
            ...     # Fast system with frequent saturation
            ...     servo = PID(kp=5.0, ki=2.0, kd=0.5, fs=100.0,
            ...                 out_min=-100.0, out_max=100.0)
            ...     servo.set_aw(mode=PID.AW_BACKCALC, k_aw=1.5)  # Aggressive
            ...     
            ...     # Slow system with occasional saturation
            ...     heater = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                  out_min=0.0, out_max=100.0)
            ...     heater.set_aw(mode=PID.AW_CLAMP)  # Simple clamping
            ...     
            ...     # System that should never saturate
            ...     flow = PID(kp=1.0, ki=0.2, kd=0.05, fs=10.0,
            ...                out_min=-50.0, out_max=50.0)
            ...     flow.set_aw(mode=PID.AW_NONE)  # No anti-windup needed
            >>> 
            >>> # Adaptive anti-windup based on saturation frequency
            >>> def adaptive_antiwindup():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     saturation_count = 0
            ...     total_updates = 0
            ...     
            ...     while True:
            ...         measurement = read_sensor()
            ...         output = pid.update(measurement)
            ...         
            ...         # Check if saturated
            ...         if output >= 99.9 or output <= 0.1:
            ...             saturation_count += 1
            ...         
            ...         total_updates += 1
            ...         
            ...         # Adjust anti-windup every 100 samples
            ...         if total_updates % 100 == 0:
            ...             saturation_rate = saturation_count / 100.0
            ...             
            ...             if saturation_rate > 0.5:  # Frequent saturation
            ...                 pid.set_aw(mode=PID.AW_BACKCALC, k_aw=2.0)
            ...             elif saturation_rate > 0.1:  # Occasional saturation
            ...                 pid.set_aw(mode=PID.AW_CLAMP)
            ...             else:  # Rare saturation
            ...                 pid.set_aw(mode=PID.AW_NONE)
            ...             
            ...             saturation_count = 0
            >>> 
            >>> # Tuning back-calculation gain
            >>> def tune_backcalc_gain():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0,
            ...               aw_mode=PID.AW_BACKCALC, k_aw=1.0)
            ...     
            ...     # Test different k_aw values
            ...     for k_aw_test in [0.5, 1.0, 1.5, 2.0]:
            ...         pid.set_aw(k_aw=k_aw_test)
            ...         pid.reset()
            ...         
            ...         # Measure overshoot after saturation
            ...         overshoot = simulate_step_response(pid)
            ...         print(f"k_aw={k_aw_test}: overshoot={overshoot:.1f}%")
            >>> 
            >>> # Change only k_aw, keep mode
            >>> motor_pid.set_aw(k_aw=2.0)  # mode unchanged
            >>> 
            >>> # Change only mode, keep k_aw
            >>> motor_pid.set_aw(mode=PID.AW_CLAMP)  # k_aw unchanged
        ```
        
        Notes:
            
            - Settings take effect on next update() call
            - AW_CLAMP is recommended for most applications
            - AW_BACKCALC provides better performance but needs tuning
            - AW_NONE should only be used if saturation never occurs
            - k_aw has no effect in AW_NONE or AW_CLAMP modes
            - Consider actuator dynamics when choosing anti-windup
        """
        ...
    
    def preload_integrator(self, i0: float) -> None:
        """
        Manually set integrator state (clamped to i_min/i_max).
        
        Directly sets the controller's integrator value, enabling initialization
        to a specific state or compensation for known disturbances. The provided
        value is automatically clamped to the configured integrator limits
        [i_min, i_max]. Useful for bumpless initialization, feed-forward
        compensation, or recovering from reset conditions.
        
        :param i0: Desired integrator value (will be clamped to [i_min, i_max])
        
        :raises TypeError: If i0 cannot be converted to float
        
        Use Cases:
            
            Bumpless initialization:
                
                - Set integrator to match expected steady-state output
                - Prevents initial output transient
                - Example: Start heater at 30% power → preload integrator to 30.0
            
            Feed-forward compensation:
                
                - Preload known disturbance compensation
                - Reduces settling time for predictable loads
                - Example: Known gravity compensation in vertical motion
            
            State recovery:
                
                - Restore controller state after temporary shutdown
                - Maintain continuity in interrupted control
                - Example: Resume from saved state after power cycle
            
            Manual-to-auto transfer:
                
                - Initialize integrator to match manual output
                - Alternative to tracking mode for simple cases
                - Example: Operator manually set 50% → preload to 50.0
        
        Example
        -------
        ```python
            >>> from ufilter import PID
            >>> 
            >>> # Bumpless startup for heater
            >>> heater_pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                  out_min=0.0, out_max=100.0)
            >>> heater_pid.set_setpoint(25.0)
            >>> 
            >>> # System at 20°C, expect ~30% power needed
            >>> heater_pid.preload_integrator(30.0)
            >>> 
            >>> # First update will start near 30% output
            >>> initial_temp = 20.0
            >>> power = heater_pid.update(initial_temp)
            >>> print(f"Initial power: {power:.1f}%")
            >>> # Initial power: 32.5% (close to preloaded value)
            >>> 
            >>> # Feed-forward for gravity compensation
            >>> def gravity_compensation():
            ...     # Vertical motion controller
            ...     pid = PID(kp=5.0, ki=2.0, kd=0.5, fs=100.0,
            ...               out_min=-100.0, out_max=100.0)
            ...     
            ...     # Known gravity compensation needed: 35% thrust
            ...     gravity_compensation_value = 35.0
            ...     pid.preload_integrator(gravity_compensation_value)
            ...     
            ...     # PID will regulate around this baseline
            ...     pid.set_setpoint(10.0)  # Target 10m height
            >>> 
            >>> # State recovery after power cycle
            >>> def save_and_restore_state():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     # Run for a while
            ...     for i in range(100):
            ...         measurement = read_sensor()
            ...         output = pid.update(measurement)
            ...     
            ...     # Save integrator state before shutdown
            ...     saved_integrator = pid.u - (pid.kp * error) - (pid.kd * derivative)
            ...     save_to_nvram(saved_integrator)
            ...     
            ...     # ... power cycle ...
            ...     
            ...     # Restore state after restart
            ...     new_pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                   out_min=0.0, out_max=100.0)
            ...     restored_value = load_from_nvram()
            ...     new_pid.preload_integrator(restored_value)
            >>> 
            >>> # Manual-to-auto transfer (simple case)
            >>> def simple_bumpless_transfer():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     pid.set_setpoint(50.0)
            ...     
            ...     # Operator has been running manually at 45%
            ...     manual_output = 45.0
            ...     
            ...     # Transfer to auto: preload integrator
            ...     pid.preload_integrator(manual_output)
            ...     
            ...     # First auto update will be close to manual output
            ...     measurement = read_sensor()
            ...     auto_output = pid.update(measurement)
            ...     print(f"Manual: {manual_output:.1f}%, Auto: {auto_output:.1f}%")
            >>> 
            >>> # Clamping demonstration
            >>> def demonstrate_clamping():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0,
            ...               i_min=0.0, i_max=100.0)
            ...     
            ...     # Try to preload beyond limits
            ...     pid.preload_integrator(150.0)  # Above i_max
            ...     # Integrator will be clamped to 100.0
            ...     
            ...     pid.preload_integrator(-50.0)  # Below i_min
            ...     # Integrator will be clamped to 0.0
            >>> 
            >>> # Adaptive baseline adjustment
            >>> def adaptive_baseline():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     # Measure steady-state disturbance
            ...     disturbance = measure_disturbance()
            ...     
            ...     # Preload to compensate
            ...     pid.preload_integrator(disturbance)
            ...     
            ...     # PID now regulates around new baseline
            >>> 
            >>> # Multi-phase initialization
            >>> def multi_phase_startup():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     # Phase 1: Warmup at 20%
            ...     pid.preload_integrator(20.0)
            ...     pid.set_setpoint(phase1_target)
            ...     # ... run phase 1 ...
            ...     
            ...     # Phase 2: Production at 50%
            ...     pid.preload_integrator(50.0)
            ...     pid.set_setpoint(phase2_target)
            ...     # ... run phase 2 ...
        ```
        
        Notes:
            
            - Provided value is clamped to [i_min, i_max]
            - Does not affect proportional or derivative terms
            - Takes effect immediately (next update() uses new value)
            - Use with caution - incorrect preload can cause transients
            - For true bumpless transfer, consider tracking mode
            - Can be called multiple times to adjust integrator
        """
        ...
    
    def start_tracking(self, u_manual: float) -> None:
        """
        Enable tracking mode to follow external output.
        
        Activates tracking mode where the controller's integrator is continuously
        adjusted to make the PID output match an external (manual) output value.
        This enables perfect bumpless transfer when switching from manual to
        automatic control - the controller output matches the manual output at
        the moment of transfer, eliminating output discontinuities.
        
        :param u_manual: External output value to track
        
        :raises TypeError: If u_manual cannot be converted to float
        
        Tracking Mode Behavior:
            
            While tracking is active:
                
                - Proportional and derivative terms computed normally
                - Integrator adjusted to make: u_PID = u_manual
                - Integrator equation: I = u_manual - P - D
                - Controller output forced to u_manual
                - No actual control action (open loop)
            
            On stop_tracking():
                
                - Integrator retains last tracked value
                - Controller resumes normal closed-loop operation
                - Output continuous (no bump or step)
        
        Use Cases:
            
            Manual-to-auto transfer:
                
                - Operator controls manually, PID tracks
                - Switch to auto: PID output = last manual output
                - Zero output discontinuity at transfer
            
            External control handoff:
                
                - Another controller manages output
                - PID tracks for bumpless takeover
                - Smooth control authority transfer
            
            Initialization with unknown steady-state:
                
                - System running under external control
                - PID tracks to learn required output
                - Transfer when PID is synchronized
            
            Safety interlocks:
                
                - Safety system overrides PID
                - PID tracks safety output
                - Bumpless return when safe
        
        Example
        -------
        ```python
            >>> from ufilter import PID
            >>> 
            >>> # Manual-to-auto bumpless transfer
            >>> pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...           out_min=0.0, out_max=100.0)
            >>> pid.set_setpoint(50.0)
            >>> 
            >>> manual_mode = True
            >>> manual_output = 30.0
            >>> 
            >>> while True:
            ...     measurement = read_sensor()
            ...     
            ...     if manual_mode:
            ...         # Manual mode: operator controls
            ...         manual_output = read_operator_input()
            ...         
            ...         # PID tracks manual output
            ...         pid.start_tracking(manual_output)
            ...         
            ...         output = manual_output
            ...     else:
            ...         # Auto mode: PID controls
            ...         pid.stop_tracking()
            ...         output = pid.update(measurement)
            ...     
            ...     apply_output(output)
            ...     
            ...     # When switching manual→auto, no output bump
            >>> 
            >>> # External controller handoff
            >>> def external_handoff():
            ...     # Two controllers for same actuator
            ...     pid_primary = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                       out_min=0.0, out_max=100.0)
            ...     pid_backup = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                      out_min=0.0, out_max=100.0)
            ...     
            ...     use_primary = True
            ...     
            ...     while True:
            ...         measurement = read_sensor()
            ...         
            ...         if use_primary:
            ...             # Primary active, backup tracks
            ...             output_primary = pid_primary.update(measurement)
            ...             pid_backup.start_tracking(output_primary)
            ...             output = output_primary
            ...         else:
            ...             # Backup active, primary tracks
            ...             output_backup = pid_backup.update(measurement)
            ...             pid_primary.start_tracking(output_backup)
            ...             output = output_backup
            ...         
            ...         apply_output(output)
            ...         
            ...         # Can switch controllers without bump
            >>> 
            >>> # Safety override with tracking
            >>> def safety_override_system():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     pid.set_setpoint(75.0)
            ...     
            ...     while True:
            ...         measurement = read_sensor()
            ...         safe = check_safety_conditions()
            ...         
            ...         if safe:
            ...             # Normal operation
            ...             pid.stop_tracking()
            ...             output = pid.update(measurement)
            ...         else:
            ...             # Safety override: reduce output
            ...             safe_output = calculate_safe_output()
            ...             pid.start_tracking(safe_output)
            ...             output = safe_output
            ...         
            ...         apply_output(output)
            ...         
            ...         # Bumpless transition safe ↔ normal
            >>> 
            >>> # Learning phase before control
            >>> def learning_phase():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     pid.set_setpoint(60.0)
            ...     
            ...     # Phase 1: Learn by tracking existing control
            ...     print("Learning phase...")
            ...     for i in range(100):
            ...         measurement = read_sensor()
            ...         existing_output = read_existing_controller()
            ...         
            ...         pid.start_tracking(existing_output)
            ...         pid.update(measurement)  # Update for tracking
            ...     
            ...     # Phase 2: Take over control
            ...     print("Taking over control...")
            ...     pid.stop_tracking()
            ...     
            ...     # Now PID controls with no bump
            ...     while True:
            ...         measurement = read_sensor()
            ...         output = pid.update(measurement)
            ...         apply_output(output)
            >>> 
            >>> # Cascade control with tracking
            >>> def cascade_control():
            ...     # Master PID sets setpoint for slave
            ...     master_pid = PID(kp=1.0, ki=0.2, kd=0.05, fs=10.0,
            ...                      out_min=0.0, out_max=100.0)
            ...     slave_pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=100.0,
            ...                     out_min=0.0, out_max=100.0)
            ...     
            ...     cascade_enabled = True
            ...     
            ...     while True:
            ...         outer_measurement = read_outer_sensor()
            ...         inner_measurement = read_inner_sensor()
            ...         
            ...         if cascade_enabled:
            ...             # Cascade: master controls slave setpoint
            ...             inner_setpoint = master_pid.update(outer_measurement)
            ...             slave_pid.set_setpoint(inner_setpoint)
            ...             slave_pid.stop_tracking()
            ...             output = slave_pid.update(inner_measurement)
            ...         else:
            ...             # Single loop: slave tracks master output
            ...             master_output = master_pid.update(outer_measurement)
            ...             slave_pid.start_tracking(master_output)
            ...             output = master_output
            ...         
            ...         apply_output(output)
            >>> 
            >>> # Gain-switched controller with tracking
            >>> def gain_switched_control():
            ...     # Two PIDs with different tuning
            ...     pid_fast = PID(kp=5.0, ki=2.0, kd=0.5, fs=50.0,
            ...                    out_min=-100.0, out_max=100.0)
            ...     pid_smooth = PID(kp=1.0, ki=0.3, kd=0.05, fs=50.0,
            ...                      out_min=-100.0, out_max=100.0)
            ...     
            ...     use_fast = True
            ...     
            ...     while True:
            ...         measurement = read_sensor()
            ...         error_magnitude = abs(measurement - setpoint)
            ...         
            ...         # Switch based on error
            ...         if error_magnitude > 10:
            ...             # Use fast controller
            ...             if not use_fast:
            ...                 pid_smooth.start_tracking(pid_fast.u)
            ...             use_fast = True
            ...         else:
            ...             # Use smooth controller
            ...             if use_fast:
            ...                 pid_fast.start_tracking(pid_smooth.u)
            ...             use_fast = False
            ...         
            ...         if use_fast:
            ...             pid_smooth.start_tracking(pid_fast.u)
            ...             output = pid_fast.update(measurement)
            ...         else:
            ...             pid_fast.start_tracking(pid_smooth.u)
            ...             output = pid_smooth.update(measurement)
            ...         
            ...         apply_output(output)
        ```
        
        Notes:
            
            - Tracking overrides normal PID computation
            - Controller output forced to u_manual while tracking
            - Integrator adjusted to maintain u_manual = P + I + D
            - Must call update() even while tracking (to update P and D terms)
            - Call stop_tracking() to resume normal control
            - Tracking mode persists until stop_tracking() or reset()
            - u_manual not clamped (tracking can exceed output limits)
        """
        ...
    
    def stop_tracking(self) -> None:
        """
        Disable tracking mode, return to normal PID operation.
        
        Deactivates tracking mode, allowing the controller to resume normal
        closed-loop operation. The integrator retains its last tracked value,
        ensuring output continuity (no bump) when transitioning from tracking
        to normal control.
        
        :return: None
        
        Behavior on Stop:
            
            - Tracking mode flag cleared
            - Integrator state preserved from last tracking update
            - Next update() computes normal PID output
            - Output continuous at transition (bumpless)
            - Proportional and derivative terms resume normal computation
        
        Transition Continuity:
            
            At the moment of stop_tracking():
                
                - Last tracked output: u_manual
                - Integrator state: I = u_manual - P - D
                - First normal output: u_normal = P + I + D = u_manual
                - Result: No output discontinuity
        
        Use Cases:
            
            - Complete manual-to-auto transfer
            - Resume control after external override
            - End of initialization/learning phase
            - Return from safety override
        
        Example
        -------
        ```python
            >>> from ufilter import PID
            >>> 
            >>> # Basic tracking cycle
            >>> pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...           out_min=0.0, out_max=100.0)
            >>> pid.set_setpoint(50.0)
            >>> 
            >>> # Enable tracking
            >>> manual_output = 35.0
            >>> pid.start_tracking(manual_output)
            >>> 
            >>> # Update while tracking
            >>> for i in range(10):
            ...     measurement = read_sensor()
            ...     pid.update(measurement)  # Updates P and D, adjusts I
            >>> 
            >>> # Stop tracking, resume control
            >>> pid.stop_tracking()
            >>> 
            >>> # Next update computes normal PID (no output bump)
            >>> measurement = read_sensor()
            >>> output = pid.update(measurement)
            >>> 
            >>> # State machine for manual/auto control
            >>> def manual_auto_state_machine():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     state = "MANUAL"  # MANUAL or AUTO
            ...     
            ...     while True:
            ...         measurement = read_sensor()
            ...         mode_switch = read_mode_switch()
            ...         
            ...         # State transitions
            ...         if mode_switch == "AUTO" and state == "MANUAL":
            ...             # Manual → Auto: stop tracking
            ...             pid.stop_tracking()
            ...             state = "AUTO"
            ...             print("Switched to AUTO mode")
            ...         
            ...         elif mode_switch == "MANUAL" and state == "AUTO":
            ...             # Auto → Manual: will start tracking next iteration
            ...             state = "MANUAL"
            ...             print("Switched to MANUAL mode")
            ...         
            ...         # State actions
            ...         if state == "MANUAL":
            ...             manual_output = read_operator_input()
            ...             pid.start_tracking(manual_output)
            ...             output = manual_output
            ...         else:  # AUTO
            ...             output = pid.update(measurement)
            ...         
            ...         apply_output(output)
            >>> 
            >>> # Conditional auto-enable
            >>> def conditional_auto_enable():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     pid.set_setpoint(60.0)
            ...     
            ...     auto_enabled = False
            ...     
            ...     while True:
            ...         measurement = read_sensor()
            ...         
            ...         # Check if conditions met for auto control
            ...         in_range = abs(measurement - 60.0) < 5.0
            ...         system_stable = check_stability()
            ...         
            ...         if in_range and system_stable and not auto_enabled:
            ...             # Enable auto control
            ...             pid.stop_tracking()
            ...             auto_enabled = True
            ...             print("Auto control enabled")
            ...         
            ...         if auto_enabled:
            ...             output = pid.update(measurement)
            ...         else:
            ...             # Manual control, PID tracks
            ...             manual_output = get_manual_output()
            ...             pid.start_tracking(manual_output)
            ...             output = manual_output
            ...         
            ...         apply_output(output)
            >>> 
            >>> # Safety system with auto-resume
            >>> def safety_with_auto_resume():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     in_override = False
            ...     
            ...     while True:
            ...         measurement = read_sensor()
            ...         safe = check_safety()
            ...         
            ...         if not safe and not in_override:
            ...             # Enter override
            ...             print("Safety override activated")
            ...             in_override = True
            ...         
            ...         if safe and in_override:
            ...             # Exit override
            ...             pid.stop_tracking()
            ...             print("Resuming normal control")
            ...             in_override = False
            ...         
            ...         if in_override:
            ...             safe_output = calculate_safe_output()
            ...             pid.start_tracking(safe_output)
            ...             output = safe_output
            ...         else:
            ...             output = pid.update(measurement)
            ...         
            ...         apply_output(output)
            >>> 
            >>> # Timed tracking release
            >>> def timed_auto_transfer():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     # Track for 5 seconds, then auto
            ...     import time
            ...     start_time = time.time()
            ...     tracking_duration = 5.0
            ...     
            ...     manual_output = 40.0
            ...     pid.start_tracking(manual_output)
            ...     
            ...     while True:
            ...         measurement = read_sensor()
            ...         elapsed = time.time() - start_time
            ...         
            ...         if elapsed >= tracking_duration:
            ...             # Time's up, enable auto
            ...             pid.stop_tracking()
            ...             
            ...             # Now in auto mode
            ...             output = pid.update(measurement)
            ...         else:
            ...             # Still tracking
            ...             pid.update(measurement)  # Update for tracking
            ...             output = manual_output
            ...         
            ...         apply_output(output)
            ...         time.sleep(0.1)
        ```
        
        Notes:
            
            - Safe to call even if not tracking (no effect)
            - Integrator state preserved for bumpless transition
            - Next update() after stop produces continuous output
            - No need to track exit order with other method calls
            - Can re-enable tracking later with start_tracking()
        """
        ...
    
    def reset(self) -> None:
        """
        Reset controller to initial state.
        
        Clears all internal controller state, returning it to the condition
        immediately after construction. This is useful when starting control
        of a different process, recovering from unusual conditions, or
        restarting after a significant disturbance. All accumulated error
        and history information is discarded.
        
        :return: None
        
        State Cleared by Reset:
            
            - Integrator (accumulated error): Set to 0
            - Previous measurement (for derivative): Cleared
            - Derivative filter state: Cleared
            - Controller output: Set to 0
            - Sample counter: Reset to 0
            - Tracking mode: Disabled
            - Setpoint: Preserved (not reset)
            - Gains and limits: Preserved (not reset)
        
        Effects:
            
            - Next update() will compute derivative assuming zero previous measurement
            - Integrator starts from zero (may cause transient if non-zero needed)
            - Output returns to zero until next update()
            - No memory of previous control actions
        
        When to Use Reset:
            
            Required:
                
                - Switching to control different process
                - Process undergoes discontinuous state change
                - Long period of inactivity (controller was stopped)
                - Recovering from fault or error condition
            
            Optional but recommended:
                
                - Large setpoint changes (> 50% of range)
                - Significant load or disturbance changes
                - After tuning gain changes
                - Mode transitions with different dynamics
            
            Usually not needed:
                
                - Normal setpoint changes
                - Temporary measurement dropout
                - Brief control interruptions
        
        Example
        -------
        ```python
            >>> from ufilter import PID
            >>> 
            >>> # Create and run controller
            >>> pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...           out_min=0.0, out_max=100.0)
            >>> pid.set_setpoint(50.0)
            >>> 
            >>> # Run for a while
            >>> for i in range(100):
            ...     measurement = read_sensor()
            ...     output = pid.update(measurement)
            >>> 
            >>> # Reset before switching processes
            >>> pid.reset()
            >>> pid.set_setpoint(75.0)  # New target
            >>> 
            >>> # Start fresh
            >>> measurement = read_sensor()
            >>> output = pid.update(measurement)
            >>> 
            >>> # Multi-process control
            >>> def multi_process_controller():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     processes = ["A", "B", "C"]
            ...     current_process = "A"
            ...     
            ...     for process in processes:
            ...         # Reset when switching processes
            ...         pid.reset()
            ...         
            ...         # Configure for new process
            ...         setpoint = get_process_setpoint(process)
            ...         pid.set_setpoint(setpoint)
            ...         
            ...         # Control this process
            ...         for i in range(100):
            ...             measurement = read_process_sensor(process)
            ...             output = pid.update(measurement)
            ...             apply_to_process(process, output)
            >>> 
            >>> # Error recovery
            >>> def error_recovery_example():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     pid.set_setpoint(60.0)
            ...     
            ...     while True:
            ...         try:
            ...             measurement = read_sensor()
            ...             output = pid.update(measurement)
            ...             apply_output(output)
            ...         
            ...         except SensorError:
            ...             # Sensor failed, stop control
            ...             apply_output(0.0)
            ...             
            ...             # Wait for sensor recovery
            ...             wait_for_sensor_recovery()
            ...             
            ...             # Reset PID before resuming
            ...             pid.reset()
            ...             print("PID reset after sensor recovery")
            >>> 
            >>> # Batch process control
            >>> def batch_process_control():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     while True:
            ...         # Wait for new batch
            ...         wait_for_batch_start()
            ...         
            ...         # Reset for new batch
            ...         pid.reset()
            ...         pid.set_setpoint(get_batch_temperature())
            ...         
            ...         # Control this batch
            ...         while batch_in_progress():
            ...             temp = read_temperature()
            ...             power = pid.update(temp)
            ...             set_heater(power)
            ...         
            ...         # Batch complete
            ...         set_heater(0.0)
            >>> 
            >>> # Mode switching with reset
            >>> def mode_switching():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     mode = "startup"
            ...     
            ...     if mode == "startup":
            ...         # Startup mode
            ...         pid.reset()
            ...         pid.set_gains(kp=1.0, ki=0.2, kd=0.05)
            ...         pid.set_setpoint(30.0)
            ...     
            ...     elif mode == "production":
            ...         # Production mode - reset for clean start
            ...         pid.reset()
            ...         pid.set_gains(kp=2.0, ki=0.5, kd=0.1)
            ...         pid.set_setpoint(75.0)
            ...     
            ...     elif mode == "shutdown":
            ...         # Shutdown - reset and ramp down
            ...         pid.reset()
            ...         pid.set_gains(kp=0.5, ki=0.1, kd=0.0)
            ...         pid.set_setpoint(0.0)
            >>> 
            >>> # Reset after parameter changes
            >>> def reset_after_tuning():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     # Run with initial gains
            ...     for i in range(100):
            ...         measurement = read_sensor()
            ...         output = pid.update(measurement)
            ...     
            ...     # Change gains significantly
            ...     pid.set_gains(kp=5.0, ki=2.0, kd=0.5)
            ...     
            ...     # Reset to avoid transient from old integrator state
            ...     pid.reset()
            ...     
            ...     # Continue with new gains
            ...     for i in range(100):
            ...         measurement = read_sensor()
            ...         output = pid.update(measurement)
            >>> 
            >>> # Selective reset (manual implementation)
            >>> def selective_reset():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     pid.set_setpoint(50.0)
            ...     
            ...     # Run controller
            ...     for i in range(100):
            ...         measurement = read_sensor()
            ...         output = pid.update(measurement)
            ...     
            ...     # Want to reset only integrator, keep setpoint and gains
            ...     current_setpoint = pid.setpoint
            ...     current_kp, current_ki, current_kd = pid.kp, pid.ki, pid.kd
            ...     
            ...     pid.reset()  # Clears everything
            ...     
            ...     # Restore what we want to keep
            ...     pid.set_setpoint(current_setpoint)
            ...     # Gains automatically preserved (not affected by reset)
        ```
        
        Notes:
            
            - Setpoint is preserved (not reset)
            - Gains (kp, ki, kd) are preserved
            - Output limits are preserved
            - Beta, tau_d, anti-windup settings are preserved
            - Only dynamic state is cleared
            - Safe to call at any time
            - No output is applied by reset() itself
        """
        ...
    
    @micropython.native
    def update(self, meas: float, dt_s: float | None = None) -> float:
        """
        Compute PID control output.
        
        Executes one iteration of the PID control algorithm, computing the control
        output based on the current measurement, setpoint, and accumulated error.
        Implements proportional-on-measurement with setpoint weighting (beta),
        derivative-on-measurement to avoid kick, optional derivative filtering,
        and anti-windup protection. Returns the computed output clamped to the
        configured limits.
        
        :param meas: Current process measurement (sensor reading)
        :param dt_s: Time step in seconds. Required if fs not provided in constructor.
                     Ignored if fs was provided (uses 1/fs instead).
        
        :return: Control output, clamped to [out_min, out_max]
        
        :raises FilterOperationError: If dt_s not provided and fs not set
        :raises TypeError: If meas or dt_s cannot be converted to float
        
        Control Algorithm:
            
            Error terms:
                
                e_p = beta × setpoint - measurement  # Proportional error
                e_i = setpoint - measurement         # Integral error
                de = -(measurement - measurement_prev) / dt  # Derivative (on measurement)
            
            Control output:
                
                P = kp × e_p
                I = ki × ∫e_i dt  (with anti-windup)
                D = kd × de  (with optional filtering)
                
                u = P + I + D
                
                u_output = clamp(u, out_min, out_max)
        
        Timing Modes:
            
            Fixed sampling rate (fs provided in constructor):
                
                - dt_s parameter ignored
                - Uses dt = 1/fs for all calculations
                - Recommended for constant-rate control loops
                - Example: fs=10.0 → dt=0.1s
            
            Variable sampling rate (fs=None in constructor):
                
                - dt_s parameter required on each update()
                - Uses provided dt_s for calculations
                - Useful for irregular sampling or event-driven control
                - Example: update(meas, dt_s=0.105)
        
        First Update Behavior:
            
            On the very first call to update():
                
                - Derivative term is zero (no previous measurement)
                - Integrator starts from preloaded value (or zero)
                - Proportional term computed normally
                - Output may differ from subsequent calls
        
        Performance Characteristics:
            
            - Execution time: ~50-100 µs (depends on platform and anti-windup mode)
            - Decorated with @micropython.native for speed
            - No memory allocation (in-place computation)
            - Deterministic execution time
        
        Example
        -------
        ```python
            >>> from ufilter import PID
            >>> import time
            >>> 
            >>> # Fixed sampling rate controller
            >>> pid_fixed = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                 out_min=0.0, out_max=100.0)
            >>> pid_fixed.set_setpoint(25.0)
            >>> 
            >>> # Control loop at 10 Hz
            >>> while True:
            ...     temp = read_thermometer()
            ...     power = pid_fixed.update(temp)  # No dt needed
            ...     set_heater(power)
            ...     time.sleep(0.1)  # 10 Hz
            >>> 
            >>> # Variable sampling rate controller
            >>> pid_variable = PID(kp=2.0, ki=0.5, kd=0.1, fs=None,
            ...                    out_min=0.0, out_max=100.0)
            >>> pid_variable.set_setpoint(50.0)
            >>> 
            >>> # Control loop with measured dt
            >>> last_time = time.time()
            >>> while True:
            ...     current_time = time.time()
            ...     dt = current_time - last_time
            ...     last_time = current_time
            ...     
            ...     measurement = read_sensor()
            ...     output = pid_variable.update(measurement, dt_s=dt)
            ...     apply_output(output)
            >>> 
            >>> # Temperature control example
            >>> def temperature_control():
            ...     oven_pid = PID(kp=3.0, ki=0.8, kd=0.2, fs=10.0,
            ...                    out_min=0.0, out_max=100.0,
            ...                    beta=0.3, tau_d_filter=0.1)
            ...     
            ...     oven_pid.set_setpoint(180.0)  # 180°C target
            ...     
            ...     while True:
            ...         current_temp = read_thermocouple()
            ...         heater_power = oven_pid.update(current_temp)
            ...         
            ...         print(f"Temp: {current_temp:.1f}°C, Power: {heater_power:.1f}%")
            ...         
            ...         set_heater_pwm(heater_power)
            ...         time.sleep(0.1)  # 10 Hz
            >>> 
            >>> # Motor speed control
            >>> def motor_speed_control():
            ...     motor_pid = PID(kp=1.5, ki=0.8, kd=0.05, fs=50.0,
            ...                     out_min=-100.0, out_max=100.0,
            ...                     aw_mode=PID.AW_BACKCALC, k_aw=1.0)
            ...     
            ...     target_rpm = 1500.0
            ...     motor_pid.set_setpoint(target_rpm)
            ...     
            ...     while True:
            ...         current_rpm = read_encoder()
            ...         pwm_output = motor_pid.update(current_rpm)
            ...         
            ...         # Output is ±100% PWM duty cycle
            ...         set_motor_pwm(pwm_output)
            ...         time.sleep(0.02)  # 50 Hz
            >>> 
            >>> # Level control with noise
            >>> def level_control():
            ...     level_pid = PID(kp=2.0, ki=0.3, kd=0.5, fs=5.0,
            ...                     out_min=0.0, out_max=100.0,
            ...                     tau_d_filter=0.2)  # Filter noisy derivative
            ...     
            ...     level_pid.set_setpoint(50.0)  # 50% level target
            ...     
            ...     while True:
            ...         level_percent = read_level_sensor()
            ...         valve_position = level_pid.update(level_percent)
            ...         
            ...         set_valve(valve_position)
            ...         time.sleep(0.2)  # 5 Hz
            >>> 
            >>> # Event-driven control (variable dt)
            >>> def event_driven_control():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=None,
            ...               out_min=0.0, out_max=100.0)
            ...     pid.set_setpoint(60.0)
            ...     
            ...     last_time = time.time()
            ...     
            ...     while True:
            ...         # Wait for sensor event (irregular timing)
            ...         wait_for_sensor_ready()
            ...         
            ...         current_time = time.time()
            ...         dt = current_time - last_time
            ...         last_time = current_time
            ...         
            ...         measurement = read_sensor()
            ...         output = pid.update(measurement, dt_s=dt)
            ...         apply_output(output)
            >>> 
            >>> # Tracking mode integration
            >>> def manual_auto_control():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     pid.set_setpoint(50.0)
            ...     
            ...     manual_mode = False
            ...     manual_output = 30.0
            ...     
            ...     while True:
            ...         measurement = read_sensor()
            ...         
            ...         if manual_mode:
            ...             # Track manual output
            ...             manual_output = read_manual_input()
            ...             pid.start_tracking(manual_output)
            ...             pid.update(measurement)  # Update for tracking
            ...             output = manual_output
            ...         else:
            ...             # Auto mode
            ...             pid.stop_tracking()
            ...             output = pid.update(measurement)
            ...         
            ...         apply_output(output)
            ...         time.sleep(0.1)
            >>> 
            >>> # Data logging
            >>> def logged_control():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     pid.set_setpoint(75.0)
            ...     
            ...     log_file = open("control_log.csv", "w")
            ...     log_file.write("time,measurement,output,setpoint\\n")
            ...     
            ...     start_time = time.time()
            ...     
            ...     while True:
            ...         measurement = read_sensor()
            ...         output = pid.update(measurement)
            ...         
            ...         elapsed = time.time() - start_time
            ...         log_file.write(f"{elapsed:.2f},{measurement:.2f},{output:.2f},{pid.setpoint:.2f}\\n")
            ...         
            ...         apply_output(output)
            ...         time.sleep(0.1)
            >>> 
            >>> # Cascade control
            >>> def cascade_control():
            ...     # Outer loop: Position control
            ...     position_pid = PID(kp=1.0, ki=0.2, kd=0.05, fs=10.0,
            ...                        out_min=-50.0, out_max=50.0)  # Output: velocity setpoint
            ...     
            ...     # Inner loop: Velocity control
            ...     velocity_pid = PID(kp=2.0, ki=1.0, kd=0.1, fs=50.0,
            ...                        out_min=-100.0, out_max=100.0)  # Output: motor PWM
            ...     
            ...     position_pid.set_setpoint(100.0)  # Target position
            ...     
            ...     # Outer loop runs at 10 Hz
            ...     for outer_tick in range(100):
            ...         position = read_position()
            ...         velocity_setpoint = position_pid.update(position)
            ...         
            ...         velocity_pid.set_setpoint(velocity_setpoint)
            ...         
            ...         # Inner loop runs 5× faster (50 Hz)
            ...         for inner_tick in range(5):
            ...             velocity = read_velocity()
            ...             pwm = velocity_pid.update(velocity)
            ...             set_motor_pwm(pwm)
            ...             time.sleep(0.02)  # 50 Hz
            >>> 
            >>> # Error handling
            >>> def robust_control():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     pid.set_setpoint(50.0)
            ...     
            ...     while True:
            ...         try:
            ...             measurement = read_sensor()
            ...             
            ...             # Validate measurement
            ...             if not (0.0 <= measurement <= 100.0):
            ...                 raise ValueError("Measurement out of range")
            ...             
            ...             output = pid.update(measurement)
            ...             apply_output(output)
            ...         
            ...         except Exception as e:
            ...             print(f"Control error: {e}")
            ...             apply_output(0.0)  # Safe state
            ...         
            ...         time.sleep(0.1)
            >>> 
            >>> # Missing dt error demonstration
            >>> try:
            ...     pid_no_fs = PID(kp=2.0, ki=0.5, kd=0.1, fs=None,
            ...                     out_min=0.0, out_max=100.0)
            ...     output = pid_no_fs.update(50.0)  # Missing dt_s
            >>> except FilterOperationError as e:
            ...     print(f"Error: {e}")
            ...     # Must provide dt_s when fs=None
        ```
        
        Notes:
            
            - Call at consistent rate when using fixed fs
            - Provide accurate dt_s when using variable rate
            - First call has no derivative (no previous measurement)
            - Output automatically clamped to [out_min, out_max]
            - Tracking mode overrides normal computation
            - Integrator managed according to anti-windup mode
            - Derivative filtered if tau_d > 0
        """
        ...
    
    def set_setpoint(self, sp: float, keep_output: bool = False) -> None:
        """
        Change controller setpoint.
        
        Updates the target value (setpoint) for the controller. Optionally
        implements bumpless setpoint change by adjusting the integrator to
        maintain the current output, preventing output discontinuities when
        the setpoint changes. This is useful for smooth setpoint ramping or
        when setpoint changes should not cause sudden actuator movements.
        
        :param sp: New setpoint value (target for the controlled variable)
        :param keep_output: If True and controller has run at least once,
                           adjusts integrator to maintain current output
                           (bumpless setpoint change). If False, integrator
                           is unchanged (may cause output step).
        
        :raises TypeError: If sp cannot be converted to float
        
        Bumpless Setpoint Change (keep_output=True):
            
            Behavior:
                
                - Calculates new error: e_new = sp_new - measurement
                - Adjusts integrator: I_new = u_current - P_new - D_current
                - Result: Next output ≈ current output (no step)
            
            Requirements:
                
                - Controller must have run at least once (update() called)
                - Valid measurement must be available
                - If not met, acts like keep_output=False
            
            Use cases:
                
                - Setpoint ramping or profiling
                - Avoiding actuator stress from sudden changes
                - Smooth transitions in multi-setpoint sequences
                - User-adjustable setpoints during operation
        
        Standard Setpoint Change (keep_output=False):
            
            Behavior:
                
                - Setpoint updated immediately
                - Integrator unchanged
                - Next output reflects new error
                - May cause output step (proportional to setpoint change)
            
            Use cases:
                
                - Fast response to setpoint changes desired
                - System can handle output steps
                - Initial setpoint setting
                - Aggressive control preferred
        
        Example
        -------
        ```python
            >>> from ufilter import PID
            >>> import time
            >>> 
            >>> # Basic setpoint change
            >>> pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...           out_min=0.0, out_max=100.0)
            >>> 
            >>> # Initial setpoint
            >>> pid.set_setpoint(25.0)
            >>> 
            >>> # Run for a while
            >>> for i in range(50):
            ...     temp = read_sensor()
            ...     power = pid.update(temp)
            ...     time.sleep(0.1)
            >>> 
            >>> # Change setpoint (standard - may cause output step)
            >>> pid.set_setpoint(30.0, keep_output=False)
            >>> 
            >>> # Bumpless setpoint change
            >>> def bumpless_setpoint_change():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     pid.set_setpoint(50.0)
            ...     
            ...     # Run until settled
            ...     for i in range(100):
            ...         measurement = read_sensor()
            ...         output = pid.update(measurement)
            ...         apply_output(output)
            ...         time.sleep(0.1)
            ...     
            ...     # Change setpoint without output bump
            ...     pid.set_setpoint(60.0, keep_output=True)
            ...     
            ...     # Output continues smoothly
            ...     measurement = read_sensor()
            ...     output = pid.update(measurement)
            >>> 
            >>> # Setpoint ramping
            >>> def setpoint_ramp():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     # Ramp from 20 to 80 over 60 seconds
            ...     start_sp = 20.0
            ...     end_sp = 80.0
            ...     ramp_time = 60.0  # seconds
            ...     
            ...     pid.set_setpoint(start_sp)
            ...     
            ...     start_time = time.time()
            ...     
            ...     while True:
            ...         elapsed = time.time() - start_time
            ...         
            ...         if elapsed < ramp_time:
            ...             # Calculate ramped setpoint
            ...             progress = elapsed / ramp_time
            ...             current_sp = start_sp + (end_sp - start_sp) * progress
            ...             
            ...             # Bumpless update
            ...             pid.set_setpoint(current_sp, keep_output=True)
            ...         else:
            ...             # Ramp complete
            ...             pid.set_setpoint(end_sp, keep_output=False)
            ...         
            ...         measurement = read_sensor()
            ...         output = pid.update(measurement)
            ...         apply_output(output)
            ...         time.sleep(0.1)
            >>> 
            >>> # Multi-step process
            >>> def multi_step_process():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     # Process steps: preheat, soak, production, cooldown
            ...     steps = [
            ...         ("preheat", 40.0, 60),    # 40°C for 60 seconds
            ...         ("soak", 60.0, 120),      # 60°C for 120 seconds
            ...         ("production", 80.0, 300), # 80°C for 300 seconds
            ...         ("cooldown", 30.0, 180)   # 30°C for 180 seconds
            ...     ]
            ...     
            ...     for step_name, setpoint, duration in steps:
            ...         print(f"Step: {step_name}, Target: {setpoint}°C")
            ...         
            ...         # Smooth transition between steps
            ...         pid.set_setpoint(setpoint, keep_output=True)
            ...         
            ...         # Hold setpoint for duration
            ...         for i in range(int(duration * 10)):  # 10 Hz
            ...             temp = read_sensor()
            ...             power = pid.update(temp)
            ...             set_heater(power)
            ...             time.sleep(0.1)
            >>> 
            >>> # User-adjustable setpoint
            >>> def user_adjustable_control():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     current_setpoint = 50.0
            ...     pid.set_setpoint(current_setpoint)
            ...     
            ...     while True:
            ...         # Check for user input
            ...         new_setpoint = read_user_input()
            ...         
            ...         if new_setpoint != current_setpoint:
            ...             # User changed setpoint - bumpless transition
            ...             pid.set_setpoint(new_setpoint, keep_output=True)
            ...             current_setpoint = new_setpoint
            ...             print(f"New setpoint: {new_setpoint:.1f}")
            ...         
            ...         measurement = read_sensor()
            ...         output = pid.update(measurement)
            ...         apply_output(output)
            ...         time.sleep(0.1)
            >>> 
            >>> # Comparing bumpless vs standard
            >>> def compare_setpoint_methods():
            ...     # Standard change
            ...     pid1 = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                out_min=0.0, out_max=100.0)
            ...     pid1.set_setpoint(50.0)
            ...     
            ...     # Bumpless change
            ...     pid2 = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...                out_min=0.0, out_max=100.0)
            ...     pid2.set_setpoint(50.0)
            ...     
            ...     # Run both until settled
            ...     for i in range(100):
            ...         measurement = 48.0  # Near setpoint
            ...         pid1.update(measurement)
            ...         pid2.update(measurement)
            ...     
            ...     # Record outputs before change
            ...     out1_before = pid1.u
            ...     out2_before = pid2.u
            ...     
            ...     # Change setpoint
            ...     pid1.set_setpoint(55.0, keep_output=False)  # Standard
            ...     pid2.set_setpoint(55.0, keep_output=True)   # Bumpless
            ...     
            ...     # Check outputs after change
            ...     out1_after = pid1.update(48.0)
            ...     out2_after = pid2.update(48.0)
            ...     
            ...     print(f"Standard: {out1_before:.1f} → {out1_after:.1f} (step)")
            ...     print(f"Bumpless: {out2_before:.1f} → {out2_after:.1f} (smooth)")
            >>> 
            >>> # Adaptive setpoint based on load
            >>> def load_adaptive_setpoint():
            ...     pid = PID(kp=2.0, ki=0.5, kd=0.1, fs=10.0,
            ...               out_min=0.0, out_max=100.0)
            ...     
            ...     base_setpoint = 60.0
            ...     pid.set_setpoint(base_setpoint)
            ...     
            ...     while True:
            ...         load = measure_load()
            ...         
            ...         # Adjust setpoint based on load
            ...         if load > 80:  # Heavy load
            ...             adjusted_sp = base_setpoint - 5.0
            ...         elif load < 20:  # Light load
            ...             adjusted_sp = base_setpoint + 5.0
            ...         else:  # Normal load
            ...             adjusted_sp = base_setpoint
            ...         
            ...         # Smooth adjustment
            ...         pid.set_setpoint(adjusted_sp, keep_output=True)
            ...         
            ...         measurement = read_sensor()
            ...         output = pid.update(measurement)
            ...         apply_output(output)
            ...         time.sleep(0.1)
            >>> 
            >>> # Setpoint profiling
            >>> def trapezoidal_profile():
            ...     pid = PID(kp=5.0, ki=2.0, kd=0.5, fs=100.0,
            ...               out_min=-100.0, out_max=100.0)
            ...     
            ...     # Trapezoidal motion profile
            ...     start_pos = 0.0
            ...     end_pos = 100.0
            ...     accel_time = 2.0  # seconds
            ...     const_velocity_time = 5.0  # seconds
            ...     decel_time = 2.0  # seconds
            ...     
            ...     # Calculate velocities
            ...     accel_dist = 0.5 * (end_pos - start_pos) * accel_time / (accel_time + const_velocity_time + decel_time)
            ...     
            ...     start_time = time.time()
            ...     
            ...     while True:
            ...         elapsed = time.time() - start_time
            ...         
            ...         if elapsed < accel_time:
            ...             # Acceleration phase
            ...             setpoint = start_pos + 0.5 * accel_dist * (elapsed / accel_time) ** 2
            ...         elif elapsed < accel_time + const_velocity_time:
            ...             # Constant velocity phase
            ...             t_const = elapsed - accel_time
            ...             setpoint = start_pos + accel_dist + const_velocity * t_const
            ...         elif elapsed < accel_time + const_velocity_time + decel_time:
            ...             # Deceleration phase
            ...             t_decel = elapsed - accel_time - const_velocity_time
            ...             # ... calculate deceleration position ...
            ...             pass
            ...         else:
            ...             # Profile complete
            ...             setpoint = end_pos
            ...         
            ...         pid.set_setpoint(setpoint, keep_output=True)
            ...         
            ...         position = read_encoder()
            ...         output = pid.update(position)
            ...         set_motor(output)
            ...         time.sleep(0.01)  # 100 Hz
        ```
        
        Notes:
            
            - New setpoint takes effect on next update() call
            - keep_output=True prevents output discontinuities
            - keep_output requires at least one prior update() call
            - Setpoint not clamped (can be any float value)
            - For smooth ramping, use small incremental changes with keep_output=True
            - Standard setpoint change (keep_output=False) causes proportional kick if beta > 0
        """
        ...


class FilterChain(Base):
    """
    Chain multiple filters in series for complex signal processing.
    
    A flexible filter composition system that connects multiple filter objects
    in series, with each filter's output feeding into the next filter's input.
    This enables creation of sophisticated signal processing pipelines by
    combining simpler filter building blocks.
    
    The filter chain implements sequential processing:
        
        y[n] = fₙ(... f₂(f₁(x[n])))
    
    Where:
        
        - f₁, f₂, ..., fₙ: Individual filter objects in the chain
        - x[n]: Input sample
        - y[n]: Output after processing through all filters
    
    Key Features:
        
        - Flexible composition of filter elements
        - Dynamic chain reconfiguration during operation
        - Unified interface through Base compatibility
        - Memory-efficient implementation
        - Runtime chain modification (add/remove filters)
        - Simple signal flow - sequential processing
        - Unified reset capability for entire chain
    
    Performance Characteristics:
        
        - Computational complexity: Sum of individual filter complexities
        - Memory usage: Sum of individual filter memory requirements
        - Overall delay: Sum of individual filter delays
        - Frequency response: Multiplication of individual responses
        - Phase response: Sum of individual phase responses
        - Group delay: Sum of individual group delays
    
    Applications:
        
        - Multi-stage signal conditioning
        - Audio processing chains (noise reduction → EQ → compression)
        - Sensor data preprocessing pipelines
        - Complex filter design via simpler building blocks
        - Signal pre/post processing combinations
        - Adaptive processing with reconfigurable stages
        - Test harnesses for filter component evaluation
    
    Chain Properties:
        
        - Overall transfer function: Product of individual transfer functions
        - Overall impulse response: Convolution of individual impulse responses
        - Overall stability: Chain is stable if all components are stable
        - Order of filters affects overall response
        - Can combine different filter types (IIR, FIR, etc.)
    """
    
    def __init__(self, *filters: Base) -> None:
        """
        Initialize filter chain with a sequence of filters.
        
        Creates a filter chain by connecting multiple filter objects in series.
        Each filter's output feeds into the next filter's input, creating a
        processing pipeline.
        
        :param *filters: One or more filter objects (variable argument list)
                        All must be instances of Base subclasses
                        Order determines processing sequence
        
        :raises ValueError: If no filters are provided or if any argument is not a Base
        
        Chain Design Guidelines:
        
            - Order matters: results can differ based on filter sequence
            - Consider placing computation-heavy filters later in chain when possible
            - Low-pass filtering early can reduce computational load for later stages
            - Consider signal levels between stages to avoid clipping/underflow
        
        Example
        -------
        ```python
            >>> # Create a multi-stage processing chain
            >>> # Stage 1: Median filter for outlier rejection
            >>> outlier_filter = Median(window_size=3)
            >>> 
            >>> # Stage 2: Low-pass filter for noise reduction
            >>> noise_filter = LowPass(fc=10.0, fs=100.0)
            >>> 
            >>> # Stage 3: Kalman filter for optimal tracking
            >>> tracker = Kalman(process_noise=0.01, measurement_noise=0.1)
            >>> 
            >>> # Create the chain connecting all three filters
            >>> processing_chain = FilterChain(outlier_filter, noise_filter, tracker)
            >>> print(f"Chain length: {len(processing_chain.filters)} filters")
            >>> 
            >>> # Parameter validation
            >>> try:
            ...     invalid_chain = FilterChain()  # No filters
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
        ```
        """

    @micropython.native
    def update(self, x: float) -> float:
        """
        Process sample through filter chain.
        
        Processes a single input sample sequentially through each filter in the chain,
        where each filter's output becomes the input to the next filter.
        
        :param x: Input sample value (any numeric type, converted to float)
        :return: Output from last filter in chain as float
        
        :raises TypeError: If input cannot be converted to float
        
        Algorithm Details:
        
            1. Convert input to float
            2. Pass input through first filter
            3. Pass that filter's output to next filter
            4. Continue through chain sequentially
            5. Return output from final filter
        
        Example
        -------
        ```python
            >>> # Create a simple processing chain
            >>> # Median filter followed by low-pass filter
            >>> chain = FilterChain(
            ...     Median(window_size=3),
            ...     LowPass(fc=10.0, fs=100.0)
            ... )
            >>> 
            >>> # Process a sample with outlier followed by valid readings
            >>> test_data = [1.0, 10.0, 2.0, 1.5, 1.8]
            >>> 
            >>> print("Input | Output")
            >>> print("-" * 15)
            >>> 
            >>> for sample in test_data:
            ...     result = chain.update(sample)
            ...     print(f"{sample:5.1f} | {result:6.3f}")
            >>> 
            >>> # Output should show outlier rejection and smoothing
        ```
        """

    def reset(self) -> None:
        """
        Reset all filters in chain.
        
        Resets the state of all filters in the chain and the chain's own sample
        counter. Each filter maintains its configuration but clears its internal state.
        
        Reset Operations:
        
            - Resets each filter in the chain
            - Resets chain's sample counter
            - Preserves chain structure and filter configurations
            - Prepares entire chain for new input sequence
        
        Example
        -------
        ```python
            >>> # Create a filter chain
            >>> chain = FilterChain(
            ...     MovingAverage(window_size=5),
            ...     LowPass(fc=10.0, fs=100.0)
            ... )
            >>> 
            >>> # Process some data
            >>> for i in range(10):
            ...     result = chain.update(i)
            >>> 
            >>> print(f"Before reset: {chain.sample_count} samples processed")
            >>> 
            >>> # Reset entire chain
            >>> chain.reset()
            >>> print(f"After reset: {chain.sample_count} samples processed")
            >>> 
            >>> # Verify filters in chain were reset
            >>> all_reset = all(f.sample_count == 0 for f in chain.filters)
            >>> print(f"All filters reset: {all_reset}")
        ```
        """

    def add_filter(self, filter_obj: Base) -> None:
        """
        Add filter to end of chain.
        
        Appends a new filter to the end of the filter chain. The new filter will 
        receive input from the previously last filter in the chain.
        
        :param filter_obj: Filter to add (must be Base instance)
        
        :raises ValueError: If filter_obj is not a Base instance
        
        Dynamic Chain Modification:
        
            - Allows runtime extension of processing pipeline
            - New filter becomes the new final stage
            - Existing chain state is preserved
            - Useful for adaptive processing systems
        
        Example
        -------
        ```python
            >>> # Create initial chain
            >>> chain = FilterChain(MovingAverage(window_size=3))
            >>> print(f"Initial chain length: {len(chain.filters)}")
            >>> 
            >>> # Add another filter dynamically
            >>> chain.add_filter(LowPass(fc=10.0, fs=100.0))
            >>> print(f"Updated chain length: {len(chain.filters)}")
            >>> 
            >>> # Process data through extended chain
            >>> result = chain.update(5.0)
            >>> print(f"Result after adding filter: {result:.3f}")
            >>> 
            >>> # Conditional filter addition
            >>> def adaptive_chain(signal_level):
            ...     '''Add appropriate filter based on signal conditions.'''
            ...     chain = FilterChain(Median(window_size=3))
            ...     
            ...     if signal_level > 10.0:
            ...         # Add high noise filtering for strong signals
            ...         chain.add_filter(LowPass(fc=5.0, fs=100.0))
            ...         print("Added strong noise filter")
            ...     else:
            ...         # Add light filtering for weaker signals
            ...         chain.add_filter(LowPass(fc=20.0, fs=100.0))
            ...         print("Added light noise filter")
            ...     
            ...     return chain
        ```
        """

    def remove_filter(self, index: int) -> Base:
        """
        Remove filter from chain.
        
        Removes a filter at the specified index from the chain. This allows
        dynamic reconfiguration of the filter chain during operation.
        
        :param index: Zero-based index of filter to remove
        :return: The removed filter object
        
        :raises ValueError: If index is out of range
        
        Chain Modification Applications:
        
            - Dynamic processing pipeline adaptation
            - A/B testing of filter configurations
            - Fault tolerance (removing problematic filters)
            - Resource management (removing unneeded stages)
        
        Example
        -------
        ```python
            >>> # Create a three-stage filter chain
            >>> chain = FilterChain(
            ...     Median(window_size=3),
            ...     LowPass(fc=10.0, fs=100.0),
            ...     MovingAverage(window_size=5)
            ... )
            >>> print(f"Initial chain length: {len(chain.filters)}")
            >>> 
            >>> # Remove the middle filter
            >>> removed = chain.remove_filter(1)
            >>> print(f"Removed: {type(removed).__name__}")
            >>> print(f"Updated chain length: {len(chain.filters)}")
            >>> 
            >>> # Invalid index
            >>> try:
            ...     chain.remove_filter(5)  # Out of range
            >>> except ValueError as e:
            ...     print(f"Error: {e}")
        ```
        """
