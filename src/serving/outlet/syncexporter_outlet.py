import json
import logging
import requests

from serving.outlet import abstract_outlet as ao

def new_outlet(configs):
    return SyncExporterOutlet(configs)

class SyncExporterOutlet(ao.AbstractOutlet):
    def _init_outlet(self):
        self.outlet_object = []

    def post_result(self, task, data):
        data = json.loads(data)
        extra_info = task.extra
        classes = extra_info["classes"]
        requests_data = {
            "MsgType": 3001,
            "ImgID": extra_info["ImgID"],
            "DetectAction": 0,
            "Result": {i:0 for i in classes},
            "Pos": [],
        }

        for temp in data:
            temp_pos = {}
            temp_pos["name"] = str(temp[0])
            requests_data["Result"][str(temp[0])] += 1
            temp_pos["Similarity"] = int(float(temp[1]) * 100)
            temp_pos["x0"] = int(temp[2])
            temp_pos["y0"] = int(temp[3])
            temp_pos["x1"] = int(temp[4])
            temp_pos["y1"] = int(temp[5])
            requests_data["Pos"].append(temp_pos)

        if len(requests_data["Pos"]) > 0:
            requests_data["DetectAction"] = 1

        url = extra_info.get("url", '')

        if url == '':
            raise RuntimeError("SyncExporter outlet:: url is None!")

        try:
            logging.info("SyncExporter outlet:: requesting {}".format(url))
            logging.info("SyncExporter outlet:: requests_data: {}".format(requests_data))
            response = requests.post(url, data=json.dumps(requests_data))
            logging.info("SyncExporter outlet:: {}".format(response))
        except Exception as err:
            logging.error("SyncExporter outlet export failed!")