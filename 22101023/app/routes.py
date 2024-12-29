from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify, current_app
from sqlalchemy import Transaction
from app import db, bcrypt, mail
from app.models import User
from app.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from app.utils.token_utils import generate_verification_token, verify_token
from app.utils.otp import generate_otp, verify_otp  # Import OTP helpers

# Define the Blueprint
main = Blueprint('main', __name__)

# Home route
@main.route("/")
@main.route("/home")
def home():
    return render_template('dashboard.html')

# Register route
@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        # Generate OTP for email verification
        otp = generate_otp(user)
        send_email(user.email, "Your OTP Code", f"Your OTP is: {otp}\n\nThis OTP is valid for 5 minutes.")

        flash('An OTP has been sent to your email for verification.', 'info')
        return redirect(url_for('main.verify_email_otp'))
    return render_template('register.html', title='Register', form=form)

# Login route
@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            otp = generate_otp(user)  # Generate OTP for 2FA
            send_email(user.email, "Your OTP Code", f"Your OTP is: {otp}\n\nThis OTP is valid for 5 minutes.")
            flash('An OTP has been sent to your email for verification.', 'info')
            return redirect(url_for('main.otp_verify_login', user_id=user.id))
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

# Logout route
@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.login'))

# Forgot Password route
@main.route("/reset_password_request", methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            # Logic for sending password reset link (not implemented)
            flash('Password reset instructions have been sent to your email.', 'info')
        else:
            flash('No account found with that email.', 'danger')
    return render_template('reset_password_request.html', title='Reset Password')

# OTP Verification after Login
@main.route("/otp-verify-login/<int:user_id>", methods=['GET', 'POST'])
def otp_verify_login(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        otp = request.form.get('otp')
        if verify_otp(user, otp):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid or expired OTP.', 'danger')
    return render_template('otp_verify.html', title='OTP Verification')

# Wishlist route
@main.route("/wishlist", methods=['GET'])
@login_required
def wishlist():
    wishlist_items = current_user.wishlist_items  # Assuming relationship is defined in User model
    return render_template('wishlist.html', title='My Wishlist', wishlist_items=wishlist_items)

# Send Email Utility Function
def send_email(recipient, subject, body, html=None):
    try:
        msg = Message(
            subject=subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[recipient]
        )
        msg.body = body
        if html:
            msg.html = html
        mail.send(msg)
        current_app.logger.info(f"Email sent to {recipient}")
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {recipient}: {e}")
        flash('Failed to send email. Please contact support.', 'danger')

# Route for Email OTP Verification (e.g., after registration)
@main.route("/verify-email-otp", methods=['GET', 'POST'])
@login_required
def verify_email_otp():
    if request.method == 'POST':
        otp = request.form.get('otp')
        if verify_otp(current_user, otp):
            current_user.is_verified = True  # Mark the user as verified
            db.session.commit()
            flash('Your email has been verified successfully!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'danger')
    return render_template('otp_verify.html', title='Verify Email')

@main.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    return render_template('account.html', title='Your Account')

@main.route("/add_funds", methods=['GET', 'POST'])
@login_required
def add_funds():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        if amount > 0:
            current_user.wallet_balance += amount
            db.session.commit()
            flash(f"${amount} has been added to your wallet.", "success")
        else:
            flash("Invalid amount.", "danger")
    return render_template('add_funds.html', title="Add Funds")

@main.route("/purchase_badge/<string:badge_type>", methods=['GET', 'POST'])
@login_required
def purchase_badge(badge_type):
    badge_prices = {'gold': 100, 'silver': 50, 'bronze': 25}

    if badge_type.lower() not in badge_prices:
        flash("Invalid badge type.", "danger")
        return redirect(url_for('main.account'))

    cost = badge_prices[badge_type.lower()]
    if current_user.wallet_balance >= cost:
        current_user.wallet_balance -= cost
        current_user.badge = badge_type.lower()
        db.session.commit()
        flash(f"You have successfully purchased the {badge_type.title()} badge!", "success")
    else:
        flash("Insufficient funds. Please add money to your wallet.", "danger")
    return redirect(url_for('main.account'))


@main.route('/test-otp/<int:user_id>')
def test_otp(user_id):
    user = User.query.get_or_404(user_id)
    otp = generate_otp(user)
    if otp:
        send_email(
            user.email,
            "Your OTP Code",
            f"Your OTP is: {otp}\n\nThis OTP is valid for 5 minutes."
        )
        return f"OTP generated and sent to {user.email}: {otp}"
    else:
        return "Failed to generate OTP."

@main.route('/test-email')
def test_email():
    try:
        send_email(
            "test-recipient@example.com",
            "Test Email",
            "This is a test email from AuctionHub."
        )
        return "Test email sent successfully."
    except Exception as e:
        return f"Failed to send test email: {e}"
