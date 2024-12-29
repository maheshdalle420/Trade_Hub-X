
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import random


app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tradehub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


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


@app.route('/delete_listing/<int:id>', methods=['POST'])
def delete_listing(id):
    if 'user_id' not in session:
        flash('Please log in to delete your listing.', 'warning')
        return redirect(url_for('login'))

    property = Property.query.get_or_404(id)

    if property.user_id != session['user_id']:
        flash('You are not authorized to delete this listing.', 'danger')
        return redirect(url_for('view_listings'))

    try:
        if property.image_filename:
            # If there's an image associated, delete it from the file system
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], property.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)

        db.session.delete(property)
        db.session.commit()
        flash('Property listing deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting listing: {e}', 'danger')
        db.session.rollback()

    return redirect(url_for('view_listings'))

@app.route('/listings')
def view_listings():
    properties = Property.query.all()
    return render_template('view_listings.html', properties=properties)



@app.route('/create_listing', methods=['GET', 'POST'])
def create_listing():
    if 'user_id' not in session:
        flash('Please log in to create a listing.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        location = request.form['location']
        start_time_str = request.form['start_time']
        end_time_str = request.form['end_time']
        image = request.files['image']

        # Parse the start_time and end_time strings into datetime objects
        try:
            # Use the correct format to parse the 'datetime-local' format (with T separator)
            start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
            end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date/time format. Please use YYYY-MM-DD HH:MM.', 'danger')
            return redirect(url_for('create_listing'))

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
        else:
            filename = None

        new_property = Property(
            user_id=session['user_id'],
            title=title,
            description=description,
            price=float(price),
            location=location,
            start_time=start_time,
            end_time=end_time,
            image_filename=filename
        )

        try:
            db.session.add(new_property)
            db.session.commit()
            flash('Property listing created successfully!', 'success')
            return redirect(url_for('view_listings'))
        except Exception as e:
            flash(f'Error creating listing: {e}', 'danger')
            db.session.rollback()

    return render_template('create_listing.html')


@app.route('/update_listing/<int:id>', methods=['GET', 'POST'])
def update_listing(id):
    if 'user_id' not in session:
        flash('Please log in to update your listing.', 'warning')
        return redirect(url_for('login'))

    property = Property.query.get_or_404(id)

    # Ensure that the logged-in user owns the property
    if property.user_id != session['user_id']:
        flash('You are not authorized to edit this listing.', 'danger')
        return redirect(url_for('view_listings'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        location = request.form['location']
        start_time_str = request.form['start_time']
        end_time_str = request.form['end_time']
        image = request.files['image']

        # Convert start_time and end_time to datetime objects
        try:
            start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
            end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date/time format. Please use YYYY-MM-DD HH:MM.', 'danger')
            return redirect(url_for('update_listing', id=id))

        property.title = title
        property.description = description
        property.price = float(price)
        property.location = location
        property.start_time = start_time
        property.end_time = end_time

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            property.image_filename = filename

        try:
            db.session.commit()
            flash('Listing updated successfully!', 'success')
            return redirect(url_for('view_listings'))
        except Exception as e:
            flash(f'Error updating listing: {e}', 'danger')
            db.session.rollback()

    return render_template('update_listing.html', property=property)

@app.route('/listings')
def view_listings():
    properties = Property.query.all()
    return render_template('view_listings.html', properties=properties)
