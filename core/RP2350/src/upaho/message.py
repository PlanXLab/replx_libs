from .properties import Properties

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


class MQTTMessage:
    __slots__ = ['timestamp', 'state', 'dup', 'mid', '_topic', '_payload', 
                 '_qos', '_retain', '_properties']
    
    def __init__(self, mid=0, topic=b""):
        self.timestamp = 0
        self.state = 0
        self.dup = False
        self.mid = mid
        self._topic = topic
        self._payload = b""
        self._qos = 0
        self._retain = False
        self._properties = Properties()
    
    @property
    def topic(self):
        if isinstance(self._topic, bytes):
            return self._topic.decode('utf-8')
        return self._topic
    
    @topic.setter
    def topic(self, value):
        if isinstance(value, str):
            self._topic = value.encode('utf-8')
        else:
            self._topic = value
    
    @property
    def payload(self):
        return self._payload
    
    @payload.setter
    def payload(self, value):
        if isinstance(value, str):
            self._payload = value.encode('utf-8')
        elif value is None:
            self._payload = b""
        else:
            self._payload = bytes(value)
    
    @property
    def qos(self):
        return self._qos
    
    @qos.setter
    def qos(self, value):
        self._qos = value
    
    @property
    def retain(self):
        return self._retain
    
    @retain.setter
    def retain(self, value):
        self._retain = value
    
    @property
    def properties(self):
        return self._properties
    
    @properties.setter
    def properties(self, value):
        self._properties = value
    
    def __repr__(self):
        return (f"MQTTMessage(topic={self.topic!r}, "
                f"payload={self._payload!r}, qos={self._qos}, "
                f"retain={self._retain}, mid={self.mid})")


class MQTTMessageInfo:
    __slots__ = ['_mid', '_rc', '_published']
    
    RC_QUEUED = 0
    RC_PUBLISHED = 1
    RC_CONFIRMED = 2
    
    def __init__(self, mid):
        self._mid = mid
        self._rc = self.RC_QUEUED
        self._published = False
    
    @property
    def mid(self):
        return self._mid
    
    @property
    def rc(self):
        return self._rc
    
    def is_published(self):
        return self._published
    
    def _set_published(self):
        self._published = True
        self._rc = self.RC_PUBLISHED
    
    def _set_confirmed(self):
        self._rc = self.RC_CONFIRMED
    
    def __repr__(self):
        return f"MQTTMessageInfo(mid={self._mid}, rc={self._rc}, published={self._published})"


class SubscriptionInfo:
    __slots__ = ['_mid', '_topic', '_qos', '_granted_qos']
    
    def __init__(self, mid, topic, qos):
        self._mid = mid
        self._topic = topic
        self._qos = qos
        self._granted_qos = None
    
    @property
    def mid(self):
        return self._mid
    
    @property
    def topic(self):
        return self._topic
    
    @property
    def qos(self):
        return self._qos
    
    @property
    def granted_qos(self):
        return self._granted_qos
    
    def _set_granted_qos(self, qos):
        self._granted_qos = qos
    
    def __repr__(self):
        return f"SubscriptionInfo(mid={self._mid}, topic={self._topic!r}, granted_qos={self._granted_qos})"
