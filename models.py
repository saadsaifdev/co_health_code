from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
db = SQLAlchemy()



class User(db.Model, UserMixin):  # تأكد من أن User يرث من UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


    # إضافة خاصية is_active
    @property
    def is_active(self):
        # هنا يمكنك إضافة المنطق الذي يحدد ما إذا كان المستخدم نشطًا أم لا
        return True  # يمكنك تغيير هذا المنطق حسب الحاجة
