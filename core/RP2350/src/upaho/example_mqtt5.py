"""
u-paho-mqtt MQTT 5.0 Advanced Example

Demonstrates MQTT 5.0 specific features:
- Properties
- Request/Response Pattern
- Message Expiry
- User Properties
"""

from upaho import Client, Properties, PropertyType, MQTTProtocolVersion
import time
import json


def on_connect(client, userdata, flags, rc, properties):
    """Called when connected to broker"""
    print(f"Connected with result code {rc}")
    print(f"Session present: {flags.get('session_present', False)}")
    
    if rc == 0 and properties:
        # Print server capabilities
        if properties.has(PropertyType.SERVER_KEEP_ALIVE):
            keepalive = properties.get(PropertyType.SERVER_KEEP_ALIVE)
            print(f"Server keepalive: {keepalive}s")
        
        if properties.has(PropertyType.MAXIMUM_PACKET_SIZE):
            max_size = properties.get(PropertyType.MAXIMUM_PACKET_SIZE)
            print(f"Maximum packet size: {max_size} bytes")
        
        if properties.has(PropertyType.TOPIC_ALIAS_MAXIMUM):
            max_alias = properties.get(PropertyType.TOPIC_ALIAS_MAXIMUM)
            print(f"Topic alias maximum: {max_alias}")
        
        # Subscribe to topics
        client.subscribe("sensor/#", qos=1)
        client.subscribe("request/#", qos=1)


def on_message(client, userdata, message):
    """Called when a message is received"""
    print(f"\n--- Message Received ---")
    print(f"Topic: {message.topic}")
    print(f"Payload: {message.payload.decode()}")
    
    # Check MQTT 5.0 properties
    props = message.properties
    
    if props.has(PropertyType.CONTENT_TYPE):
        content_type = props.get(PropertyType.CONTENT_TYPE)
        print(f"Content-Type: {content_type}")
    
    if props.has(PropertyType.MESSAGE_EXPIRY_INTERVAL):
        expiry = props.get(PropertyType.MESSAGE_EXPIRY_INTERVAL)
        print(f"Expires in: {expiry}s")
    
    if props.has(PropertyType.USER_PROPERTY):
        user_props = props.get(PropertyType.USER_PROPERTY)
        print(f"User Properties: {user_props}")
    
    # Handle request/response pattern
    if props.has(PropertyType.RESPONSE_TOPIC):
        response_topic = props.get(PropertyType.RESPONSE_TOPIC)
        correlation_data = props.get(PropertyType.CORRELATION_DATA, b"")
        
        print(f"Response requested to: {response_topic}")
        
        # Send response
        response_props = Properties()
        response_props.set(PropertyType.CORRELATION_DATA, correlation_data)
        response_props.set(PropertyType.CONTENT_TYPE, "application/json")
        
        response_payload = json.dumps({
            "status": "ok",
            "timestamp": time.time(),
            "original": message.payload.decode()
        })
        
        client.publish(response_topic, response_payload,
                      qos=1, properties=response_props)
        print(f"Response sent to {response_topic}")


def publish_with_properties(client):
    """Publish messages with MQTT 5.0 properties"""
    
    # Example 1: Message with expiry and content type
    print("\n--- Publishing with Message Expiry ---")
    props1 = Properties()
    props1.set(PropertyType.MESSAGE_EXPIRY_INTERVAL, 300)  # 5 minutes
    props1.set(PropertyType.CONTENT_TYPE, "text/plain")
    
    client.publish("sensor/temperature", "23.5", qos=1, properties=props1)
    
    # Example 2: JSON data with content type
    print("\n--- Publishing JSON Data ---")
    props2 = Properties()
    props2.set(PropertyType.CONTENT_TYPE, "application/json")
    props2.set(PropertyType.USER_PROPERTY, ("device", "sensor_01"))
    props2.set(PropertyType.USER_PROPERTY, ("location", "room_A"))
    
    data = json.dumps({
        "temperature": 23.5,
        "humidity": 65.2,
        "pressure": 1013.25
    })
    
    client.publish("sensor/data", data, qos=1, properties=props2)
    
    # Example 3: Request/Response pattern
    print("\n--- Publishing Request with Response Topic ---")
    props3 = Properties()
    props3.set(PropertyType.RESPONSE_TOPIC, "response/sensor_01")
    props3.set(PropertyType.CORRELATION_DATA, b"req_001")
    props3.set(PropertyType.CONTENT_TYPE, "application/json")
    
    request = json.dumps({
        "command": "get_status",
        "target": "all_sensors"
    })
    
    client.publish("request/status", request, qos=1, properties=props3)


def main():
    # Create MQTT 5.0 client
    client = Client(
        client_id="upaho_mqtt5_example",
        protocol=MQTTProtocolVersion.MQTTv5
    )
    
    # Set authentication
    # client.username_pw_set("username", "password")
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Set connect properties (MQTT 5.0)
    connect_props = Properties()
    connect_props.set(PropertyType.SESSION_EXPIRY_INTERVAL, 3600)  # 1 hour
    connect_props.set(PropertyType.RECEIVE_MAXIMUM, 100)
    connect_props.set(PropertyType.USER_PROPERTY, ("device_type", "sensor"))
    connect_props.set(PropertyType.USER_PROPERTY, ("firmware_version", "1.0.0"))
    
    client._connect_properties = connect_props
    
    # Connect to MQTT 5.0 broker
    print("Connecting to MQTT 5.0 broker...")
    rc = client.connect("test.mosquitto.org", 1883, 60)
    
    if rc != 0:
        print(f"Connection failed with code {rc}")
        return
    
    # Wait for connection
    time.sleep(1)
    
    # Publish examples
    publish_with_properties(client)
    
    # Run loop
    print("\nRunning loop...")
    try:
        while True:
            client.loop(timeout=1.0)
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        client.disconnect()


if __name__ == "__main__":
    main()
