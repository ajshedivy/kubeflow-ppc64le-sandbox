from dash import Dash, html, dcc, Input, Output, dash_table
import pandas as pd

app = Dash(__name__)

# Sample transactions data
data = {
    "Transaction ID": [1, 2, 3, 4, 5],
    "Amount": [100.50, 200.00, 350.75, 400.00, 150.25],
    "Place": ["Supermarket", "Online Store", "Restaurant", "Bookstore", "Cafe"],
    "Date": ["2024-04-01", "2024-04-02", "2024-04-03", "2024-04-04", "2024-04-05"],
    "Category": ["Groceries", "Electronics", "Dining", "Books", "Beverages"],
    "Method": ["Credit Card", "Debit Card", "Credit Card", "Cash", "Cash"]
}

# Convert to DataFrame
transactions_df = pd.DataFrame(data)

# Additional details (usually hidden)
additional_details = {
    "Details": [
        "Bought groceries including vegetables and fruits.",
        "Purchased a new smartphone.",
        "Dinner with family.",
        "Bought latest release novels.",
        "Coffee and snacks."
    ]
}

additional_details_df = pd.DataFrame(additional_details)

# Combine both DataFrames
transactions_df = pd.concat([transactions_df, additional_details_df], axis=1)

# Define the layout
app.layout = html.Div([
    dash_table.DataTable(
        id='transactions-table',
        columns=[
            {"name": "Transaction ID", "id": "Transaction ID"},
            {"name": "Amount", "id": "Amount"},
            {"name": "Place", "id": "Place"},
            {"name": "Date", "id": "Date"}
            # Exclude "Category" and "Method" from initial view to be part of the detailed view
        ],
        data=transactions_df.drop(columns=['Details']).to_dict('records'), # Exclude details from initial data
        row_selectable='single',
        selected_rows=[],
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(220, 220, 220)',
            }
        ],
        style_header={
            'backgroundColor': 'rgb(210, 210, 210)',
            'color': 'black',
            'fontWeight': 'bold'
        },
        page_size=10,
    ),
    html.Div(id='transaction-details')
])

# Callback to update the details section based on the selected row
@app.callback(
    Output('transaction-details', 'children'),
    [Input('transactions-table', 'selected_rows')]
)
def display_transaction_details(selected_rows):
    if selected_rows:
        selected_row = transactions_df.iloc[selected_rows[0]]
        return html.Div([
            html.H5("Transaction Details"),
            html.P(f"Category: {selected_row['Category']}"),
            html.P(f"Method: {selected_row['Method']}"),
            html.P(f"Details: {selected_row['Details']}")
        ])
    else:
        return "Select a transaction to see detailed information."

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)

