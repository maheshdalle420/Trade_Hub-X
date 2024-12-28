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



# Dashboard route (Protected by login)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
  
    user = User.query.get(session['user_id'])

    if not user:
        flash('User not found. Please log in again.', 'danger')
        return redirect(url_for('login'))

    return render_template('dashboard.html', user=user)


# Unified Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Query the database for the user by email
        user = User.query.filter_by(email=email).first()

        # Check if user exists and if the password is correct
        if user and check_password_hash(user.password, password):
            if not user.is_verified:
                flash("Please verify your email before logging in.", 'warning')
                return redirect(url_for('login'))

            session['user_id'] = user.id  # Store user ID in session for login tracking

            # Check if the user is an admin
            if user.is_admin:
                session['admin_logged_in'] = True  # Set admin session
                flash('Welcome Admin!', 'success')
                return redirect(url_for('admin_panel'))  # Redirect admin to the admin panel

            flash('Login successful.', 'success')
            return redirect(url_for('dashboard'))  # Redirect to user dashboard

        else:
            flash('Invalid login credentials!', 'danger')

    return render_template('login.html')





#logout
@app.route('/logout')
def logout():
    # Clear the session to log the user out
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

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




# Change password in dashboard route
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if not check_password_hash(user.password, current_password):
            flash('Current password is incorrect!', 'danger')
            return redirect(url_for('change_password'))

        if new_password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('change_password'))

        user.password = generate_password_hash(new_password)
        db.session.commit()

        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('change_password.html')



# Reset password route
@app.route('/reset_password/<int:id>', methods=['GET', 'POST'])
def reset_password(id):
    user = User.query.get(id)

    if not user:
        return "User not found!", 404

    if request.method == 'POST':
        entered_otp = request.form['otp']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('reset_password', id=id))

        if entered_otp == user.otp and datetime.now() < user.otp_expiry:
            user.password = generate_password_hash(new_password)
            user.otp = None
            user.otp_expiry = None
            db.session.commit()

            flash('Password reset successfully!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired OTP!', 'danger')

    return render_template('reset_password.html', id=id)


#Forgot password route
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('No account found with this email.', 'danger')
            return redirect(url_for('forgot_password'))

        # Generate OTP and expiry
        otp = str(random.randint(100000, 999999))
        otp_expiry = datetime.now() + timedelta(minutes=10)

        user.otp = otp
        user.otp_expiry = otp_expiry
        db.session.commit()

        # Send OTP email
        send_otp_email(user.email, otp)
        flash('An OTP has been sent to your email for password reset.', 'info')
        return redirect(url_for('reset_password', id=user.id))

    return render_template('forgot_password.html')




# Send OTP email function
def send_otp_email(email, otp):
    msg = Message('Your OTP for Email Verification',
                  recipients=[email])
    msg.body = f'Your OTP is: {otp}. It is valid for 10 minutes.'
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")



with app.app_context():
    db.create_all()
    print("Database tables created successfully.")

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
