
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
    tier = db.Column(db.String(50), default="None")
    email_notifications = db.Column(db.Boolean, default=False)
    def __repr__(self):
        return f'<User {self.username} - Tier {self.tier}>'






# Auction Cart Model
class AuctionCart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    checkout_time_limit = db.Column(db.DateTime, nullable=False)  # Time limit for payment
    is_paid = db.Column(db.Boolean, default=False)

    property = db.relationship('Property', backref='auction_carts')  # Fetch property details easily

    def __repr__(self):
        return f'<AuctionCart User {self.user_id} Property {self.property_id} Paid {self.is_paid}>'



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


# Wishlist Model
class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)

    def __repr__(self):
        return f'<Wishlist User {self.user_id} Property {self.property_id}>'



class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bid_amount = db.Column(db.Float, nullable=False)
    auto_increment = db.Column(db.Float, nullable=True)  
    end_limit = db.Column(db.Float, nullable=True)  
    is_prioritized = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)
    is_winner = db.Column(db.Boolean, default=False)
    user = db.relationship('User', backref='bids')

    def __repr__(self):
        return f'<Bid Property {self.property_id} User {self.user_id} Amount {self.bid_amount}>'

class GameHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_name = db.Column(db.String(50), nullable=False)
    amount_earned = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/auctions')
def auctions():
    now = datetime.now()
    live_properties = Property.query.filter(
        Property.approved == True,
        Property.start_time <= now,
        Property.end_time > now
    ).all()
    upcoming_properties = Property.query.filter(
        Property.approved == True,
        Property.start_time > now
    ).all()
    past_properties = Property.query.filter(
        Property.approved == True,
        Property.end_time <= now
    ).all()

    return render_template(
        'auctions.html',
        live_properties=live_properties,
        upcoming_properties=upcoming_properties,
        past_properties=past_properties,
        now=now
    )


