from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

# -------------------- Models --------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# -------------------- Authentication --------------------
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

# -------------------- Pages --------------------
@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/services')
def services():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('services.html')

@app.route('/checkup', methods=['GET', 'POST'])
def checkup():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        symptoms = request.form['symptoms']
        return render_template('checkup_result.html', symptoms=symptoms)

    return render_template('online_checkup.html')

# -------------------- NEW ROUTES --------------------
@app.route('/health_records')
def health_records():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('health_records.html')

@app.route('/support_247', methods=['GET', 'POST'])
def support_247():
    if request.method == 'POST':
        message = request.form.get('message')  # يمسك النص اللي يكتبه المستخدم
        return render_template('support_247.html', success=True, message=message)

    return render_template('support_247.html')


# --------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
