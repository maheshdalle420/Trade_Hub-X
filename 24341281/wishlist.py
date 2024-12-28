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


# Wishlist Model
class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)

    def __repr__(self):
        return f'<Wishlist User {self.user_id} Property {self.property_id}>'
    
    
    
    
# View Wishlist Route
@app.route('/wishlist')
def view_wishlist():
    if 'user_id' not in session:
        flash('Please log in to view your wishlist.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    wishlist_items = Wishlist.query.filter_by(user_id=user_id).all()
    properties = [Property.query.get(item.property_id) for item in wishlist_items]

    return render_template('wishlist.html', properties=properties)


# Add to Wishlist Route
@app.route('/wishlist/add/<int:property_id>', methods=['POST'])
def add_to_wishlist(property_id):
    if 'user_id' not in session:
        flash('Please log in to add items to your wishlist.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    existing_entry = Wishlist.query.filter_by(user_id=user_id, property_id=property_id).first()

    if existing_entry:
        flash('This item is already in your wishlist.', 'info')
    else:
        new_wishlist_item = Wishlist(user_id=user_id, property_id=property_id)
        try:
            db.session.add(new_wishlist_item)
            db.session.commit()
            flash('Item added to your wishlist.', 'success')
        except Exception as e:
            flash(f'Error adding to wishlist: {str(e)}', 'danger')
            db.session.rollback()

    return redirect(url_for('auctions'))



# Remove from Wishlist Route
@app.route('/wishlist/remove/<int:property_id>', methods=['POST'])
def remove_from_wishlist(property_id):
    if 'user_id' not in session:
        flash('Please log in to manage your wishlist.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    wishlist_item = Wishlist.query.filter_by(user_id=user_id, property_id=property_id).first()

    if wishlist_item:
        try:
            db.session.delete(wishlist_item)
            db.session.commit()
            flash('Item removed from your wishlist.', 'success')
        except Exception as e:
            flash(f'Error removing from wishlist: {str(e)}', 'danger')
            db.session.rollback()
    else:
        flash('Item not found in your wishlist.', 'info')

    return redirect(url_for('view_wishlist'))
