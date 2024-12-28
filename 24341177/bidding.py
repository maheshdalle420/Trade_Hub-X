
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

def schedule_auction_end_notification(user, property):
    """
    Schedule an email notification for when the auction is about to end.
    """
    time_remaining = property.end_time - datetime.now()
    if time_remaining.total_seconds() > 300:  # Only schedule if more than 5 minutes remain
        notification_time = property.end_time - timedelta(minutes=5)
        # Simulate scheduling (use a task queue like Celery in production)
        send_auction_end_email(user, property, notification_time)


@app.route('/bidding/<int:property_id>', methods=['GET', 'POST'])
def bidding(property_id):
    if 'user_id' not in session:
        flash('Please log in to place a bid.', 'warning')
        return redirect(url_for('login'))

    property = Property.query.get_or_404(property_id)
    user = User.query.get(session['user_id'])  # Get the current user

    if request.method == 'POST':
        bid_amount = float(request.form['bid_amount'])
        auto_increment = float(request.form['auto_increment']) if 'auto_increment' in request.form else None
        end_limit = float(request.form['end_limit']) if 'end_limit' in request.form else None
        is_prioritized = 'is_prioritized' in request.form
        notify_auction_end = 'notify_auction_end' in request.form  # Check if the user opted for notifications

        # Fetch the current highest bid
        highest_bid = Bid.query.filter_by(property_id=property_id).order_by(Bid.bid_amount.desc()).first()

        # Ensure the bid is higher than the current highest bid
        if highest_bid and bid_amount <= highest_bid.bid_amount:
            flash('Your bid must be higher than the current highest bid.', 'danger')
            return redirect(url_for('bidding', property_id=property_id))

        # Create a new explicit bid
        new_bid = Bid(
            property_id=property_id,
            user_id=session['user_id'],
            bid_amount=bid_amount,
            auto_increment=auto_increment,
            end_limit=end_limit,
            is_prioritized=is_prioritized
        )

        try:
            db.session.add(new_bid)
            db.session.commit()

            # If the user opted for notifications, schedule a notification
            if notify_auction_end and user.tier in ['Silver', 'Gold']:
                schedule_auction_end_notification(user, property)

            flash('Your bid has been placed successfully!', 'success')

            # Trigger auto-bidding if applicable
            if not auto_increment and not end_limit:
                handle_auto_bidding(property_id, bid_amount)
        except Exception as e:
            db.session.rollback()
            flash(f'Error placing bid: {e}', 'danger')

    # Fetch the current highest bid and all bids for the property
    highest_bid = Bid.query.filter_by(property_id=property_id).order_by(Bid.bid_amount.desc()).first()
    bids = Bid.query.filter_by(property_id=property_id).order_by(Bid.timestamp.desc()).all()

    return render_template('bidding.html', property=property, highest_bid=highest_bid, bids=bids, user=user)


def handle_auto_bidding(property_id, explicit_bid_amount):
    """
    Handle auto-bidding for a property when a new explicit bid surpasses the current highest bid.
    """
    # Fetch the current highest bid after the explicit bid
    highest_bid = Bid.query.filter_by(property_id=property_id).order_by(Bid.bid_amount.desc()).first()

    # Ensure the new highest bid is the explicit bid
    if highest_bid and highest_bid.bid_amount == explicit_bid_amount:
        competing_bids = Bid.query.filter(
            Bid.property_id == property_id,
            Bid.auto_increment.isnot(None),
            Bid.end_limit > highest_bid.bid_amount
        ).order_by(Bid.timestamp)

        while True:
            placed_bid = False  # Track if any auto-bid is placed in this iteration

            for bid in competing_bids:
                next_bid_amount = highest_bid.bid_amount + bid.auto_increment

                # Place the auto-bid only if it doesn't exceed the user's end limit
                if next_bid_amount <= bid.end_limit:
                    new_auto_bid = Bid(
                        property_id=property_id,
                        user_id=bid.user_id,
                        bid_amount=next_bid_amount,
                        auto_increment=bid.auto_increment,
                        end_limit=bid.end_limit,
                        is_prioritized=bid.is_prioritized
                    )
                    try:
                        db.session.add(new_auto_bid)
                        db.session.commit()

                        # Update the highest bid for the next iteration
                        highest_bid = new_auto_bid
                        placed_bid = True

                        # Notify prioritized users when they are outbid
                        if bid.is_prioritized:
                            send_prioritized_email(bid.user_id, property_id, "outbid")
                    except Exception as e:
                        db.session.rollback()

                # Notify if the user's limit has been exceeded
                if bid.is_prioritized and bid.end_limit <= highest_bid.bid_amount:
                    send_prioritized_email(bid.user_id, property_id, "limit")

            # Exit the loop if no new bids were placed
            if not placed_bid:
                break


# Email Notifications
def send_prioritized_email(user_id, property_id, reason):
    user = User.query.get(user_id)
    property = Property.query.get(property_id)

    if user:
        if reason == "outbid":
            subject = 'Action Required: Your Priority Item'
            body = f"Your priority item, {property.title}, has been outbid."
        elif reason == "limit":
            subject = 'Increase Your Bid Limit'
            body = f"Your priority item, {property.title}, has exceeded your bid limit. Increase your limit to stay in the auction."

        msg = Message(
            subject,
            recipients=[user.email]
        )
        msg.body = body
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error sending prioritized email: {e}")

# Handle Next Highest Bidder
def handle_next_bidder(property_id, current_user_id):
    current_highest_bid = Bid.query.filter_by(property_id=property_id, user_id=current_user_id).first()
    next_highest_bid = Bid.query.filter(
        Bid.property_id == property_id,
        Bid.id != current_highest_bid.id
    ).order_by(Bid.bid_amount.desc()).first()

    if next_highest_bid:
        next_highest_user = User.query.get(next_highest_bid.user_id)
        add_to_cart(property_id, next_highest_user.id)
        notify_next_highest_bidder(next_highest_user, next_highest_bid, property_id)

# Notify Next Highest Bidder
def notify_next_highest_bidder(user, bid, property_id):
    property = Property.query.get(property_id)
    subject = f'Auction Opportunity for {property.title}'
    body = f"Dear {user.full_name},\n\nThe highest bidder failed to complete the payment for '{property.title}'.\nYou now have the opportunity to win this auction at your bid amount of ৳{bid.bid_amount}. Please complete the payment within 24 hours.\n\nThank you,\nAuctions Platform Team"
    msg = Message(subject, recipients=[user.email])
    msg.body = body
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

def add_to_cart(property_id, user_id):
    # Set a 24-hour timer for payment
    checkout_time_limit = datetime.now() + timedelta(hours=24)
    new_cart_item = AuctionCart(
        user_id=user_id,
        property_id=property_id,
        checkout_time_limit=checkout_time_limit
    )
    try:
        db.session.add(new_cart_item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error adding to cart: {e}")        


           
