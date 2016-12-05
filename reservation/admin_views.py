from flask_admin.contrib.sqla import ModelView
from wtforms import validators

from reservation.validators import IsReserved, StartLessEnd, OneOfRequired


class UserAdminView(ModelView):
    form_excluded_columns = ['reservation']
    form_args = {
        'email': {'validators': [validators.email(), OneOfRequired('email', 'github_id')]}
    }


class ResourceAdminView(ModelView):
    form_excluded_columns = ['reservation']
    form_args = {
        'name': {'validators': [validators.required()]},
        'ResourceType': {'label': 'Resource type', 'validators': [validators.required()]}
    }


class ReservationAdminView(ModelView):
    form_args = {
        'end_datetime': {'validators': [validators.required(), IsReserved(), StartLessEnd()]},
        'start_datetime': {'validators': [validators.required()]},
        'token': {'validators': [validators.required()]},
        'Resource': {'validators': [validators.required()]},
        'User': {'validators': [validators.required()]}
    }

    column_list = ['start_datetime', 'end_datetime', 'Resource', 'User', 'token']


class ResourceTypeAdminView(ModelView):
    form_excluded_columns = ['resource']
    form_args = {
        'name': {'validators': [validators.required()]}
    }
