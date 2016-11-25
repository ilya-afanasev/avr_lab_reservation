from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import flask_admin as admin


# Create application
app = Flask(__name__)


db = SQLAlchemy(app)


@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'

# Create admin
admin = admin.Admin(app, name='Example: SQLAlchemy2', template_mode='bootstrap3')

if __name__ == '__main__':

    # Create DB
    db.create_all()

    # Start app
    app.run(debug=True)
