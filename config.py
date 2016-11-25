# Create dummy secrey key so we can use sessions
import os

_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
WTF_CSRF_ENABLED = True
SECRET_KEY = '123456790'
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI',
                                    'sqlite:///' + os.path.join(_basedir, 'reservation.db'))
SESSION_TYPE = 'filesystem'
SQLALCHEMY_ECHO = True