from flask import Flask
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy

import flask_admin as admin


# Create application
app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

from reservation.models import *
db.create_all()


@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'

# Create admin
admin = admin.Admin(app, name='Example: SQLAlchemy2', template_mode='bootstrap3')
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Reservation, db.session))
admin.add_view(ModelView(Resource, db.session))
admin.add_view(ModelView(ResourceType, db.session))
