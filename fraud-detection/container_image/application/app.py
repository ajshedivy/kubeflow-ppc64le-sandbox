import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import pandas as pd
from trino.dbapi import Connection
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        logging.info("WebSocket opened")

    def on_message(self, message):
        try:
            number_of_rows = int(message)
            # Simulating a database query. Replace with your actual database query logic.
            data = query_database(number_of_rows)
            # Convert your query result to JSON format and send it to the client
            json_data = data.to_dict(orient='records')
            self.write_message(json.dumps(json_data))
        except Exception as e:
            self.write_message(f"An exception as occured: {e}")

    def on_close(self):
        logging.info("WebSocket closed")

def query_database(number_of_rows):
    try:
        logging.info('Establishing connection to Trino')
        # with Connection(
        #     host="trino.trino",
        #     port="8080",
        #     user="anybody",
        #     catalog="jtopen",
        #     schema="demo",
        # ) as conn:
        #     link = conn.cursor()
        #     link.execute(f"SELECT * FROM fraud LIMIT {number_of_rows} OFFSET {1_000_000}")
        #     return pd.DataFrame(
        #         link.fetchall(), 
        #         columns=[i.name for i in link.description])
        df = pd.DataFrame([[1,2,3], [4,5,6]])
        return df
    except Exception as e:
        logging.info(f'Exception occcured with trino: {e}')

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/websocket", WebSocketHandler),
    ],
    template_path='templates',
    static_path='static')

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()

