"""
WiFi Module

Station (STA) mode WiFi management for MicroPython devices.
Provides connection management, scanning, and network information.

Key Features:

    - Connect to WiFi networks with timeout
    - Multi-network fallback connection
    - Network scanning and SSID enumeration
    - Connection status and signal strength (RSSI)
    - IP configuration (IP, gateway, DNS, netmask)
    - MAC address and hostname management

Author: PlanXLab Development Team
"""


class Wifi:
    """
    WiFi station (STA) mode manager.
    
    All methods are static - no instantiation required.
    Lazily initializes the WLAN interface on first use.
    
    Example
    --------
    Basic connection::
    
        >>> from wifi import Wifi
        >>> 
        >>> if Wifi.connect("MyNetwork", "password123"):
        ...     print(f"Connected! IP: {Wifi.ip()}")
        ... else:
        ...     print("Connection failed")
    """
    
    AUTH_OPEN: int
    """Open network (no authentication)."""
    
    AUTH_WEP: int
    """WEP authentication."""
    
    AUTH_WPA_PSK: int
    """WPA-PSK authentication."""
    
    AUTH_WPA2_PSK: int
    """WPA2-PSK authentication."""
    
    AUTH_WPA_WPA2_PSK: int
    """WPA/WPA2-PSK mixed mode."""

    PM_NONE: int | None
    """Disable WiFi power management. Best for reliability. None if not supported."""
    
    PM_PERFORMANCE: int | None
    """Balance power savings and WiFi performance. None if not supported."""
    
    PM_POWERSAVE: int | None
    """Maximum power savings, reduced WiFi performance. None if not supported."""

    @staticmethod
    def scan() -> list[tuple]:
        """
        Scan for available WiFi networks.
        
        :return: List of tuples (ssid, bssid, channel, rssi, authmode, hidden)
        
        Example
        --------
        ```python
            >>> for ap in Wifi.scan():
            ...     ssid = ap[0].decode()
            ...     rssi = ap[3]
            ...     print(f"{ssid}: {rssi} dBm")
        ```
        """

    @staticmethod
    def ssids() -> list[str]:
        """
        Get list of available SSID names.
        
        Convenience method that extracts unique SSIDs from scan results.
        
        :return: List of SSID strings (duplicates removed)
        
        Example
        --------
        ```python
            >>> networks = Wifi.ssids()
            >>> print(f"Found {len(networks)} networks:")
            >>> for ssid in networks:
            ...     print(f"  - {ssid}")
        ```
        """

    @staticmethod
    def connect(ssid: str, password: str = "", *, timeout_s: float = 20.0, pm: int = None) -> bool:
        """
        Connect to a WiFi network.
        
        If already connected to a different network, disconnects first.
        If already connected to the same network, returns True immediately.
        
        :param ssid: Network SSID
        :param password: Network password (empty for open networks)
        :param timeout_s: Connection timeout in seconds
        :param pm: Power management mode (PM_NONE, PM_PERFORMANCE, PM_POWERSAVE).
                   Use PM_NONE for reliable communication.
        
        :return: True if connected, False if timeout
        
        Example
        --------
        ```python
            >>> if Wifi.connect("HomeNetwork", "secret123"):
            ...     print(f"Connected to {Wifi.ssid()}")
            ...     print(f"IP address: {Wifi.ip()}")
            
            >>> # Open network (no password)
            >>> Wifi.connect("PublicWiFi")
            
            >>> # Disable power management for stable connection
            >>> Wifi.connect("IoTNetwork", "pass", pm=Wifi.PM_NONE)
            
            >>> # Short timeout for quick retry
            >>> Wifi.connect("FastNet", "pass", timeout_s=5.0)
        ```
        """

    @staticmethod
    def disconnect() -> None:
        """
        Disconnect from current WiFi network.
        
        Example
        --------
        ```python
            >>> Wifi.disconnect()
            >>> print(f"Connected: {Wifi.is_connected()}")  # False
        ```
        """

    @staticmethod
    def is_connected() -> bool:
        """
        Check if connected to a WiFi network.
        
        :return: True if connected, False otherwise
        
        Example
        --------
        ```python
            >>> if not Wifi.is_connected():
            ...     Wifi.connect("MyNetwork", "password")
        ```
        """

    @staticmethod
    def ifconfig() -> tuple | None:
        """
        Get IP configuration.
        
        :return: Tuple (ip, netmask, gateway, dns) or None if not connected
        
        Example
        --------
        ```python
            >>> cfg = Wifi.ifconfig()
            >>> if cfg:
            ...     ip, mask, gw, dns = cfg
            ...     print(f"IP: {ip}, Gateway: {gw}")
        ```
        """

    @staticmethod
    def ip() -> str | None:
        """
        Get assigned IP address.
        
        :return: IP address string or None if not connected
        
        Example
        --------
        ```python
            >>> ip = Wifi.ip()
            >>> if ip:
            ...     print(f"Device IP: {ip}")
        ```
        """

    @staticmethod
    def gateway() -> str | None:
        """
        Get gateway IP address.
        
        :return: Gateway address or None if not connected
        """

    @staticmethod
    def dns() -> str | None:
        """
        Get DNS server IP address.
        
        :return: DNS address or None if not connected
        """

    @staticmethod
    def netmask() -> str | None:
        """
        Get network subnet mask.
        
        :return: Netmask or None if not connected
        """

    @staticmethod
    def mac() -> str:
        """
        Get device MAC address.
        
        :return: MAC address in XX:XX:XX:XX:XX:XX format
        
        Example
        --------
        ```python
            >>> print(f"MAC: {Wifi.mac()}")
            MAC: A4:CF:12:34:56:78
        ```
        """

    @staticmethod
    def rssi() -> int | None:
        """
        Get current connection signal strength.
        
        :return: RSSI in dBm or None if not connected
        
        Example
        --------
        ```python
            >>> rssi = Wifi.rssi()
            >>> if rssi:
            ...     if rssi > -50:
            ...         print("Excellent signal")
            ...     elif rssi > -70:
            ...         print("Good signal")
            ...     else:
            ...         print("Weak signal")
        ```
        """

    @staticmethod
    def ssid() -> str | None:
        """
        Get connected network SSID.
        
        :return: SSID string or None if not connected
        
        Example
        --------
        ```python
            >>> if Wifi.is_connected():
            ...     print(f"Connected to: {Wifi.ssid()}")
        ```
        """

    @staticmethod
    def hostname(name: str = None) -> str:
        """
        Get or set device hostname.
        
        :param name: New hostname (None to only get current)
        
        :return: Current hostname
        
        Example
        --------
        ```python
            >>> # Get current hostname
            >>> print(f"Hostname: {Wifi.hostname()}")
            
            >>> # Set new hostname
            >>> Wifi.hostname("my-device")
        ```
        """

    @staticmethod
    def status() -> dict:
        """
        Get comprehensive connection status.
        
        :return: Dict with keys: connected, ssid, ip, rssi, mac
        
        Example
        --------
        ```python
            >>> status = Wifi.status()
            >>> print(f"Connected: {status['connected']}")
            >>> if status['connected']:
            ...     print(f"Network: {status['ssid']}")
            ...     print(f"IP: {status['ip']}")
            ...     print(f"Signal: {status['rssi']} dBm")
        ```
        """

    @staticmethod
    def connect_multi(
        networks: list[tuple[str, str]],
        *,
        timeout_s: float = 10.0
    ) -> str | None:
        """
        Try connecting to multiple networks in order.
        
        Attempts each network until one succeeds.
        Useful for fallback configurations.
        
        :param networks: List of (ssid, password) tuples
        :param timeout_s: Timeout per network attempt
        
        :return: SSID of connected network, or None if all failed
        
        Example
        --------
        ```python
            >>> networks = [
            ...     ("PrimaryNetwork", "pass1"),
            ...     ("BackupNetwork", "pass2"),
            ...     ("MobileHotspot", "pass3"),
            ... ]
            >>> connected = Wifi.connect_multi(networks)
            >>> if connected:
            ...     print(f"Connected to {connected}")
        ```
        """

    @staticmethod
    def wait_connected(timeout_s: float = 30.0) -> bool:
        """
        Wait for connection to establish.
        
        Useful after boot.py connection or reconnection attempts.
        
        :param timeout_s: Maximum wait time
        
        :return: True if connected, False if timeout
        
        Example
        --------
        ```python
            >>> # Wait for boot.py WiFi connection
            >>> if Wifi.wait_connected(timeout_s=30):
            ...     print("WiFi ready")
            ... else:
            ...     print("WiFi not available")
        ```
        """

    @staticmethod
    def deactivate() -> None:
        """
        Deactivate WiFi interface completely.
        
        Turns off WiFi radio to save power.
        
        Example
        --------
        ```python
            >>> # Going to deep sleep, disable WiFi first
            >>> Wifi.deactivate()
        ```
        """
