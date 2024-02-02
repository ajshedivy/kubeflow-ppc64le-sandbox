import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import pandas as pd
from trino.dbapi import Connection
from sklearn_pandas import DataFrameMapper
import logging
import requests
import numpy as np
from tensorflow import keras
import dill
import os
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

MODEL_NAME = "fraud-detection-fd6e7"
NAMESPACE = "user-example-com"
HOST = f"{MODEL_NAME}-predictor-default.{NAMESPACE}"
HEADERS = {"Host": HOST}
MODEL_ENDPOINT = f"http://{MODEL_NAME}-predictor-default/v2/models/model"
PREDICT_ENDPOINT = MODEL_ENDPOINT + "/infer"


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


# class DBHandler(tornado.web.RequestHandler):
#     def post(self):
#         num_rows = int(self.get_body_argument("num_rows"))
#         data = query_database(num_rows)
#         json_data = data.to_dict(orient="records")
#         self.write(f"data: {json_data}")

class DBHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        logging.info('websocket opened')
    
    
    async def on_message(self, message):
        try:
            if message:
                logging.info("get input from user")
                num_rows = int(message)
                data = query_database(num_rows)
                json_data = data.to_dict(orient="records")
                self.write_message(f"data: {json_data}")
                
                dataset_tranformer = FraudDatasetTransformer()
                t_mapper = get_df_mapper()
                vdf = dataset_tranformer.transform(data, t_mapper)
                outputs = predict(vdf)
                for res in outputs:
                    self.write_message(res[0])
                    self.write_message(res[1])
            else:
                logging.info('message not sent')
        except Exception as e:
            logging.info({e})
            self.write_message(f'error: {e}')
                
    def on_close(self):
        logging.info('websocket closed')


class FraudDatasetTransformer:
    def __init__(self):
        ...

    def transform(self, dataset: pd.DataFrame, mapper: DataFrameMapper):
        tdf = dataset.copy()
        tdf["merchant name"] = tdf["merchant name"].astype(str)
        tdf.drop(["mcc", "zip", "merchant state"], axis=1, inplace=True)
        tdf.sort_values(by=["user", "card"], inplace=True)
        tdf.reset_index(inplace=True, drop=True)

        tdf = mapper.transform(tdf)
        return tdf


def query_database(number_of_rows):
    try:
        logging.info("Establishing connection to Trino")
        with Connection(
            host="trino.trino",
            port="8080",
            user="anybody",
            catalog="jtopen",
            schema="demo",
        ) as conn:
            link = conn.cursor()
            link.execute(f"SELECT * FROM fraud OFFSET 1000000 LIMIT {number_of_rows}")
            return pd.DataFrame(
                link.fetchall(), columns=[i.name for i in link.description]
            )
    except Exception as e:
        logging.info(f"Exception occcured with trino: {e}")
        raise e
        
def get_df_mapper():
    with open(os.path.join("encoders", "data", "mapper.pkl"), "rb") as f:
        t_mapper = dill.load(f)
        return t_mapper
    


def predict(vdf: pd.DataFrame):
    
    outputs = []
    
    res_svc = requests.get(MODEL_ENDPOINT, headers=HEADERS)
    response_svc = json.loads(res_svc.text)

    x, y = vdf.drop(vdf.columns.values[0], axis=1).to_numpy(), vdf[
        vdf.columns.values[0]
    ].to_numpy().reshape(len(vdf), 1)

    dataset = keras.preprocessing.timeseries_dataset_from_array(
        x, y, sequence_length=response_svc["inputs"][0]["shape"][1], batch_size=128
    )

    # code for making the request
    for batch in dataset.take(10):
        input_d, output_d = batch[0], batch[1]
        for in_x, out_y in zip(input_d, output_d):
            payload = {
                "inputs": [
                    {
                        "name": response_svc["inputs"][0]["name"],
                        "shape": [
                            1,
                            4,
                            103,
                        ],  # has to match response_svc["inputs"][0]["shape"] (except for 1. dimension)
                        "datatype": response_svc["inputs"][0]["datatype"],
                        "data": in_x.numpy().tolist(),
                    }
                ]
            }
            res = requests.post(
                PREDICT_ENDPOINT, headers=HEADERS, data=json.dumps(payload)
            )
            response = json.loads(res.text)
            logging.info(response["outputs"])
            pred = response["outputs"][0]["data"][0]
            out_str = f"Actual ({out_y.numpy()[0]}) vs. Prediction ({round(pred, 3)} => {int(round(pred, 0))})"
            logging.info(out_str)
            
            outputs.append((response['outputs'], out_str))


def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/data", DBHandler),
        ],
        template_path='templates',
        static_path='static'
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
