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




#Update Profile

@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # Get updated data from the form
        user.full_name = request.form.get('full_name', user.full_name)
        user.username = request.form.get('username', user.username)
        user.email = request.form.get('email', user.email)

        # Convert date_of_birth to a datetime.date object if provided
        date_of_birth_str = request.form.get('date_of_birth')
        if date_of_birth_str:
            try:
                user.date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                return redirect(url_for('update_profile'))

        user.profession = request.form.get('profession', user.profession)
        user.city = request.form.get('city', user.city)
        user.area = request.form.get('area', user.area)
        user.road = request.form.get('road', user.road)

        # Validate email uniqueness
        if User.query.filter(User.email == user.email, User.id != user.id).first():
            flash('This email is already in use.', 'danger')
            return redirect(url_for('update_profile'))

        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error updating profile: {str(e)}', 'danger')
            db.session.rollback()

    return render_template('update_profile.html', user=user)