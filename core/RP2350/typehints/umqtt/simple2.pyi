
class MQTTException(Exception):
    pass


def pid_gen(pid=0):
    while True:
        pid = pid + 1 if pid < 65535 else 1
        yield pid


class MQTTClient:

    def __init__(self, client_id:str, server:str, port:int=0, user:str=None, password:str=None, keepalive:int=0,
                 ssl:bool=False, ssl_params:dict=None, socket_timeout:int=5, message_timeout:int=10):
        """
        Initializes MQTTClient object.
        
        :param client_id: Unique MQTT ID attached to client. It must be unique for each client.
        :param server: MQTT host address.
        :param port: MQTT Port, typically 1883. If unset, the port number will default to 1883 of 8883 base on ssl.
        :param user: Username if your server requires it.
        :param password: Password if your server requires it.
        :param keepalive: The Keep Alive is a time interval measured in seconds since the last
                          correct control packet was received.
        :param ssl: Require SSL for the connection.
        :param ssl_params: Required SSL parameters. Kwargs from function ssl.wrap_socket.
                           See documentation: https://docs.micropython.org/en/latest/library/ssl.html#ssl.ssl.wrap_socket
                           For esp8266, please refer to the capabilities of the axTLS library applied to the micropython port.
                           https://axtls.sourceforge.net
        :param socket_timeout: The time in seconds after which the socket interrupts the connection to the server when
                               no data exchange takes place. None - socket blocking, positive number - seconds to wait.
        :param message_timeout: The time in seconds after which the library recognizes that a message with QoS=1
                                or topic subscription has not been received by the server.
        """


    def set_callback(self, f:callable):
        """
        Set callback for received subscription messages.
        
        :param f: callable(topic, msg, retained, duplicate)
        """

    def set_callback_status(self, f:callable):
        """
        Set the callback for information about whether the sent packet (QoS=1)
        or subscription was received or not by the server.
        
        :param f: callable(pid, status)

        Where:
            status = 0 - timeout
            status = 1 - successfully delivered
            status = 2 - Unknown PID. It is also possible that the PID is outdated,
                         i.e. it came out of the message timeout.
        """

    def set_last_will(self, topic:bytes, msg:bytes, retain:bool=False, qos:int=0):
        """
        Sets the last will and testament of the client. This is used to perform an action by the broker
        in the event that the client "dies".
        Learn more at https://www.hivemq.com/blog/mqtt-essentials-part-9-last-will-and-testament/
        
        :param topic: Topic of LWT. Takes the from "path/to/topic"
        :param msg: Message to be published to LWT topic.
        :param retain: Have the MQTT broker retain the message.
        :param qos: Sets quality of service level. Accepts values 0 to 2. PLEASE NOTE qos=2 is not actually supported.
        """
        
    def connect(self, clean_session:bool=True):
        """
        Establishes connection with the MQTT server.
        
        :param clean_session: Starts new session on true, resumes past session if false.
        :return: Existing persistent session of the client from previous interactions.
        """

    def disconnect(self):
        """
        Disconnects from the MQTT server.
        """

    def ping(self):
        """
        Pings the MQTT server.
        """

    def publish(self, topic:bytes, msg:bytes, retain:bool=False, qos:int=0, dup:bool=False):
        """
        Publishes a message to a specified topic.

        :param topic: Topic you wish to publish to. Takes the form "path/to/topic"
        :param msg: Message to publish to topic.
        :param retain: Have the MQTT broker retain the message.
        :param qos: Sets quality of service level. Accepts values 0 to 2. PLEASE NOTE qos=2 is not actually supported.
        :param dup: Duplicate delivery of a PUBLISH Control Packet
        """
        
    def subscribe(self, topic:bytes, qos:int=0):
        """
        Subscribes to a given topic.
        
        :param topic: Topic you wish to publish to. Takes the form "path/to/topic"
        :param qos: Sets quality of service level. Accepts values 0 to 1. This gives the maximum QoS level at which
                    the Server can send Application Messages to the Client.
        """

    def check_msg(self):
        """
        Checks whether a pending message from server is available.

        If socket_timeout=None, this is the socket lock mode. That is, it waits until the data can be read.

        Otherwise it will return None, after the time set in the socket_timeout.

        It processes such messages:
        - response to PING
        - messages from subscribed topics that are processed by functions set by the set_callback method.
        - reply from the server that he received a QoS=1 message or subscribed to a topic
        """

    def wait_msg(self):
        """
        This method waits for a message from the server.

        Compatibility with previous versions.

        It is recommended not to use this method. Set socket_time=None instead.
        """