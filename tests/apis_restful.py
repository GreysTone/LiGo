import json
import time
import base64
import requests

DRAW = False
if DRAW:
    import cv2


def api_post():
    image_path = '/tmp/image'
    with open(image_path, 'rb') as f:
        img = str(base64.b64encode(f.read()), encoding='utf-8')

    result = requests.post("http://localhost:5000/api/detect", 
                           data=json.dumps({'image': img}))

    res = result.json()['result']
    print("raw:", res)
    if DRAW:
        draw(image_path, json.loads(res['simple']))


def draw(path, box):
    frame = cv2.imread(path)
    frame = cv2.resize(frame, (416, 416))
    for b in box:
        lbl = str(b[0])
        xmin = int(b[2])
        xmax = int(b[4])
        ymin = int(b[3])
        ymax = int(b[5])
        frame = cv2.putText(frame, lbl, (xmin, ymin), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (0, 0, 255))
        frame = cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 0, 255), 4)
    cv2.imwrite('result.jpg', frame)


if __name__ == "__main__":
    idx = 0
    for i in range(50):
        time.sleep(0.5)
        idx = idx + 1
        print(">>>>", idx)
        api_post()
