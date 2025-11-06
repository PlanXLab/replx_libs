"""
RP2350 Board Control Library

Comprehensive hardware abstraction and control library for the RP2350 (Tiny Internet of Things Connected Learning Environment) board.
This library provides high-level interfaces for all onboard peripherals and sensors, enabling rapid prototyping and development
of IoT applications with professional-grade functionality and robust error handling.

The RP2350 board is built around the Raspberry Pi RP2350 microcontroller and features integrated WiFi connectivity,
multiple GPIO interfaces, analog inputs, PWM outputs, I2C communication, and various onboard sensors. This library
abstracts the hardware complexity and provides intuitive Python interfaces for seamless development.

Core Features:

- Complete hardware abstraction for RP2350 board peripherals
- WiFi connectivity management with automatic reconnection
- Multi-channel analog-to-digital conversion with precision voltage readings
- Flexible PWM generation for servo control, LED dimming, and motor control
- I2C communication interface with automatic bus detection
- Digital input/output control with interrupt callback support
- Built-in LED and button interfaces for immediate feedback
- Advanced serial communication with REPL integration
- System monitoring and diagnostics capabilities
- Memory and filesystem information utilities

Hardware Interfaces:

- GPIO Control: Digital input/output with configurable pull resistors and interrupts
- ADC Channels: 16-bit analog inputs on GPIO 26, 27, 28 with voltage conversion
- PWM Outputs: Multi-channel pulse width modulation with frequency and duty cycle control
- I2C Communication: Dual-bus I2C with automatic device detection and comprehensive register access
- WiFi Connectivity: Station mode with network scanning, connection management, and status monitoring
- Built-in Components: LED control (WL_GPIO0) and BOOTSEL button interface
- Serial Interface: Advanced REPL integration with line editing and UTF-8 support

"""

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


import machine
from typing import Callable

# Constants
LOW: int
HIGH: int
STAT_OK: int
STAT_TIMEOUT: int
STAT_BUS_ERR: int
STAT_NO_DEVICE: int
I2C0_SPINLOCK_ID: int
I2C1_SPINLOCK_ID: int
SPI0_SPINLOCK_ID: int
SPI1_SPINLOCK_ID: int

def get_sys_info() -> tuple:
    """
    Get system information including core frequency and temperature.
    
    This function retrieves the current CPU frequency and internal temperature
    of the RP2350 board, automatically detecting the chip type for proper
    temperature sensor access.
    
    :return: tuple of (frequency, temperature)
    
    :raises ValueError: If temperature sensor GPIO is not accessible
    
    Example
    --------
    ```python
        >>> freq, temp = get_sys_info()
        >>> print(f"CPU Frequency: {freq/1000000:.1f} MHz")
        >>> print(f"Temperature: {temp:.1f}°C")
        >>> # Output: CPU Frequency: 150.0 MHz
        >>> # Output: Temperature: 23.4°C
        >>> 
        >>> # Check for overheating
        >>> if temp > 70:
        ...     print("Warning: High temperature detected!")
        >>> 
        >>> # Monitor system performance
        >>> import utime
        >>> for i in range(5):
        ...     freq, temp = get_sys_info()
        ...     print(f"Reading {i+1}: {freq/1000000:.1f}MHz, {temp:.1f}°C")
        ...     utime.sleep(1)
        >>> 
        >>> # System health check
        >>> freq, temp = get_sys_info()
        >>> if freq < 100000000:  # Less than 100MHz
        ...     print("Warning: Low CPU frequency detected")
        >>> if temp > 80:
        ...     print("Critical: High temperature - consider cooling")
        >>> elif temp > 60:
        ...     print("Warning: Elevated temperature detected")
        >>> 
        >>> # Performance monitoring loop
        >>> import utime
        >>> max_temp = 0
        >>> min_temp = 100
        >>> while True:
        ...     freq, temp = get_sys_info()
        ...     max_temp = max(max_temp, temp)
        ...     min_temp = min(min_temp, temp)
        ...     print(f"Current: {temp:.1f}°C, Range: {min_temp:.1f}-{max_temp:.1f}°C")
        ...     utime.sleep(10)
    ```
    """

def get_mem_info() -> tuple:
    """
    Get memory usage information of RP2350.
    
    This function performs garbage collection and returns detailed memory
    statistics including free, used, and total memory in bytes.
    
    :return: tuple of (free, used, total) memory in bytes
    
    Example
    --------
    ```python
        >>> free, used, total = get_mem_info()
        >>> print(f"Free memory: {free/1024:.1f} KB")
        >>> print(f"Used memory: {used/1024:.1f} KB")
        >>> print(f"Total memory: {total/1024:.1f} KB")
        >>> print(f"Memory usage: {used/total*100:.1f}%")
        >>> # Output: Free memory: 180.5 KB
        >>> # Output: Used memory: 83.2 KB
        >>> # Output: Total memory: 263.7 KB
        >>> # Output: Memory usage: 31.5%
        >>> 
        >>> # Memory monitoring loop
        >>> import utime
        >>> while True:
        ...     free, used, total = get_mem_info()
        ...     usage = used / total * 100
        ...     print(f"Memory usage: {usage:.1f}%")
        ...     if usage > 90:
        ...         print("Warning: Low memory!")
        ...     utime.sleep(10)
        >>> 
        >>> # Memory allocation tracking
        >>> def track_memory_usage(func):
        ...     '''Decorator to track memory usage of a function'''
        ...     def wrapper(*args, **kwargs):
        ...         before = get_mem_info()
        ...         result = func(*args, **kwargs)
        ...         after = get_mem_info()
        ...         print(f"Memory change: {after[1] - before[1]} bytes")
        ...         return result
        ...     return wrapper
        >>> 
        >>> @track_memory_usage
        >>> def create_large_list():
        ...     return [i for i in range(1000)]
        >>> 
        >>> data = create_large_list()
        >>> 
        >>> # Memory optimization check
        >>> free, used, total = get_mem_info()
        >>> if free < 10240:  # Less than 10KB free
        ...     print("Critical: Very low memory available")
        ...     import gc
        ...     gc.collect()
        ...     print("Garbage collection performed")
        >>> 
        >>> # Memory efficiency calculation
        >>> free, used, total = get_mem_info()
        >>> efficiency = (total - used) / total * 100
        >>> print(f"Memory efficiency: {efficiency:.1f}%")
        >>> if efficiency < 50:
        ...     print("Consider optimizing memory usage")
    ```
    """


def get_fs_info(path: str = '/') -> tuple:
    """
    Get filesystem information for the given path.
    
    This function retrieves detailed filesystem statistics including total,
    used, and free space along with usage percentage for the specified path.
    
    :param path: Path to check filesystem info for (default: '/')
    :return: tuple of (total, used, free, usage percentage)
    
    Example
    --------
    ```python
        >>> total, used, free, usage = get_fs_info()
        >>> print(f"Total space: {total/1024:.1f} KB")
        >>> print(f"Used space: {used/1024:.1f} KB")
        >>> print(f"Free space: {free/1024:.1f} KB")
        >>> print(f"Usage: {usage:.1f}%")
        >>> # Output: Total space: 1024.0 KB
        >>> # Output: Used space: 156.3 KB
        >>> # Output: Free space: 867.7 KB
        >>> # Output: Usage: 15.3%
        >>> 
        >>> # Check specific directory
        >>> try:
        ...     total, used, free, usage = get_fs_info('/lib')
        ...     print(f"Library usage: {usage:.1f}%")
        >>> except:
        ...     print("Directory not found or inaccessible")
        >>> 
        >>> # Storage monitoring
        >>> total, used, free, usage = get_fs_info()
        >>> if usage > 80:
        ...     print("Warning: Low storage space!")
        >>> elif usage > 95:
        ...     print("Critical: Storage nearly full!")
        >>> 
        >>> # Storage cleanup recommendation
        >>> total, used, free, usage = get_fs_info()
        >>> if free < 50 * 1024:  # Less than 50KB free
        ...     print("Consider removing unnecessary files")
        ...     print("Available space is critically low")
        >>> 
        >>> # File system health check
        >>> def check_filesystem_health():
        ...     total, used, free, usage = get_fs_info()
        ...     print(f"Filesystem Health Report:")
        ...     print(f"  Total Capacity: {total/1024:.1f} KB")
        ...     print(f"  Used Space: {used/1024:.1f} KB ({usage:.1f}%)")
        ...     print(f"  Free Space: {free/1024:.1f} KB ({100-usage:.1f}%)")
        ...     
        ...     if usage < 50:
        ...         print("  Status: Healthy")
        ...     elif usage < 75:
        ...         print("  Status: Moderate usage")
        ...     elif usage < 90:
        ...         print("  Status: High usage - monitor closely")
        ...     else:
        ...         print("  Status: Critical - cleanup needed")
        >>> 
        >>> check_filesystem_health()
        >>> 
        >>> # Storage usage comparison
        >>> root_stats = get_fs_info('/')
        >>> print(f"Root filesystem usage: {root_stats[3]:.1f}%")
        >>> 
        >>> # Monitor storage over time
        >>> import utime
        >>> previous_usage = 0
        >>> while True:
        ...     total, used, free, usage = get_fs_info()
        ...     if abs(usage - previous_usage) > 1.0:  # Significant change
        ...         print(f"Storage usage changed: {usage:.1f}% (was {previous_usage:.1f}%)")
        ...         previous_usage = usage
        ...     utime.sleep(30)
    ```
    """


class KeyReader:
    """
    Context manager for reading keyboard input with escape sequence support.
    
    This class provides a context manager interface for reading keyboard input
    with support for special keys (arrow keys, Enter, Tab, Escape, etc.) and
    non-blocking key detection.
    
    Key Features:
    
        - Non-blocking key detection with polling
        - Automatic escape sequence handling
        - Special key name mapping (UP, DOWN, LEFT, RIGHT, etc.)
        - UTF-8 character decoding
        - Context manager interface for safe resource management
    
    Supported Special Keys:
    
        - Arrow keys: UP, DOWN, LEFT, RIGHT
        - Control keys: TAB, ENTER, SPACE, ESC
        - Extended keys automatically detected
    """
    
    ESC: bytes
    EXT_CODE_TBL: dict[bytes, bytes]
    
    def __enter__(self) -> "KeyReader":
        """
        Enter the context manager and set up key reading.
        
        Initializes the input poller and registers stdin for reading.
        
        :return: The KeyReader instance
        
        Example
        --------
        ```python
            >>> with KeyReader() as reader:
            ...     while True:
            ...         key = reader.ch
            ...         if key:
            ...             print(f"Key pressed: {key}")
            ...             if key == 'ESC':
            ...                 break
            ...         utime.sleep_ms(50)
        ```
        """
        ...
    
    def __exit__(self, type, value, traceback) -> None:
        """
        Exit the context manager and clean up resources.
        
        Unregisters stdin from the poller and releases resources.
        
        :param type: Exception type if an exception occurred
        :param value: Exception value if an exception occurred
        :param traceback: Exception traceback if an exception occurred
        """
        ...
    
    @property
    def ch(self) -> str | None:
        """
        Read a single character or special key name.
        
        Returns the decoded character or special key name (e.g., 'UP', 'DOWN',
        'ENTER', 'ESC', etc.). Returns None if no key is pressed (non-blocking).
        
        :return: Character string or special key name, or None if no key pressed
        
        Example
        --------
        ```python
            >>> # Simple key detection
            >>> with KeyReader() as reader:
            ...     print("Press any key (ESC to exit):")
            ...     while True:
            ...         key = reader.ch
            ...         if key:
            ...             if key == 'ESC':
            ...                 print("Exiting...")
            ...                 break
            ...             elif key in ('UP', 'DOWN', 'LEFT', 'RIGHT'):
            ...                 print(f"Arrow key: {key}")
            ...             elif key == 'ENTER':
            ...                 print("Enter pressed")
            ...             else:
            ...                 print(f"Character: {key}")
            ...         utime.sleep_ms(10)
            >>> 
            >>> # Game control example
            >>> player_x, player_y = 0, 0
            >>> with KeyReader() as reader:
            ...     while True:
            ...         key = reader.ch
            ...         if key == 'UP':
            ...             player_y -= 1
            ...         elif key == 'DOWN':
            ...             player_y += 1
            ...         elif key == 'LEFT':
            ...             player_x -= 1
            ...         elif key == 'RIGHT':
            ...             player_x += 1
            ...         elif key == 'ESC':
            ...             break
            ...         print(f"Position: ({player_x}, {player_y})")
            ...         utime.sleep_ms(50)
            >>> 
            >>> # Menu navigation
            >>> menu_items = ["Start", "Settings", "Exit"]
            >>> selected = 0
            >>> with KeyReader() as reader:
            ...     while True:
            ...         print("\n" * 10)  # Clear screen (simple method)
            ...         for i, item in enumerate(menu_items):
            ...             prefix = "> " if i == selected else "  "
            ...             print(f"{prefix}{item}")
            ...         
            ...         key = reader.ch
            ...         if key == 'UP':
            ...             selected = (selected - 1) % len(menu_items)
            ...         elif key == 'DOWN':
            ...             selected = (selected + 1) % len(menu_items)
            ...         elif key == 'ENTER':
            ...             print(f"Selected: {menu_items[selected]}")
            ...             break
            ...         utime.sleep_ms(100)
        ```
        """
        ...


def input(prompt: str = "") -> str:
    """
    Advanced input function with full-featured line editing capabilities.
    
    This function provides a sophisticated replacement for the standard input()
    function with comprehensive line editing features including UTF-8 support,
    cursor movement, text insertion/deletion, and terminal control sequences.
    
    Features:
    
        - Full UTF-8 support for international characters (1-4 bytes per character)
        - Left/Right arrow key cursor movement with proper character width handling
        - Backspace deletion before cursor position
        - Delete key support for deletion at cursor position
        - Text insertion at any cursor position (not just at end)
        - Home/End key support for cursor positioning
        - Proper display width calculation for multi-byte characters
        - Terminal control sequence handling for professional appearance
        - Robust input validation and error handling
    
    :param prompt: Optional prompt string to display before input (default: "")
    :return: User-entered string (UTF-8 decoded)
    
    Example
    --------
    ```python
        >>> # Basic input with prompt
        >>> name = input("Enter your name: ")
        >>> print(f"Hello, {name}!")
        >>> 
        >>> # Interactive command shell
        >>> while True:
        ...     command = input(">>> ")
        ...     if command == "exit":
        ...         break
        ...     elif command == "help":
        ...         print("Available commands: help, exit, status")
        ...     elif command == "status":
        ...         print("System is running normally")
        ...     else:
        ...         print(f"Unknown command: {command}")
        >>> 
        >>> # Configuration input with validation
        >>> while True:
        ...     try:
        ...         port = input("Enter port number (1-65535): ")
        ...         port_num = int(port)
        ...         if 1 <= port_num <= 65535:
        ...             print(f"Port {port_num} configured successfully")
        ...             break
        ...         else:
        ...             print("Port number must be between 1 and 65535")
        ...     except ValueError:
        ...         print("Please enter a valid number")
        >>> 
        >>> # Multi-language support
        >>> greeting = input("Enter greeting (支持中文): ")
        >>> print(f"Your greeting: {greeting}")
        >>> 
        >>> # Interactive menu system
        >>> def show_menu():
        ...     print("\\n=== System Menu ===")
        ...     print("1. View Status")
        ...     print("2. Configure Network")
        ...     print("3. Exit")
        ...     return input("Select option (1-3): ")
        >>> 
        >>> while True:
        ...     choice = show_menu()
        ...     if choice == "1":
        ...         print("System Status: OK")
        ...     elif choice == "2":
        ...         ssid = input("WiFi SSID: ")
        ...         password = input("Password: ")
        ...         print(f"Configuring network: {ssid}")
        ...     elif choice == "3":
        ...         print("Goodbye!")
        ...         break
        ...     else:
        ...         print("Invalid choice")
        >>> 
        >>> # Batch data entry
        >>> contacts = []
        >>> while True:
        ...     name = input("Contact name (or 'done' to finish): ")
        ...     if name.lower() == 'done':
        ...         break
        ...     email = input("Email address: ")
        ...     contacts.append({"name": name, "email": email})
        >>> print(f"Added {len(contacts)} contacts")
    ```
    """
    ...


class WifiManager:
    """
    Comprehensive WiFi management class for RP2350 board connectivity.
    
    This class provides complete WiFi functionality including network scanning,
    connection management, status monitoring, and configuration retrieval.
    Uses lazy initialization to defer WiFi interface activation until first use,
    minimizing resource usage when WiFi is not needed.
    
    The manager handles automatic interface activation on demand, connection timeouts,
    and provides convenient methods for network discovery and status monitoring.
    Designed for reliable WiFi connectivity in IoT applications with proper
    resource management and clean disconnection capabilities.
    
    Key Features:
    
        - Lazy initialization: WiFi interface activated only when first used
        - Network scanning with detailed access point information
        - Robust connection handling with configurable timeouts
        - Connection status monitoring and IP address retrieval
        - Clean disconnection and resource management
        - Support for multiple network credentials
        - Network interface configuration access
        - All methods are static - no instance creation required
    
    Security Support:
    
        - Open networks (no authentication)
        - WEP encryption (legacy, not recommended)
        - WPA-PSK and WPA2-PSK (recommended)
        - WPA/WPA2 mixed mode
        - Automatic security detection during scan
    
    Connection States:
    
        - Inactive: Interface disabled
        - Scanning: Searching for networks
        - Connecting: Authentication in progress
        - Connected: Successfully connected with IP
        - Disconnected: Not connected to any network
        
    """
    
    @staticmethod
    def scan() -> list[tuple[str,int,int,int]]:
        """
        Scan for available WiFi networks in the area.
        
        Performs a comprehensive WiFi scan and returns detailed information about
        all discovered access points including signal strength, channel, and security.
        The scan may take several seconds to complete.
        
        :return: List of tuples containing (SSID, RSSI, channel, security).
        
            - SSID (bytes): Network name as raw bytes
            - RSSI (int): Signal strength in dBm (negative values, closer to 0 = stronger)
            - Channel (int): WiFi channel number (1-14 for 2.4GHz)
            - Security (int): Security type (0=Open, 1=WEP, 2=WPA-PSK, 3=WPA2-PSK, 4=WPA/WPA2-PSK)
    
        :raises OSError: If WiFi scanning fails or interface is not active
        
        Example
        --------
        ```python
            >>> networks = WifiManager.scan()
            >>> 
            >>> for ssid, rssi, channel, security in networks:
            ...     ssid_str = ssid.decode('utf-8', 'ignore')
            ...     security_types = ["Open", "WEP", "WPA-PSK", "WPA2-PSK", "WPA/WPA2-PSK"]
            ...     security_str = security_types[security] if security < len(security_types) else f"Unknown({security})"
            ...     print(f"{ssid_str:20} | {rssi:4d}dBm | CH{channel:2d} | {security_str}")
            >>> 
            >>> # Find strongest network
            >>> if networks:
            ...     strongest = max(networks, key=lambda x: x[1])
            ...     print(f"Strongest: {strongest[0].decode('utf-8')} ({strongest[1]}dBm)")
        ```
        """

    @staticmethod
    def available_ssids() -> list[str]:
        """
        Get a clean list of available network names (SSIDs).
        
        Scans for networks and returns a simplified list of unique SSIDs as strings,
        filtering out empty names and handling UTF-8 decoding gracefully.
        This is more convenient than scan() when you only need network names.
        
        :return: List of unique SSIDs found in the scanned access points.
        
        :raises OSError: If WiFi scanning fails or interface is not active
        
        Example
        --------
        ```python
            >>> ssids = WifiManager.available_ssids()
            >>> print("Available networks:")
            >>> for i, ssid in enumerate(ssids, 1):
            ...     print(f"  {i}. {ssid}")
            >>> 
            >>> # Check if specific network exists
            >>> if "MyNetwork" in WifiManager.available_ssids():
            ...     print("Home network found!")
        ```
        """

    @staticmethod
    def connect(ssid: str, password: str, timeout: float = 20.0) -> bool:
        """
        Connect to a WiFi network with comprehensive error handling.
        
        Attempts to connect to the specified network with configurable timeout.
        Returns immediately if already connected to the same network.
        Handles connection failures gracefully and provides detailed status feedback.
        
        :param ssid: SSID of the WiFi network to connect to.
        :param password: Password for the WiFi network. Use empty string for open networks.
        :param timeout: Timeout in seconds for the connection attempt (default: 20.0 seconds).
        :return: True if connected successfully, False otherwise.
        
        :raises ValueError: If SSID is empty or timeout is negative
        :raises OSError: If WiFi interface is not available
        
        Example
        --------
        ```python
            >>> # Basic connection
            >>> if WifiManager.connect("MyNetwork", "password123"):
            ...     print(f"Connected! IP: {WifiManager.ip()}")
            ... else:
            ...     print("Connection failed")
            >>> 
            >>> # Open network connection
            >>> if WifiManager.connect("PublicWiFi", ""):  # Empty password
            ...     print("Connected to open network")
            >>> 
            >>> # Connection with custom timeout
            >>> success = WifiManager.connect("SlowNetwork", "password", timeout=30.0)
        ```
        """

    @staticmethod
    def disconnect() -> None:
        """
        Safely disconnect from the current WiFi network.
        
        Cleanly disconnects from the current network if connected, with a brief
        delay to ensure proper disconnection. Safe to call even if not connected.
        
        Example
        --------
        ```python
            >>> WifiManager.connect("MyNetwork", "password")
            >>> print(f"Connected: {WifiManager.is_connected()}")  # True
            >>> 
            >>> WifiManager.disconnect()
            >>> print(f"Connected: {WifiManager.is_connected()}")  # False
        ```
        """
    
    @staticmethod
    def ifconfig() -> tuple | None:
        """
        Get complete network interface configuration.
        
        Returns the full network configuration including IP address,
        netmask, gateway, and DNS server if connected. Useful for
        network diagnostics and advanced configuration.
        
        :return: Tuple containing (ip, netmask, gateway, dns) if connected, None otherwise.
        
        Example
        --------
        ```python
            >>> WifiManager.connect("MyNetwork", "password")
            >>> 
            >>> config = WifiManager.ifconfig()
            >>> if config:
            ...     ip, netmask, gateway, dns = config
            ...     print(f"IP: {ip}, Gateway: {gateway}, DNS: {dns}")
        ```
        """

    @staticmethod
    def is_connected() -> bool:
        """
        Check if the WiFi interface is currently connected to a network.
        
        Returns the current connection status. This is a real-time check
        that reflects the actual network connectivity state.
        
        :return: True if connected, False otherwise.
        
        Example
        --------
        ```python
            >>> print(f"Initial state: {WifiManager.is_connected()}")  # False
            >>> 
            >>> WifiManager.connect("MyNetwork", "password")
            >>> print(f"After connect: {WifiManager.is_connected()}")  # True
            >>> 
            >>> # Connection monitoring
            >>> if WifiManager.is_connected():
            ...     print("Network operations available")
            ... else:
            ...     print("No network connection")
        ```
        """

    @staticmethod
    def ip() -> str | None:
        """
        Get the current IP address of the WiFi connection.
        
        Returns the IP address as a string if connected, None otherwise.
        This is a convenient way to get just the IP address without
        the full interface configuration.
        
        :return: IP address as a string if connected, None otherwise.
        
        Example
        --------
        ```python
            >>> print(f"IP before connect: {WifiManager.ip()}")  # None
            >>> 
            >>> WifiManager.connect("MyNetwork", "password")
            >>> ip = WifiManager.ip()
            >>> if ip:
            ...     print(f"Connected with IP: {ip}")
            ...     if ip.startswith("192.168."):
            ...         print("Private network detected")
            ... else:
            ...     print("No IP address assigned")
        ```
        """


class BLEBroker:    
    _IRQ_CENTRAL_CONNECT: int
    _IRQ_CENTRAL_DISCONNECT: int
    _IRQ_GATTS_WRITE: int
    _FLAG_READ: int
    _FLAG_WRITE: int
    _FLAG_NOTIFY: int
    _MAX_QUEUE: int
    _MAX_CONNECTIONS: int
    _MAX_MESSAGE_SIZE: int
    _MAX_TOPIC_LENGTH: int

    def __init__(self, name: str = "TiCLE_BLEBroker", *,
                 service_uuid: str = "12345678-0000-0000-0000-000000000010",
                 char_uuid: str = "12345678-0000-0000-0000-000000000011",
                 max_connections: int = 4):
        """
        Initialize BLE broker with GATT service.
        
        Creates and activates a BLE GATT server with a single characteristic that
        supports read, write, and notify operations. The service immediately starts
        advertising and accepting connections up to the specified limit.
        
        :param name: BLE device name for advertising (max 29 characters)
        :param service_uuid: 128-bit service UUID string in format "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        :param char_uuid: 128-bit characteristic UUID string in same format
        :param max_connections: Maximum concurrent connections (1-4, default: 4)
        
        :raises ValueError: If name exceeds 29 chars or max_connections not in 1-4 range
        :raises OSError: If BLE initialization fails or hardware not available
        
        Example
        -------
        ```python
            >>> # Standard initialization
            >>> broker = BLEBroker(name="MyDevice")
            >>> 
            >>> # Custom UUIDs and connection limit
            >>> broker = BLEBroker(
            ...     name="Sensor",
            ...     service_uuid="12345678-1234-5678-1234-567812345678",
            ...     char_uuid="87654321-4321-8765-4321-876543218765",
            ...     max_connections=2
            ... )
        ```
        """

    @property
    def on_connect(self) -> callable | None:
        """
        Get connection event callback.
        
        Callback is invoked when a BLE central device successfully connects.
        Signature: callback() - no parameters.
        
        :return: Current callback function or None
        """

    @on_connect.setter
    def on_connect(self, cb: callable | None):
        """
        Set connection event callback.
        
        :param cb: Callback function with signature: callback()
        
        Example
        -------
        ```python
            >>> def on_connect():
            ...     print("Client connected")
            >>> broker.on_connect = on_connect
        ```
        """

    @property
    def on_disconnect(self) -> callable | None:
        """
        Get disconnection event callback.
        
        Callback is invoked when a connected central device disconnects.
        Signature: callback() - no parameters.
        
        :return: Current callback function or None
        """

    @on_disconnect.setter
    def on_disconnect(self, cb: callable | None):
        """
        Set disconnection event callback.
        
        :param cb: Callback function with signature: callback()
        
        Example
        -------
        ```python
            >>> def on_disconnect():
            ...     print("Client disconnected")
            >>> broker.on_disconnect = on_disconnect
        ```
        """

    @property
    def on_publish(self) -> callable | None:
        """
        Get publish event callback.
        
        Callback is invoked after successfully publishing a message to clients.
        Signature: callback(topic: str, message: str)
        
        :return: Current callback function or None
        """

    @on_publish.setter
    def on_publish(self, cb: callable | None):
        """
        Set publish event callback.
        
        :param cb: Callback function with signature: callback(topic: str, message: str)
        
        Example
        -------
        ```python
            >>> def on_publish(topic, message):
            ...     print(f"Published {topic}: {message}")
            >>> broker.on_publish = on_publish
        ```
        """

    @property
    def on_subscribe(self) -> callable | None:
        """
        Get subscription event callback.
        
        Callback is invoked when successfully subscribing to a topic.
        Signature: callback(topic: str)
        
        :return: Current callback function or None
        """

    @on_subscribe.setter
    def on_subscribe(self, cb: callable | None):
        """
        Set subscription event callback.
        
        :param cb: Callback function with signature: callback(topic: str)
        
        Example
        -------
        ```python
            >>> def on_subscribe(topic):
            ...     print(f"Subscribed to {topic}")
            >>> broker.on_subscribe = on_subscribe
        ```
        """

    @property
    def on_message(self) -> callable | None:
        """
        Get message receive callback.
        
        Callback is invoked when a message is received for a subscribed topic.
        Signature: callback(topic: str, payload: str)
        
        :return: Current callback function or None
        """

    @on_message.setter
    def on_message(self, cb: callable | None):
        """
        Set message receive callback.
        
        :param cb: Callback function with signature: callback(topic: str, payload: str)
        
        Example
        -------
        ```python
            >>> def on_message(topic, payload):
            ...     print(f"Received {topic}: {payload}")
            >>> broker.on_message = on_message
            >>> broker.subscribe("temperature")
        ```
        """

    @property
    def on_error(self) -> callable | None:
        """
        Get error callback.
        
        Callback is invoked when errors occur during broker operation.
        Signature: callback(error_type: str, details: str)
        
        Error types include:
            - "queue_overflow": Event queue full, events dropped
            - "connection_limit": Max connections reached, new connection rejected
            - "decode_error": Failed to decode incoming message
            - "dispatch_error": Error processing event
            - "invalid_message": Malformed message received
            - "message_handler_error": Error in user message callback
            - "callback_error": Error in user callback
            - "notify_error": Failed to send notification to client
            - "advertise_error": Failed to start advertising
            - "deinit_error": Error during cleanup
        
        :return: Current callback function or None
        """

    @on_error.setter
    def on_error(self, cb: callable | None):
        """
        Set error callback for handling errors.
        
        :param cb: Callback function with signature: callback(error_type: str, details: str)
        
        Example
        -------
        ```python
            >>> def on_error(err_type, details):
            ...     print(f"BLE Error [{err_type}]: {details}")
            >>> broker.on_error = on_error
        ```
        """

    @property
    def is_active(self) -> bool:
        """
        Check if BLE broker is active and operational.
        
        Returns True if broker was initialized and not yet deinitialized.
        Does not indicate connection status - use connection_count for that.
        
        :return: True if broker is active, False after deinit()
        
        Example
        -------
        ```python
            >>> broker = BLEBroker()
            >>> print(broker.is_active)  # True
            >>> broker.deinit()
            >>> print(broker.is_active)  # False
        ```
        """

    @property
    def connection_count(self) -> int:
        """
        Get number of currently active connections.
        
        Returns the count of BLE central devices currently connected.
        Maximum value is limited by max_connections parameter.
        
        :return: Number of active connections (0 to max_connections)
        
        Example
        -------
        ```python
            >>> print(f"Connections: {broker.connection_count}")
            >>> if broker.connection_count == 0:
            ...     print("No clients connected")
        ```
        """

    @property
    def subscribed_topics(self) -> list[str]:
        """
        Get list of currently subscribed topics.
        
        Returns a copy of the subscription list. Modifications to the returned
        list do not affect actual subscriptions - use subscribe/unsubscribe methods.
        
        :return: List of topic names currently subscribed
        
        Example
        -------
        ```python
            >>> broker.subscribe("temp")
            >>> broker.subscribe("humidity")
            >>> print(broker.subscribed_topics)  # ['temp', 'humidity']
        ```
        """

    @property
    def dropped_event_count(self) -> int:
        """
        Get number of events dropped due to queue overflow.
        
        Events are dropped when the internal event queue (max 32 events) is full
        and new events arrive. This indicates the system is overloaded or callbacks
        are blocking too long. Counter is cumulative since broker initialization.
        
        :return: Total number of dropped events since init
        
        Example
        -------
        ```python
            >>> if broker.dropped_event_count > 0:
            ...     print(f"Warning: {broker.dropped_event_count} events lost")
        ```
        """

    def __enter__(self) -> "BLEBroker":
        """
        Context manager entry.
        
        :return: Self for context manager protocol
        """

    def __exit__(self, *args) -> None:
        """
        Context manager exit - cleanup resources.
        
        Automatically calls deinit() when exiting context.
        """

    def deinit(self) -> None:
        """
        Cleanup BLE resources and stop advertising.
        
        Safely disconnects all clients, stops advertising, and deactivates
        the BLE interface. Safe to call multiple times - subsequent calls
        are ignored. After calling, the broker cannot be reused.
        
        :raises: No exceptions raised - all errors are suppressed or sent to error callback
        
        Example
        -------
        ```python
            >>> broker = BLEBroker()
            >>> # ... use broker ...
            >>> broker.deinit()  # Clean shutdown
            >>> 
            >>> # Or use context manager for automatic cleanup
            >>> with BLEBroker() as broker:
            ...     pass  # deinit() called automatically
        ```
        """

    def subscribe(self, topic: str) -> bool:
        """
        Subscribe to a topic for receiving messages.
        
        After subscribing, messages sent to this topic from connected clients
        will trigger the on_message callback. Subscribing to the same topic
        multiple times has no effect.
        
        :param topic: Topic name (1-64 chars, no ':' allowed)
        
        :return: Always returns True on success
        
        :raises ValueError: If topic is empty, not a string, contains ':', or exceeds 64 chars
        
        Example
        -------
        ```python
            >>> broker.on_message = lambda t, p: print(f"{t}: {p}")
            >>> broker.subscribe("sensors/temp")
            >>> broker.subscribe("sensors/humidity")
            >>> 
            >>> # Invalid topics raise ValueError
            >>> broker.subscribe("bad:topic")  # ValueError: contains ':'
            >>> broker.subscribe("")  # ValueError: empty topic
        ```
        """

    def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribe from a topic.
        
        After unsubscribing, messages for this topic will no longer trigger
        the on_message callback. Safe to call even if not subscribed.
        
        :param topic: Topic name to unsubscribe from
        
        :return: True if topic was subscribed, False if not subscribed
        
        Example
        -------
        ```python
            >>> broker.subscribe("temp")
            >>> broker.unsubscribe("temp")  # True
            >>> broker.unsubscribe("temp")  # False (already unsubscribed)
        ```
        """

    def publish(self, topic: str, message: str) -> None:
        """
        Publish a message to all connected clients.
        
        Sends a message with the specified topic to all currently connected
        BLE clients via GATT notify. The message format is "topic:payload".
        Failed connections are automatically removed.
        
        :param topic: Topic name (same rules as subscribe)
        :param message: Message payload (string, converted if needed)
        
        :raises ValueError: If topic is invalid, empty, contains ':', or message too large
        :raises ValueError: If total "topic:message" exceeds 512 bytes (BLE MTU limit)
        
        Example
        -------
        ```python
            >>> broker.publish("status", "ready")
            >>> broker.publish("temp", "25.5")
            >>> 
            >>> # Non-string messages are converted
            >>> broker.publish("count", str(42))
            >>> 
            >>> # Large messages raise ValueError
            >>> broker.publish("data", "x" * 600)  # ValueError: too large
        ```
        """


class Led(machine.Pin):
    """
    Built-in LED control class for RP2350 board wireless module.
    
    This class provides direct control of the built-in LED connected to the
    wireless module GPIO (WL_GPIO0). Inherits from machine.Pin with output
    configuration, enabling standard Pin object operations for simple on/off
    control and visual feedback.
    
    The LED is directly connected to the wireless module's GPIO pin and provides
    immediate visual feedback without requiring external components or wiring.
    It supports all standard Pin object operations and can be integrated into
    various signaling patterns for system status indication.
    
    Key Features:
    
        - Direct control of built-in hardware LED
        - Standard machine.Pin interface (on/off/value/toggle)
        - No external wiring or components required
        - Low power consumption suitable for battery applications
        - Immediate visual feedback for debugging and status indication
        - Active high logic (HIGH = LED on, LOW = LED off)
        
    """
    
    def __init__(self):
        """
        Initialize the built-in LED control interface.
        
        Creates an LED control instance configured for the RP2350 board's
        built-in LED connected to WL_GPIO0. The LED is initialized as an
        output pin and ready for immediate use.
        
        Example
        --------
        ```python
            >>> # Basic LED control
            >>> led = Led()
            >>> led.on()     # Turn LED on
            >>> led.off()    # Turn LED off
            >>> led.toggle() # Toggle current state
            >>> 
            >>> # Status indication based on system state
            >>> led = Led()
            >>> wifi = WifiManager()
            >>> if wifi.connect("MyNetwork", "password"):
            ...     led.on()  # Solid on when connected
            ... else:
            ...     # Blink pattern for connection failure
            ...     for _ in range(3):
            ...         led.on()
            ...         utime.sleep_ms(200)
            ...         led.off()
            ...         utime.sleep_ms(200)
            >>> 
            >>> # Heartbeat pattern for system monitoring
            >>> led = Led()
            >>> def heartbeat():
            ...     led.on()
            ...     utime.sleep_ms(100)   # Short pulse
            ...     led.off()
            ...     utime.sleep_ms(1900)  # Long pause (2 second cycle)
        ```
        """


class Button:
    """
    Built-in BOOTSEL button interface for RP2350 board user input.
    
    This class provides access to the built-in BOOTSEL button on the RP2350 board,
    enabling user input without requiring external components or wiring. The button
    serves dual purposes: boot selection during startup and general-purpose input
    during normal operation, making it ideal for simple user interfaces and control.
    
    The button is hardware-debounced and provides reliable digital input through
    the RP2040/RP2350's dedicated BOOTSEL functionality. It offers immediate
    response suitable for real-time applications while maintaining electrical
    isolation from user circuits.
    """
    
    @staticmethod
    def read() -> bool:
        """
        Read the current state of the built-in BOOTSEL button.
        
        This method provides immediate access to the button state without
        debouncing delays or edge detection. The hardware handles bounce
        elimination, providing clean digital readings suitable for both
        polling and edge detection applications.
        
        :return: True if button is currently pressed, False if released
        
        :raises OSError: If button hardware access fails (rare)
        
        Example
        --------
        ```python
            >>> # Basic button state checking
            >>> if Button.read():
            ...     print("Button pressed")
            >>> 
            >>> # Wait for button press with timeout
            >>> import utime
            >>> timeout_ms = 5000
            >>> start = utime.ticks_ms()
            >>> 
            >>> while not Button.read():
            ...     if utime.ticks_diff(utime.ticks_ms(), start) > timeout_ms:
            ...         print("Timeout - no button press")
            ...         break
            ... else:
            ...     print("Button pressed within timeout")
            >>> 
            >>> # Edge detection for event-driven control
            >>> last_state = False
            >>> while True:
            ...     current = Button.read()
            ...     if current and not last_state:  # Rising edge
            ...         print("Button press detected")
            ...         # Handle button press event here
            ...     last_state = current
            ...     utime.sleep_ms(50)  # Polling interval
        ```
        """


class Din:
    """
    Digital input pin control class for multiple GPIO pins with advanced callback support.
    
    This class provides comprehensive digital input functionality for multiple
    GPIO pins with support for pull-up/pull-down resistors, interrupt callbacks,
    and convenient indexing operations. Designed for reading switches, buttons,
    sensors, and other digital input devices.
    
    Features:
    
        - Multiple pin support with unified interface
        - Configurable pull-up, pull-down, or open-drain modes
        - Individual and group callback configuration via indexing/slicing
        - Edge detection capabilities (rising/falling/both)
        - Automatic measurement control with user callbacks
        - Pin number extraction for callbacks
        - Unified indexing/slicing interface consistent with other classes
    
    Constants:
    
        - Din.LOW (0): Logic low level
        - Din.HIGH (1): Logic high level
        - Din.PULL_DOWN: Pull-down resistor configuration
        - Din.PULL_UP: Pull-up resistor configuration
        - Din.OPEN_DRAIN: Open-drain configuration
        - Din.CB_FALLING: Falling edge interrupt trigger
        - Din.CB_RISING: Rising edge interrupt trigger
    """
    LOW         = 0
    HIGH        = 1
    
    PULL_DOWN   = machine.Pin.PULL_DOWN
    PULL_UP     = machine.Pin.PULL_UP
    OPEN_DRAIN  = machine.Pin.OPEN_DRAIN
    CB_FALLING  = machine.Pin.IRQ_FALLING
    CB_RISING   = machine.Pin.IRQ_RISING
    CB_BOTH     = machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING
        
    def __init__(self, pins: list[int]|tuple[int, ...]):
        """
        Initialize digital input pins with optional pull resistors.
        
        Creates digital input pin objects with configurable pull resistors.
        Callbacks and edge detection are configured via the view interface
        after initialization.
        
        :param pins: List of GPIO pin numbers to be used as digital inputs
                
        :raises ValueError: If pins list is empty or contains invalid pin numbers
        :raises OSError: If GPIO pin initialization fails
        
        Example
        --------
        ```python
            >>> # Basic setup - configure pull resistors separately
            >>> inputs = Din([12, 13, 14, 15])
            >>> inputs[:].pull = Din.PULL_UP     # All pins pull-up
            >>> inputs[0].pull = Din.PULL_DOWN   # First pin pull-down
            >>> inputs[1:3].pull = None          # Pins 1-2 no pull
        ```
        """
        
    def deinit(self) -> None:
        """
        Deinitialize all digital input pins and release resources.
        
        Safely shuts down all input pins by disabling interrupts and
        releasing GPIO resources. Should be called when inputs are
        no longer needed.
        
        Example
        -------
        ```python
            >>> inputs = Din([10, 11, 12])
            >>> # ... use inputs ...
            >>> inputs.deinit()  # Clean shutdown
        ```
        """

    def __getitem__(self, idx: int|slice) -> "_DinView":
        """
        Get a view for controlling specific input pin(s) through indexing or slicing.
        
        Returns a DinView that provides access to individual pins or groups of pins
        using the same interface. Supports both single indexing and slice notation.
        
        :param idx: Index (int) or slice for pin selection
        
            - int: Single pin index (0-based)
            - slice: Range of pins (supports start:stop:step)

        :return: _DinView instance for selected pin(s)
        
        :raises IndexError: If pin index is out of range
        :raises TypeError: If index is not int or slice
        
        Example
        --------
        ```python
            >>> inputs = Din([10, 11, 12, 13])
            >>> 
            >>> # Single pin access
            >>> first_pin = inputs[0]           # First pin
            >>> last_pin = inputs[-1]           # Last pin
            >>> 
            >>> # Multiple pin access with slicing
            >>> first_two = inputs[0:2]         # First two pins
            >>> last_two = inputs[2:4]          # Last two pins
            >>> all_pins = inputs[:]            # All pins
            >>> even_pins = inputs[::2]         # Even-indexed pins (0, 2)
            >>> odd_pins = inputs[1::2]         # Odd-indexed pins (1, 3)
        ```
        """
        if isinstance(idx, slice):
            indices = list(range(*idx.indices(len(self._pins))))
            return Din._DinView(self, indices)
        elif isinstance(idx, int):
            if not (0 <= idx < len(self._pins)):
                raise IndexError("Pin index out of range")
            return Din._DinView(self, [idx])
        else:
            raise TypeError("Index must be int or slice")
        
    def __len__(self) -> int:
        """
        Get the number of digital input pins configured.
        
        :return: Number of pins configured
        
        Example
        --------
        ```python
            >>> inputs = Din([10, 11, 12, 13, 14])
            >>> print(len(inputs))  # Output: 5
        ```
        """


    class _DinView:
        """
        View class for controlling individual digital input pins or groups of pins.
        
        This class provides a unified interface for controlling one or more pins
        through the same API. It's returned by Din.__getitem__() and allows
        seamless control of single pins or groups using identical syntax.
        
        Features:
        
            - Consistent API for single pin or multi-pin control
            - Property-based interface for intuitive control
            - Callback configuration and management
            - Edge detection configuration
            - Measurement enable/disable control
            
        """

        def __init__(self, parent: "Din", indices: list[int]):
            """
            Initialize input view with parent reference and pin indices.
            
            :param parent: Parent Din instance
            :param indices: List of pin indices this view controls
            """

        def __getitem__(self, idx: int|slice) -> "Din._DinView":
            """
            Get a sub-view of this view for further pin selection.
            
            Allows nested selection of pins from an existing view,
            enabling fine-grained control over pin groups.
            
            :param idx: Index or slice for sub-selection
            :return: New _DinView with selected pins
            
            Example
            --------
            ```python
                >>> inputs = Din([10, 11, 12, 13])
                >>> group = inputs[0:3]        # First three pins
                >>> subgroup = group[1:3]      # Second and third from original
                >>> subgroup.measurement = True # Control sub-selection
            ```
            """
            if isinstance(idx, slice):
                selected_indices = [self._indices[i] for i in range(*idx.indices(len(self._indices)))]
                return Din._DinView(self._parent, selected_indices)
            else:
                return Din._DinView(self._parent, [self._indices[idx]])
            
        def __len__(self) -> int:
            """
            Get the number of pins in this view.
            
            :return: Number of pins controlled by this view
            
            Example
            --------
                >>> inputs = Din([10, 11, 12, 13])
                >>> group = inputs[1:3]
                >>> print(len(group))  # Output: 2
            ```
            """

        @property
        def pull(self) -> list[int|None]:
            """
            Get pull resistor configuration for pins in this view.
            
            Returns the current pull resistor settings for each pin.
            Values can be Din.PULL_UP, Din.PULL_DOWN, or None.
            
            :return: List of pull resistor configurations
            
            Example
            --------
            ```python
                >>> inputs = Din([10, 11, 12])
                >>> 
                >>> # Check current pull settings
                >>> pull_configs = inputs[:].pull
                >>> print(f"Pull configs: {pull_configs}")  # [None, None, None]
                >>> 
                >>> # Check specific pin
                >>> first_pull = inputs[0].pull
                >>> print(f"First pin pull: {first_pull}")  # [None]
            ```
            """

        @pull.setter
        def pull(self, pull_type: int|None|list[int|None]):
            """
            Set pull resistor configuration for pins in this view.
            
            Configures the internal pull resistors for the selected pins.
            This provides much more flexibility than setting pull in __init__.
            
            :param pull_type: Pull resistor configuration
                             - Din.PULL_UP: Enable internal pull-up resistor
                             - Din.PULL_DOWN: Enable internal pull-down resistor
                             - None: No pull resistor (floating input)
                             - List: Individual settings for each pin
            
            Example
            --------
            ```python
                >>> inputs = Din([10, 11, 12, 13])
                >>> 
                >>> # Set all pins to pull-up
                >>> inputs[:].pull = Din.PULL_UP
                >>> 
                >>> # Set individual pin configurations
                >>> inputs[0].pull = Din.PULL_DOWN   # First pin pull-down
                >>> inputs[1].pull = Din.PULL_UP     # Second pin pull-up
                >>> inputs[2].pull = None            # Third pin floating
                >>> 
                >>> # Set different pulls for different groups
                >>> inputs[0:2].pull = Din.PULL_UP   # First two pull-up
                >>> inputs[2:].pull = Din.PULL_DOWN  # Last two pull-down
                >>> 
                >>> # Set individual configurations with list
                >>> inputs[:].pull = [Din.PULL_UP, Din.PULL_DOWN, None, Din.PULL_UP]
                >>> 
                >>> # Button setup with appropriate pulls
                >>> buttons = Din([2, 3, 4])
                >>> buttons[:].pull = Din.PULL_UP    # Buttons typically need pull-up
                >>> 
                >>> # Sensor setup with mixed configurations
                >>> sensors = Din([20, 21, 22, 23])
                >>> sensors[0:2].pull = Din.PULL_DOWN   # Digital sensors
                >>> sensors[2:].pull = None             # Analog sensors (floating)
                >>> 
                >>> # Runtime reconfiguration
                >>> if sensor_type == "DIGITAL":
                ...     inputs[0].pull = Din.PULL_UP
                ... elif sensor_type == "ANALOG":
                ...     inputs[0].pull = None
                >>> 
                >>> # Configuration validation
                >>> current_pulls = inputs[:].pull
                >>> for i, pull in enumerate(current_pulls):
                ...     if pull == Din.PULL_UP:
                ...         print(f"Pin {i}: Pull-up enabled")
                ...     elif pull == Din.PULL_DOWN:
                ...         print(f"Pin {i}: Pull-down enabled")
                ...     else:
                ...         print(f"Pin {i}: Floating input")
            ```
            """

        @property
        def pins(self) -> list:
            """
            Get the underlying machine.Pin objects for pins in this view.
            
            :return: List of machine.Pin objects for selected pins
            
            Example
            --------
            ```python
                >>> din = Din([2, 3, 4])
                >>> first_pin = din[0].pins[0]  # GPIO 2 Pin object
                >>> all_pins = din[:].pins       # All Pin objects
            ```
            """
        
        @property
        def value(self) -> list[int]:
            """
            Get current values of pins in this view.
            
            Returns the current digital values for all pins in the view.
            Always returns a list, even for single pins.
            
            :return: List of digital values (0 or 1)
            
            Example
            --------
            ```python
                >>> inputs = Din([2, 3, 4, 5])
                >>> 
                >>> # Read individual pin (returns list)
                >>> pin0_state = inputs[0].value
                >>> print(f"Pin 0: {pin0_state}")  # Output: Pin 0: [0]
                >>> 
                >>> # Read multiple pins
                >>> first_two = inputs[0:2].value
                >>> print(f"First two: {first_two}")  # Output: First two: [0, 1]
                >>> 
                >>> # Read all pins
                >>> all_states = inputs[:].value
                >>> print(f"All pins: {all_states}")  # Output: All pins: [0, 1, 0, 1]
                >>> 
                >>> # Use in conditions
                >>> if inputs[0].value[0] == Din.HIGH:
                ...     print("First input is HIGH")
                >>> 
                >>> # Check multiple inputs
                >>> states = inputs[:].value
                >>> active_count = sum(states)
                >>> print(f"Active inputs: {active_count}/{len(states)}")
            ```
            """

        @property
        def callback(self) -> list[callable]:
            """
            Get callback functions for pins in this view.
            
            Returns the callback functions that will be called when
            edge events occur on the pins.
            
            :return: List of callback functions or None values
            
            Example
            --------
            ```python
                >>> inputs = Din([10, 11, 12])
                >>> callbacks = inputs[:].callback
                >>> print(f"Callbacks: {callbacks}")  # [None, None, None]
                >>> 
                >>> # Check if callback is set
                >>> if inputs[0].callback[0] is not None:
                ...     print("Callback is set for first pin")
            ```
            """

        @callback.setter
        def callback(self, fn: callable | list[callable]):
            """
            Set callback function for pins in this view.
            
            Sets the function to be called when edge events occur.
            Callback receives (pin, rising) parameters where pin is the
            GPIO number and rising is True for rising edge, False for falling.
            
            :param fn: Callback function, None, or list of callbacks
            
            :raises ValueError: If list length doesn't match number of pins
            :raises TypeError: If callback is not callable or None
            
            Example
            --------
            ```python
                >>> inputs = Din([10, 11, 12])
                >>> 
                >>> # Simple callback for all pins
                >>> def input_callback(pin, rising):
                ...     edge_type = "Rising" if rising else "Falling"
                ...     print(f"Pin {pin}: {edge_type} edge detected")
                >>> 
                >>> inputs[:].callback = input_callback
                >>> 
                >>> # Different callbacks for different pins
                >>> def pin1_callback(pin, rising):
                ...     print(f"Button 1: {'Pressed' if not rising else 'Released'}")
                >>> 
                >>> def pin2_callback(pin, rising):
                ...     print(f"Sensor 2: {'Triggered' if rising else 'Clear'}")
                >>> 
                >>> inputs[:].callback = [pin1_callback, pin2_callback, None]
                >>> 
                >>> # Enable edge detection and measurement
                >>> inputs[:].edge = Din.CB_FALLING | Din.CB_RISING
                >>> inputs[:].measurement = True
            ```
            """

        @property
        def edge(self) -> list[int]:
            """
            Get edge detection configuration for pins in this view.
            
            Returns the edge detection settings for each pin.
            Values can be Din.CB_RISING, Din.CB_FALLING, or their combination.
            
            :return: List of edge configuration values
            
            Example
            --------
            ```python
                >>> inputs = Din([10, 11, 12])
                >>> 
                >>> # Check current edge settings
                >>> edges = inputs[:].edge
                >>> print(f"Edge configs: {edges}")  # [0, 0, 0] (no detection)
                >>> 
                >>> # Check specific pin
                >>> first_edge = inputs[0].edge
                >>> print(f"First pin edge: {first_edge}")  # [0]
            ```
            """

        @edge.setter
        def edge(self, edge_type: int):
            """
            Set edge detection type for pins in this view.
            
            Configures which edges trigger interrupts:
            - Din.CB_RISING: Rising edge (LOW to HIGH)
            - Din.CB_FALLING: Falling edge (HIGH to LOW)
            - Din.CB_RISING | Din.CB_FALLING: Both edges
            
            :param edge_type: Edge detection configuration
            
            Example
            --------
            ```python
                >>> inputs = Din([10, 11, 12])
                >>> 
                >>> # Rising edge detection for all pins
                >>> inputs[:].edge = Din.CB_RISING
                >>> 
                >>> # Falling edge for first pin only
                >>> inputs[0].edge = Din.CB_FALLING
                >>> 
                >>> # Both edges for middle pins
                >>> inputs[1:3].edge = Din.CB_RISING | Din.CB_FALLING
                >>> 
                >>> # Setup complete callback system
                >>> def edge_callback(pin, rising):
                ...     print(f"Pin {pin}: {'↑' if rising else '↓'}")
                >>> 
                >>> inputs[:].callback = edge_callback
                >>> inputs[:].edge = Din.CB_RISING | Din.CB_FALLING
                >>> inputs[:].measurement = True
            ```
            """

        @property
        def debounce_us(self) -> list[int]:
            """
            Get debounce filter time in microseconds for pins in this view.
            
            Returns the debounce time settings for each pin. Debouncing helps
            eliminate electrical noise and contact bounce in mechanical switches.
            
            :return: List of debounce times in microseconds
            
            Example
            --------
            ```python
                >>> inputs = Din([10, 11, 12])
                >>> 
                >>> # Check current debounce settings
                >>> debounce_times = inputs[:].debounce_us
                >>> print(f"Debounce times: {debounce_times}")  # [0, 0, 0] (no debouncing)
                >>> 
                >>> # Check specific pin
                >>> first_debounce = inputs[0].debounce_us
                >>> print(f"First pin debounce: {first_debounce}")  # [0]
            ```
            """

        @debounce_us.setter
        def debounce_us(self, us: int):
            """
            Set debounce filter time in microseconds for pins in this view.
            
            Sets the debounce time for noise filtering on mechanical switches.
            When debouncing is enabled, rapid state changes within the debounce
            window are ignored, providing stable readings.
            
            :param us: Debounce time in microseconds
            
                - 0: No debouncing (default)
                - 1000-50000: Typical range for mechanical switches
                - Higher values = more filtering, slower response
    
            Example
            --------
            ```python
                >>> inputs = Din([10, 11, 12])
                >>> 
                >>> # Set debounce for all pins (typical for buttons)
                >>> inputs[:].debounce_us = 20000  # 20ms debounce
                >>> 
                >>> # Different debounce for different pins
                >>> inputs[0].debounce_us = 10000  # 10ms for sensitive button
                >>> inputs[1].debounce_us = 50000  # 50ms for noisy switch
                >>> 
                >>> # Setup complete button system with debouncing
                >>> def button_callback(pin, rising):
                ...     if rising:
                ...         print(f"Button {pin} pressed")
                ...     else:
                ...         print(f"Button {pin} released")
                >>> 
                >>> buttons = Din([2, 3, 4], pull=Din.PULL_UP)
                >>> buttons[:].debounce_us = 20000  # 20ms debounce
                >>> buttons[:].callback = button_callback
                >>> buttons[:].edge = Din.CB_FALLING | Din.CB_RISING
                >>> buttons[:].measurement = True
            ```
            """

        @property
        def measurement(self) -> list[bool]:
            """
            Get measurement state for pins in this view.
            
            Returns whether interrupt-based measurement is enabled for each pin.
            Measurement must be enabled for callbacks to function.
            
            :return: List of measurement state flags
            
            Example
            --------
            ```python
                >>> inputs = Din([10, 11, 12])
                >>> 
                >>> # Check measurement states
                >>> states = inputs[:].measurement
                >>> print(f"Measurement states: {states}")  # [False, False, False]
                >>> 
                >>> # Check specific pin
                >>> first_state = inputs[0].measurement
                >>> print(f"First pin enabled: {first_state}")  # [False]
            ```
            """

        @measurement.setter
        def measurement(self, enabled: bool | list[bool]):
            """
            Enable or disable interrupt-based measurement for pins in this view.
            
            Controls whether callbacks are triggered for edge events.
            Pins must have both callback and edge configuration set to function.
            
            :param enabled: Single boolean for all pins or list of booleans
            
            :raises ValueError: If list length doesn't match number of pins
            
            Example
            --------
            ```python
                >>> inputs = Din([10, 11, 12])
                >>> 
                >>> # Setup callback system
                >>> def my_callback(pin, rising):
                ...     print(f"Pin {pin} edge: {rising}")
                >>> 
                >>> inputs[:].callback = my_callback
                >>> inputs[:].edge = Din.CB_RISING | Din.CB_FALLING
                >>> 
                >>> # Enable measurement for all pins
                >>> inputs[:].measurement = True
                >>> 
                >>> # Enable only specific pins
                >>> inputs[:].measurement = [True, False, True]  # First and third only
                >>> 
                >>> # Disable all measurements
                >>> inputs[:].measurement = False
                >>> 
                >>> # Individual pin control
                >>> inputs[0].measurement = True   # Enable first pin
                >>> inputs[1].measurement = False  # Disable second pin
            ```
            """

        def measure_pulse_width(self, level: int, timeout_ms: int = 1000) -> int:
            """
            Measure pulse width using machine.time_pulse_us() for hardware-level precision.
            
            This method uses MicroPython's built-in hardware timing function to measure
            pulse widths with microsecond accuracy. Works only with single pin for
            optimal precision and timing accuracy.
            
            :param level: Level to measure (Din.HIGH or Din.LOW)
            :param timeout_ms: Timeout in milliseconds
            :return: Pulse width in microseconds, -1 if timeout or error
            
            :raises ValueError: If this view contains more than one pin
            
            Example
            --------
            ```python
                >>> din = Din([12, 13, 14, 15])
                >>> din[15].pull = Din.PULL_UP
                >>> 
                >>> # Measure button press (LOW pulse when pressed)
                >>> width = din[15].measure_pulse_width(Din.LOW, 5000)
                >>> if width > 0:
                ...     print(f"Button pressed for {width}μs ({width/1000:.1f}ms)")
                >>> elif width == -1:
                ...     print("Measurement timeout or error")
                >>> 
                >>> # Ultrasonic sensor echo measurement
                >>> echo_pin = Din([3])
                >>> echo_pin[0].pull = None  # No pull resistor for sensor
                >>> width = echo_pin[0].measure_pulse_width(Din.HIGH, 30)
                >>> if width > 0:
                ...     distance_cm = (width * 0.0343) / 2
                ...     print(f"Distance: {distance_cm:.1f}cm")
                >>> 
                >>> # Continuous measurement
                >>> button = Din([12])
                >>> button[0].pull = Din.PULL_UP
                >>> for i in range(10):
                ...     print(f"Measurement {i+1}/10 - Press button...")
                ...     width = button[0].measure_pulse_width(Din.LOW, 3000)
                ...     if width > 0:
                ...         if width < 1000:
                ...             print(f"  Quick press: {width}μs")
                ...         else:
                ...             print(f"  Long press: {width/1000:.1f}ms")
                ...     else:
                ...         print("  No press detected")
                ...     utime.sleep_ms(500)
                >>> 
                >>> # Multiple pins - use individual calls
                >>> sensors = Din([14, 15, 16])
                >>> # Correct - individual measurements
                >>> width1 = sensors[0].measure_pulse_width(Din.HIGH, 1000)
                >>> width2 = sensors[1].measure_pulse_width(Din.HIGH, 1000)
                >>> width3 = sensors[2].measure_pulse_width(Din.HIGH, 1000)
                >>> 
                >>> # Incorrect - will raise ValueError
                >>> # width = sensors[:].measure_pulse_width(Din.HIGH, 1000)
            ```
            """


class Dout:
    """
    Digital output pin control class with Active High/Low logic support.
    
    This class provides comprehensive digital output functionality with support
    for both Active High and Active Low logic, making it compatible with various
    hardware devices that have different activation requirements.
    
    Logic Types:
    
        - LOGIC_HIGH (Active High): HIGH = active/on, LOW = inactive/off
        - LOGIC_LOW (Active Low): LOW = active/on, HIGH = inactive/off
    
    Constants:
    
        - Dout.LOW (0): Logic low level
        - Dout.HIGH (1): Logic high level
        - Dout.LOGIC_HIGH: Active high logic (default)
        - Dout.LOGIC_LOW: Active low logic
        - Dout.PULL_DOWN: Pull-down resistor configuration
        - Dout.PULL_UP: Pull-up resistor configuration
        - Dout.OPEN_DRAIN: Open-drain configuration
        
    """
    LOW         = 0
    HIGH        = 1
    LOGIC_HIGH  = True   # Active High: HIGH = active
    LOGIC_LOW   = False  # Active Low: LOW = active
    PULL_DOWN   = machine.Pin.PULL_DOWN
    PULL_UP     = machine.Pin.PULL_UP
    OPEN_DRAIN  = machine.Pin.OPEN_DRAIN

    def __init__(self, pins: list[int]|tuple[int, ...]):
        """
        Initialize digital output pins with default active high logic.
        
        Creates digital output pin objects configured for driving external devices.
        All pins are initially set to inactive state (logical LOW) for safety.
        Active logic can be configured per pin via the view interface.
        
        :param pins: List of GPIO pin numbers to be used as digital outputs
        
        :raises ValueError: If pins list is empty or contains invalid pin numbers
        :raises OSError: If GPIO pin initialization fails
        
        Example
        --------
        ```python
            >>> # Basic setup with mixed device types
            >>> outputs = Dout([10, 11, 12, 13])
            >>> 
            >>> # Configure active logic per device
            >>> outputs[0:2].active = Dout.LOGIC_HIGH   # LEDs (active high)
            >>> outputs[2:4].active = Dout.LOGIC_LOW    # Relays (active low)
            >>> 
            >>> # All start in inactive state regardless of logic type
            >>> outputs[:].value = Dout.LOW             # All devices OFF
        ```
        """

    def deinit(self) -> None:
        """
        Deinitialize all digital output pins and release resources.
        
        This method safely shuts down all output pins by setting them to inactive
        state (considering active logic) and then switching to input mode with
        pull-down to avoid floating states.
        
        Example
        --------
        ```python
            >>> outputs = Dout([10, 11, 12])
            >>> outputs[0].active = Dout.LOGIC_HIGH
            >>> outputs[1].active = Dout.LOGIC_LOW
            >>> outputs[:].value = Dout.HIGH  # Turn on all devices
            >>> 
            >>> # Safe shutdown - all devices will be turned off
            >>> outputs.deinit()
        ```
        """

    def __getitem__(self, idx: int|slice) -> "_DoutView":
        """
        Get a view for controlling specific output pin(s).
        
        :param idx: Index (int) or slice for pin selection
        
            - int: Single pin index (0-based)
            - slice: Range of pins (supports start:stop:step)
        
        :return: _DoutView instance for selected pin(s)
        
        :raises IndexError: If pin index is out of range
        :raises TypeError: If index is not int or slice
        
        Example
        --------
        ```python
            >>> outputs = Dout([10, 11, 12, 13])
            >>> 
            >>> # Single pin access
            >>> first_pin = outputs[0]           # First pin
            >>> last_pin = outputs[-1]           # Last pin
            >>> 
            >>> # Multiple pin access with slicing
            >>> first_two = outputs[0:2]         # First two pins
            >>> last_two = outputs[2:4]          # Last two pins
            >>> all_pins = outputs[:]             # All pins
            >>> even_pins = outputs[::2]          # Even-indexed pins (0, 2)
            >>> odd_pins = outputs[1::2]          # Odd-indexed pins (1, 3)
        ```
        """
        if isinstance(idx, slice):
            indices = list(range(*idx.indices(len(self._pins))))
            return Dout._DoutView(self, indices)
        elif isinstance(idx, int):
            if not (0 <= idx < len(self._pins)):
                raise IndexError("Pin index out of range")
            return Dout._DoutView(self, [idx])
        else:
            raise TypeError("Index must be int or slice")

    def __len__(self) -> int:
        """
        Get the number of digital output pins configured.
        
        :return: Number of pins configured
        
        Example
        --------
        ```python
            >>> outputs = Dout([10, 11, 12, 13, 14])
            >>> print(len(outputs))  # Output: 5
        ``` 
        """

    class _DoutView:
        """View class for controlling individual digital output pins or groups."""

        def __init__(self, parent: "Dout", indices: list[int]):
            """
            Initialize output view with parent reference and pin indices.

            :param parent: Parent Dout instance
            :param indices: List of pin indices this view controls
            """

        def __getitem__(self, idx: int|slice) -> "Dout._DoutView":
            """
            Get a sub-view of this view for further pin selection.
            
            Allows nested selection of pins from an existing view,
            enabling fine-grained control over pin groups.
            
            :param idx: Index or slice for sub-selection
            :return: New _DoutView with selected pins
            
            Example
            --------
            ```python
                >>> outputs = Dout([10, 11, 12, 13])
                >>> group = outputs[0:3]        # First three pins
                >>> subgroup = group[1:3]       # Second and third from original
                >>> subgroup.measurement = True # Control sub-selection
            ```
            """
            if isinstance(idx, slice):
                selected_indices = [self._indices[i] for i in range(*idx.indices(len(self._indices)))]
                return Dout._DoutView(self._parent, selected_indices)
            else:
                return Dout._DoutView(self._parent, [self._indices[idx]])

        def __len__(self) -> int:
            """
            Get the number of pins in this view.
            
            :return: Number of pins controlled by this view
            
            Example
            --------
            ```python
                >>> outputs = Dout([10, 11, 12, 13])
                >>> group = outputs[1:3]
                >>> print(len(group))  # Output: 2
            ```
            """

        @property
        def active(self) -> list[bool]:
            """
            Get active logic configuration for pins in this view.
            
            Returns the current active logic settings for each pin.
            Values are Dout.LOGIC_HIGH (True) or Dout.LOGIC_LOW (False).
            
            :return: List of active logic configurations
            
            Example
            --------
            ```python
                >>> outputs = Dout([10, 11, 12])
                >>> outputs[1].active = Dout.LOGIC_LOW
                >>> 
                >>> # Check active logic settings
                >>> logic_configs = outputs[:].active
                >>> print(f"Active logic: {logic_configs}")  # [True, False, True]
                >>> 
                >>> # Check specific pin
                >>> first_logic = outputs[0].active
                >>> print(f"First pin logic: {first_logic}")  # [True]
            ```
            """

        @active.setter
        def active(self, logic_type: bool | list[bool]):
            """
            Set active logic configuration for pins in this view.
            
            Configures whether pins use active high or active low logic.
            This affects how logical HIGH/LOW values are translated to physical
            pin states, allowing unified control of mixed device types.
            
            :param logic_type: Active logic configuration
            
                - Dout.LOGIC_HIGH (True): HIGH = active, LOW = inactive
                - Dout.LOGIC_LOW (False): LOW = active, HIGH = inactive
                - List: Individual settings for each pin
            
            Example
            --------
            ```python
                >>> outputs = Dout([10, 11, 12, 13])
                >>> 
                >>> # Set all pins to active high (default)
                >>> outputs[:].active = Dout.LOGIC_HIGH
                >>> 
                >>> # Set specific pins to active low
                >>> outputs[1:3].active = Dout.LOGIC_LOW  # Relay modules
                >>> 
                >>> # Mixed configuration with list
                >>> outputs[:].active = [Dout.LOGIC_HIGH, Dout.LOGIC_LOW, 
                ...                      Dout.LOGIC_LOW, Dout.LOGIC_HIGH]
                >>> 
                >>> # Device-specific configuration
                >>> led_strip = Dout([14, 15, 16])
                >>> led_strip[:].active = Dout.LOGIC_HIGH  # Standard LEDs
                >>> 
                >>> relay_board = Dout([20, 21, 22, 23])
                >>> relay_board[:].active = Dout.LOGIC_LOW  # Active-low relays
                >>> 
                >>> # Logical control works the same for all
                >>> led_strip[:].value = Dout.HIGH    # LEDs on (physical HIGH)
                >>> relay_board[:].value = Dout.HIGH  # Relays on (physical LOW)
                >>> 
                >>> # Runtime logic change (preserves current state)
                >>> motor = Dout([25])
                >>> motor[0].value = Dout.HIGH        # Motor on
                >>> motor[0].active = Dout.LOGIC_LOW  # Change to active low
                >>> # Motor stays on, but now HIGH means on via LOW signal
            ```
            """

        @property
        def pull(self) -> list[int|None]:
            """
            Get pull resistor configuration for pins in this view.
            Returns the current pull resistor settings for each pin.
            
            :return: List of pull configurations (None, PULL_UP, PULL_DOWN)
            
            Example
            --------
            ```python    
                >>> outputs = Dout([10, 11, 12])
                >>> outputs[0].pull = Dout.PULL_UP
                >>> outputs[1].pull = Dout.PULL_DOWN
                >>> outputs[2].pull = None
                >>>
                # Check pull configurations
                >>> pull_configs = outputs[:].pull
                >>> print(f"Pull configs: {pull_configs}")  # [Dout.PULL_UP, Dout.PULL_DOWN, None]
            ```
            """

        @pull.setter
        def pull(self, pull_type: int|None|list[int|None]):
            """
            Set pull resistor configuration for pins in this view.
            Configures the pull-up or pull-down resistors for each pin.
            
            :param pull_type: Pull configuration
            
                - int: Single pull type for all pins (Dout.PULL_UP, Dout.PULL_DOWN, None)
                - None: No pull resistor
                - list: Individual pull settings for each pin

            :raises ValueError: If list length doesn't match number of pins
      
            Example
            --------
            ```python
                >>> outputs = Dout([10, 11, 12])
                >>> outputs[:].pull = Dout.PULL_UP      # All pins pull-up
                >>> outputs[0].pull = Dout.PULL_DOWN    # First pin pull-down
            ```
            """

        @property
        def pins(self) -> list:
            """
            Get the underlying machine.Pin objects for pins in this view.
            
            :return: List of machine.Pin objects for selected pins
            
            Example
            --------
            ```python
                >>> dout = Dout([2, 3, 4])
                >>> first_pin = dout[0].pins[0]   # GPIO 2 Pin object
                >>> all_pins = dout[:].pins       # All Pin objects
            ```
            """

        @property
        def value(self) -> list[int]:
            """
            Get current logical values of pins in this view.
            
            Returns the logical values (considering active logic configuration).
            Always returns a list, even for single pins.
            
            :return: List of logical values (0 or 1)
            
            Example
            --------
            ```python
                >>> outputs = Dout([10, 11])
                >>> outputs[0].active = Dout.LOGIC_HIGH
                >>> outputs[1].active = Dout.LOGIC_LOW
                >>> 
                >>> # Both devices are logically "on"
                >>> outputs[:].value = Dout.HIGH
                >>> 
                >>> # Read logical states
                >>> logical_states = outputs[:].value  # [1, 1]
                >>> print(f"Logical states: {logical_states}")
                >>> 
                >>> # Check physical pins
                >>> pin0_physical = outputs[0].pins[0].value()  # 1 (HIGH)
                >>> pin1_physical = outputs[1].pins[0].value()  # 0 (LOW)
                >>> print(f"Physical: pin0={pin0_physical}, pin1={pin1_physical}")
            ```
            """

        @value.setter
        def value(self, val: int | list[int]):
            """
            Set logical values of pins in this view.
            
            Sets the logical values which are automatically translated to appropriate
            physical pin states based on each pin's active logic configuration.
            
            :param val: Logical value(s) to set
            
                - int: Same logical value for all pins (0 or 1)
                - list: Individual logical values for each pin
    
            :raises ValueError: If list length doesn't match number of pins
            
            Example
            --------
            ```python
                >>> outputs = Dout([10, 11, 12, 13])
                >>> 
                >>> # Configure mixed active logic
                >>> outputs[0:2].active = Dout.LOGIC_HIGH  # LEDs
                >>> outputs[2:4].active = Dout.LOGIC_LOW   # Relays
                >>> 
                >>> # Logical control - all devices "ON"
                >>> outputs[:].value = Dout.HIGH
                >>> # Result: LEDs get HIGH, Relays get LOW
                >>> 
                >>> # Individual logical control
                >>> outputs[:].value = [1, 0, 1, 0]  # Mixed on/off pattern
                >>> 
                >>> # Unified device control regardless of polarity
                >>> all_on = [Dout.HIGH] * len(outputs)
                >>> outputs[:].value = all_on
                >>> 
                >>> # Device-type specific control
                >>> led_controller = Dout([14, 15, 16])
                >>> led_controller[:].active = Dout.LOGIC_HIGH
                >>> led_controller[:].value = Dout.HIGH  # All LEDs on
                >>> 
                >>> relay_controller = Dout([20, 21, 22])
                >>> relay_controller[:].active = Dout.LOGIC_LOW
                >>> relay_controller[:].value = Dout.HIGH  # All relays on
            ```
            """

        def toggle(self) -> None:
            """
            Toggle the logical state of all pins in this view.
            
            Changes each pin from logical HIGH to LOW or LOW to HIGH,
            automatically handling the physical pin transitions based on
            active logic configuration.
            
            Example
            --------
            ```python
                >>> outputs = Dout([10, 11])
                >>> outputs[0].active = Dout.LOGIC_HIGH
                >>> outputs[1].active = Dout.LOGIC_LOW
                >>> 
                >>> # Start with both logically OFF
                >>> outputs[:].value = Dout.LOW
                >>> 
                >>> # Toggle both to logically ON
                >>> outputs[:].toggle()
                >>> # Pin 10: LOW->HIGH (active high)
                >>> # Pin 11: HIGH->LOW (active low)
                >>> 
                >>> # Toggle back to logically OFF
                >>> outputs[:].toggle()
                >>> # Pin 10: HIGH->LOW (active high)
                >>> # Pin 11: LOW->HIGH (active low)
            ```
            """

        @property
        def physical_value(self) -> list[int]:
            """
            Get current physical pin values (bypass active logic).
            
            Returns the actual physical pin states without considering
            active logic configuration. Useful for debugging and diagnostics.
            
            :return: List of physical pin values (0 or 1)
            
            Example
            --------
            ```python
                >>> outputs = Dout([10, 11])
                >>> outputs[0].active = Dout.LOGIC_HIGH
                >>> outputs[1].active = Dout.LOGIC_LOW
                >>> outputs[:].value = Dout.HIGH  # Both logically ON
                >>> 
                >>> logical = outputs[:].value      # [1, 1]
                >>> physical = outputs[:].physical_value  # [1, 0]
                >>> 
                >>> print(f"Logical: {logical}, Physical: {physical}")
                >>> # Output: Logical: [1, 1], Physical: [1, 0]
            ```
            """


class Adc:
    """
    Multi-channel analog-to-digital converter for GPIO pins with advanced callback support.
    
    This class provides comprehensive ADC functionality for reading analog voltages from
    multiple GPIO pins with support for automatic periodic sampling, user-defined
    callback functions, and convenient indexing operations. Only GPIO pins 26, 27, and 28
    support ADC functionality on the RP2350 board.
    
    Features:
    
        - Multiple ADC channel support (GPIO 26, 27, 28 only)
        - Individual and group callback configuration via indexing/slicing
        - High-resolution 16-bit ADC readings (0-65535 range)
        - Automatic voltage conversion with 3.3V reference
        - Periodic sampling with configurable intervals
        - Non-blocking measurement control
        - Precision voltage readings to 3 decimal places
        - Unified indexing/slicing interface consistent with other classes
    
    Hardware Specifications:
    
        - Resolution: 16-bit (65536 levels)
        - Reference Voltage: 3.3V
        - Supported Pins: GPIO 26, 27, 28 only
        - Voltage Resolution: ~0.806mV per step
        - Sample Rate: Configurable via timer callbacks
    """
    
    def __init__(self, pins: list[int]|tuple[int, ...]):
        """
        Initialize ADC controller for multiple analog input pins.
        
        Creates ADC instances for the specified GPIO pins. Only GPIO pins 26, 27, and 28
        support ADC functionality on the RP2350 board. Callbacks and periodic sampling
        are configured via the view interface after initialization.
        
        :param pins: List or tuple of GPIO pin numbers (only 26, 27, 28 supported)
        
        :raises ValueError: If unsupported GPIO pins are specified or pins list is empty
        :raises OSError: If ADC initialization fails
        
        Example
        --------
        ```python
            >>> # All ADC channels
            >>> adc = Adc([26, 27, 28])
            >>> 
            >>> # Single channel
            >>> temp_sensor = Adc([26])
            >>> 
            >>> # Two channels for differential measurement
            >>> diff_adc = Adc([26, 27])
            >>> 
            >>> # Configure callbacks after initialization
            >>> adc[:].callback = my_callback
            >>> adc[:].period_ms = 100
            >>> adc[:].measurement = True
        ```
        """

    def deinit(self) -> None:
        """
        Deinitialize all ADC channels and release resources.
        
        Safely shuts down all ADC channels by stopping timers and
        releasing GPIO resources. Should be called when ADC is
        no longer needed.
        
        Example
        --------
        ```python
            >>> adc = Adc([26, 27, 28])
            >>> # ... use ADC ...
            >>> adc.deinit()  # Clean shutdown
        ```
        """

    def __getitem__(self, idx: int|slice) -> "_AdcView":
        """
        Get a view for controlling specific ADC channel(s) through indexing or slicing.
        
        Returns an AdcView that provides access to individual channels or groups of channels
        using the same interface. Supports both single indexing and slice notation.
        
        :param idx: Index (int) or slice for channel selection
                   - int: Single channel index (0-based)
                   - slice: Range of channels (supports start:stop:step)
        :return: _AdcView instance for selected channel(s)
        
        :raises IndexError: If channel index is out of range
        :raises TypeError: If index is not int or slice
        
        Example
        --------
        ```python
            >>> adc = Adc([26, 27, 28])
            >>> 
            >>> # Single channel access
            >>> first_channel = adc[0]        # First channel (GPIO 26)
            >>> last_channel = adc[-1]        # Last channel (GPIO 28)
            >>> 
            >>> # Multiple channel access with slicing
            >>> first_two = adc[0:2]          # First two channels
            >>> all_channels = adc[:]         # All channels
            >>> even_channels = adc[::2]      # Even-indexed channels
        ```
        """
        if isinstance(idx, slice):
            indices = list(range(*idx.indices(len(self._pins))))
            return Adc._AdcView(self, indices)
        elif isinstance(idx, int):
            if not (0 <= idx < len(self._pins)):
                raise IndexError("ADC channel index out of range")
            return Adc._AdcView(self, [idx])
        else:
            raise TypeError("Index must be int or slice")

    def __len__(self) -> int:
        """
        Get the number of ADC channels configured.
        
        :return: Number of channels configured
        
        Example
        --------
        ```python
            >>> adc = Adc([26, 27, 28])
            >>> print(len(adc))  # Output: 3
        ```
        """

    class _AdcView:
        """
        View class for controlling individual ADC channels or groups of channels.
        
        This class provides a unified interface for controlling one or more ADC channels
        through the same API. It's returned by Adc.__getitem__() and allows
        seamless control of single channels or groups using identical syntax.
        
        Features:
        
            - Consistent API for single channel or multi-channel control
            - Property-based interface for intuitive control
            - Callback configuration and management
            - Automatic sampling control
            - Voltage and raw value access
            
        """

        def __init__(self, parent: "Adc", indices: list[int]):
            """
            Initialize ADC view with parent reference and channel indices.
            
            :param parent: Parent Adc instance
            :param indices: List of channel indices this view controls
            """

        def __getitem__(self, idx: int|slice) -> "Adc._AdcView":
            """
            Get a sub-view of this view for further channel selection.
            
            Allows nested selection of channels from an existing view,
            enabling fine-grained control over channel groups.
            
            :param idx: Index or slice for sub-selection
            :return: New _AdcView with selected channels
            
            Example
            --------
            ```python
                >>> adc = Adc([26, 27, 28])
                >>> group = adc[0:3]        # First three channels
                >>> subgroup = group[1:3]   # Second and third from original
                >>> subgroup.measurement = True # Control sub-selection
            ```
            """
            if isinstance(idx, slice):
                selected_indices = [self._indices[i] for i in range(*idx.indices(len(self._indices)))]
                return Adc._AdcView(self._parent, selected_indices)
            else:
                return Adc._AdcView(self._parent, [self._indices[idx]])

        def __len__(self) -> int:
            """
            Get the number of channels in this view.
            
            :return: Number of channels controlled by this view
            
            Example
            --------
            ```python
                >>> adc = Adc([26, 27, 28])
                >>> group = adc[1:3]
                >>> print(len(group))  # Output: 2
            ```
            """

        @property
        def pins(self) -> list[machine.Pin]:
            """
            Get the underlying machine.ADC objects for channels in this view.
            
            :return: List of machine.ADC objects for selected channels
            
            Example
            --------
            ```python
                >>> adc = Adc([26, 27, 28])
                >>> adc_objects = adc[:].pins     # All ADC objects
                >>> first_adc = adc[0].pins[0]    # First ADC object
                >>> raw_value = first_adc.read_u16()  # Direct ADC access
            ```
            """

        @property
        def value(self) -> list[float]:
            """
            Get current voltage values of channels in this view.
            
            Returns the current analog voltage values for all channels in the view.
            Always returns a list, even for single channels. Values are in volts
            with 3 decimal places precision.
                        
            :return: List of voltage values in volts (0.000-3.300V)
            
            Example
            --------
            ```python
                >>> adc = Adc([26, 27, 28])
                >>> 
                >>> # Read individual channel (returns list)
                >>> voltage = adc[0].value
                >>> print(f"Channel 0: {voltage[0]:.3f}V")
                >>> 
                >>> # Read multiple channels
                >>> voltages = adc[:].value
                >>> for i, v in enumerate(voltages):
                ...     print(f"Channel {i}: {v:.3f}V")
                >>> 
                >>> # Use in conditions
                >>> if adc[0].value[0] > 2.5:
                ...     print("High voltage detected")
                >>> 
                >>> # Temperature sensor reading (TMP36)
                >>> temp_voltage = adc[0].value[0]
                >>> temp_celsius = (temp_voltage - 0.5) * 100
                >>> print(f"Temperature: {temp_celsius:.1f}°C")
            ```
            """

        @property
        def raw_value(self) -> list[int]:
            """
            Get current raw ADC values of channels in this view.
            
            Returns the current raw 16-bit ADC values for all channels in the view.
            Always returns a list, even for single channels. Values range from 0-65535.
            
            :return: List of raw ADC values (0-65535)
            
            Example
            --------
            ```python
                >>> adc = Adc([26, 27, 28])
                >>> 
                >>> # Read individual channel raw value
                >>> raw_value = adc[0].raw_value[0]
                >>> print(f"Raw value: {raw_value}")
                >>> 
                >>> # Read all channels raw values
                >>> raw_values = adc[:].raw_value
                >>> for i, raw in enumerate(raw_values):
                ...     print(f"Channel {i}: {raw}/65535")
                >>> 
                >>> # Calculate percentage
                >>> percentage = (adc[0].raw_value[0] / 65535) * 100
                >>> print(f"Input level: {percentage:.1f}%")
                >>> 
                >>> # High-resolution measurements
                >>> raw = adc[0].raw_value[0]
                >>> voltage = raw * (3.3 / 65535)
                >>> print(f"Precise voltage: {voltage:.6f}V")
            ```
            """

        @property
        def callback(self) -> list[callable]:
            """
            Get callback functions for channels in this view.
            
            Returns the callback functions that will be called during
            automatic sampling for the channels.
            
            :return: List of callback functions or None values
            
            Example
            --------
            ```python
                >>> adc = Adc([26, 27, 28])
                >>> callbacks = adc[:].callback
                >>> print(f"Callbacks: {callbacks}")  # [None, None, None]
                >>> 
                >>> # Check if callback is set
                >>> if adc[0].callback[0] is not None:
                ...     print("Callback is set for first channel")
            ```
            """

        @callback.setter
        def callback(self, fn: callable | list[callable]):
            """
            Set callback function for channels in this view.
            
            Sets the function to be called during automatic sampling.
            Callback receives (pin, voltage, raw) parameters where pin is the
            GPIO number, voltage is the value in volts, and raw is the 16-bit value.
            
            :param fn: Callback function, None, or list of callbacks
            
            :raises ValueError: If list length doesn't match number of channels
            :raises TypeError: If callback is not callable or None
            
            Example
            --------
            ```python
                >>> adc = Adc([26, 27, 28])
                >>> 
                >>> # Simple callback for all channels
                >>> def adc_callback(pin, voltage, raw):
                ...     print(f"Pin {pin}: {voltage:.3f}V (raw: {raw})")
                >>> 
                >>> adc[:].callback = adc_callback
                >>> 
                >>> # Different callbacks for different channels
                >>> def temp_callback(pin, voltage, raw):
                ...     temp_c = (voltage - 0.5) * 100  # TMP36 conversion
                ...     print(f"Temperature: {temp_c:.1f}°C")
                >>> 
                >>> def light_callback(pin, voltage, raw):
                ...     light_pct = (voltage / 3.3) * 100
                ...     print(f"Light level: {light_pct:.1f}%")
                >>> 
                >>> adc[:].callback = [temp_callback, light_callback, None]
                >>> 
                >>> # Enable sampling and measurement
                >>> adc[:].period_ms = 500  # Sample every 500ms
                >>> adc[:].measurement = True
            ```
            """

        @property
        def period_ms(self) -> list[int]:
            """
            Get sampling period in milliseconds for channels in this view.
            
            Returns the sampling period settings for each channel.
            0 means automatic sampling is disabled.
            
            :return: List of period values in milliseconds
            
            Example
            --------
            ```python
                >>> adc = Adc([26, 27, 28])
                >>> 
                >>> # Check current period settings
                >>> periods = adc[:].period_ms
                >>> print(f"Periods: {periods}")  # [0, 0, 0] (disabled)
                >>> 
                >>> # Check specific channel
                >>> first_period = adc[0].period_ms
                >>> print(f"First channel period: {first_period}")  # [0]
            ```
            """

        @period_ms.setter
        def period_ms(self, ms: int):
            """
            Set sampling period in milliseconds for channels in this view.
            
            Sets the period for automatic sampling. Must be > 0 to enable
            automatic sampling. Requires both callback and measurement to be enabled.
            
            :param ms: Sampling period in milliseconds
                      - 0: Disable automatic sampling (default)
                      - >0: Enable automatic sampling with specified interval
            
            Example
            --------
            ```python
                >>> adc = Adc([26, 27, 28])
                >>> 
                >>> # Set period for all channels
                >>> adc[:].period_ms = 100  # Sample every 100ms
                >>> 
                >>> # Different periods for different channels
                >>> adc[0].period_ms = 50   # Fast sampling for first channel
                >>> adc[1].period_ms = 200  # Slower sampling for second channel
                >>> 
                >>> # Setup complete automatic sampling system
                >>> def sensor_callback(pin, voltage, raw):
                ...     if pin == 26:  # Temperature sensor
                ...         temp = (voltage - 0.5) * 100
                ...         print(f"Temperature: {temp:.1f}°C")
                ...     elif pin == 27:  # Light sensor
                ...         light = (voltage / 3.3) * 100
                ...         print(f"Light: {light:.1f}%")
                >>> 
                >>> adc[:].callback = sensor_callback
                >>> adc[:].period_ms = 1000  # Sample every second
                >>> adc[:].measurement = True  # Start sampling
            ```
            """

        @property
        def measurement(self) -> list[bool]:
            """
            Get measurement state for channels in this view.
            
            Returns whether automatic sampling is enabled for each channel.
            Measurement must be enabled for callbacks to function.
            
            :return: List of measurement state flags
            
            Example
            --------
            ```python
                >>> adc = Adc([26, 27, 28])
                >>> 
                >>> # Check measurement states
                >>> states = adc[:].measurement
                >>> print(f"Measurement states: {states}")  # [False, False, False]
                >>> 
                >>> # Check specific channel
                >>> first_state = adc[0].measurement
                >>> print(f"First channel enabled: {first_state}")  # [False]
            ```
            """

        @measurement.setter
        def measurement(self, enabled: bool | list[bool]):
            """
            Enable or disable automatic sampling for channels in this view.
            
            Controls whether callbacks are triggered for automatic sampling.
            Channels must have both callback and period_ms configured to function.
            
            :param enabled: Single boolean for all channels or list of booleans
            
            :raises ValueError: If list length doesn't match number of channels
            
            Example
            --------
            ```python
                >>> adc = Adc([26, 27, 28])
                >>> 
                >>> # Setup callback system
                >>> def my_callback(pin, voltage, raw):
                ...     print(f"Pin {pin}: {voltage:.3f}V")
                >>> 
                >>> adc[:].callback = my_callback
                >>> adc[:].period_ms = 100
                >>> 
                >>> # Enable measurement for all channels
                >>> adc[:].measurement = True
                >>> 
                >>> # Enable only specific channels
                >>> adc[:].measurement = [True, False, True]  # First and third only
                >>> 
                >>> # Disable all measurements
                >>> adc[:].measurement = False
                >>> 
                >>> # Individual channel control
                >>> adc[0].measurement = True   # Enable first channel
                >>> adc[1].measurement = False  # Disable second channel
                >>> 
                >>> # Data logging system
                >>> def data_logger(pin, voltage, raw):
                ...     timestamp = utime.ticks_ms()
                ...     print(f"[{timestamp}] Pin {pin}: {voltage:.3f}V")
                >>> 
                >>> logger_adc = Adc([26, 27])
                >>> logger_adc[:].callback = data_logger
                >>> logger_adc[:].period_ms = 500  # Log every 500ms
                >>> logger_adc[:].measurement = True  # Start logging
                >>> 
                >>> # Later stop logging
                >>> logger_adc[:].measurement = False
            ```
            """


class Pwm:
    """
    Multi-channel Pulse Width Modulation (PWM) controller with advanced control features.
    
    This class provides comprehensive PWM functionality for controlling multiple GPIO pins
    with support for various control modes, precise timing, and flexible grouping operations.
    Uses indexing and slicing for intuitive channel control.
    """
    __FULL_RANGE     = 65_535
    __MICROS_PER_SEC = 1_000_000

    def __init__(self, pins: list[int]|tuple[int, ...]):
        """
        Initialize PWM controller for multiple GPIO pins.
        
        Creates PWM instances for the specified GPIO pins. All channels start 
        disabled (0% duty cycle) for safety. Use indexing/slicing to control channels.
        
        :param pins: List or tuple of GPIO pin numbers
        
        Example
        --------
        ```python
            >>> # Basic setup - use indexing/slicing for control
            >>> pwm = Pwm([10, 11, 12, 13])
            >>> pwm[:].freq = 1000      # Set frequency for all
            >>> pwm[:].duty = 0         # Start with all off
            >>> 
            >>> # Individual control
            >>> pwm[0].duty = 50        # First channel 50%
            >>> pwm[1:3].duty = 75      # Channels 1-2 to 75%
        ```
        """

    def deinit(self) -> None:
        """
        Deinitialize all PWM channels and release hardware resources.
        
        Safely shuts down all PWM channels by stopping timers and
        releasing GPIO resources. Should be called when PWM is no longer needed.
        
        Example
        --------
        ```python
            >>> pwm = Pwm([10, 11, 12, 13])
            >>> # ... use PWM ...
            >>> pwm.deinit()
        ```
        """

    def __getitem__(self, idx: int|slice) -> "_PwmView":
        """
        Get a view for controlling specific PWM channels or groups.
        
        This is the primary interface for PWM control. Returns a view object 
        that provides control over the selected channels.
        
        :param idx: Index (int) for single channel or slice for channel groups
        :return: PWM view object for controlling selected channels
        
        Example
        --------
        ```python
            >>> pwm = Pwm([10, 11, 12, 13])
            >>> 
            >>> # All channels
            >>> pwm[:].freq = 1000
            >>> pwm[:].duty = 50
            >>> 
            >>> # Single channel
            >>> pwm[0].duty = 75
            >>> 
            >>> # Channel range
            >>> pwm[1:3].duty = 25
            >>> 
            >>> # Every other channel
            >>> pwm[::2].duty = 100
        ```
        """

    def __len__(self) -> int:
        """
        Get the number of PWM channels configured in this controller.
        
        :return: Number of PWM channels
        
        Example
        --------
        ```python
            >>> pwm = Pwm([10, 11, 12, 13])
            >>> print(len(pwm))
        ```
        """
        return len(self._pins)

    class _PwmView:
        """
        View class for controlling individual PWM channels or groups.
        
        This class provides the actual control interface through properties.
        Accessed via indexing/slicing on the main Pwm object.
        """

        def __init__(self, parent: "Pwm", indices: list[int]):
            """
            Initialize PWM view with parent reference and channel indices.
            
            :param parent: Parent Pwm instance
            :param indices: List of channel indices this view controls
            
            :raises ValueError: If indices are empty or invalid
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11, 12])
                >>> pwm_view = pwm[0:2]
                >>> print(pwm_view.pins)  # List of machine.PWM objects for channels 0 and 1
            ```
            """

        def __getitem__(self, idx: int|slice) -> "Pwm._PwmView":
            """
            Get a sub-view of this view for further channel selection.
            Allows nested selection of channels from an existing view,
            enabling fine-grained control over channel groups.
            
            :param idx: Index or slice for sub-selection
            :return: New _PwmView with selected channels
            
            :raises IndexError: If channel index is out of range
            :raises TypeError: If index is not int or slice
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11, 12, 13])
                >>> group = pwm[0:3]        # First three channels
                >>> subgroup = group[1:3]   # Second and third from original
                >>> subgroup.freq = 500      # Control sub-selection frequency
            ```
            """
            if isinstance(idx, slice):
                selected_indices = [self._indices[i] for i in range(*idx.indices(len(self._indices)))]
                return Pwm._PwmView(self._parent, selected_indices)
            else:
                return Pwm._PwmView(self._parent, [self._indices[idx]])

        def __len__(self) -> int:
            """
            Get the number of channels in this view.
            
            :return: Number of channels controlled by this view
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11, 12, 13])
                >>> group = pwm[1:3]
                >>> print(len(group))
            ```
            """

        @property
        def pins(self) -> list:
            """
            Get the underlying machine.PWM objects for channels in this view.
            Returns a list of machine.PWM objects corresponding to the selected channels.
            
            :return: List of machine.PWM objects for selected channels
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11, 12])
                >>> pwm[:].pins
            ```
            """

        @property
        def freq(self) -> list[int]:
            """
            Get the frequency of selected PWM channels in Hz.
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11, 12])
                >>> pwm[:].freq = 1000
                >>> frequencies = pwm[:].freq  # [1000, 1000, 1000]
                >>> single_freq = pwm[0].freq  # [1000]
            ```
            """

        @freq.setter
        def freq(self, hz: int | list[int]):
            """
            Set the frequency of selected PWM channels.
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11, 12])
                >>> pwm[:].freq = 1000      # All channels
                >>> pwm[0].freq = 2000      # First channel only
                >>> pwm[1:].freq = 500      # Channels 1-2
            ```
            """

        @property
        def period(self) -> list[int]:
            """
            Get the period of selected PWM channels in microseconds.
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11])
                >>> pwm[:].freq = 1000
                >>> periods = pwm[:].period  # [1000, 1000] μs
            ```
            """

        @period.setter
        def period(self, us: int | list[int]):
            """
            Set the period of selected PWM channels in microseconds.
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11])
                >>> pwm[:].period = 20000   # 20ms = 50Hz
                >>> pwm[0].period = 1000    # 1ms = 1kHz for first channel
            ```
            """

        @property
        def duty(self) -> list[int]:
            """
            Get the duty cycle of selected PWM channels as percentage.
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11, 12])
                >>> pwm[:].duty = 50
                >>> duties = pwm[:].duty     # [50, 50, 50]
                >>> first_duty = pwm[0].duty # [50]
            ```
            """

        @duty.setter
        def duty(self, pct: int | list[int]):
            """
            Set the duty cycle of selected PWM channels.
            
            :param pct: Single percentage (0-100) or list of percentages
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11, 12])
                >>> pwm[:].duty = 50            # All channels to 50%
                >>> pwm[0].duty = 75            # First channel to 75%
                >>> pwm[:].duty = [25, 50, 75]  # Individual values
            ```
            """

        @property
        def duty_u16(self) -> list[int]:
            """
            Get raw duty cycle values (0-65535).
            Returns the raw duty cycle values for the selected PWM channels.
            These values represent the duty cycle as a 16-bit integer,
            where 0 is 0% and 65535 is 100%.
            
            :return: List of raw duty cycle values (0-65535)
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11, 12])
                >>> pwm[:].duty_u16 = 32768  # Set all to 50% duty cycle
                >>> duties = pwm[:].duty_u16  # [32768, 32768, 32768]
                >>> first_duty = pwm[0].duty_u16  # [32768]
            ```
            """
   
        @duty_u16.setter
        def duty_u16(self, raw: int | list[int]):
            """
            Set raw duty cycle values (0-65535) for selected PWM channels.
            Sets the duty cycle for the selected PWM channels using raw 16-bit values.
            
            :param raw: Single value (0-65535) or list of values
            :raises ValueError: If list length doesn't match number of channels
            
            :raises TypeError: If raw value is not int or list of ints
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11, 12])
                >>> pwm[:].duty_u16 = 32768  # Set all to 50% duty cycle
                >>> pwm[0].duty_u16 = 16384   # First channel to 25%
                >>> pwm[:].duty_u16 = [0, 32768, 65535]  # Individual values
            ```
            """

        @property
        def duty_us(self) -> list[int]:
            """
            Get duty cycle in microseconds.
            Returns the duty cycle for the selected PWM channels in microseconds.
            The value represents the duration of the HIGH state in microseconds
            relative to the PWM period.
            
            :return: List of duty cycle values in microseconds
            
            :raises ValueError: If period is not set for the channels
            :raises TypeError: If period is not an int or list of ints
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11, 12])
                >>> pwm[:].freq = 50             # Set frequency to 50Hz
                >>> pwm[:].duty_us = 1500        # Set all to center (1.5ms)
                >>> duties = pwm[:].duty_us      # [1500, 1500, 1500]
                >>> first_duty = pwm[0].duty_us  # [1500]
            ```
            """

        @duty_us.setter
        def duty_us(self, us: int | list[int]):
            """
            Set duty cycle in microseconds.
            
            Example
            --------
            ```python
                >>> servo = Pwm([14, 15, 16])
                >>> servo[:].freq = 50
                >>> servo[:].duty_us = 1500    # All to center
                >>> servo[:].duty_us = [1000, 1500, 2000]  # Individual positions
            ```
            """

        @property
        def enabled(self) -> list[bool]:
            """
            Get enabled state of selected PWM channels.
            Returns a list indicating whether each PWM channel is enabled (True) or disabled (False).
            
            :return: List of boolean flags for each channel
            
            :raises ValueError: If indices are empty
            :raises TypeError: If indices are not a list or tuple
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11, 12])
                >>> pwm[:].duty = 50
                >>> pwm[:].enabled  # [True, True, True] (all enabled)
                >>> pwm[0].enabled  # [True]
                >>> pwm[1].enabled  # [True]
                >>> pwm[2].enabled  # [True]
            ```
            """

        @enabled.setter
        def enabled(self, flag: bool | list[bool]):
            """
            Enable or disable selected PWM channels.
            
            Example
            --------
            ```python
                >>> pwm = Pwm([10, 11, 12])
                >>> pwm[:].duty = 50
                >>> pwm[:].enabled = False   # Disable all (duty preserved)
                >>> pwm[0].enabled = True    # Enable first channel only
            ```
            """


def i2cdetect(*, 
              id: int | None = None, 
              sda: int | None = None, 
              scl: int | None = None, 
              deny_pairs: set | None = None, 
              show: bool = False) -> list | None:
    """
    Scan for I2C devices with flexible bus and pin configuration options.
    
    This function scans the I2C bus for connected devices with support for automatic
    bus detection, specific pin pair configuration, and pin pair filtering. Returns
    detailed information about found devices and their locations.
    
    :param id: I2C bus number (0 or 1, optional)
    :param sda: Specific SDA pin to scan (optional)
    :param scl: Specific SCL pin to scan (optional)
    :param deny_pairs: Set of (SDA, SCL) pin pairs to exclude from scanning
    :param show: Display mode control
        
        - True: Print visual device map to console
        - False: Return list of tuples containing pin pairs and device addresses
    
    :return: List of ((sda, scl), [addresses]) tuples if show=False, empty list if no devices found
    
    :raises OSError: If I2C bus initialization fails
    
    Example
    --------
    ```python
        >>> # Quick device detection - get addresses only
        >>> devices = i2cdetect(0)  # Scan bus 0
        >>> if devices:
        ...     print(f"Found {len(devices)} devices: {[hex(addr) for addr in devices]}")
        ... else:
        ...     print("No I2C devices found")
        >>> # Output: Found 2 devices: ['0x48', '0x68']
        >>> 
        >>> # Visual device map display
        >>> i2cdetect(0, show=True)
        >>> # Output:
        >>> #      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
        >>> # 00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
        >>> # 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
        >>> # 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
        >>> # 30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
        >>> # 40: -- -- -- -- -- -- -- -- 48 -- -- -- -- -- -- -- 
        >>> # 50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
        >>> # 60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- -- 
        >>> # 70: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
        >>> 
        >>> # Check for specific devices
        >>> devices = i2cdetect(1)
        >>> if 0x3C in devices:
        ...     print("OLED display found at 0x3C")
        >>> if 0x68 in devices:
        ...     print("RTC module found at 0x68")
        >>> 
        >>> # Scan both I2C buses
        >>> for bus in [0, 1]:
        ...     print(f"Scanning I2C bus {bus}:")
        ...     devices = i2cdetect(bus)
        ...     if devices:
        ...         for addr in devices:
        ...             print(f"  Device at 0x{addr:02X} ({addr})")
        ...     else:
        ...         print("  No devices found")
        >>> 
        >>> # Diagnostic mode - visual display for troubleshooting
        >>> print("I2C Bus Diagnostic:")
        >>> i2cdetect(0, show=True)
        >>> 
        >>> # Integration with I2c class
        >>> devices = i2cdetect(0)
        >>> if 0x48 in devices:
        ...     temp_sensor = I2c(scl=5, sda=4, addr=0x48)
        ...     print("Temperature sensor initialized")
    ```
    """


class SpinLock:
    """
    Hardware spinlock for safe multi-core resource access.
    
    This class provides access to the RP2350's hardware spinlock mechanism for
    coordinating access to shared resources between cores or interrupt handlers.
    Supports both busy-wait and polite (yielding) locking strategies.
    
    Features:
    
        - Hardware-level atomic locking for multi-core safety
        - 32 independent hardware spinlocks (IDs 0-31)
        - Busy-wait mode for minimal latency
        - Polite mode with periodic yielding for CPU efficiency
        - Context manager support for automatic lock management
        - Reserved IDs for I2C and SPI bus protection
    
    Reserved Lock IDs:
    
        - 30: I2C0 bus protection
        - 31: I2C1 bus protection
        - 32: SPI0 bus protection (if supported)
        - 33: SPI1 bus protection (if supported)
    """
    
    def __init__(self, *, lock_id: int, polite: bool = False, yield_every: int = 64):
        """
        Initialize a hardware spinlock.
        
        :param lock_id: Hardware spinlock ID (0-31)
        :param polite: Use polite locking with yielding (default: False)
        :param yield_every: Iterations between yields in polite mode (default: 64)
        
        :raises ValueError: If lock_id is not in range 0-31
        
        Example
        --------
        ```python
            >>> # Basic spinlock usage
            >>> lock = SpinLock(lock_id=10)
            >>> 
            >>> # Manual lock management
            >>> lock.acquire()
            >>> try:
            ...     # Critical section
            ...     shared_data = process_data()
            ... finally:
            ...     lock.release()
            >>> 
            >>> # Context manager (recommended)
            >>> lock = SpinLock(lock_id=10)
            >>> with lock:
            ...     # Critical section automatically protected
            ...     shared_counter += 1
            >>> 
            >>> # Polite locking for longer critical sections
            >>> nice_lock = SpinLock(lock_id=11, polite=True, yield_every=32)
            >>> with nice_lock:
            ...     # Longer operation that yields periodically
            ...     for item in large_dataset:
            ...         process_item(item)
            >>> 
            >>> # Multi-core data structure protection
            >>> data_lock = SpinLock(lock_id=5)
            >>> shared_list = []
            >>> 
            >>> def core0_task():
            ...     with data_lock:
            ...         shared_list.append("core0_data")
            >>> 
            >>> def core1_task():
            ...     with data_lock:
            ...         shared_list.append("core1_data")
            >>> 
            >>> # Using reserved locks for I2C
            >>> i2c_lock = SpinLock(lock_id=I2C0_SPINLOCK_ID)
            >>> with i2c_lock:
            ...     # Custom I2C operations protected
            ...     i2c.writeto(0x48, data)
        ```
        """
        ...
    
    def acquire(self) -> None:
        """
        Acquire the spinlock, blocking until available.
        
        In busy-wait mode, spins continuously until lock is available.
        In polite mode, periodically yields to allow other tasks to run.
        
        Example
        --------
        ```python
            >>> lock = SpinLock(lock_id=15)
            >>> lock.acquire()
            >>> try:
            ...     # Protected code here
            ...     critical_operation()
            ... finally:
            ...     lock.release()
        ```
        """
        ...
    
    def release(self) -> None:
        """
        Release the spinlock.
        
        Makes the lock available for other cores or tasks to acquire.
        Should only be called by the core that acquired the lock.
        
        Example
        --------
        ```python
            >>> lock = SpinLock(lock_id=15)
            >>> lock.acquire()
            >>> # ... critical section ...
            >>> lock.release()
        ```
        """
        ...
    
    def __enter__(self) -> "SpinLock":
        """
        Enter context manager and acquire lock.
        
        :return: The SpinLock instance
        
        Example
        --------
        ```python
            >>> lock = SpinLock(lock_id=20)
            >>> with lock:
            ...     # Lock automatically acquired here
            ...     modify_shared_resource()
            >>> # Lock automatically released here
        ```
        """
        ...
    
    def __exit__(self, et, ev, tb) -> None:
        """
        Exit context manager and release lock.
        
        :param et: Exception type if an exception occurred
        :param ev: Exception value if an exception occurred
        :param tb: Exception traceback if an exception occurred
        """
        ...


class I2CMaster:
    """
    Advanced I2C master interface with hardware spinlock protection.
    
    This class provides a more advanced I2C interface with automatic spinlock
    protection for multi-core safety, retry mechanisms, and enhanced error handling.
    Suitable for complex applications requiring thread-safe I2C access and robust
    error recovery.
    
    Features:
    
        - Automatic hardware spinlock protection for multi-core safety
        - Configurable retry policy for failed operations
        - Enhanced error tracking and reporting
        - Scoped frequency changes with automatic restoration
        - Support for 8-bit and 16-bit register addressing
        - Extended memory operations for complex protocols
        - Thread-safe operation across multiple cores
    """
    
    def __init__(self, *, sda: int, scl: int, freq: int = 400_000, timeout_us: int = 50_000):
        """
        Initialize I2C master with spinlock protection.
        
        :param sda: SDA pin number
        :param scl: SCL pin number
        :param freq: I2C frequency in Hz (default: 400kHz)
        :param timeout_us: I2C operation timeout in microseconds (default: 50ms)
        
        :raises ValueError: If invalid pin combination is provided
        :raises OSError: If I2C initialization fails
        
        Example
        --------
        ```python
            >>> # Standard sensor setup with spinlock protection
            >>> i2c = I2CMaster(sda=4, scl=5, freq=400_000)
            >>> 
            >>> # High-speed device
            >>> fast_i2c = I2CMaster(sda=20, scl=21, freq=1_000_000)
            >>> 
            >>> # Slow device with longer timeout
            >>> slow_i2c = I2CMaster(sda=12, scl=13, freq=100_000, timeout_us=100_000)
            >>> 
            >>> # Multi-core safe access
            >>> sensor = I2CMaster(sda=4, scl=5)
            >>> def core0_read():
            ...     temp = sensor.read_u8(0x48, 0x00)
            ...     return temp
            >>> 
            >>> def core1_read():
            ...     pressure = sensor.read_u16(0x76, 0xF7)
            ...     return pressure
        ```
        """
        ...
    
    @property
    def bus_id(self) -> int:
        """
        Get the I2C bus ID (0 or 1).
        
        :return: I2C bus number
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> print(f"Using I2C bus {i2c.bus_id}")
        ```
        """
        ...
    
    @property
    def pins(self) -> tuple[int, int]:
        """
        Get the (SDA, SCL) pin tuple.
        
        :return: Tuple of (SDA pin, SCL pin)
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> sda, scl = i2c.pins
            >>> print(f"Using pins: SDA={sda}, SCL={scl}")
        ```
        """
        ...
    
    @property
    def last_error(self) -> int:
        """
        Get the last error code from I2C operations.
        
        :return: Error code (STAT_OK, STAT_TIMEOUT, STAT_BUS_ERR, STAT_NO_DEVICE)
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> try:
            ...     data = i2c.read_u8(0x48, 0x00)
            ... except OSError:
            ...     if i2c.last_error == STAT_TIMEOUT:
            ...         print("Operation timed out")
            ...     elif i2c.last_error == STAT_NO_DEVICE:
            ...         print("Device not found")
        ```
        """
        ...
    
    def set_retry_policy(self, *, retries: int | None = None, delay_us: int | None = None) -> None:
        """
        Configure retry policy for failed I2C operations.
        
        :param retries: Number of retry attempts (None to keep current)
        :param delay_us: Delay between retries in microseconds (None to keep current)
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> # Set aggressive retry policy
            >>> i2c.set_retry_policy(retries=5, delay_us=500)
            >>> 
            >>> # Disable retries
            >>> i2c.set_retry_policy(retries=0)
        ```
        """
        ...
    
    def set_timeout(self, timeout_us: int) -> None:
        """
        Set I2C operation timeout in microseconds.
        
        :param timeout_us: Timeout value in microseconds
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> # Set longer timeout for slow devices
            >>> i2c.set_timeout(100_000)  # 100ms
        ```
        """
        ...
    
    def set_freq(self, freq: int) -> None:
        """
        Set I2C bus frequency in Hz.
        
        :param freq: Frequency in Hz (typically 100kHz or 400kHz)
        
        :raises ValueError: If frequency is <= 0
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> # Switch to standard mode
            >>> i2c.set_freq(100_000)
        ```
        """
        ...
    
    def scoped_freq(self, freq: int):
        """
        Context manager for temporary frequency change.
        
        :param freq: Temporary frequency in Hz
        :return: Context manager that restores original frequency on exit
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5, freq=400_000)
            >>> # Temporarily use slower frequency
            >>> with i2c.scoped_freq(100_000):
            ...     # Operations here use 100kHz
            ...     data = i2c.read_u8(0x50, 0x00)
            >>> # Frequency restored to 400kHz here
        ```
        """
        ...
    
    def deinit(self) -> None:
        """
        Deinitialize the I2C master.
        
        Releases I2C hardware resources. Should be called when done with the interface.
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> # ... use i2c ...
            >>> i2c.deinit()
        ```
        """
        ...
    
    def probe(self, addr: int) -> bool:
        """
        Test if device exists at given address.
        
        :param addr: 7-bit I2C device address (0x00-0x7F)
        :return: True if device responds, False otherwise
        
        :raises ValueError: If address is out of valid range
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> if i2c.probe(0x48):
            ...     print("Temperature sensor found")
            ... else:
            ...     print("No device at 0x48")
        ```
        """
        ...
    
    def readfrom(self, addr: int, nbytes: int, *, stop: bool = True) -> bytes:
        """
        Read bytes from I2C device.
        
        :param addr: 7-bit I2C device address
        :param nbytes: Number of bytes to read
        :param stop: Send stop condition after read (default: True)
        :return: Bytes read from device
        
        :raises ValueError: If addr is out of range
        :raises OSError: If I2C communication fails
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> data = i2c.readfrom(0x48, 2)
            >>> print(f"Read: {data.hex()}")
        ```
        """
        ...
    
    def readfrom_into(self, addr: int, buf: bytearray, *, stop: bool = True) -> None:
        """
        Read bytes from I2C device into buffer.
        
        :param addr: 7-bit I2C device address
        :param buf: Bytearray to store read data
        :param stop: Send stop condition after read (default: True)
        
        :raises ValueError: If addr is out of range
        :raises OSError: If I2C communication fails
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> buffer = bytearray(10)
            >>> i2c.readfrom_into(0x48, buffer)
        ```
        """
        ...
    
    def writeto(self, addr: int, buf: bytes, *, stop: bool = True) -> int:
        """
        Write bytes to I2C device.
        
        :param addr: 7-bit I2C device address
        :param buf: Bytes to write
        :param stop: Send stop condition after write (default: True)
        :return: Number of bytes written
        
        :raises ValueError: If addr is out of range
        :raises OSError: If I2C communication fails
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> data = bytes([0x01, 0x02, 0x03])
            >>> i2c.writeto(0x48, data)
        ```
        """
        ...
    
    def readfrom_mem(self, addr: int, reg: int, nbytes: int, *, addrsize: int = 8) -> bytes:
        """
        Read bytes from device memory/register.
        
        :param addr: 7-bit I2C device address
        :param reg: Register/memory address
        :param nbytes: Number of bytes to read
        :param addrsize: Register address size in bits (8 or 16, default: 8)
        :return: Bytes read from register
        
        :raises ValueError: If parameters are out of range
        :raises OSError: If I2C communication fails
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> # Read 6 bytes starting from register 0x28
            >>> data = i2c.readfrom_mem(0x48, 0x28, 6)
        ```
        """
        ...
    
    def readfrom_mem_into(self, addr: int, reg: int, buf: bytearray, *, addrsize: int = 8) -> None:
        """
        Read bytes from device memory into buffer.
        
        :param addr: 7-bit I2C device address
        :param reg: Register/memory address
        :param buf: Bytearray to store read data
        :param addrsize: Register address size in bits (8 or 16, default: 8)
        
        :raises ValueError: If parameters are out of range
        :raises OSError: If I2C communication fails
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> buffer = bytearray(16)
            >>> i2c.readfrom_mem_into(0x50, 0x00, buffer)
        ```
        """
        ...
    
    def writeto_mem(self, addr: int, reg: int, buf: bytes, *, addrsize: int = 8) -> None:
        """
        Write bytes to device memory/register.
        
        :param addr: 7-bit I2C device address
        :param reg: Register/memory address
        :param buf: Bytes to write
        :param addrsize: Register address size in bits (8 or 16, default: 8)
        
        :raises ValueError: If parameters are out of range
        :raises OSError: If I2C communication fails
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> config = bytes([0x20, 0x30])
            >>> i2c.writeto_mem(0x48, 0x10, config)
        ```
        """
        ...
    
    def read_u8(self, addr: int, reg: int, *, addrsize: int = 8) -> int:
        """
        Read unsigned 8-bit value from register.
        
        :param addr: 7-bit I2C device address
        :param reg: Register address
        :param addrsize: Register address size in bits (8 or 16, default: 8)
        :return: Unsigned 8-bit value (0-255)
        
        :raises ValueError: If parameters are out of range
        :raises OSError: If I2C communication fails
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> temp = i2c.read_u8(0x48, 0x00)
            >>> print(f"Temperature: {temp}°C")
        ```
        """
        ...
    
    def read_u16(self, addr: int, reg: int, *, little_endian: bool = True, addrsize: int = 8) -> int:
        """
        Read unsigned 16-bit value from register.
        
        :param addr: 7-bit I2C device address
        :param reg: Register address
        :param little_endian: Byte order (True=LSB first, False=MSB first)
        :param addrsize: Register address size in bits (8 or 16, default: 8)
        :return: Unsigned 16-bit value (0-65535)
        
        :raises ValueError: If parameters are out of range
        :raises OSError: If I2C communication fails
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> # Read ADC value (little-endian)
            >>> adc = i2c.read_u16(0x48, 0x00)
            >>> # Read pressure (big-endian)
            >>> pressure = i2c.read_u16(0x76, 0xF7, little_endian=False)
        ```
        """
        ...
    
    def write_u8(self, addr: int, reg: int, val: int, *, addrsize: int = 8) -> None:
        """
        Write unsigned 8-bit value to register.
        
        :param addr: 7-bit I2C device address
        :param reg: Register address
        :param val: Value to write (0-255, automatically masked)
        :param addrsize: Register address size in bits (8 or 16, default: 8)
        
        :raises ValueError: If parameters are out of range
        :raises OSError: If I2C communication fails
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> # Set power mode
            >>> i2c.write_u8(0x48, 0x20, 0x27)
        ```
        """
        ...
    
    def write_u16(self, addr: int, reg: int, val: int, *, little_endian: bool = True, addrsize: int = 8) -> None:
        """
        Write unsigned 16-bit value to register.
        
        :param addr: 7-bit I2C device address
        :param reg: Register address
        :param val: Value to write (0-65535, automatically masked)
        :param little_endian: Byte order (True=LSB first, False=MSB first)
        :param addrsize: Register address size in bits (8 or 16, default: 8)
        
        :raises ValueError: If parameters are out of range
        :raises OSError: If I2C communication fails
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> # Set threshold value
            >>> i2c.write_u16(0x48, 0x02, 5000)
        ```
        """
        ...
    
    def write_mem_ex(self, addr: int, reg_bytes: bytes, payload: bytes, *, stop: bool = True) -> None:
        """
        Extended write with separate register and payload bytes.
        
        :param addr: 7-bit I2C device address
        :param reg_bytes: Register address as bytes (for complex addressing)
        :param payload: Data to write
        :param stop: Send stop condition after write (default: True)
        
        :raises ValueError: If addr is out of range
        :raises OSError: If I2C communication fails
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> # Write to 16-bit register address
            >>> reg = bytes([0x10, 0x00])  # Address 0x1000
            >>> data = bytes([0x01, 0x02, 0x03])
            >>> i2c.write_mem_ex(0x50, reg, data)
        ```
        """
        ...
    
    def read_mem_ex(self, addr: int, reg_bytes: bytes, n: int, out: bytearray | None = None) -> bytes | None:
        """
        Extended read with custom register bytes.
        
        :param addr: 7-bit I2C device address
        :param reg_bytes: Register address as bytes (for complex addressing)
        :param n: Number of bytes to read
        :param out: Optional output buffer (if None, creates new bytes)
        :return: Bytes read (or None if out buffer was provided)
        
        :raises ValueError: If addr is out of range
        :raises OSError: If I2C communication fails
        
        Example
        --------
        ```python
            >>> i2c = I2CMaster(sda=4, scl=5)
            >>> # Read from 16-bit register address
            >>> reg = bytes([0x10, 0x00])
            >>> data = i2c.read_mem_ex(0x50, reg, 16)
            >>> 
            >>> # Read into existing buffer
            >>> buffer = bytearray(32)
            >>> i2c.read_mem_ex(0x50, reg, 32, buffer)
        ```
        """
        ...


class Spi:
    """
    SPI (Serial Peripheral Interface) master with automatic chip select management.
    
    This class provides comprehensive SPI communication with automatic chip select
    control, spinlock protection for multi-core safety, and flexible configuration.
    Ideal for interfacing with SPI devices like displays, sensors, and memory chips.
    
    Features:
    
        - Automatic chip select (CS) assertion and deassertion
        - Hardware spinlock protection for multi-core safety
        - Configurable clock polarity and phase (SPI modes 0-3)
        - Configurable baudrate and bit order
        - Context manager support for manual CS control
        - Retry mechanism for robust communication
        - Support for various transfer patterns
    
    SPI Modes:
    
        - Mode 0: CPOL=0, CPHA=0 (clock idle low, sample on leading edge)
        - Mode 1: CPOL=0, CPHA=1 (clock idle low, sample on trailing edge)
        - Mode 2: CPOL=1, CPHA=0 (clock idle high, sample on leading edge)
        - Mode 3: CPOL=1, CPHA=1 (clock idle high, sample on trailing edge)
    """
    
    def __init__(self, *,
                 sck: int, mosi: int, miso: int,
                 cs: int, cs_active_low: bool = True,
                 baudrate: int = 10_000_000, polarity: int = 0, phase: int = 0,
                 bits: int = 8, firstbit: int | None = None):
        """
        Initialize SPI master interface.
        
        :param sck: SCK (clock) pin number
        :param mosi: MOSI (master out) pin number
        :param miso: MISO (master in) pin number
        :param cs: CS (chip select) pin number
        :param cs_active_low: CS is active low (default: True)
        :param baudrate: SPI baudrate in Hz (default: 10MHz)
        :param polarity: Clock polarity 0 or 1 (default: 0)
        :param phase: Clock phase 0 or 1 (default: 0)
        :param bits: Bits per word (default: 8)
        :param firstbit: MSB or LSB first (default: MSB)
        
        :raises ValueError: If invalid pin configuration or parameters
        :raises OSError: If SPI initialization fails
        
        Example
        --------
        ```python
            >>> # Standard SPI device (Mode 0, active-low CS)
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> 
            >>> # High-speed SPI flash (Mode 3)
            >>> flash = Spi(sck=10, mosi=11, miso=12, cs=13,
            ...             baudrate=20_000_000, polarity=1, phase=1)
            >>> 
            >>> # Display with active-high CS (Mode 0)
            >>> display = Spi(sck=18, mosi=19, miso=16, cs=17,
            ...               cs_active_low=False, baudrate=8_000_000)
            >>> 
            >>> # LSB-first device
            >>> special = Spi(sck=6, mosi=7, miso=8, cs=9,
            ...               firstbit=machine.SPI.LSB)
        ```
        """
        ...
    
    @property
    def bus_id(self) -> int:
        """
        Get the SPI bus ID (0 or 1).
        
        :return: SPI bus number
        """
        ...
    
    @property
    def pins(self) -> tuple[int, int, int]:
        """
        Get the (SCK, MOSI, MISO) pin tuple.
        
        :return: Tuple of (SCK pin, MOSI pin, MISO pin)
        """
        ...
    
    @property
    def cs_pin(self) -> machine.Pin:
        """
        Get the chip select Pin object.
        
        :return: machine.Pin object for CS
        """
        ...
    
    @property
    def last_error(self) -> int:
        """
        Get the last error code from SPI operations.
        
        :return: Error code (STAT_OK, STAT_TIMEOUT, STAT_BUS_ERR)
        """
        ...
    
    def set_retry_policy(self, *, retries: int | None = None, delay_us: int | None = None) -> None:
        """
        Configure retry policy for failed SPI operations.
        
        :param retries: Number of retry attempts (None to keep current)
        :param delay_us: Delay between retries in microseconds (None to keep current)
        
        :raises ValueError: If retries or delay_us is negative
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> spi.set_retry_policy(retries=3, delay_us=100)
        ```
        """
        ...
    
    def deinit(self) -> None:
        """
        Deinitialize the SPI master.
        
        Deasserts CS and releases SPI hardware resources.
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> # ... use spi ...
            >>> spi.deinit()
        ```
        """
        ...
    
    def reinit(self, *, baudrate: int | None = None, polarity: int | None = None, 
               phase: int | None = None, bits: int | None = None, firstbit: int | None = None) -> None:
        """
        Reinitialize SPI with new parameters.
        
        :param baudrate: New baudrate in Hz (None to keep current)
        :param polarity: New clock polarity (None to keep current)
        :param phase: New clock phase (None to keep current)
        :param bits: New bits per word (None to keep current)
        :param firstbit: New bit order (None to keep current)
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> # Change to slower speed
            >>> spi.reinit(baudrate=1_000_000)
            >>> # Change to Mode 3
            >>> spi.reinit(polarity=1, phase=1)
        ```
        """
        ...
    
    def select(self) -> None:
        """
        Manually assert chip select.
        
        Use this for manual CS control. Must call deselect() when done.
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> spi.select()
            >>> spi.write(b'\\x01\\x02')
            >>> spi.deselect()
        ```
        """
        ...
    
    def deselect(self) -> None:
        """
        Manually deassert chip select.
        
        Releases CS after manual selection.
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> spi.select()
            >>> spi.write(b'\\x03')
            >>> spi.deselect()
        ```
        """
        ...
    
    def selected(self):
        """
        Context manager for automatic chip select control.
        
        :return: Context manager for CS control
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> with spi.selected():
            ...     spi.write(b'\\x9F')  # Read ID command
            ...     device_id = spi.read(3)
            >>> # CS automatically deasserted here
        ```
        """
        ...
    
    def write(self, buf: bytes, *, hold_cs: bool = False) -> None:
        """
        Write data to SPI device.
        
        :param buf: Bytes to write
        :param hold_cs: Keep CS asserted after write (default: False)
        
        :raises OSError: If SPI communication fails
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> spi.write(b'\\x02\\x00\\x00')  # Write command
            >>> # Write with CS held for next operation
            >>> spi.write(b'\\x03\\x00', hold_cs=True)
        ```
        """
        ...
    
    def readinto(self, buf: bytearray, *, write: int = 0xFF, hold_cs: bool = False) -> None:
        """
        Read data from SPI device into buffer.
        
        :param buf: Bytearray to store read data
        :param write: Byte value to write during read (default: 0xFF)
        :param hold_cs: Keep CS asserted after read (default: False)
        
        :raises OSError: If SPI communication fails
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> buffer = bytearray(16)
            >>> spi.readinto(buffer)
            >>> print(f"Read: {buffer.hex()}")
        ```
        """
        ...
    
    def read(self, n: int, *, write: int = 0xFF) -> bytes:
        """
        Read n bytes from SPI device.
        
        :param n: Number of bytes to read
        :param write: Byte value to write during read (default: 0xFF)
        :return: Bytes read from device
        
        :raises OSError: If SPI communication fails
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> # Read device ID
            >>> spi.write(b'\\x9F')  # Read ID command
            >>> device_id = spi.read(3)
            >>> print(f"ID: {device_id.hex()}")
        ```
        """
        ...
    
    def write_readinto(self, wbuf: bytes, rbuf: bytearray, *, hold_cs: bool = False) -> None:
        """
        Simultaneous write and read operation.
        
        :param wbuf: Bytes to write
        :param rbuf: Bytearray to store read data
        :param hold_cs: Keep CS asserted after operation (default: False)
        
        :raises OSError: If SPI communication fails
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> write_buf = b'\\x0B\\x00\\x00\\x00'
            >>> read_buf = bytearray(16)
            >>> spi.write_readinto(write_buf, read_buf)
        ```
        """
        ...
    
    def write_then_readinto(self, cmd_bytes: bytes, rx_buf: bytearray, *, dummy: int = 0xFF) -> None:
        """
        Write command then read data.
        
        :param cmd_bytes: Command bytes to write first
        :param rx_buf: Bytearray to store read data
        :param dummy: Byte value to write during read (default: 0xFF)
        
        :raises OSError: If SPI communication fails
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> # Read from address
            >>> cmd = b'\\x03\\x00\\x10\\x00'  # Read from 0x001000
            >>> data = bytearray(256)
            >>> spi.write_then_readinto(cmd, data)
        ```
        """
        ...
    
    def write_then_write(self, cmd_bytes: bytes, payload_bytes: bytes) -> None:
        """
        Write command then write payload.
        
        :param cmd_bytes: Command bytes to write first
        :param payload_bytes: Payload data to write after command
        
        :raises OSError: If SPI communication fails
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> # Write to address
            >>> cmd = b'\\x02\\x00\\x10\\x00'  # Write to 0x001000
            >>> data = b'\\x01\\x02\\x03\\x04'
            >>> spi.write_then_write(cmd, data)
        ```
        """
        ...
    
    def write_u8(self, v: int) -> None:
        """
        Write single 8-bit value.
        
        :param v: Value to write (0-255, automatically masked)
        
        :raises OSError: If SPI communication fails
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> spi.write_u8(0x06)  # Write enable command
        ```
        """
        ...
    
    def read_u8(self) -> int:
        """
        Read single 8-bit value.
        
        :return: Unsigned 8-bit value (0-255)
        
        :raises OSError: If SPI communication fails
        
        Example
        --------
        ```python
            >>> spi = Spi(sck=2, mosi=3, miso=4, cs=5)
            >>> spi.write_u8(0x05)  # Read status command
            >>> status = spi.read_u8()
            >>> print(f"Status: 0x{status:02X}")
        ```
        """
        ...


class ReplSerial:
    """
    Advanced REPL (Read-Eval-Print Loop) serial communication interface with buffered I/O.
    
    This class provides a sophisticated interface for reading from and writing to the REPL
    using a ring buffer system. It enables non-blocking reads, pattern-based reading,
    and configurable timeout operations for robust serial communication in MicroPython
    applications.
    
    Features:
    
        - Ring buffer for efficient data storage and retrieval
        - Non-blocking, blocking, and timeout-based read operations
        - Pattern-based reading (read until specific byte sequence)
        - Automatic background data pumping via timer interrupts
        - Configurable buffer size and polling intervals
        - UTF-8 compatible data handling
        - Safe exception handling for robust operation
    
    """
    
    def __init__(self, timeout:float|None=None, *, bufsize:int=512, poll_ms:int=10):
        """
        Initialize REPL serial interface with configurable parameters.
        
        Creates a buffered serial interface that automatically reads from REPL stdin
        and stores data in a ring buffer. The interface supports various timeout modes
        and configurable buffer sizes for different application requirements.
        
        :param timeout: Read operation timeout behavior (default: None)
                       
            - None: Blocking reads (wait indefinitely)
            - 0: Non-blocking reads (return immediately)
            - \>0: Timeout in seconds (wait up to specified time)
                       
        :param bufsize: Ring buffer size in bytes (default: 512)
                       
            - Larger buffers can handle burst data better
            - Smaller buffers use less memory
            - Must be > 0
                       
        :param poll_ms: Polling interval in milliseconds (default: 10)
                       
            - How often to check for new data from REPL stdin
            - Lower values = more responsive but higher CPU usage
            - Higher values = less CPU usage but slower response
        
        :raises ValueError: If bufsize <= 0 or poll_ms <= 0
        :raises OSError: If REPL stdin/stdout access fails
        
        Example
        -------
        ```python
            >>> # Default configuration - blocking reads
            >>> repl = ReplSerial()
            >>> 
            >>> # Non-blocking configuration for real-time applications
            >>> fast_repl = ReplSerial(timeout=0, poll_ms=5)
            >>> 
            >>> # Large buffer for data logging
            >>> logger = ReplSerial(timeout=30.0, bufsize=2048, poll_ms=20)
            >>> 
            >>> # Interactive shell with reasonable timeout
            >>> shell = ReplSerial(timeout=60.0, bufsize=256, poll_ms=10)
            >>> 
            >>> # High-frequency data acquisition
            >>> daq = ReplSerial(timeout=0.1, bufsize=4096, poll_ms=1)
            >>> 
            >>> # Protocol handler with custom timing
            >>> protocol = ReplSerial(timeout=5.0, bufsize=1024, poll_ms=15)
        ```
        """

    @property
    def timeout(self) -> float|None:
        """
        Get the current timeout setting for read operations.
        
        :return: Current timeout value:
        
            - None: Blocking mode (wait indefinitely)
            - 0: Non-blocking mode (return immediately)
            - >0: Timeout in seconds
    
        Example
        -------
        ```python
            >>> repl = ReplSerial(timeout=5.0)
            >>> print(f"Current timeout: {repl.timeout} seconds")
            >>> 
            >>> # Check timeout mode
            >>> if repl.timeout is None:
            ...     print("Blocking mode")
            >>> elif repl.timeout == 0:
            ...     print("Non-blocking mode")
            >>> else:
            ...     print(f"Timeout mode: {repl.timeout} seconds")
        ```
        """
    
    @timeout.setter
    def timeout(self, value:float|None):
        """
        Set the timeout for read operations.
        
        Changes the timeout behavior for all subsequent read operations.
        This allows dynamic switching between blocking, non-blocking, and
        timeout modes during runtime.
        
        :param value: New timeout value:
        
            - None: Blocking mode (wait indefinitely)
            - 0: Non-blocking mode (return immediately)
            - >0: Timeout in seconds

        :raises ValueError: If value is negative (except for None and 0)
        
        Example
        -------
        ```python 
            >>> repl = ReplSerial()
            >>> 
            >>> # Switch to non-blocking mode
            >>> repl.timeout = 0
            >>> data = repl.read(10)  # Returns immediately
            >>> 
            >>> # Switch to timeout mode
            >>> repl.timeout = 2.5  # 2.5 second timeout
            >>> data = repl.read(100)  # Wait up to 2.5 seconds
            >>> 
            >>> # Switch to blocking mode
            >>> repl.timeout = None
            >>> data = repl.read(50)  # Wait indefinitely
            >>> 
            >>> # Dynamic timeout based on conditions
            >>> if urgent_mode:
            ...     repl.timeout = 0.1  # Quick timeout for urgent data
            >>> else:
            ...     repl.timeout = 10.0  # Longer timeout for normal operation
        ```
        """

    def read(self, size:int=1) -> bytes:
        """
        Read a specified number of bytes from the REPL buffer.
        
        Reads up to 'size' bytes from the internal ring buffer. The behavior
        depends on the current timeout setting and data availability.
        
        :param size: Number of bytes to read (default: 1)

            - If size <= 0, returns empty bytes
            - If size > available data, behavior depends on timeout

        :return: Bytes read from the buffer (may be less than requested size)
        
        Timeout Behavior:
        
            - None (blocking): Waits until at least some data is available
            - 0 (non-blocking): Returns immediately with available data
            - \>0 (timeout): Waits up to timeout seconds for data
        
        :raises ValueError: If size is not an integer

        Example
        -------
            >>> repl = ReplSerial()
            >>> 
            >>> # Read single byte (blocking)
            >>> byte = repl.read(1)
            >>> if byte:
            ...     print(f"Received: {byte[0]:02X}")
            >>> 
            >>> # Read multiple bytes
            >>> repl.timeout = 5.0
            >>> data = repl.read(100)  # Wait up to 5 seconds for 100 bytes
            >>> print(f"Received {len(data)} bytes: {data}")
            >>> 
            >>> # Non-blocking read for polling
            >>> repl.timeout = 0
            >>> while True:
            ...     chunk = repl.read(64)
            ...     if chunk:
            ...         process_data(chunk)
            ...     else:
            ...         utime.sleep_ms(10)  # Small delay when no data
            >>> 
            >>> # Read with size checking
            >>> repl.timeout = 2.0
            >>> expected_size = 50
            >>> data = repl.read(expected_size)
            >>> if len(data) == expected_size:
            ...     print("Received complete packet")
            >>> else:
            ...     print(f"Partial packet: {len(data)}/{expected_size} bytes")
            >>> 
            >>> # Stream processing
            >>> repl.timeout = 0.5
            >>> buffer = bytearray()
            >>> while len(buffer) < 256:
            ...     chunk = repl.read(32)
            ...     if chunk:
            ...         buffer.extend(chunk)
            ...     else:
            ...         break  # Timeout or no more data
        ```
        """

    def read_until(self, expected:bytes=b'\r', max_size:int|None=None) -> bytes:
        """
        Read from the buffer until a specific byte pattern is found.
        
        Reads data from the ring buffer until the expected byte sequence is
        encountered, the maximum size is reached, or a timeout occurs. This is
        ideal for protocol implementations and line-based communication.
        
        :param expected: Byte sequence to search for (default: b'\\r')  

            - Common patterns: b'\\r\\n', b'\\n', b'\\x00', b'END'  
            - Can be any byte sequence  
        
        :param max_size: Maximum bytes to read (default: None for no limit)
        
            - Prevents memory exhaustion with malformed data
            - Returns data when limit is reached, even without pattern
        
        :return: Bytes read including the expected pattern (if found)
        
            - Empty bytes if timeout in non-blocking/timeout modes
            - May not contain expected pattern if max_size reached
        
        Timeout Behavior:
        
            - 0 (non-blocking): Returns immediately with available data
            - >0 (timeout): Waits up to timeout seconds for pattern/max_size
            - None (blocking): Waits indefinitely for pattern/max_size
        
        :raises ValueError: If expected is not bytes or max_size is negative
        
        Example
        -------
        ```python
            >>> repl = ReplSerial()
            >>> 
            >>> # Read line-based input
            >>> line = repl.read_until(b'\\r\\n')
            >>> if line:
            ...     command = line.decode().strip()
            ...     print(f"Command: {command}")
            >>> 
            >>> # Protocol message reading
            >>> repl.timeout = 5.0
            >>> message = repl.read_until(b'\\x00', max_size=1024)  # Null-terminated
            >>> if message:
            ...     if message.endswith(b'\\x00'):
            ...         print("Complete message received")
            ...     else:
            ...         print("Message truncated at max_size")
            >>> 
            >>> # Interactive shell implementation
            >>> repl = ReplSerial(timeout=30.0)
            >>> while True:
            ...     try:
            ...         cmd_line = repl.read_until(b'\\r\\n', max_size=256)
            ...         if cmd_line:
            ...             command = cmd_line.decode().strip()
            ...             if command == 'exit':
            ...                 break
            ...             response = execute_command(command)
            ...             repl.write(response.encode() + b'\\r\\n')
            ...     except KeyboardInterrupt:
            ...         break
            >>> 
            >>> # Data packet reading with validation
            >>> repl.timeout = 1.0
            >>> while True:
            ...     packet = repl.read_until(b'END', max_size=512)
            ...     if packet:
            ...         if packet.endswith(b'END'):
            ...             process_packet(packet[:-3])  # Remove 'END' marker
            ...         else:
            ...             print("Malformed packet (no END marker)")
            ...     else:
            ...         print("No packet received (timeout)")
            >>> 
            >>> # Multi-delimiter reading
            >>> delimiters = [b'\\r\\n', b'\\n', b'\\r']
            >>> for delimiter in delimiters:
            ...     repl.timeout = 0.1  # Quick check
            ...     data = repl.read_until(delimiter, max_size=100)
            ...     if data and data.endswith(delimiter):
            ...         print(f"Found data with delimiter: {delimiter}")
            ...         break
        ```
        """

    def write(self, data:bytes) -> int:
        """
        Write data to the REPL output stream.
        
        Sends the provided data to the REPL stdout, making it visible in the
        terminal or connected serial interface. This method provides direct
        access to the output stream for sending responses, status messages,
        or any other data.
        
        :param data: Data to write (must be bytes or bytearray)
    
            - String data must be encoded first: text.encode('utf-8')
            - Binary data can be written directly
            
        :return: Number of bytes actually written
        
        :raises TypeError: If data is not bytes or bytearray
        :raises OSError: If write operation fails
        
        Example
            --------
            ```python
            >>> repl = ReplSerial()
            >>> 
            >>> # Write string data
            >>> message = "Hello, World!\\r\\n"
            >>> bytes_written = repl.write(message.encode('utf-8'))
            >>> print(f"Wrote {bytes_written} bytes")
            >>> 
            >>> # Write binary data
            >>> binary_data = bytes([0x01, 0x02, 0x03, 0x04])
            >>> repl.write(binary_data)
            >>> 
            >>> # Command response system
            >>> def send_response(repl, status, message):
            ...     response = f"STATUS:{status}:{message}\\r\\n"
            ...     return repl.write(response.encode('utf-8'))
            >>> 
            >>> bytes_sent = send_response(repl, "OK", "Command executed")
            >>> 
            >>> # JSON protocol implementation
            >>> import json
            >>> def send_json_response(repl, data):
            ...     json_str = json.dumps(data) + "\\r\\n"
            ...     return repl.write(json_str.encode('utf-8'))
            >>> 
            >>> response_data = {"result": "success", "value": 42}
            >>> send_json_response(repl, response_data)
            >>> 
            >>> # Progress indicator
            >>> def show_progress(repl, percent):
            ...     bar = "=" * (percent // 2) + " " * (50 - percent // 2)
            ...     progress = f"\\rProgress: [{bar}] {percent}%"
            ...     repl.write(progress.encode('utf-8'))
            >>> 
            >>> for i in range(0, 101, 10):
            ...     show_progress(repl, i)
            ...     utime.sleep(0.1)
            >>> 
            >>> # Echo server implementation
            >>> while True:
            ...     data = repl.read_until(b'\\r\\n')
            ...     if data:
            ...         echo = b"ECHO: " + data
            ...         repl.write(echo)
        """

    def close(self):
        """
        Close the REPL serial interface and release resources.
        
        Properly shuts down the serial interface by stopping the background
        timer and releasing system resources. Should be called when the
        interface is no longer needed to prevent resource leaks.
        
        Note: After calling close(), the ReplSerial instance should not be
        used for further operations.
        
        Example
        -------
        ```python
            >>> repl = ReplSerial()
            >>> 
            >>> # Use the interface
            >>> data = repl.read(10)
            >>> repl.write(b"Response\\r\\n")
            >>> 
            >>> # Clean shutdown
            >>> repl.close()
            >>> 
            >>> # Context manager pattern (recommended)
            >>> class ReplSerialContext:
            ...     def __init__(self, *args, **kwargs):
            ...         self.repl = ReplSerial(*args, **kwargs)
            ...     def __enter__(self):
            ...         return self.repl
            ...     def __exit__(self, exc_type, exc_val, exc_tb):
            ...         self.repl.close()
            >>> 
            >>> with ReplSerialContext(timeout=5.0) as repl:
            ...     data = repl.read(100)
            ...     repl.write(b"Done\\r\\n")
            >>> # Automatically closed when exiting context
            >>> 
            >>> # Cleanup in exception handler
            >>> repl = ReplSerial()
            >>> try:
            ...     # Main processing loop
            ...     while True:
            ...         data = repl.read_until(b'\\r\\n')
            ...         if data:
            ...             process_command(data.decode().strip())
            ... except KeyboardInterrupt:
            ...     print("Shutting down...")
            ... finally:
            ...     repl.close()  # Ensure cleanup
        ```
        """