import os

from reservation import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    debug = os.environ.get('DEBUG', 'True') == 'True'
    app.run(host=host, port=port, debug=debug)
