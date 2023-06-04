import logging
import os
import json
import time
import requests

from serving.core.memory import REQUESTS_COUNT

def enable():
    try:
        edgegw_addr = os.getenv("GATEWAY_ADDR")
        port_name = os.getenv("PORT_NAME")
        if edgegw_addr == None:
            edgegw_addr = '127.0.0.1:5000'
        if port_name == None:
            port_name = '5000'

        requests_dic = {
            'ai_name' : "ligo",
            'heartbeat_path' : "/api/ping",
            'address' : "edgegw.iotedge:{}".format(port_name),
        }

#        global REQUESTS_COUNT
#        current_count = REQUESTS_COUNT
        resp = requests.post('http://{}/api/v1/ai/v1/register'.format(edgegw_addr), data=json.dumps(requests_dic))
        logging.debug(resp)
#        while True:
#            time.sleep(120)
#            if current_count == REQUESTS_COUNT:
#                resp = requests.post('http://{}/api/v1/ai/v1/register'.format(edgegw_addr), data=json.dumps(requests_dic))
#                logging.debug(resp)
    except Exception as e:
        logging.debug("Fail to register ai-service, please check the network")
