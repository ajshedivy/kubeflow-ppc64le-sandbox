from dash import Dash, html, dcc, Input, Output, dash_table
import pandas as pd
import random

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
# Assuming transactions_df is already defined
transactions_df['Fraud Status'] = 'Unchecked'  # Initialize all transactions as 'Unchecked'
# Assuming transactions_df is already defined
if 'Tested' not in transactions_df.columns:
    transactions_df['Tested'] = False  # Initialize all rows as not tested



from dash import Dash, html, dcc, Input, Output, dash_table, State
import pandas as pd

# Assuming transactions_df is already defined and includes 'Fraud Status' column

app = Dash(__name__)

app.layout = html.Div([
    dash_table.DataTable(
        id='transactions-table',
        columns=[
            {"name": "Transaction ID", "id": "Transaction ID"},
            {"name": "Amount", "id": "Amount"},
            {"name": "Place", "id": "Place"},
            {"name": "Date", "id": "Date"},
            # Potentially hide 'Fraud Status' from the view or include it based on your preference
        ],
        data=transactions_df.drop(columns=['Details', 'Fraud Status']).to_dict('records'),
        row_selectable='single',
        selected_rows=[],
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(220, 220, 220)',
            },
            {
                'if': {'state': 'selected'},  # Applies to selected rows; adjust as needed for highlighting
                'backgroundColor': 'rgba(0, 116, 217, 0.3)',
                'border': '1px solid blue'
            },
            {
                'if': {
                    'filter_query': '{Fraud Status} = "Detected"',
                    'column_id': 'Transaction ID'
                },
                'backgroundColor': 'rgba(255, 0, 0, 0.7)',
                'color': 'white'
            },
        ],
        page_size=10,
    ),
    html.Button('Test for Fraud', id='fraud-test-button', n_clicks=0),
    html.Div(id='transaction-details'),
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

# Assuming transactions_df is defined and includes 'Tested' column

@app.callback(
    Output('transactions-table', 'style_data_conditional'),
    Input('fraud-test-button', 'n_clicks'),
    State('transactions-table', 'selected_rows'),
    State('transactions-table', 'style_data_conditional'),
    prevent_initial_call=True  # Prevents the callback from running on app load
)
def test_for_fraud(n_clicks, selected_rows, style):
    if selected_rows:
        selected_row_index = selected_rows[0]
        # Check if the row has already been tested
        if not transactions_df.iloc[selected_row_index]['Tested']:
            # Mark the row as tested
            transactions_df.at[selected_row_index, 'Tested'] = True

            # Generating a random fraud confidence interval for demonstration
            fraud_confidence = random.randint(0, 100)

            # Determine the color based on fraud_confidence
            if fraud_confidence < 20:
                background_color = 'rgba(0, 255, 0, 0.7)'  # Green
            elif 20 <= fraud_confidence <= 50:
                background_color = 'rgba(255, 200, 0, 0.7)'  # Yellow
            else:
                background_color = 'rgba(255, 0, 0, 0.7)'  # Red
                transactions_df.at[selected_row_index, 'Fraud Status'] = 'Detected'

            # Update the style to include the new background color for the selected row
            for condition in style:
                if condition.get('if', {}).get('row_index') == selected_row_index:
                    condition['backgroundColor'] = background_color
                    return style

            style.append({
                'if': {
                    'row_index': selected_row_index,
                },
                'backgroundColor': background_color,
                'color': 'black'
            })

    return style


if __name__ == '__main__':
    app.run_server(debug=True)


