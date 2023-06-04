import logging

import paho.mqtt.client as mqtt

from serving.core import exception
from serving.outlet import abstract_outlet as ao


def new_outlet(configs):
    return MQTTOutlet(configs)

class MQTTOutlet(ao.AbstractOutlet):
    def __init__(self, configs):
        super().__init__(configs)
        self.qos = configs.get('qos')
        if self.qos is None:
            logging.warning("mqtt qos not provided, use qos=0")
            self.qos = 0
        if self.qos != 0 and self.qos != 1 and self.qos != 2:
            raise exception.ParamValidationError(": invalid mqtt qos")
        self.key_as_topic = configs.get('key_as_topic')
        if self.key_as_topic is None:
            self.key_as_topic = True
        self.topic = configs.get('topic')
        if self.topic is None and not self.key_as_topic:
            raise exception.ParamValidationError(": invalid mqtt topic")

    def _init_outlet(self):
        conf_host = self.configs.get('host')
        if conf_host is None:
            conf_host = '127.0.0.1'
        conf_port = self.configs.get('port')
        if conf_port is None:
            conf_port = 1883
        conf_keepalive = self.configs.get('keepalive')
        if conf_keepalive is None:
            conf_keepalive = 60
        self.outlet_object = mqtt.Client()
        self.outlet_object.on_log = _mqtt_on_log
        self.outlet_object.on_connect = _mqtt_on_connect
        self.outlet_object.on_publish = _mqtt_on_publish
        self.outlet_object.connect(conf_host, conf_port, conf_keepalive)

    def post_result(self, task, data):
        if self.key_as_topic:
            self.outlet_object.publish(task.task_id, payload="{}".format(data), qos=self.qos)
        else:
            self.outlet_object.publish(self.topic, payload="{}:{}".format(task.task_id, data), qos=self.qos)

def _mqtt_on_log(client, userdata, level, buf):
    logging.debug("MQTTOutlet on_log: %s", buf)

def _mqtt_on_publish(client, userdata, mid):
    logging.debug("MQTTOutlet on_publish: %s", mid)

def _mqtt_on_connect(client, userdata, flags, rc):
    logging.debug("MQTTOutlet on_connect: returns %s", str(rc))

def _mqtt_on_message(self, client, userdata, msg):
    logging.debug("MQTTOutlet on_message: %s << %s", msg.topic, msg.payload)
