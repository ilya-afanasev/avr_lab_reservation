from flask import Flask
from flask_restful import Api
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy

import flask_admin


# Create application
app = Flask(__name__)
app.config.from_object('config')
api = Api(app)
db = SQLAlchemy(app)

from reservation.models import *
db.create_all()

# Create admin
admin = flask_admin.Admin(app, name='Reservation server', template_mode='bootstrap3')

from reservation.admin_views import UserAdminView, ResourceAdminView, ReservationAdminView, ResourceTypeAdminView

admin.add_view(UserAdminView(User, db.session))
admin.add_view(ReservationAdminView(Reservation, db.session))
admin.add_view(ResourceAdminView(Resource, db.session))
admin.add_view(ResourceTypeAdminView(ResourceType, db.session))

from reservation import view as rest_view

api.add_resource(rest_view.Users, '/users', endpoint='users')
api.add_resource(rest_view.Users, '/users/<int:user_id>', endpoint='user')

api.add_resource(rest_view.Resources, '/resources', endpoint='resources')

api.add_resource(rest_view.Reservations, '/reservations', endpoint='reservations')
api.add_resource(rest_view.Reservations, '/reservations/<int:reservation_id>', endpoint='reservation')


@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'
