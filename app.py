import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import unicodedata

# ======================
# APP CONFIG
# ======================
app = Flask(__name__, template_folder='templates')
app.secret_key = "your_secret_key"

# ======================
# PATH CONFIG
# ======================
basedir = os.path.abspath(os.path.dirname(__file__))

instance_folder = os.path.join(basedir, "instance")
os.makedirs(instance_folder, exist_ok=True)

UPLOAD_FOLDER = os.path.join(basedir, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(instance_folder, 'database.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ======================
# DATABASE MODELS
# ======================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.String(500))
    date = db.Column(db.String(50))

class SymptomMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(20))
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ======================
# CREATE DATABASE
# ======================
with app.app_context():
    db.create_all()

# ======================
# HELPERS
# ======================
def safe_filename(filename):
    # إزالة الأحرف الغريبة وتحويل الاسم إلى ASCII ثم تأمينه
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    return secure_filename(filename)

# ======================
# AUTH ROUTES
# ======================
@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_input = request.form["username"]
        password_input = request.form["password"]
        user = User.query.filter_by(username=username_input).first()
        if user and check_password_hash(user.password, password_input):
            session["username"] = username_input
            return redirect(url_for("home"))
        else:
            flash("اسم المستخدم أو كلمة المرور خاطئة", "error")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username_input = request.form["username"]
        password_input = request.form["password"]

        existing_user = User.query.filter_by(username=username_input).first()
        if existing_user:
            flash("اسم المستخدم موجود مسبقاً", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(
            password_input, method="pbkdf2:sha256", salt_length=16
        )
        new_user = User(username=username_input, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("تم إنشاء الحساب بنجاح! الرجاء تسجيل الدخول.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ======================
# MAIN PAGES
# ======================
@app.route("/home")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")

@app.route("/services")
def services():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("services.html")

# ======================
# PATIENTS PAGE (GET + POST)
# ======================
@app.route("/patients", methods=["GET", "POST"])
def patients():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        phone = request.form.get("phone")
        notes = request.form.get("notes")

        if name and age and gender:
            new_patient = Patient(
                name=name,
                age=int(age),
                gender=gender,
                phone=phone,
                notes=notes
            )
            db.session.add(new_patient)
            db.session.commit()
            flash("تمت إضافة المريض بنجاح!", "success")
            return redirect(url_for("patients"))

    patients_list = Patient.query.order_by(Patient.created_at.desc()).all()
    return render_template("patients.html", patients=patients_list)

# ======================
# CHECKUP PAGE
# ======================
@app.route("/checkup", methods=["GET", "POST"])
def checkup():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    if request.method == "POST":
        symptoms = request.form.get("symptoms")
        if symptoms:
            msg = SymptomMessage(username=username, message=symptoms)
            db.session.add(msg)
            db.session.commit()
            flash("تم استلام الأعراض بنجاح!", "success")
            return redirect(url_for("checkup"))

    messages = SymptomMessage.query.filter_by(username=username)\
        .order_by(SymptomMessage.timestamp.desc()).all()

    return render_template("checkup.html", messages=messages)

# ======================
# HEALTH RECORDS (UPLOAD, DELETE, DOWNLOAD)
# ======================
@app.route("/health_records", methods=["GET", "POST"])
def health_records():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    if request.method == "POST":
        file = request.files.get("file")
        notes = request.form.get("notes")

        if file:
            filename = safe_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            record = HealthRecord(
                username=username,
                filename=filename,
                notes=notes,
                date=datetime.now().strftime("%Y-%m-%d %H:%M")
            )
            db.session.add(record)
            db.session.commit()
            flash("تم رفع السجل بنجاح!", "success")
            return redirect(url_for("health_records"))

    records = HealthRecord.query.filter_by(username=username)\
        .order_by(HealthRecord.date.desc()).all()

    return render_template("health_records.html", records=records)


@app.route("/delete_record/<int:record_id>")
def delete_record(record_id):
    if "username" not in session:
        return redirect(url_for("login"))

    record = HealthRecord.query.get_or_404(record_id)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], record.filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(record)
    db.session.commit()
    flash("تم حذف السجل بنجاح!", "success")
    return redirect(url_for("health_records"))


@app.route("/download/<int:record_id>")
def download_record(record_id):
    if "username" not in session:
        return redirect(url_for("login"))

    record = HealthRecord.query.get_or_404(record_id)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], record.filename)

    if os.path.exists(file_path):
        return send_from_directory(app.config["UPLOAD_FOLDER"], record.filename, as_attachment=True)
    else:
        flash("الملف المطلوب غير موجود على الخادم.", "error")
        return redirect(url_for("health_records"))

# ======================
# SUPPORT PAGE
# ======================
@app.route("/support", methods=["GET", "POST"])
def support():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    success = False
    sent_message = None

    if request.method == "POST":
        sent_message = request.form.get("message")
        if sent_message:
            msg = SymptomMessage(username=username, message=sent_message)
            db.session.add(msg)
            db.session.commit()
            success = True

    return render_template("support.html", success=success, message=sent_message)

# ======================
# RUN APP
# ======================
if __name__ == "__main__":
    app.run(debug=True)
