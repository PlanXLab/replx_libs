"""
Blynk MQTT Client Module

Blynk IoT platform integration for MicroPython devices using MQTT protocol.
Provides real-time data exchange, remote monitoring, and device control
through Blynk Cloud.

Key Features:

    - MQTT-based communication with Blynk Cloud
    - SSL/TLS secure connection support
    - Datastream publishing and subscription
    - Automatic reconnection with exponential backoff
    - UTC time synchronization from Blynk servers
    - GeoDNS server redirect handling
    - Widget property control
    - Event logging and metadata management

Protocol:
    Uses Blynk MQTT API with topics like ds/DATASTREAM for publishing
    and downlink/# for receiving. Supports MQTT 3.1.1 and MQTT 5.

Author: PlanXLab Development Team
"""


class BlynkMQTTClient:
 
    def __init__(self, auth_token: str, server: str = "blynk.cloud", 
                 keepalive: int = 45, ssl: bool = False, verbose: bool = False,
                 template_id: str = "", fw_version: str = "1.0.0", 
                 fw_build: str = "") -> None:      
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
        :param template_id: Blynk template ID for device identification
        :param fw_version: Firmware version string (default: "1.0.0")
        :param fw_build: Firmware build string (default: ""); if empty, build info is set from time.localtime()[:6]
        
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
        Connect to the Blynk MQTT broker and send firmware info.
        
        Establishes a connection to the Blynk Cloud MQTT broker, subscribes
        to all downlink topics, and automatically sends firmware information
        (info/mcu) as required by the Blynk API. Handles GeoDNS redirect if needed.
        
        :param clean_session: Start a new session if True (only True is supported)
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
        
        Closes the connection to the Blynk platform. The broker will detect
        the disconnect and update the device status automatically.
        
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
        strategy with minimum 10-second delay between attempts. Useful for
        handling temporary network issues or server maintenance periods.
        
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
                          ("_utc", "_loc", "_meta", "_ota", "_reboot", "_redirect", "_diag", "__all__")
        :param callback: Function to call when message is received
        
        Callback Signatures:
        
            - Datastream: callback(value_str) or callback(values_str) for multi-value
            - _utc: callback(payload_str)
            - _loc: callback(payload_str)
            - _meta: callback(field, value_str)
            - _ota: callback(payload_str)
            - _reboot: callback()
            - _redirect: callback(uri_str)
            - _diag: callback(payload_str)
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

    def publish(self, datastream: str, value: str | int | float | list, qos: int = 0) -> None:
        """
        Publish a value or multiple values to a specific datastream.
        
        Sends data to the Blynk Cloud for a specific datastream. This data
        is displayed on the Blynk mobile app and can trigger events or
        notifications based on your project configuration. Supports multi-value
        datastreams by passing a list.
        
        :param datastream: Datastream name (e.g., "V5")
        :param value: Single value or list of values to publish
        :param qos: MQTT Quality of Service level (int)

        Example
        -------
            >>> # Single value
            >>> client.publish("V2", temperature)
            >>> # Multiple values
            >>> client.publish("V3", [x, y, z])
        ```
        """

    def publish_batch(self, datastreams: dict, qos: int = 0) -> None:
        """
        Publish multiple datastreams in a single message (saves quota).
        
        Efficiently sends multiple datastream values in one MQTT message,
        reducing message quota usage. This is the recommended method when
        updating multiple values simultaneously.
        
        :param datastreams: Dictionary mapping datastream names to values
        :param qos: MQTT Quality of Service level (int)
        
        Example
        -------
            >>> data = {"V1": temp, "V2": humidity, "V3": pressure}
            >>> client.publish_batch(data)
        ```
        """

    def log_event(self, event_code: str, description: str = "", qos: int = 0) -> None:
        """
        Log an event to Blynk for notifications and history.
        
        Sends an event to the Blynk platform which can trigger push notifications,
        emails, or be stored in the event log. Event codes must be configured
        in the Blynk Console.
        
        :param event_code: Event code defined in Blynk Console
        :param description: Optional event description
        :param qos: MQTT Quality of Service level (int)
        
        Example
        -------
            >>> client.log_event("high_temp", "Temperature exceeded 50°C")
        ```
        """

    def set_property(self, datastream: str, prop: str, value: str | int | float | list, qos: int = 0) -> None:
        """
        Set a property for a specific datastream widget.
        
        Dynamically updates widget properties such as label, color, or
        min/max values. This allows runtime customization of the mobile
        app interface based on device state or user preferences.
        Supports multi-value properties by passing a list.
        
        :param datastream: Target datastream name (e.g., "V2")
        :param prop: Property to change (e.g., "label", "color", "min", "max")
        :param value: New value for the property (single value or list)
        :param qos: MQTT Quality of Service level (int)
        
        Example
        -------
            >>> client.set_property("V2", "label", "CPU Temp")
            >>> client.set_property("V2", "color", "#FF0000")
            >>> client.set_property("V2", "labels", ["Off", "On"])
        ```
        """

    def erase_property(self, datastream: str, prop: str, qos: int = 0) -> None:
        """
        Erase a property value for a specific datastream widget.
        
        Removes the stored property value for the specified datastream widget,
        reverting it to its default state.
        
        :param datastream: Target datastream name (e.g., "V2")
        :param prop: Property to erase (e.g., "label", "color")
        :param qos: MQTT Quality of Service level (int)
        
        Example
        -------
            >>> client.erase_property("V2", "color")
        ```
        """

    def set_metadata(self, field: str, value: str, qos: int = 0) -> None:
        """
        Set a metadata field value on the Blynk server.
        
        Updates device metadata such as description, connectivity info, etc.
        Metadata fields must be defined in the Blynk Console.
        
        :param field: Metadata field name
        :param value: New value for the field
        :param qos: MQTT Quality of Service level (int)
        
        Example
        -------
            >>> client.set_metadata("description", "Living Room Sensor")
        ```
        """

    def get_metadata(self, *fields: str, qos: int = 1) -> None:
        """
        Request metadata field values from the Blynk server.
        
        Requests one or more metadata field values. The response is delivered
        via the "_meta" callback.
        
        :param fields: One or more metadata field names to request
        :param qos: MQTT Quality of Service level (int)
        
        Example
        -------
            >>> def on_meta(field, value):
            ...     print(f"{field} = {value}")
            >>> client.add_subscribe_callback("_meta", on_meta)
            >>> client.get_metadata("description", "location")
        ```
        """

    def get_datastreams(self, *names: str, qos: int = 1) -> None:
        """
        Request specific datastream values from the Blynk server.
        
        Requests current values of one or more datastreams. Responses are
        delivered via registered datastream callbacks.
        
        :param names: One or more datastream names to request
        :param qos: MQTT Quality of Service level (int)
        
        Example
        -------
            >>> client.get_datastreams("V1", "V2", "V3")
        ```
        """

    def get_all_datastreams(self, qos: int = 1) -> None:
        """
        Request all datastream values from the Blynk server.
        
        Requests current values of all datastreams. Responses are delivered
        via registered datastream callbacks.
        
        :param qos: MQTT Quality of Service level (int)
        
        Example
        -------
            >>> client.get_all_datastreams()
        ```
        """

    def erase_datastream(self, datastream: str, qos: int = 0) -> None:
        """
        Delete the value of a datastream on the Blynk server.
        
        Removes the stored value for the specified datastream.
        
        :param datastream: Datastream name to erase
        :param qos: MQTT Quality of Service level (int)
        
        Example
        -------
            >>> client.erase_datastream("V5")
        ```
        """

    def get_location(self, qos: int = 1) -> None:
        """
        Request device location from the Blynk server.
        
        Requests the device's location. The response is delivered
        via the "_loc" callback as a payload string.
        
        :param qos: MQTT Quality of Service level (int)
        
        Example
        -------
            >>> def on_location(payload):
            ...     print(f"Location payload: {payload}")
            >>> client.add_subscribe_callback("_loc", on_location)
            >>> client.get_location()
        ```
        """

    def get_utc(self, timeout_ms: int = 5000) -> dict | None:
        """
        Get the current UTC time from the Blynk server with timeout.
        
        Requests and retrieves the current UTC time from the Blynk Cloud
        server. Useful for devices without a real-time clock to synchronize
        time. The method blocks until response is received or timeout occurs.
        
        :param timeout_ms: Maximum time to wait for response in milliseconds
        :return: Dictionary with 'time' (ISO8601 string) and 'zone' (timezone name), or None on timeout
        
        Example
        -------
            >>> utc_data = client.get_utc()
            >>> if utc_data:
            ...     print(f"Time: {utc_data['time']}, Zone: {utc_data['zone']}")
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
