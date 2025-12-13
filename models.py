from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
db = SQLAlchemy()



class User(db.Model, UserMixin):  
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


    @property
    def is_active(self):
        return True
