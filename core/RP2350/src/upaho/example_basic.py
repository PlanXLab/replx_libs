"""
u-paho-mqtt Basic Example

Simple publish and subscribe example.
"""

from upaho import Client
import time


def on_connect(client, userdata, flags, rc, properties):
    """Called when connected to broker"""
    print(f"Connected with result code {rc}")
    
    if rc == 0:
        # Subscribe to topics
        client.subscribe("test/topic", qos=1)
        print("Subscribed to test/topic")


def on_message(client, userdata, message):
    """Called when a message is received"""
    print(f"\n--- Message Received ---")
    print(f"Topic: {message.topic}")
    print(f"Payload: {message.payload.decode()}")
    print(f"QoS: {message.qos}")
    print(f"Retain: {message.retain}")


def on_publish(client, userdata, mid):
    """Called when a message is published"""
    print(f"Message {mid} published")


def on_subscribe(client, userdata, mid, granted_qos, properties):
    """Called when subscription is confirmed"""
    print(f"Subscribed with QoS: {granted_qos}")


def on_disconnect(client, userdata, rc, properties):
    """Called when disconnected from broker"""
    print(f"Disconnected with result code {rc}")


def main():
    # Create client
    client = Client(client_id="upaho_example")
    
    # Set authentication (if needed)
    # client.username_pw_set("username", "password")
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.on_subscribe = on_subscribe
    client.on_disconnect = on_disconnect
    
    # Connect to broker
    print("Connecting to MQTT broker...")
    rc = client.connect("test.mosquitto.org", 1883, 60)
    
    if rc != 0:
        print(f"Connection failed with code {rc}")
        return
    
    # Publish messages periodically
    counter = 0
    try:
        while True:
            # Process network events
            client.loop(timeout=0.1)
            
            # Publish every 5 seconds
            if counter % 50 == 0:
                msg = f"Hello from u-paho-mqtt! Count: {counter // 50}"
                client.publish("test/topic", msg, qos=1)
            
            counter += 1
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        client.disconnect()


if __name__ == "__main__":
    main()
