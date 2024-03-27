import json
import logging
import os
import time

import dash_bootstrap_components as dbc
import dill
import numpy as np
import pandas as pd
import requests
from jproperties import Properties
from sklearn_pandas import DataFrameMapper
from tensorflow import keras
from trino.dbapi import Connection

import dash
from dash import Input, Output, State, dash_table, dcc, html, dash_table

# ------- Model Params -------

MODEL_NAME = "fraud-detection-fd6e7"
NAMESPACE = "user-example-com"
HOST = f"{MODEL_NAME}-predictor-default.{NAMESPACE}"
HEADERS = {"Host": HOST}
MODEL_ENDPOINT = f"http://{MODEL_NAME}-predictor-default/v2/models/model"
PREDICT_ENDPOINT = MODEL_ENDPOINT + "/infer"

# instantiate config
configs = Properties()
# load properties into configs
with open("app-config.properties", "rb") as config_file:
    configs.load(config_file)
# read into dictionary
configs_dict = {}
items_view = configs.items()
for item in items_view:
    configs_dict[item[0]] = item[1].data


# Read Sample text from file
sample_from_file = ""
with open("email_conv.txt", "r") as sample_text_f:
    sample_from_file = sample_text_f.read()

errors_list = [
    "None",
    "Technical Glitch,                                   ",
    "Insufficient Balance,                               ",
    "Bad PIN,                                            ",
    "Bad PIN,Insufficient Balance,                       ",
    "Bad Expiration,                                     ",
    "Bad PIN,Technical Glitch,                           ",
    "Bad Card Number,                                    ",
    "Bad CVV,                                            ",
    "Bad Zipcode,                                        ",
    "Insufficient Balance,Technical Glitch,              ",
    "Bad Card Number,Insufficient Balance,               ",
    "Bad Card Number,Bad CVV,                            ",
    "Bad CVV,Insufficient Balance,                       ",
    "Bad Card Number,Bad Expiration,                     ",
    "Bad Expiration,Bad CVV,                             ",
    "Bad Expiration,Insufficient Balance,                ",
    "Bad Expiration,Technical Glitch,                    ",
    "Bad Card Number,Bad Expiration,Technical Glitch,    ",
    "Bad CVV,Technical Glitch,                           ",
]

states_list = [
    "ONLINE",
    "AK",
    "AL",
    "AR",
    "AS",
    "AZ",
    "CA",
    "CO",
    "CT",
    "DC",
    "DE",
    "FL",
    "GA",
    "GU",
    "HI",
    "IA",
    "ID",
    "IL",
    "IN",
    "KS",
    "KY",
    "LA",
    "MA",
    "MD",
    "ME",
    "MI",
    "MN",
    "MO",
    "MP",
    "MS",
    "MT",
    "NC",
    "ND",
    "NE",
    "NH",
    "NJ",
    "NM",
    "NV",
    "NY",
    "OH",
    "OK",
    "OR",
    "PA",
    "PR",
    "RI",
    "SC",
    "SD",
    "TN",
    "TT",
    "TX",
    "UT",
    "VA",
    "VI",
    "VT",
    "WA",
    "WI",
    "WV",
    "WY",
]

app = dash.Dash(
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css?family=IBM+Plex+Sans:400,600&display=swap",
    ],
    suppress_callback_exceptions=True
)
app.title = configs_dict["tabtitle"]

navbar_main = dbc.Navbar(
    [
        dbc.Col(
            configs_dict["navbartitle"],
            style={"fontSize": "0.875rem", "fontWeight": "600"},
        ),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem(
                    "View payload",
                    id="payload-button",
                    n_clicks=0,
                    class_name="dmi-class",
                ),
            ],
            toggle_class_name="nav-dropdown-btn",
            caret=False,
            nav=True,
            in_navbar=True,
            label=html.Img(
                src="/assets/settings.svg",
                height="16px",
                width="16px",
                style={"filter": "invert(1)"},
            ),
            align_end=True,
        ),
    ],
    style={
        "paddingLeft": "1rem",
        "height": "3rem",
        "borderBottom": "1px solid #393939",
        "color": "#fff",
    },
    class_name="bg-dark",
)

payload_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("My Payloads")),
        dbc.ModalBody([dbc.Tabs(id="payload-modal-tb", active_tab="payload-tab-0")]),
    ],
    id="payload-modal",
    size="xl",
    scrollable=True,
    is_open=False,
)

user_input = dbc.InputGroup(
    [
        dbc.Textarea(
            id="user-input",
            disabled=eval(configs_dict["app_locked"]),
            value=(
                sample_from_file
                if len(sample_from_file) > 0
                else configs_dict["sample_text"]
            ),
            placeholder=configs_dict["input_placeholder_text"],
            rows=(
                configs_dict["input_h_rows"]
                if configs_dict["layout"] == "horizontal"
                else configs_dict["input_v_rows"]
            ),
            class_name="carbon-input",
        ),
    ],
    className="mb-3",
)

transaction_data = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Merchant Name"),
                dbc.Input(id="merchant_name", type="text", value="Stop n Shop"),
            ]
        ),
        html.Div(
            [dbc.Label("Amount ($)"), dbc.Input(id="amount", type="number", value=0)]
        ),
        html.Div([dbc.Label("User"), dbc.Input(id="user", type="number", value=0)]),
        html.Div([dbc.Label("Card"), dbc.Input(id="card", type="number", value=0)]),
        html.Div(
            [
                dbc.Label("year"),
                dcc.Dropdown(
                    id="year",
                    options=[{"label": i, "value": i} for i in range(1996, 2021)],
                    value=2015,
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Month"),
                dcc.Dropdown(
                    id="month",
                    options=[{"label": i, "value": i} for i in range(1, 13)],
                    value=1,
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Day"),
                dcc.Dropdown(
                    id="day",
                    options=[{"label": i, "value": i} for i in range(1, 31)],
                    value=1,
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Transaction Type"),
                dcc.Dropdown(
                    id="transaction_type",
                    options=[
                        "Swipe Transaction",
                        "Chip Transaction",
                        "Online Transaction",
                    ],
                    value="payment method",
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Merchant City (can use ONLINE)"),
                dbc.Input(id="merchant_city", type="text", value="Bucyrus"),
            ]
        ),
        html.Div(
            [
                dbc.Label("Merchant State (empty if online)"),
                dcc.Dropdown(
                    id='merchant_state',
                    options=states_list,
                    value="OH"
                )
            ]
        ),
        html.Div(
            [
                dbc.Label("Zip (0 if ONLINE)"),
                dbc.Input(id="zip", type="number", value=0),
            ]
        ),
        html.Div(
            [
                dbc.Label("errors"),
                dcc.Dropdown(id="errors", options=errors_list, value=errors_list[0]),
            ]
        ),
    ],
    body=True,
)

generate_button = dbc.Button(
    configs_dict["generate_btn_text"],
    id="generate-button",
    outline=True,
    color="primary",
    n_clicks=0,
    className="carbon-btn",
)

# upload_button = dcc.Upload(
#     id="upload-data",
#     className="upload-data",
#     children=[
#         dbc.Button(
#             "Upload File",
#             outline=True,
#             color="primary",
#             n_clicks=0,
#             className="carbon-btn",
#         ),
#     ],
# )
clear_button = dbc.Button(
    "Clear Transactions", 
    id="clear-transactions-btn", 
    outline=True,
    n_clicks=0,
    className="carbon-btn",
    color="warning"
)

export_button = dbc.Button(
    "Export Transactions", 
    id="export-transactions-btn",
    outline=True,
    n_clicks=0,
    className="carbon-btn",
    color="success"
)

buttonsPanel = (
    dbc.Row(
        [
            # dbc.Col(upload_button),
            dbc.Col(generate_button),
            dbc.Col(clear_button),
            dbc.Col(export_button),
        ]
    )
    if configs_dict["show_upload"] in ["true", "True"]
    else dbc.Row(
        [
            dbc.Col(generate_button, className="text-center"),
        ]
    )
)

footer = html.Footer(
    dbc.Row([dbc.Col(configs_dict["footer_text"], className="p-3")]),
    style={
        "paddingLeft": "1rem",
        "paddingRight": "5rem",
        "color": "#c6c6c6",
        "lineHeight": "22px",
    },
    className="bg-dark position-fixed bottom-0",
)


# Construct the button panel
output_buttons_panel = dbc.Row(
    [
        dbc.Col(clear_button, width={"size": 6, "offset": 0}, className="text-center"),
        dbc.Col(export_button, width={"size": 6, "offset": 0}, className="text-center"),
    ],
    justify="around",  # This will space out the buttons evenly
)


vertical_layout = dbc.Row(
    [
        dbc.Col(className="col-2"),
        dbc.Col(
            children=[
                html.H5(configs_dict["Input_title"]),
                html.Div(transaction_data),
                html.Br(),
                buttonsPanel,
                html.Br(),
                html.Hr(),
                html.Div(
                    [
                        html.H5(configs_dict['output_title']),
                        # Insert the output_buttons_panel here to have it at the top of the generate-output area
                        html.Div(id="generate-output"),  # This div holds the generated transaction output
                    ],
                    style={"padding": "1rem 1rem"},
                ),
            ],
            className="col-8",
        ),
        dbc.Col(className="col-2"),
    ],
    className="px-3 pb-5",
)
download_component = dcc.Download(id='download-transaction-data')

vertical_layout.children[1].children.append(download_component)  # Assuming vertical_layout is your main layout structure


# horizontal_layout = dbc.Row(
#     [
#         dbc.Col(className="col-1"),
#         dbc.Col(
#             children=[
#                 html.H5(configs_dict["Input_title"]),
#                 html.Div(transaction_data),
#                 html.Br(),
#                 buttonsPanel,
#                 html.Br(),
#                 html.Br(),
#             ],
#             className="col-5 border-end",
#             style={"padding": "1rem"},
#         ),
#         dbc.Col(
#             children=[
#                 html.Div(
#                     [
#                         # html.H5(configs.get('Output_title')),
#                         html.Div(
#                             children=[
#                                 html.P(
#                                     configs_dict["helper_text"],
#                                     style={
#                                         "color": "#525252",
#                                         "fontSize": "1rem",
#                                         "fontStyle": "italic",
#                                     },
#                                 )
#                             ],
#                             id="generate-output",
#                         )
#                     ],
#                     style={"padding": "1rem 3rem"},
#                 ),
#             ],
#             className="col-5",
#         ),
#         dbc.Col(className="col-1"),
#     ],
#     className="px-3 pb-5",
# )

app.layout = html.Div(
    children=[
        navbar_main,
        html.Div(payload_modal),
        html.Br(),
        html.Br(),
        vertical_layout,
        html.Br(),
        html.Br(),
        download_component,
        footer,
    ],
    className="bg-white",
    style={"fontFamily": "'IBM Plex Sans', sans-serif"},
)

# app.layout = html.Div(
#     children=[
#         navbar_main,
#         html.Div(payload_modal),
#         html.Br(),
#         dcc.Tabs(id="main-tabs", value='new-transaction', children=[
#             dcc.Tab(label='New Transaction', value='new-transaction', children=[get_transaction_tab_content()]),
#             dcc.Tab(label='Transaction History', value='transaction-history', children=[get_transaction_history_tab_content()])
#         ]),
#         html.Br(),
#         (
#             horizontal_layout
#             if configs_dict["layout"] == "horizontal"
#             else vertical_layout
#         ),
#         html.Br(),
#         dcc.Store(id='store-transaction-history', storage_type='memory'),  # This line adds the Store component
#         footer,
#     ],
#     className="bg-white",
#     style={"fontFamily": "'IBM Plex Sans', sans-serif"},
# )


# ------------------------------ end UI Code ------------------------------

class FraudDatasetTransformer:
    def __init__(self): ...

    def transform(self, dataset: pd.DataFrame, mapper: DataFrameMapper):
        """
        
        dropped columns:
            - mcc
            - zip
            - merchant state

        Args:
            dataset (pd.DataFrame): _description_
            mapper (DataFrameMapper): _description_

        Returns:
            _type_: _description_
        """
        tdf = dataset.copy()
        tdf["merchant name"] = tdf["merchant name"].astype(str)
        tdf.drop(["mcc", "zip", "merchant state"], axis=1, inplace=True)
        tdf.sort_values(by=["user", "card"], inplace=True)
        tdf.reset_index(inplace=True, drop=True)

        tdf = mapper.transform(tdf)
        return tdf


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


test_input = {
    "user": 0,
    "card": 0,
    "merchant name": "Stop n Shop",
    "amount": 0,
    "year": 2015,
    "month": 1,
    "day": 1,
    "transaction type": "payment method",
    "merchant city": "Bucyrus",
    "merchant state": "OH",
    "zip": 0,
    "errors": "None",
    "mcc": 0,
    'is fraud?': 'No'
}


@app.callback(
    Output('generate-output', 'children'),
    [Input('generate-button', 'n_clicks')],
    [State('generate-output', 'children')] +  # Existing output
    [State(component_id, 'value') for component_id in [
        'merchant_name', 'amount', 'user', 'card', 'year',
        'month', 'day', 'transaction_type', 'merchant_city',
        'merchant_state', 'zip', 'errors']]
)
def update_output(n_clicks, existing_output, merchant_name, amount, user, card, year, month, day, transaction_type, merchant_city, merchant_state, zip, errors):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    
    # Parse existing output
    if not existing_output:
        existing_output = []
    elif isinstance(existing_output, str):
        # In case the existing_output is just a string representation (unlikely, but just in case)
        existing_output = json.loads(existing_output)
    
    # Create the new transaction detail as a collapsible element
    new_transaction_detail = html.Details([
        html.Summary(f'Merchant: {merchant_name}, Amount: {amount}', style={'cursor': 'pointer'}),
        dash_table.DataTable(
            data=[
                {'Attribute': 'Merchant Name', 'Value': merchant_name},
                {'Attribute': 'Amount', 'Value': amount},
                {'Attribute': 'User', 'Value': user},
                {'Attribute': 'Card', 'Value': card},
                {'Attribute': 'Date', 'Value': f'{year}-{month}-{day}'},
                {'Attribute': 'Transaction Type', 'Value': transaction_type},
                {'Attribute': 'Merchant City', 'Value': merchant_city},
                {'Attribute': 'Merchant State', 'Value': merchant_state},
                {'Attribute': 'ZIP', 'Value': zip},
                {'Attribute': 'Errors', 'Value': errors}
            ],
            columns=[{'name': i, 'id': i} for i in ['Attribute', 'Value']],
            style_table={'overflowX': 'auto'},
            style_cell={
                'height': 'auto',
                'minWidth': '150px', 'width': '150px', 'maxWidth': '150px',
                'whiteSpace': 'normal'
            },
            style_header={
                'fontWeight': 'bold',
                'textAlign': 'left'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'Attribute'},
                    'textAlign': 'left'
                },
                {
                    'if': {'column_id': 'Value'},
                    'textAlign': 'right'
                }
            ]
        )
    ], style={'marginTop': '20px'})

    # Append the new transaction to the existing output
    updated_output = existing_output + [new_transaction_detail]

    return updated_output
        
@app.callback(
    Output('generate-output', 'children', allow_duplicate=True),
    [Input('clear-transactions-btn', 'n_clicks')],
    prevent_initial_call=True
)
def clear_transactions(n_clicks):
    # Return an empty list to clear the transactions
    return []


import json
from dash.exceptions import PreventUpdate

@app.callback(
    Output('download-transaction-data', 'data'),
    [Input('export-transactions-btn', 'n_clicks')],
    [State('generate-output', 'children')],
    prevent_initial_call=True
)
def export_transactions(n_clicks, content):
    if not content:
        raise PreventUpdate  # If there's no content, do nothing
    
    all_transactions = []  # Initialize a list to hold all the transaction data

    # Loop through each 'Details' component in the content
    for details in content:
        if ('props' in details and 
            'children' in details['props'] and 
            isinstance(details['props']['children'], list)):
            for child in details['props']['children']:
                # Check if this child is a DataTable
                if (child['type'] == 'DataTable' and
                    'props' in child and
                    'data' in child['props']):
                    # Extract the data from this DataTable and append to all_transactions
                    all_transactions.extend(child['props']['data'])

    # Convert all transaction data to JSON format
    transactions_json = json.dumps(all_transactions, indent=4)

    # Return the JSON string for download
    return dcc.send_string(transactions_json, filename="transactions.json")


        
        
        
        



if __name__ == "__main__":
    SERVICE_PORT = os.getenv("SERVICE_PORT", default="8050")
    DEBUG_MODE = eval(os.getenv("DEBUG_MODE", default="True"))
    app.run(
        host="0.0.0.0", port=SERVICE_PORT, debug=DEBUG_MODE, dev_tools_hot_reload=False
    )
