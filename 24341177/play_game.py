
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

class GameHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_name = db.Column(db.String(50), nullable=False)
    amount_earned = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

wallet_limits = {
    "None": 1000,
    "Bronze": 100000,
    "Silver": 500000,
    "Gold": 1000000
}

@app.route('/play_game', methods=['GET', 'POST'])
def play_game():
    if 'user_id' not in session:
        flash('Please log in to play games.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        try:
            earned_money = float(request.form['earned_money'])
            if earned_money > 0:
                # Apply tier-based bonus
                tier_bonus = {
                    "Bronze": 1.1,  # 10% bonus
                    "Silver": 1.3,  # 30% bonus
                    "Gold": 1.5   # 50% bonus
                }.get(user.tier, 1.0)

                total_earned = earned_money * tier_bonus
                user.wallet_balance += total_earned

                # Ensure wallet balance does not exceed the current tier's limit
                current_limit = wallet_limits.get(user.tier, wallet_limits["None"])
                if user.wallet_balance > current_limit:
                    user.wallet_balance = current_limit

                db.session.commit()

                # Log the reward in game history
                game_history = GameHistory(
                    user_id=user.id,
                    game_name="Snake Game",
                    amount_earned=total_earned
                )
                db.session.add(game_history)
                db.session.commit()

                flash(f'You earned ৳{total_earned:.2f} with your {user.tier} tier bonus! Wallet capped at ৳{current_limit}.', 'success')
        except ValueError:
            flash('Invalid reward amount.', 'danger')
        return redirect(url_for('wallet'))

    return render_template('play_game.html', user=user)





@app.route('/reward', methods=['POST'])
def reward():
    if 'user_id' not in session:
        flash('Please log in to claim your reward.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    game_name = request.form.get('game_name')
    earned_money = float(request.form.get('earned_money', 0))

    if earned_money > 0:
        user = User.query.get(user_id)
        if user:
            # Update wallet balance
            user.wallet_balance += earned_money
            db.session.commit()

            # Log the reward in game history
            game_history = GameHistory(user_id=user_id, game_name=game_name, amount_earned=earned_money)
            db.session.add(game_history)
            db.session.commit()

            flash(f'Congratulations! You earned ৳{earned_money:.2f} from {game_name.capitalize()}!', 'success')
        else:
            flash('User not found. Please try again.', 'danger')
    else:
        flash('No reward earned. Play the game to earn money!', 'warning')

    return redirect(url_for('wallet'))
