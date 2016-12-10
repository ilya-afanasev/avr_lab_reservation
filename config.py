# Create dummy secrey key so we can use sessions
import os

_basedir = os.path.abspath(os.path.dirname(__file__))

ERROR_404_HELP=False
DEBUG = True
WTF_CSRF_ENABLED = True
SECRET_KEY = '123456790'
SECURITY_PASSWORD_SALT = '0987654321'
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI',
                                    'sqlite:///' + os.path.join(_basedir, 'reservation.db'))
SESSION_TYPE = 'filesystem'
SQLALCHEMY_ECHO = True
RESOURCE_CONFIG_PATH = os.path.join(_basedir, 'config.ini')
