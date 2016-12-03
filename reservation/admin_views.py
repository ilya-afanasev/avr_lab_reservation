from flask_admin.contrib.sqla import ModelView
from wtforms import validators

from reservation.validators import IsReserved, StartLessEnd


class UserAdminView(ModelView):
    form_excluded_columns = ['reservation']
    form_args = {
        'email': {'validators': [validators.email()]}
    }


class ResourceAdminView(ModelView):
    form_excluded_columns = ['reservation']


class ReservationAdminView(ModelView):
    form_args = {
        'end_datetime': {'validators': [IsReserved(), StartLessEnd()]}
    }


class ResourceTypeAdminView(ModelView):
    form_excluded_columns = ['resource']
