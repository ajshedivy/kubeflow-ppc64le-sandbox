import tornado.ioloop
import tornado.web
import math

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("""
        <html>
        <body>
        <form action="/gcd" method="post">
            <input type="number" name="num1" required>
            <input type="number" name="num2" required>
            <input type="submit" value="Compute GCD">
        </form>
        </body>
        </html>
        """)

class GCDHandler(tornado.web.RequestHandler):
    def post(self):
        num1 = int(self.get_body_argument("num1"))
        num2 = int(self.get_body_argument("num2"))
        gcd = math.gcd(num1, num2)
        self.write(f"The GCD of {num1} and {num2} is {gcd}")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/gcd", GCDHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
