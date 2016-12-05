import os

from reservation import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5555))
    host = '0.0.0.0'
    debug = os.environ.get('DEBUG', 'True') == 'True'
    app.run(host=host, port=port, debug=debug)
