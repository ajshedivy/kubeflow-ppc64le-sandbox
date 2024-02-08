from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
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
app = Flask(__name__)

MODEL_NAME = "fraud-detection-fd6e7"
NAMESPACE = "user-example-com"
HOST = f"{MODEL_NAME}-predictor-default.{NAMESPACE}"
HEADERS = {"Host": HOST}
MODEL_ENDPOINT = f"http://{MODEL_NAME}-predictor-default/v2/models/model"
PREDICT_ENDPOINT = MODEL_ENDPOINT + "/infer"


def generate_dataframe(rows):
    # Example function to generate a DataFrame.
    data = {'Column1': range(1, rows + 1), 'Column2': ['Row' + str(i) for i in range(1, rows + 1)]}
    df = pd.DataFrame(data)
    return df.to_html(classes='table table-striped', index=False, border=0)

@app.route('/', methods=['GET', 'POST'])
def landing():
    if request.method == 'POST':
        rows = int(request.form['rows'])
        table_name = request.form['table_name']
        
        return redirect(url_for('results', rows=rows, table_name=table_name))
    return render_template('landing.html')

@app.route('/results')
def results():
    rows = int(request.args.get('rows', 0))
    table_name = request.args.get('table_name', 'Prediction Results')
    data = query_database(rows)
    dataset_transformer = FraudDatasetTransformer()
    t_mapper = get_df_mapper()
    vdf = dataset_transformer.transform(data, t_mapper)
    outputs = predict(vdf).to_html()
    # outputs = generate_dataframe(rows)
    return render_template('results.html', table_name=table_name, df_html=outputs)
  
class FraudDatasetTransformer:
    def __init__(self): ...

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


def predict(vdf: pd.DataFrame) -> pd.DataFrame:

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
            response["outputs"][0]["actual"] = out_y.numpy()[0]
            response["outputs"][0]["pred"] = int(round(pred, 0))

            outputs.append(response)

    df = pd.json_normalize(
        outputs, "outputs", ["model_name", "model_version"], record_prefix="outputs_"
    )

    return df

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)

