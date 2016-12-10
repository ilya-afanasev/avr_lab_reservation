import flask_admin
from flask import Flask, redirect, url_for, flash
from flask_admin import AdminIndexView
from flask_admin.menu import MenuLink
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
api = Api(app)
db = SQLAlchemy(app)


from reservation.models import *
from reservation.initializer import init_resources
db.create_all()

# Create admin
admin = flask_admin.Admin(app, name='Reservation server', template_mode='bootstrap3', index_view=AdminIndexView(
        name='Home',
        template='admin/home.html',
        url='/'
    ))
admin.add_link(MenuLink(name='Reload Resources', url='/update_resources'))

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

api.add_resource(rest_view.ReservationToken, '/reservation/token/<token>', endpoint='reservation_token')


@app.route('/update_resources')
def update_resources():
    try:
        init_resources()
    except Exception as ex:
        app.logger.error(ex)
        flash(str(ex), category='error')
        return redirect(url_for('admin.index'))
    flash('Resource settings were reloaded from config successfully.', category='success')
    return redirect(url_for('admin.index'))

