"""
Blynk MQTT Client Library

Advanced Blynk IoT platform integration for MicroPython devices with MQTT protocol.
Provides seamless connectivity to Blynk Cloud for real-time data exchange,
remote monitoring, and device control.

Features:

- MQTT-based communication with Blynk Cloud
- SSL/TLS secure connection support
- Datastream subscription and publishing
- Automatic connection management and keepalive
- UTC time synchronization from Blynk servers
- Remote device reboot capability
- Callback-based event handling system
- Robust error handling and reconnection
- Memory-efficient implementation for embedded systems
- Comprehensive logging and debugging support

Supported Operations:

- Publish sensor data to Blynk datastreams
- Subscribe to widget updates from mobile app
- Remote device control and configuration
- Real-time bidirectional communication
- Cloud-based data storage and visualization
- Mobile app notifications and alerts

Security:

- Device authentication via auth tokens
- Optional SSL/TLS encryption
- Secure server hostname verification
- Protected MQTT credential handling
"""

import sys


__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"

print("""
    ___  __          __
   / _ )/ /_ _____  / /__
  / _  / / // / _ \\/  '_/
 /____/_/\\_, /_//_/_/\\_\\2@MQTT
        /___/ for uPython v""" + __version__ + " (" + sys.platform + ")\n")


class BlynkMQTTClient:
    """
    Blynk MQTT Client for secure IoT connectivity to Blynk Cloud platform.
    
    This class provides a robust MicroPython implementation for the Blynk IoT
    platform using MQTT protocol. It enables devices to communicate with
    Blynk Cloud for real-time data exchange, remote control, and monitoring
    through mobile applications and web dashboards.
    
    The client handles secure authentication, automatic connection management,
    datastream publishing/subscription, and provides callback-based event
    handling for incoming messages from the Blynk platform.
    
    Key Features:
    
        - Secure MQTT communication with SSL/TLS support
        - Automatic connection management and keepalive handling
        - Last Will and Testament (LWT) for offline status reporting
        - Robust reconnection logic with exponential backoff
        - Event-driven architecture using callbacks for datastreams
        - Support for publishing hardware info and setting widget properties
        - UTC time synchronization from Blynk servers
    
    Communication Flow:
    
        1. Connect to Blynk Cloud MQTT broker
        2. Subscribe to datastream updates from mobile app
        3. Publish sensor data to datastreams
        4. Handle remote control commands via callbacks
        5. Maintain connection with automatic ping/reconnect
    
    Security Features:
    
        - Device authentication via auth tokens
        - Optional SSL/TLS encryption with hostname verification
        - Secure MQTT credential handling
        - Protected message routing and validation
        
    """    

    def __init__(self, auth_token: str, server: str = "blynk.cloud", 
                 keepalive: int = 45, ssl: bool = False, verbose: bool = False) -> None:      
        """
        Initialize the Blynk MQTT Client with connection parameters.
        
        Creates a new Blynk MQTT client instance with the specified authentication
        token and connection settings. The client is ready to connect after
        initialization but does not establish a connection automatically.
        
        :param auth_token: Blynk authentication token from the Blynk Console
        :param server: Blynk server address (default: "blynk.cloud")
        :param keepalive: MQTT keepalive interval in seconds (default: 45)
        :param ssl: Enable SSL/TLS secure connection (default: False)
        :param verbose: Enable detailed logging for debugging (default: False)
        
        :raises ValueError: If the server address cannot be resolved
        
        Example
        --------
        ```python
            >>> # Basic client
            >>> client = BlynkMQTTClient(auth_token="YOUR_TOKEN")
            >>> 
            >>> # Secure client with logging
            >>> secure_client = BlynkMQTTClient(
            ...     auth_token="YOUR_TOKEN",
            ...     ssl=True,
            ...     verbose=True
            ... )
        ```
        """
    
    def connect(self, clean_session: bool = True) -> bool:
        """
        Connect to the Blynk MQTT broker with Last Will and Testament.
        
        Establishes a connection to the Blynk Cloud MQTT broker and subscribes
        to all downlink topics. Sets up LWT to automatically publish an "offline"
        status if disconnected unexpectedly.
        
        :param clean_session: Start a new session if True, or resume a previous one
        :return: True if connection is successful, False otherwise

        Example
        -------
            >>> if client.connect():
            ...     print("Connected to Blynk")
            ... else:
            ...     print("Connection failed")
        ```
        """

    def disconnect(self) -> None:
        """
        Gracefully disconnect from the Blynk MQTT broker.
        
        Publishes an "offline" status before closing the connection to ensure
        proper cleanup and status reporting to the Blynk platform.
        
        Example
        -------
            >>> client.disconnect()
            >>> print("Disconnected from Blynk")
        ```
        """

    def is_connected(self) -> bool:
        """
        Check if the client is currently connected to the Blynk MQTT broker.
        
        Returns the current connection status based on internal state tracking.
        Use this method to verify connectivity before performing operations.
        
        :return: True if connected, False otherwise
        
        Example
        -------
            >>> if client.is_connected():
            ...     client.publish("V1", sensor_value)
            ... else:
            ...     print("Not connected")
        ```
        """

    def reconnect(self, max_attempts: int = 5) -> bool:
        """
        Attempt to reconnect to the broker with exponential backoff.
        
        Tries to re-establish a lost connection using exponential backoff
        strategy. Useful for handling temporary network issues or server
        maintenance periods.
        
        :param max_attempts: Maximum number of reconnection attempts
        :return: True if reconnected successfully, False otherwise
        
        Example
        -------
            >>> if not client.is_connected():
            ...     if client.reconnect():
            ...         print("Reconnected successfully")
            ...     else:
            ...         print("Failed to reconnect")
        ```
        """

    def add_subscribe_callback(self, datastream: str, callback: callable) -> None:
        """
        Register a callback for a specific datastream or system event.
        
        Associates a callback function with a datastream to be called when
        data is received from the Blynk platform. Enables event-driven
        programming for handling remote control commands.
        
        :param datastream: Datastream name (e.g., "V1") or system event
                          ("reboot", "utc", "property", "loglevel", "__all__")
        :param callback: Function to call when message is received
        
        Callback Signatures:
        
            - Datastream: callback(value)
            - UTC: callback(payload)
            - Reboot: callback()
            - Property: callback(pin, property_name, value)
            - __all__: callback(topic, payload)
        
        Example
        -------
            >>> def on_slider(value):
            ...     pwm.duty(int(float(value) * 10.23))
            >>> client.add_subscribe_callback("V1", on_slider)
        ```
        """

    def remove_subscribe_callback(self, datastream: str) -> None:
        """
        Remove a callback for a specific datastream.
        
        Removes the previously registered callback for the specified datastream.
        After removal, incoming data for this datastream will be ignored.
        
        :param datastream: Datastream name to remove callback for
        
        Example
        -------
            >>> client.remove_subscribe_callback("V1")
        ```
        """

    def publish(self, datastream: str, value: str | int | float, qos: int = 0) -> None:
        """
        Publish a value to a specific datastream.
        
        Sends data to the Blynk Cloud for a specific datastream. This data
        is displayed on the Blynk mobile app and can trigger events or
        notifications based on your project configuration.
        
        :param datastream: Datastream name (e.g., "V5")
        :param value: Value to publish (automatically converted to string)
        :param qos: MQTT Quality of Service level (0 or 1)

        Example
        -------
            >>> # Publish sensor readings
            >>> client.publish("V2", temperature)
            >>> client.publish("V3", humidity)
        ```
        """

    def publish_device_status(self, status: str) -> None:
        """
        Publish device online/offline status to Blynk.
        
        Updates the device status on the Blynk platform. This is handled
        automatically by connect() and disconnect() but can be called
        manually if needed.
        
        :param status: "online" or "offline"

        Example
        -------
            >>> client.publish_device_status("online")
        ```
        """

    def publish_hardware_info(self, info: dict) -> None:
        """
        Publish device hardware information to Blynk.
        
        Sends hardware details about the device to the Blynk Cloud.
        Typically sent once after connecting to inform the platform
        about device capabilities.
        
        :param info: Dictionary containing hardware details
        
        Example
        -------
            >>> hw_info = {"board": "RP2350", "firmware": "1.26.0"}
            >>> client.publish_hardware_info(hw_info)
        ```
        """

    def set_property(self, datastream: str, prop: str, value: str | int | float) -> None:
        """
        Set a property for a specific datastream widget.
        
        Dynamically updates widget properties such as label, color, or
        min/max values. This allows runtime customization of the mobile
        app interface based on device state or user preferences.
        
        :param datastream: Target datastream name (e.g., "V2")
        :param prop: Property to change (e.g., "label", "color", "min", "max")
        :param value: New value for the property
        
        Example
        -------
            >>> client.set_property("V2", "label", "CPU Temp")
            >>> client.set_property("V2", "color", "#FF0000")
        ```
        """

    def get_utc(self, timeout_ms: int = 5000) -> dict | None:
        """
        Get the current UTC time from the Blynk server with timeout.
        
        Requests and retrieves the current UTC time from the Blynk Cloud
        server. Useful for devices without a real-time clock to synchronize
        time. The method blocks until response is received or timeout occurs.
        
        :param timeout_ms: Maximum time to wait for response in milliseconds
        :return: Dictionary with "time" (ISO8601 format) and "zone", or None on timeout
        
        Example
        -------
            >>> time_data = client.get_utc()
            >>> if time_data:
            ...     print(f"Current time: {time_data['time']}")
        ```
        """

    def loop(self) -> None:
        """
        Process pending messages and maintain connection in non-blocking manner.
        
        This method should be called regularly in your main loop to handle
        incoming data, send queued messages, and maintain the connection
        via pings. It includes automatic reconnection logic for lost connections.

        Example
        -------
            >>> while True:
            ...     client.loop()
            ...     # Your application code here
            ...     time.sleep_ms(10)
        ```
        """

    def loop_forever(self) -> None:
        """
        Run the client loop indefinitely (blocking).
        
        This method handles all communication automatically and will block
        the execution of subsequent code. Use this when you don't need to
        run other code alongside Blynk communication.
        
        Example
        -------
            >>> # This will run forever, processing Blynk events
            >>> client.loop_forever()
        ```
        """
