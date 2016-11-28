from datetime import datetime

from flask_restful.reqparse import RequestParser
from flask_restful import abort, Resource as ResourceBase, marshal_with, fields
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from reservation import models, db


def get_item_or_404(Type, **kwargs):
    item = Type.query.filter_by(**kwargs).first()
    if not item:
        abort(404, message="Items with type {} and parameters {} do not exist".format(Type.__name__, kwargs))
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

        return result, 200

    def delete(self, user_id):
        user = get_item_or_404(models.User, id=user_id)
        db.session.delete(user)
        db.session.commit()
        return '', 204

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

        return user, 201

    @marshal_with(user_fields)
    def post(self):

        user_parser = RequestParser()
        user_parser.add_argument('email', type=str, default='')
        user_parser.add_argument('github_id', type=int, default=0)

        args = user_parser.parse_args()
        if not args:
            abort(400, message='Cannot find email or github_id in arguments')
        try:
            user = models.User(**args)
            db.session.add(user)
            db.session.commit()

        except IntegrityError as ex:
            abort(422, message=str(ex))
        return user, 201


class Reservations(ResourceBase):
    reservation_fields = {
        'reservation': {
            'id': fields.Integer(),
            'start_datetime': fields.DateTime("iso8601"),
            'end_datetime': fields.DateTime("iso8601")
        },
        'user': {
            'id': fields.Integer(attribute='User.id'),
            'email': fields.String(attribute='User.email'),
            'github_id': fields.Integer(attribute='User.github_id', default=None)
        },
        'resource': {
            'id': fields.Integer(attribute='Resource.id'),
            'name': fields.String(attribute='Resource.name'),
            'type': fields.String(attribute='Resource.ResourceType.name')
        }
    }

    @marshal_with(reservation_fields)
    def get(self):
        args_parser = RequestParser()

        args_parser.add_argument('id', type=int, store_missing=False)
        args_parser.add_argument('email', type=str, store_missing=False)
        args_parser.add_argument('github_id', type=str, store_missing=False)
        args_parser.add_argument('resource_name', type=str, store_missing=False)
        params = args_parser.parse_args()

        user_args = {k: v for (k, v) in params.items() if k in ('email', 'github_id')}
        resource_args = {'name': v for (k, v) in params.items() if k == 'resource_name'}
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
            abort(404, message="Reservations with parameters {} do not exist".format(params))
        return reservations, 200

    def delete(self, reservation_id):
        reservation = get_item_or_404(models.Reservation, id=reservation_id)
        db.session.delete(reservation)
        db.session.commit()
        return '', 204

    @marshal_with(reservation_fields)
    def put(self, reservation_id):

        args_parser = RequestParser()
        args_parser.add_argument('resource_name', type=str, required=True, nullable=False)
        args_parser.add_argument('start_datetime', type=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"),
                                 required=True, nullable=False)
        args_parser.add_argument('end_datetime', type=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"),
                                 required=True, nullable=False)

        args = args_parser.parse_args()

        try:
            resource = get_item_or_404(models.Resource, name=args['resource_name'])

            reservation = models.Reservation.query. \
                filter_by(id=reservation_id). \
                join(models.User). \
                join(models.Resource). \
                join(models.ResourceType).first()

            if not reservation:
                abort(404, message="Reservation with parameters {} do not exist".format(id=reservation_id))
            reservation.resource_id = resource.id
            reservation.start_datetime = args['start_datetime']
            reservation.end_datetime = args['end_datetime']

            if not self.validate_reservation(reservation):
                abort(400, message="The time is already reserved")

            db.session.commit()

        except IntegrityError as ex:
            abort(422, message=str(ex))

        return reservation, 201

    @staticmethod
    def validate_reservation(reservation):
        count = models.Reservation.query.\
            filter_by(resource_id=reservation.resource_id).\
            filter(and_(models.Reservation.start_datetime < reservation.end_datetime,
                        models.Reservation.end_datetime > reservation.start_datetime,
                        models.Reservation.id != reservation.id)).count()
        return count == 0

    @staticmethod
    def create_user_if_not_exist(**user_params):
        user = models.User.query.filter_by(**user_params).first()
        if not user:
            user = models.User(**user_params)
            db.session.add(user)
        return user

    @marshal_with(reservation_fields)
    def post(self):

        args_parser = RequestParser()
        args_parser.add_argument('resource_name', type=str, required=True, nullable=False, dest='name')
        args_parser.add_argument('start_datetime', type=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"),
                                 required=True, nullable=False)
        args_parser.add_argument('end_datetime', type=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"),
                                 required=True, nullable=False)
        args_parser.add_argument('email', type=str, nullable=False, store_missing=False)
        args_parser.add_argument('github_id', type=str, nullable=False, store_missing=False)

        params = args_parser.parse_args()

        user_args = {k: v for (k, v) in params.items() if k in ('email', 'github_id')}
        if not user_args:
            abort(400, message='Cannot find email or github_id in arguments')
        resource_args = {k: v for (k, v) in params.items() if k == 'name'}
        reservation_args = {k: v for (k, v) in params.items() if k in ('start_datetime', 'end_datetime')}

        try:
            user = self.create_user_if_not_exist(**user_args)
            resource = get_item_or_404(models.Resource, **resource_args)
            reservation = models.Reservation(resource_id=resource.id,
                                             user_id=user.id,
                                             **reservation_args)
            if not self.validate_reservation(reservation):
                abort(400, message="The time is already reserved")

            reservation_info = reservation.query.join(models.User). \
                join(models.Resource). \
                join(models.ResourceType).first()

            db.session.add(reservation)
            db.session.commit()

        except IntegrityError as ex:
            abort(422, message=str(ex))
        return reservation_info, 201


class Resources(ResourceBase):
    resource_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'type': fields.String(attribute='ResourceType.name')
    }

    @marshal_with(resource_fields)
    def get(self):
        args_parser = RequestParser()

        args_parser.add_argument('id', type=int, store_missing=False)
        args_parser.add_argument('type', type=str, store_missing=False)
        args_parser.add_argument('name', type=str, store_missing=False)
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
            abort(404, message="Resources with parameters {} do not exist".format(params))

        db.session.commit()
        return resources, 200
