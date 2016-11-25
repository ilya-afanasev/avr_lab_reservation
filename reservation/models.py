from reservation import db


class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)

    type = db.Column(db.Integer, db.ForeignKey('resource_types'))
    reservation = db.relationship('reservations', backref='resources')


class ResourceType(db.Model):
    __tablename__ = 'resource_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    resource = db.relationship('resources', backref='resource_types')


class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)

    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)

    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))

    db.CheckConstraint('start_datetime < end_datetime', name='dates_check')


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))

    email = db.Column(db.String(255), unique=True)
    github_id = db.Column(db.Integer(), unique=True)
