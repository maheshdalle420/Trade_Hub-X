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
    



# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get the form data
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        date_of_birth_str = request.form.get('date_of_birth')
        profession = request.form.get('profession')
        city = request.form.get('city')
        area = request.form.get('area')
        road = request.form.get('road')

        # Validate inputs
        if not all([full_name, username, email, password, confirm_password, date_of_birth_str, city, area, road]):
            flash('All fields except profession are required.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        try:
            date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return redirect(url_for('register'))

        # Hash the password before saving
        hashed_password = generate_password_hash(password)

        # Create new user object
        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            password=hashed_password,
            date_of_birth=date_of_birth,
            profession=profession,
            city=city,
            area=area,
            road=road
        )

        # Add the user to the database
        try:
            db.session.add(new_user)
            db.session.commit()

            # Generate OTP
            otp = str(random.randint(100000, 999999))
            otp_expiry = datetime.now() + timedelta(minutes=10)

            new_user.otp = otp
            new_user.otp_expiry = otp_expiry
            db.session.commit()

            # Send OTP
            send_otp_email(new_user.email, otp)

            flash('An OTP has been sent to your email for verification.', 'info')
            return redirect(url_for('verify_otp', id=new_user.id))
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'danger')
            db.session.rollback()

    return render_template('register.html')

# Send OTP email function
def send_otp_email(email, otp):
    msg = Message('Your OTP for Email Verification',
                  recipients=[email])
    msg.body = f'Your OTP is: {otp}. It is valid for 10 minutes.'
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")