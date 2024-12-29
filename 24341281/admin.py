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



# Property Model
class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    image_filename = db.Column(db.String(300), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    approved = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Property {self.title}>'
    
    
# Admin Panel Route
@app.route('/admin/panel')
def admin_panel():
    if not session.get('admin_logged_in'):
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    pending_properties = Property.query.filter_by(approved=False).all()
    active_auctions = Property.query.filter(
        Property.approved == True,
        Property.start_time <= datetime.now(),
        Property.end_time > datetime.now()
    ).all()

    auction_details = []
    for auction in active_auctions:
        current_bid = Bid.query.filter_by(property_id=auction.id).order_by(Bid.bid_amount.desc()).first()

        # Count unique users, excluding auto-bidding increments
        active_users = Bid.query.filter(
            Bid.property_id == auction.id,
            Bid.auto_increment.is_(None)
        ).distinct(Bid.user_id).count()

        auction_details.append({
            'auction': auction,
            'current_bid': current_bid.bid_amount if current_bid else 'No bids',
            'active_users': active_users
        })

    users = User.query.all()

    return render_template('admin_panel.html', properties=pending_properties, auction_details=auction_details, users=users)

# Manage Users (Ban/Delete)
@app.route('/admin/manage_users', methods=['POST'])
def manage_users():
    if not session.get('admin_logged_in'):
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    action = request.form.get('action')
    user_id = request.form.get('user_id')
    user = User.query.get_or_404(user_id)

    if action == 'ban':
        ban_duration = int(request.form.get('ban_duration', 0))
        user.banned_until = datetime.now() + timedelta(hours=ban_duration)
        db.session.commit()
        flash(f'User {user.username} has been banned for {ban_duration} hours.', 'success')
    elif action == 'delete':
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} has been deleted.', 'success')

    return redirect(url_for('admin_panel'))



#created an admin
with app.app_context():
    def create_admin_user():
        admin_email = 'admin@example.com'
        admin_password = 'admin123'  # Replace with a secure password
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            hashed_password = generate_password_hash(admin_password)
            admin_user = User(
                full_name='Admin User',
                username='admin',
                email=admin_email,
                password=hashed_password,
                date_of_birth=datetime(2000, 1, 1),
                city='Admin City',
                area='Admin Area',
                road='Admin Road',
                
                is_verified=True,
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created: admin@example.com / admin123")
        else:
            print("Admin user already exists.")

    # Call the function during app initialization
    create_admin_user()
