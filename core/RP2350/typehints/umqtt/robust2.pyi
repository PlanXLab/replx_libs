from . import simple2


class MQTTClient(simple2.MQTTClient):
    DEBUG = False

    # Information whether we store unsent messages with the flag QoS==0 in the queue.
    KEEP_QOS0 = True
    # Option, limits the possibility of only one unique message being queued.
    NO_QUEUE_DUPS = True
    # Limit the number of unsent messages in the queue.
    MSG_QUEUE_MAX = 5
    # How many PIDs we store for a sent message
    CONFIRM_QUEUE_MAX = 10
    # When you reconnect, all existing subscriptions are renewed.
    RESUBSCRIBE = True

    def __init__(self, client_id:str, server:str, port:int=0, user:str=None, password:str=None, keepalive:int=0,
                 ssl:bool=False, ssl_params:dict=None, socket_timeout:int=5, message_timeout:int=10):
        """
        initializes MQTTClient object.
        
        :param client_id: Unique MQTT ID attached to client. It must be unique for each client.
        :param server: MQTT host address.
        :param port: MQTT Port, typically 1883. If unset, the port number will default to 1883 of 8883 base on ssl.
        :param user: Username if your server requires it.
        :param password: Password if your server requires it.
        :param keepalive: The Keep Alive is a time interval measured in seconds since the last correct control packet was received.
        :param ssl: Require SSL for the connection.
        :param ssl_params: Required SSL parameters. Kwargs from function ssl.wrap_socket.
        :param socket_timeout: The time in seconds after which the socket interrupts the connection to the server when no data exchange takes place. None - socket blocking, positive number - seconds to wait.
        :param message_timeout: The time in seconds after which the library recognizes that a message with QoS=1 or topic subscription has not been received by the server.
        """

    def is_keepalive(self):
        """
        It checks if the connection is active. If the connection is not active at the specified time,
        saves an error message and returns False.

        :return: If the connection is not active at the specified time returns False otherwise True.
        """

    def set_callback_status(self, f:callable):
        """
        See documentation for `umqtt.simple2.MQTTClient.set_callback_status()`
        """

    def cbstat(self, pid:int, stat:int):
        """
        Captured message statuses affect the queue here.

        :param pid: PID of the message or subscription
        :param stat: Status of the message or subscription
            stat == 0 - the message goes back to the message queue to be sent
            stat == 1 or 2 - the message is removed from the queue
        """

    def connect(self, clean_session:bool=True):
        """
        See documentation for `umqtt.simple2.MQTTClient.connect()`.
        If clean_session==True, then the queues are cleared.

        Connection problems are captured and handled by `is_conn_issue()`

        :param clean_session: If True, clears the message and subscription queues before connecting.
        :return: None or True if the connection is successful.
        """

    def log(self):
        """
        This function is used to log connection issues.
        It prints the last connection issue to the console if DEBUG is enabled.
        The connection issue is stored in `self.conn_issue` and can be checked using `is_conn_issue()`.
        It is best to call this function after checking the connection issue with `is_conn_issue()`.
        """

    def reconnect(self):
        """
        The function tries to resume the connection.

        Connection problems are captured and handled by `is_conn_issue()`
        """

    def resubscribe(self):
        """
        Function from previously registered subscriptions, sends them again to the server.
        """

    def things_to_do(self):
        """
        The sum of all actions in the queues.

        When the value equals 0, it means that the library has sent and confirms the sending:
          * all messages
          * all subscriptions

        When the value equals 0, it means that the device can go into hibernation mode,
        assuming that it has not subscribed to some topics.

        :return: 0 (nothing to do) or int (number of things to do)
        """
        
    def add_msg_to_send(self, data:tuple):
        """
        By overwriting this method, you can control the amount of stored data in the queue.
        
        This is important because we do not have an infinite amount of memory in the devices.
        Currently, this method limits the queue length to MSG_QUEUE_MAX messages.
        The number of active messages is the sum of messages to be sent with messages awaiting confirmation.
        
        :param data: tuple (topic, msg, retain, qos) or (topic, qos) for subscriptions
        """

    def disconnect(self):
        """
        See documentation for `umqtt.simple2.MQTTClient.disconnect()`
        Connection problems are captured and handled by `is_conn_issue()`
        """

    def ping(self):
        """
        See documentation for `umqtt.simple2.MQTTClient.ping()`
        Connection problems are captured and handled by `is_conn_issue()`
        """

    def publish(self, topic:str, msg:str, retain:bool=False, qos:int=0):
        """
        See documentation for `umqtt.simple2.MQTTClient.publish()`
        The function tries to send a message. If it fails, the message goes to the message queue for sending.
        The function does not support the `dup` parameter!
        When we have messages with the retain flag set, only one last message with that flag is sent!
        Connection problems are captured and handled by `is_conn_issue()`

        :param topic: Topic to publish the message to
        :param msg: Message to be sent
        :param retain: If True, the message will be retained by the broker
        :param qos: Quality of Service level (0, 1, or 2)
        :return: None od PID for QoS==1 (only if the message is sent immediately, otherwise it returns None)
        """

    def subscribe(self, topic:str, qos:int=0, resubscribe:bool=True):
        """
        See documentation for `umqtt.simple2.MQTTClient.subscribe()`
        The function tries to subscribe to the topic. If it fails,
        the topic subscription goes into the subscription queue.
        Connection problems are captured and handled by `is_conn_issue()`
        
        :param topic: Topic to subscribe to
        :param qos: Quality of Service level (0, 1, or 2)
        :param resubscribe: If True, the topic will be re-subscribed if it already exists in the subscription list.
                            This is useful when reconnecting to the broker.
        :return: PID of the subscription (if successful) or None if it fails
        """

    def send_queue(self):
        """
        The function tries to send all messages and subscribe to all topics that are in the queue to send.

        :return: True if the queue's empty.
        """

    def is_conn_issue(self):
        """
        With this function we can check if there is any connection problem.
        It is best to use this function with the reconnect() method to resume the connection when it is broken.

        You can also check the result of methods such as this:
        `connect()`, `publish()`, `subscribe()`, `reconnect()`, `send_queue()`, `disconnect()`, `ping()`, `wait_msg()`,
        `check_msg()`, `is_keepalive()`.

        The value of the last error is stored in self.conn_issue.

        :return: Connection problem
        """

    def wait_msg(self):
        """
        See documentation for `umqtt.simple2.MQTTClient.wait_msg()`

        Connection problems are captured and handled by `is_conn_issue()`
        """

    def check_msg(self):
        """
        See documentation for `umqtt.simple2.MQTTClient.check_msg()`

        Connection problems are captured and handled by `is_conn_issue()`
        """
