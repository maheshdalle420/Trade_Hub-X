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

# Wallet limits based on tiers
wallet_limits = {
    "None": 1000,
    "Bronze": 100000,
    "Silver": 500000,
    "Gold": 1000000
}

tier_subscription_cost = {
    'None': 0,       # No subscription
    'Bronze': 3000,  # Bronze subscription cost
    'Silver': 6000,  # Silver subscription cost
    'Gold': 10000     # Gold subscription cost
}


# Features for Each Tier
tier_features = {
    "Bronze": [
        "10% Wallet Boost on Play Game",
        "Access to Public Listings"
    ],
    "Silver": [
        "30% Wallet Boost on Play Game",
        "Priority Bidding",
        "Discounted Fees",
        "Access to Exclusive Listings"
    ],
    "Gold": [
        "50% Wallet Boost on Play Game",
        "Premium Support",
        "Free Listing Creation",
        "Higher Wallet Limits",
        "Analytics Dashboard"
    ]
}


def schedule_auction_end_notification(user, property):
    """
    Schedule an email notification for when the auction is about to end.
    """
    time_remaining = property.end_time - datetime.now()
    if time_remaining.total_seconds() > 300:  # Only schedule if more than 5 minutes remain
        notification_time = property.end_time - timedelta(minutes=5)
        # Simulate scheduling (use a task queue like Celery in production)
        send_auction_end_email(user, property, notification_time)

def send_auction_end_email(user, property, notification_time):
    """
    Send an email notification to the user about the auction ending soon.
    """
    subject = f"Reminder: Auction for '{property.title}' Ending Soon!"
    body = (f"Dear {user.full_name},\n\n"
            f"The auction for '{property.title}' is ending in less than 5 minutes.\n"
            f"Current highest bid: ৳{property.price}.\n\n"
            f"Don't miss your chance to bid!\n\n"
            f"Best regards,\nAuctions Platform Team")
    msg = Message(subject, recipients=[user.email])
    msg.body = body

    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending auction end email: {e}")
@app.route('/update_notifications', methods=['POST'])
def update_notifications():
    if 'user_id' not in session:
        flash('Please log in to update your preferences.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    email_notifications = request.form.get('email_notifications') == 'true'
    user.email_notifications = email_notifications
    db.session.commit()

    flash('Your preferences have been updated.', 'success')
    return redirect(url_for('dashboard'))


def notify_users_before_auction_ends():
    soon_to_end = Property.query.filter(
        Property.end_time <= datetime.now() + timedelta(hours=1),
        Property.end_time > datetime.now()
    ).all()

    for property in soon_to_end:
        interested_users = AuctionCart.query.filter_by(property_id=property.id).join(User).all()
        for user in interested_users:
            if user.email_notifications:
                send_email_notification(user, property)

def send_email_notification(user, property):
    subject = f"Auction for {property.title} is Ending Soon!"
    body = f"Dear {user.username},\n\nThe auction for '{property.title}' will end in less than 1 hour. Don't miss the chance to place your bid!\n\nThank you,\nTradeHubX Team"
    msg = Message(subject, recipients=[user.email])
    msg.body = body
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

def notify_wishlist_items_going_live():
    soon_to_start = Property.query.filter(
        Property.start_time <= datetime.now() + timedelta(minutes=15),
        Property.start_time > datetime.now()
    ).all()

    for property in soon_to_start:
        wishlisted_users = Wishlist.query.filter_by(property_id=property.id).join(User).all()
        for wishlist in wishlisted_users:
            user = wishlist.user
            if user.tier == 'Gold':
                send_wishlist_notification(user, property)

def send_wishlist_notification(user, property):
    subject = f"Wishlist Alert: {property.title} is Going Live Soon!"
    body = f"Dear {user.username},\n\nThe item '{property.title}' in your wishlist is going live in less than 15 minutes. Get ready to bid!\n\nThank you,\nTradeHubX Team"
    msg = Message(subject, recipients=[user.email])
    msg.body = body
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending wishlist notification: {e}")


# Tier Subscription Downgrade Route
@app.route('/downgrade_tier/<new_tier>', methods=['POST'])
def downgrade_tier(new_tier):
    if 'user_id' not in session:
        flash('Please log in to manage your subscription.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    current_tier = user.tier
    valid_tiers = ["None", "Bronze", "Silver", "Gold"]

    # Ensure the downgrade is valid
    if new_tier not in valid_tiers or valid_tiers.index(new_tier) >= valid_tiers.index(current_tier):
        flash('Invalid downgrade request.', 'danger')
        return redirect(url_for('dashboard'))

    # Calculate refund based on tier cost difference
    refund_amount = tier_subscription_cost.get(current_tier, 0) - tier_subscription_cost.get(new_tier, 0)
    user.wallet_balance += refund_amount
    user.tier = new_tier

    db.session.commit()
    flash(f'Successfully downgraded to {new_tier} tier. Refund of ৳{refund_amount:.2f} has been added to your wallet.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/upgrade_tier/<new_tier>', methods=['POST'])
def upgrade_tier(new_tier):
    if 'user_id' not in session:
        flash('Please log in to manage your subscription.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    valid_tiers = ["None", "Bronze", "Silver", "Gold"]

    # Ensure the upgrade is valid
    if new_tier not in valid_tiers or valid_tiers.index(new_tier) <= valid_tiers.index(user.tier):
        flash('Invalid upgrade request.', 'danger')
        return redirect(url_for('dashboard'))

    # Calculate the cost difference for the upgrade
    upgrade_cost = tier_subscription_cost[new_tier] - tier_subscription_cost[user.tier]

    # Ensure user has enough balance
    if user.wallet_balance < upgrade_cost:
        flash(f'Insufficient balance for upgrading to {new_tier}. You need ৳{upgrade_cost:.2f}.', 'danger')
        return redirect(url_for('dashboard'))

    # Deduct the cost and upgrade the tier
    user.wallet_balance -= upgrade_cost
    user.tier = new_tier

    db.session.commit()
    flash(f'Successfully upgraded to {new_tier} tier. Your wallet has been charged ৳{upgrade_cost:.2f}.', 'success')
    return redirect(url_for('dashboard'))


# Tier Subscription Route
@app.route('/subscribe_tier/<tier>', methods=['POST'])
def subscribe_tier(tier):
    if 'user_id' not in session:
        flash('Please log in to subscribe to a tier.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    cost = tier_subscription_cost.get(tier, 0)

    if user.wallet_balance < cost:
        flash(f'Insufficient balance. You need ৳{cost - user.wallet_balance:.2f} more to subscribe to {tier} tier.', 'danger')
        return redirect(url_for('dashboard'))

    user.wallet_balance -= cost
    user.tier = tier
    db.session.commit()

    flash(f'Successfully subscribed to {tier} tier!', 'success')
    return redirect(url_for('dashboard'))
