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
        self.write("""
        <html>
        <body>
        <form action="/data" method="post">
            <input type="number" name="num_rows" required>
            <input type="submit" value="Get Data">
        </form>
        </body>
        </html>
        """)

class DBHandler(tornado.web.RequestHandler):
    def post(self):
        num_rows = int(self.get_body_argument("num_rows"))
        data = query_database(num_rows)
        json_data = data.to_dict(orient='records')
        self.write(f"data: {json_data}")


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
        (r"/data", DBHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()

