from reservation import db


class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    model = db.Column(db.String(100))
    path = db.Column(db.String)
    available = db.Column(db.Boolean)

    type = db.Column(db.Integer, db.ForeignKey('resource_types.id'))
    reservation = db.relationship('Reservation', backref='Resource')

    def __str__(self):
        return str(self.name)


class ResourceType(db.Model):
    __tablename__ = 'resource_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    resource = db.relationship('Resource', backref='ResourceType')

    def __str__(self):
        return str(self.name)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(255), unique=True)
    github_id = db.Column(db.Integer(), unique=True)

    reservation = db.relationship('Reservation', backref='User')

    def __str__(self):
        return "ID: {}, Email: {} github_id: {}".format(
            self.id, self.email, self.github_id)


class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)

    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)

    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    token = db.Column(db.String(150), unique=True)

    db.CheckConstraint('start_datetime < end_datetime', name='dates_check')

    def __str__(self):
        return "Resource id {}, user_id {}, start {}, end {}".format(
            self.resource_id, self.user_id, self.start_datetime, self.end_datetime)
