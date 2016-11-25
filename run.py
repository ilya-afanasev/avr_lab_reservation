import os

from reservation import app

if __name__ == '__main__':
    port = 5555
    host = '127.0.0.1'
    debug = os.environ.get('DEBUG', 'True') == 'True'
    app.run(host=host, port=port, debug=debug)
