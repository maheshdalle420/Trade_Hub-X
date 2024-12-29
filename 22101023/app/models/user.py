from flask_login import UserMixin
from datetime import datetime

from app import db



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=False)
    otp_secret = db.Column(db.String(32), nullable=True)
    otp_valid_until = db.Column(db.DateTime, nullable=True)
    wallet_balance = db.Column(db.Float, default=0.0)  # Add wallet balance
    badge = db.Column(db.String(10), nullable=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
