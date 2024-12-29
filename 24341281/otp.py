from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import random

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tradehub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'juhayer.rahman@g.bracu.ac.bd'
app.config['MAIL_PASSWORD'] = 'hxbb ogzr utzw hcop'
app.config['MAIL_DEFAULT_SENDER'] = 'juhayer.rahman@g.bracu.ac.bd'

mail = Mail(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)



# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    profession = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    area = db.Column(db.String(100), nullable=False)
    road = db.Column(db.String(200), nullable=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    wallet_balance = db.Column(db.Float, default=0.0)


    def __repr__(self):
        return f'<User {self.username}>'


# Send OTP email function
def send_otp_email(email, otp):
    msg = Message('Your OTP for Email Verification',
                  recipients=[email])
    msg.body = f'Your OTP is: {otp}. It is valid for 10 minutes.'
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")



# OTP Verification route
@app.route('/verify_otp/<int:id>', methods=['GET', 'POST'])
def verify_otp(id):
    user = User.query.get(id)

    if not user:
        return "User not found!", 404

    if request.method == 'POST':
        entered_otp = request.form['otp']

        # Check if OTP matches and is within the expiry time (10 minutes)
        if entered_otp == user.otp:
            if datetime.now() < user.otp_expiry:  # Check if OTP is not expired
                user.is_verified = True  # Mark the email as verified
                db.session.commit()
                flash('Email successfully verified!', 'success')
                return redirect(url_for('login'))  # Redirect to login page after successful verification
            else:
                flash("OTP has expired!", 'danger')  # OTP expired
        else:
            flash("Invalid OTP!", 'danger')  # OTP mismatch

    return render_template('verify_otp.html', id=user.id)
