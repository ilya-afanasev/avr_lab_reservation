from flask import request
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from wtforms import ValidationError

from reservation import models


class IsReserved:

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        error = False
        try:
            start_datetime = form['start_datetime'].data
            end_datetime = form['end_datetime'].data
            resource_id = form['Resource'].data.id
            resource_name = form['Resource'].data.name
            reservation_id = request.args.get('id', None)
        except KeyError:
            raise ValidationError(field.gettext("Invalid field name in reservation validator."))

        count = 0

        try:
            count = models.Reservation.query. \
                filter_by(resource_id=resource_id). \
                filter(and_(models.Reservation.start_datetime <= end_datetime,
                            models.Reservation.end_datetime >= start_datetime,
                            models.Reservation.id != reservation_id)).count()
        except SQLAlchemyError:
            error = True
        if error or count != 0:
            message = self.message
            if message is None:
                message = field.gettext('Resource {} is already reserved. Please, check your dates.')
            raise ValidationError(message.format(resource_name))


class StartLessEnd:

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        try:
            start_datetime = form['start_datetime'].data
            end_datetime = form['end_datetime'].data
        except KeyError:
            raise ValidationError(field.gettext("Invalid field name in reservation validator."))
        if end_datetime < start_datetime:
            message = self.message
            if message is None:
                message = field.gettext('Start time should be less than end. Please, check your dates.')
            raise ValidationError(message)
