from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'

db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    from models import User, Task
    db.create_all()

    from routes import *

if __name__ == "__main__":
    app.run(debug=True)
