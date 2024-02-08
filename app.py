from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session  # Flask-Session extension for session management
import pandas as pd

app = Flask(__name__)

# Configure Flask session (use filesystem-based session for simplicity)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def generate_dataframe(rows):
    data = {'Column1': range(1, rows + 1), 'Column2': ['Row' + str(i) for i in range(1, rows + 1)]}
    df = pd.DataFrame(data)
    return df.to_html(classes='table table-striped', index=False, border=0)

@app.route('/', methods=['GET', 'POST'])
def landing():
    if request.method == 'POST':
        rows = int(request.form['rows'])
        df_html = generate_dataframe(rows)
        # Initialize the session list if it doesn't exist
        if 'df_html_list' not in session:
            session['df_html_list'] = []
        session['df_html_list'].append(df_html)
        session.modified = True  # Ensure the session is marked as modified
        return redirect(url_for('results'))
    return render_template('landing.html')

@app.route('/results')
def results():
    df_html_list = session.get('df_html_list', [])
    return render_template('results.html', df_html_list=df_html_list)

if __name__ == '__main__':
    app.run(debug=True)
