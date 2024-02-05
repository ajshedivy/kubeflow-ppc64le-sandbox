import requests
import json

MODEL_NAME = "fraud-detection-fd6e7"
NAMESPACE = "user-example-com"
HOST = "fraud-detection-fd6e7-user-example-com.apps.b2s001.pbm.ihost.com"
HEADERS = {"Host": HOST}
MODEL_ENDPOINT = "http://fraud-detection-fd6e7-user-example-com.apps.b2s001.pbm.ihost.com"
PREDICT_ENDPOINT = MODEL_ENDPOINT + "/infer"

try:
        res = requests.get(MODEL_ENDPOINT, headers=HEADERS)
        print(res.json)
except Exception as e:
        print(f"except: {e}")