"""
BLE Mesh Module

Simple flooding mesh network over BLE advertising. Provides connectionless,
relay-based communication for MCU-to-MCU messaging without pairing.

Key Features:

    - Connectionless: No pairing or connection management
    - Automatic relay: Messages forwarded by intermediate nodes
    - Deduplication: Prevents message loops via sequence tracking
    - Multi-group: Logical network segmentation
    - Ping/Pong: Network discovery and latency measurement

Architecture:
    Each node broadcasts messages via BLE advertising. Other nodes in range
    receive and optionally relay the message (with decremented TTL).
    
    ```
    Node A ──broadcast──> Node B ──relay──> Node C
                           ↓
                         Node D
    ```

Protocol:
    Messages encoded in manufacturer advertising data (Company ID 0xFFFF).
    Max payload: 13 bytes (BLE advertising limit - 7 byte header).

Author: PlanXLab Development Team
"""

from typing import Callable


class BLEMesh:
    """
    Simple flooding mesh network over BLE advertising.
    
    Each node broadcasts messages and relays received messages
    from other nodes. Uses TTL to prevent infinite loops.
    
    Features:
    
        - No connection management (pure advertising)
        - Automatic message relay with TTL
        - Message deduplication via sequence tracking
        - Group-based filtering
        - Ping/Pong for network discovery
    
    Example
    --------
    Basic mesh node::
    
        >>> from mesh import BLEMesh
        >>> 
        >>> mesh = BLEMesh(node_id=0x0001, group_id=1)
        >>> mesh.on_message = lambda src, data, rssi: print(f"From {src:04X}: {data}")
        >>> 
        >>> mesh.start()
        >>> mesh.send(b"Hello mesh!")
    """
    
    def __init__(self, node_id: int = None, *, group_id: int = 0x01):
        """
        Initialize mesh node.
        
        :param node_id: Unique node identifier (0x0000-0xFFFF).
            If None, uses last 2 bytes of MAC address.
        :param group_id: Logical group for message filtering (0x00-0xFF).
            Messages to group 0x00 are received by all groups.
        
        Example
        --------
        ```python
            >>> # Auto-generated node ID from MAC
            >>> mesh = BLEMesh()
            
            >>> # Explicit node ID
            >>> mesh = BLEMesh(node_id=0x1234)
            
            >>> # Different group for network segmentation
            >>> mesh_sensors = BLEMesh(node_id=0x0001, group_id=1)
            >>> mesh_actuators = BLEMesh(node_id=0x0002, group_id=2)
        ```
        """

    # ─────────────────────────────────────────────────────────────
    # Properties
    # ─────────────────────────────────────────────────────────────

    @property
    def node_id(self) -> int:
        """
        This node's unique identifier.
        
        :return: 16-bit node ID
        """

    @property
    def group_id(self) -> int:
        """
        This node's group identifier.
        
        :return: 8-bit group ID
        """

    @property
    def is_running(self) -> bool:
        """
        Check if mesh is active (scanning and ready to send).
        
        :return: True if running, False otherwise
        """

    @property
    def relay_enabled(self) -> bool:
        """
        Check if message relay is enabled.
        
        :return: True if relaying received messages
        """
    
    @relay_enabled.setter
    def relay_enabled(self, value: bool) -> None:
        """
        Enable or disable message relay.
        
        When disabled, this node only receives messages but doesn't forward them.
        Useful for edge nodes or to reduce network traffic.
        
        :param value: True to enable relay, False to disable
        
        Example
        --------
        ```python
            >>> # Edge node that doesn't relay
            >>> mesh.relay_enabled = False
        ```
        """

    @property
    def stats(self) -> dict[str, int]:
        """
        Get transmission statistics.
        
        :return: Dictionary with keys:
            - ``tx_count``: Messages sent by this node
            - ``rx_count``: Unique messages received
            - ``relay_count``: Messages relayed
            - ``dup_count``: Duplicate messages filtered
        
        Example
        --------
        ```python
            >>> stats = mesh.stats
            >>> print(f"TX: {stats['tx_count']}, RX: {stats['rx_count']}")
            >>> print(f"Relayed: {stats['relay_count']}, Duplicates: {stats['dup_count']}")
        ```
        """

    def reset_stats(self) -> None:
        """
        Reset all statistics to zero.
        """

    # ─────────────────────────────────────────────────────────────
    # Callbacks
    # ─────────────────────────────────────────────────────────────

    @property
    def on_message(self) -> Callable[[int, bytes, int], None] | None:
        """
        Callback invoked when a data message is received.
        
        Signature: ``callback(src: int, data: bytes, rssi: int) -> None``
        
        :param src: Source node ID
        :param data: Message payload (bytes)
        :param rssi: Signal strength in dBm
        
        Example
        --------
        ```python
            >>> def handle_message(src, data, rssi):
            ...     print(f"Node {src:04X} ({rssi}dBm): {data.decode()}")
            >>> mesh.on_message = handle_message
        ```
        """
    
    @on_message.setter
    def on_message(self, cb: Callable[[int, bytes, int], None] | None) -> None: ...

    @property
    def on_ping(self) -> Callable[[int, int], None] | None:
        """
        Callback invoked when a ping request or pong response is received.
        
        Signature: ``callback(node_id: int, rssi: int) -> None``
        
        For ping: Called when another node pings us
        For pong: Called when we receive a response to our ping
        
        Example
        --------
        ```python
            >>> def handle_ping(node_id, rssi):
            ...     print(f"Ping from {node_id:04X}, RSSI: {rssi}dBm")
            >>> mesh.on_ping = handle_ping
            >>> 
            >>> # Discover nearby nodes
            >>> mesh.ping()
        ```
        """
    
    @on_ping.setter
    def on_ping(self, cb: Callable[[int, int], None] | None) -> None: ...

    @property
    def on_error(self) -> Callable[[str, str], None] | None:
        """
        Callback invoked when an error occurs.
        
        Signature: ``callback(error_type: str, details: str) -> None``
        
        Error types:
            - ``start_error``: Failed to start scanning
            - ``send_error``: Failed to broadcast message
            - ``relay_error``: Failed to relay message
        
        Example
        --------
        ```python
            >>> mesh.on_error = lambda t, d: print(f"Error [{t}]: {d}")
        ```
        """
    
    @on_error.setter
    def on_error(self, cb: Callable[[str, str], None] | None) -> None: ...

    def start(self) -> bool:
        """
        Start the mesh network (begin scanning).
        
        :return: True if started successfully
        
        Example
        --------
        ```python
            >>> mesh = BLEMesh(node_id=0x0001)
            >>> mesh.on_message = handle_message
            >>> if mesh.start():
            ...     print("Mesh active")
        ```
        """

    def stop(self) -> None:
        """
        Stop the mesh network (stop scanning).
        
        Does not deactivate BLE, can be restarted with start().
        """

    def deinit(self) -> None:
        """
        Fully shut down the mesh and release BLE resources.
        
        Cannot be restarted after deinit().
        """

    def __enter__(self) -> "BLEMesh":
        """Enter context manager (calls start())."""
    
    def __exit__(self, *args) -> None:
        """Exit context manager (calls deinit())."""

    def send(self, data: bytes | str, *, ttl: int = None, target_group: int = None) -> bool:
        """
        Broadcast a message to the mesh network.
        
        :param data: Payload to send (bytes or str, max 13 bytes)
        :param ttl: Time-to-live (hop count), default 3, max 7
        :param target_group: Target group ID, None = own group, 0x00 = all groups
        
        :return: True if broadcast initiated
        
        :raises ValueError: If payload exceeds 13 bytes
        
        Example
        --------
        ```python
            >>> # Simple message
            >>> mesh.send(b"TEMP:23.5")
            
            >>> # String auto-encoded to UTF-8
            >>> mesh.send("Hello!")
            
            >>> # High TTL for larger network
            >>> mesh.send(b"DATA", ttl=5)
            
            >>> # Broadcast to all groups
            >>> mesh.send(b"ALERT", target_group=0x00)
        ```
        """

    def ping(self, target_node: int = 0xFFFF) -> bool:
        """
        Send a ping to discover nodes or measure latency.
        
        :param target_node: Node to ping, 0xFFFF = broadcast (all nodes respond)
        
        :return: True if ping sent
        
        Responses arrive via on_ping callback.
        
        Example
        --------
        ```python
            >>> # Discover all nearby nodes
            >>> mesh.ping()
            
            >>> # Ping specific node
            >>> mesh.ping(target_node=0x1234)
        ```
        """
