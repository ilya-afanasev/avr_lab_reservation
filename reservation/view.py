from datetime import datetime, timedelta

from http import HTTPStatus
from flask_restful import abort, Resource as ResourceBase, marshal_with, fields
from flask_restful.reqparse import RequestParser
from itsdangerous import URLSafeSerializer
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from reservation import models, db, app


def get_item_or_404(Type, **kwargs):
    item = Type.query.filter_by(**kwargs).first()
    if not item:
        abort(HTTPStatus.NOT_FOUND, message="Items with type {} and parameters {} do not exist".format(Type.__name__, kwargs))
    return item


def get_items(Type, **kwargs):
    return Type.query.filter_by(**kwargs).all()


class Users(ResourceBase):
    user_fields = {
        'id': fields.Integer,
        'email': fields.String,
        'github_id': fields.Integer
    }

    @marshal_with(user_fields)
    def get(self):
        user_parser = RequestParser()
        user_parser.add_argument('id', type=int, store_missing=False)
        user_parser.add_argument('email', type=str, store_missing=False)
        user_parser.add_argument('github_id', type=str, store_missing=False)
        params = user_parser.parse_args()
        if 'id' in params:
            result = get_item_or_404(models.User, **params)
        else:
            result = get_items(models.User, **params)

        db.session.commit()

        return result, HTTPStatus.OK

    def delete(self, user_id):
        user = get_item_or_404(models.User, id=user_id)
        db.session.delete(user)
        db.session.commit()
        return '', HTTPStatus.NO_CONTENT

    @marshal_with(user_fields)
    def put(self, user_id):

        user_parser = RequestParser()
        user_parser.add_argument('email', type=str)
        user_parser.add_argument('github_id', type=str)

        args = user_parser.parse_args()
        user = get_item_or_404(models.User, id=user_id)

        user.email = args.get('email', user.email)
        user.github_id = args.get('github_id', user.github_id)

        db.session.commit()

        return user, HTTPStatus.CREATED

    @marshal_with(user_fields)
    def post(self):

        user_parser = RequestParser()
        user_parser.add_argument('email', type=str, default='')
        user_parser.add_argument('github_id', type=int, default=0)

        args = user_parser.parse_args()
        if not args:
            abort(HTTPStatus.BAD_REQUEST, message='Cannot find email or github_id in arguments')
        try:
            user = models.User(**args)
            db.session.add(user)
            db.session.commit()

        except IntegrityError as ex:
            abort(HTTPStatus.UNPROCESSABLE_ENTITY, message=str(ex))
        return user, HTTPStatus.CREATED


class Reservations(ResourceBase):
    reservation_fields = {
        'reservation': {
            'id': fields.Integer(),
            'start_datetime': fields.DateTime("iso8601"),
            'end_datetime': fields.DateTime("iso8601"),
            'token': fields.String(),
            'user': {
                'id': fields.Integer(attribute='User.id'),
                'email': fields.String(attribute='User.email', default=None),
                'github_id': fields.Integer(attribute='User.github_id', default=None)
            },
            'resource': {
                'id': fields.Integer(attribute='Resource.id'),
                'model': fields.String(attribute='Resource.model'),
                'type': fields.String(attribute='Resource.ResourceType.name')
            }
        }
    }

    @marshal_with(reservation_fields)
    def get(self):
        args_parser = RequestParser()

        args_parser.add_argument('id', type=int, store_missing=False)
        args_parser.add_argument('email', type=str, store_missing=False)
        args_parser.add_argument('github_id', type=str, store_missing=False)
        args_parser.add_argument('resource_id', type=str, store_missing=False)
        params = args_parser.parse_args()

        user_args = {k: v for (k, v) in params.items() if k in ('email', 'github_id')}
        resource_args = {'id': v for (k, v) in params.items() if k == 'resource_id'}
        reservation_args = {k: v for (k, v) in params.items() if k == 'id'}

        query = models.Reservation.query
        if reservation_args:
            query = query.filter_by(**reservation_args)

        query = query.join(models.User)
        if user_args:
            query = query.filter_by(**user_args)

        query = query.join(models.Resource)
        if resource_args:
            query = query.filter_by(**resource_args)

        query = query.join(models.ResourceType)

        reservations = query.all()

        db.session.commit()
        if reservation_args and not reservations:
            abort(HTTPStatus.NOT_FOUND, message="Reservations with parameters {} do not exist".format(params))
        return reservations, HTTPStatus.OK

    def delete(self, reservation_id):
        reservation = get_item_or_404(models.Reservation, id=reservation_id)
        db.session.delete(reservation)
        db.session.commit()
        return '', HTTPStatus.NO_CONTENT

    @staticmethod
    def _generate_unique_token(reservation):
        serializer = URLSafeSerializer(app.config['SECRET_KEY'])
        token = serializer.dumps(str(datetime.now()) + reservation, salt=app.config['SECURITY_PASSWORD_SALT'])
        if models.Reservation.query.filter_by(token=token).count() == 0:
            return token
        raise RuntimeError('Cannot generate unique access token')

    @marshal_with(reservation_fields)
    def put(self, reservation_id):

        args_parser = RequestParser()
        args_parser.add_argument('resource_id', type=str, required=True, nullable=False)
        args_parser.add_argument('start_datetime', type=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"),
                                 required=True, nullable=False)
        args_parser.add_argument('end_datetime', type=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"),
                                 required=True, nullable=False)

        args = args_parser.parse_args()

        self._validate_args(args)

        try:
            resource = get_item_or_404(models.Resource, id=args['resource_id'])

            reservation = models.Reservation.query. \
                filter_by(id=reservation_id). \
                join(models.User). \
                join(models.Resource). \
                join(models.ResourceType).first()

            if not reservation:
                abort(HTTPStatus.NOT_FOUND, message="Reservation with parameters {} do not exist".format(reservation_id))

            if self._is_active_reservation(reservation.start_datetime, reservation.end_datetime):
                abort(HTTPStatus.FORBIDDEN, message='It is active reservation. You can only delete it')

            reservation.resource_id = resource.id
            reservation.start_datetime = args['start_datetime']
            reservation.end_datetime = args['end_datetime']

            reservation.token = Reservations._generate_unique_token(str(reservation))

            if self._is_reserved_already(reservation):
                abort(HTTPStatus.FORBIDDEN, message="The time is already reserved")

            db.session.commit()

        except IntegrityError as ex:
            abort(HTTPStatus.UNPROCESSABLE_ENTITY, message=str(ex))
        except RuntimeError as ex:
            abort(HTTPStatus.UNPROCESSABLE_ENTITY, message=str(ex))

        return reservation, HTTPStatus.CREATED

    @staticmethod
    def _validate_args(args):
        if not Reservations._start_less_end(args['start_datetime'], args['end_datetime']):
            abort(HTTPStatus.FORBIDDEN, message='Start date and time should be more than end')

        if not Reservations._start_in_future(args['start_datetime']):
            abort(HTTPStatus.FORBIDDEN, message='Start date and time should be in the future')

        if not Reservations._check_duration(args['start_datetime'], args['end_datetime']):
            abort(HTTPStatus.FORBIDDEN,
                  message='Max reservation duration is {} hours'.format(app.config['MAX_RESERVATION_DURATION_HOURS']))

    @staticmethod
    def _check_reservations_count(email, github_id):
        now = datetime.utcnow()
        count = models.Reservation.query. \
            filter_by(email=email, github_id=github_id). \
            filter(models.Reservation.end_datetime > now).count()
        return count < app.config['MAX_RESERVATIONS_FOR_USER']

    @staticmethod
    def _check_duration(start_datetime, end_datetime):
        return end_datetime - start_datetime < timedelta(hours=app.config['MAX_RESERVATION_DURATION_HOURS'])

    @staticmethod
    def _start_less_end(start_datetime, end_datetime):
        return start_datetime < end_datetime

    @staticmethod
    def _is_active_reservation(start_datetime, end_datetime):
        return start_datetime <= datetime.utcnow() < end_datetime

    @staticmethod
    def _start_in_future(start_datetime):
        return start_datetime > datetime.utcnow()

    @staticmethod
    def _is_reserved_already(reservation):
        count = models.Reservation.query. \
            filter_by(resource_id=reservation.resource_id). \
            filter((and_(models.Reservation.start_datetime <= reservation.end_datetime,
                         models.Reservation.end_datetime >= reservation.start_datetime,
                         models.Reservation.id != reservation.id))).count()
        return count != 0

    @staticmethod
    def _create_user_if_not_exist(**user_params):
        user = models.User.query.filter_by(**user_params).first()
        if not user:
            user = models.User(**user_params)
            db.session.add(user)
        return user

    @marshal_with(reservation_fields)
    def post(self):

        args_parser = RequestParser()
        args_parser.add_argument('resource_id', type=str, required=True, nullable=False)
        args_parser.add_argument('start_datetime', type=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"),
                                 required=True, nullable=False)
        args_parser.add_argument('end_datetime', type=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"),
                                 required=True, nullable=False)
        args_parser.add_argument('email', type=str, nullable=False, store_missing=False)
        args_parser.add_argument('github_id', type=str, nullable=False, store_missing=False)

        params = args_parser.parse_args()

        self._validate_args(params)

        user_args = {k: v for (k, v) in params.items() if k in ('email', 'github_id')}
        if not user_args:
            abort(HTTPStatus.BAD_REQUEST, message='Cannot find email or github_id in arguments')
        resource_args = {'id': v for (k, v) in params.items() if k == 'resource_id'}
        reservation_args = {k: v for (k, v) in params.items() if k in ('start_datetime', 'end_datetime')}

        try:
            user = self._create_user_if_not_exist(**user_args)
            resource = get_item_or_404(models.Resource, **resource_args)

            if not self._check_reservations_count(user.email, user.github_id):
                abort(HTTPStatus.FORBIDDEN,
                      message='Max count of reservations for user is {}'.format(app.config['MAX_RESERVATIONS_FOR_USER']))

            reservation = models.Reservation(resource_id=resource.id,
                                             user_id=user.id,
                                             **reservation_args)

            if self._is_reserved_already(reservation):
                abort(HTTPStatus.FORBIDDEN, message="The time is already reserved")

            reservation.token = Reservations._generate_unique_token(str(reservation))

            db.session.add(reservation)
            db.session.commit()

            reservation_info = models.Reservation.query. \
                filter_by(id=reservation.id). \
                join(models.User). \
                join(models.Resource). \
                join(models.ResourceType).first()

        except IntegrityError as ex:
            abort(HTTPStatus.UNPROCESSABLE_ENTITY, message=str(ex))
        except RuntimeError as ex:
            abort(HTTPStatus.UNPROCESSABLE_ENTITY, message=str(ex))
        return reservation_info, HTTPStatus.CREATED


class Resources(ResourceBase):
    resource_fields = {
        'id': fields.Integer,
        'model': fields.String,
        'available': fields.Boolean,
        'type': fields.String(attribute='ResourceType.name')
    }

    @marshal_with(resource_fields)
    def get(self):
        args_parser = RequestParser()

        args_parser.add_argument('id', type=int, store_missing=False)
        args_parser.add_argument('type', type=str, store_missing=False)
        args_parser.add_argument('model', type=str, store_missing=False)
        args_parser.add_argument('available', type=bool, store_missing=False)

        params = args_parser.parse_args()

        if 'type' in params:
            resource_type = get_item_or_404(models.ResourceType, name=params['type'])
            params['type'] = resource_type.id

        query = models.Resource.query
        if params:
            query = query.filter_by(**params)
        query.join(models.ResourceType)
        resources = query.all()

        if not resources:
            abort(HTTPStatus.NOT_FOUND, message="Resources with parameters {} do not exist".format(params))

        db.session.commit()
        return resources, HTTPStatus.OK


class ReservationToken(ResourceBase):
    @marshal_with(Reservations.reservation_fields)
    def get(self, token):
        reservation_info = models.Reservation.query. \
            filter_by(token=token). \
            join(models.User). \
            join(models.Resource). \
            join(models.ResourceType).first()

        if not reservation_info:
            abort(HTTPStatus.BAD_REQUEST, message='Invalid reservation token')

        db.session.commit()
        return reservation_info, HTTPStatus.OK
