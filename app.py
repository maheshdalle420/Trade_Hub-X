from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import smtplib
import random
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'Tradehub_X'

mysql = MySQL(app)

# Modularized email sending function
def send_email(subject, recipient, body):
    sender_email = 'juhayer.rahman@g.bracu.ac.bd'
    sender_password = 'hxbb ogzr utzw hcop'
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(sender_email, recipient, message)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# Helper function to send OTP
def send_otp(email):
    otp = random.randint(100000, 999999)
    subject = "Your OTP for Verification"
    body = f"Your OTP is: {otp}."
    if send_email(subject, email, body):
        return otp
    return None



@app.route('/welcome')
def welcome():
    return render_template('welcome.html')



@app.route('/')
def home():
    if 'username' in session:
        # Pass the logged-in username to the home.html template
        return render_template('home.html', username=session['username'])
    # Redirect unauthenticated users to the welcome page
    return redirect(url_for('welcome'))


@app.route('/auctions')
def view_auctions():
    if 'username' not in session:
        flash('Please log in to view auctions.', 'warning')
        return redirect(url_for('login'))

    # Get the current datetime for auction status updates
    current_datetime = datetime.now()

    try:
        cursor = mysql.connection.cursor()

        # Update auction statuses dynamically
        cursor.execute("""
            UPDATE auction_items ai
            JOIN properties p ON ai.property_id = p.id
            SET ai.status = CASE
                WHEN CONCAT(p.starting_date, ' ', p.starting_time) > %s THEN 'Upcoming'
                WHEN CONCAT(p.starting_date, ' ', p.starting_time) <= %s 
                     AND CONCAT(p.ending_date, ' ', p.ending_time) >= %s THEN 'Live'
                WHEN CONCAT(p.ending_date, ' ', p.ending_time) < %s THEN 'Past'
            END
        """, (current_datetime, current_datetime, current_datetime, current_datetime))

        mysql.connection.commit()

        # Fetch live auctions
        cursor.execute("""
            SELECT p.id, p.name, p.description, p.starting_price, p.starting_date, p.starting_time, 
                   p.ending_date, p.ending_time, p.city, p.area, p.road, p.contact_info, ai.status, 
                   (SELECT image_url FROM property_images WHERE property_id = p.id LIMIT 1) AS image_url
            FROM auction_items ai
            JOIN properties p ON ai.property_id = p.id
            WHERE ai.status = 'Live'
        """)
        live_auctions = cursor.fetchall()

        # Fetch upcoming auctions
        cursor.execute("""
            SELECT p.id, p.name, p.description, p.starting_price, p.starting_date, p.starting_time, 
                   p.ending_date, p.ending_time, p.city, p.area, p.road, p.contact_info, ai.status, 
                   (SELECT image_url FROM property_images WHERE property_id = p.id LIMIT 1) AS image_url
            FROM auction_items ai
            JOIN properties p ON ai.property_id = p.id
            WHERE ai.status = 'Upcoming'
        """)
        upcoming_auctions = cursor.fetchall()

        # Fetch past auctions
        cursor.execute("""
            SELECT p.id, p.name, p.description, p.starting_price, p.starting_date, p.starting_time, 
                   p.ending_date, p.ending_time, p.city, p.area, p.road, p.contact_info, ai.status, 
                   (SELECT image_url FROM property_images WHERE property_id = p.id LIMIT 1) AS image_url
            FROM auction_items ai
            JOIN properties p ON ai.property_id = p.id
            WHERE ai.status = 'Past'
        """)
        past_auctions = cursor.fetchall()

        cursor.close()

        # Return the template with the fetched data
        return render_template(
            'auctions.html', 
            live_auctions=live_auctions, 
            upcoming_auctions=upcoming_auctions, 
            past_auctions=past_auctions
        )
    
    except Exception as e:
        # Handle exceptions
        mysql.connection.rollback()
        flash(f"Error occurred: {str(e)}", 'danger')
        return redirect(url_for('home'))




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        date_of_birth = request.form['dob']
        profession = request.form['profession']
        city = request.form['city']
        area = request.form['area']
        road = request.form['road']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password, date_of_birth, profession, city, area, road, is_verified) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (username, email, password, date_of_birth, profession, city, area, road, 0)
            )
            mysql.connection.commit()

            otp = send_otp(email)
            if otp:
                session['otp'] = otp
                session['email'] = email
                flash('Registration successful! Verify your email.', 'success')
                return redirect(url_for('verify_email'))
            else:
                flash('Failed to send OTP. Try again.', 'danger')
                return redirect(url_for('register'))

        except Exception as e:
            print(e)
            flash('Username or email already exists!', 'danger')
            return redirect(url_for('register'))
        finally:
            cursor.close()

    return render_template('register.html')

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if 'otp' in session and int(entered_otp) == session['otp']:
            cursor = mysql.connection.cursor()
            cursor.execute("UPDATE users SET is_verified = %s WHERE email = %s", (1, session['email']))
            mysql.connection.commit()
            cursor.close()

            session.pop('otp', None)
            session.pop('email', None)

            flash('Email verified successfully! You can log in now.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Try again.', 'danger')

    return render_template('verify_email.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            otp = send_otp(email)
            if otp:
                session['otp'] = otp
                session['email'] = email
                flash('An OTP has been sent to your email.', 'success')
                return redirect(url_for('verify_otp'))
            else:
                flash('Failed to send OTP. Please try again.', 'danger')
        else:
            flash('Email not found in our records.', 'danger')

    return render_template('reset_password.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'otp' not in session:
        flash('Invalid request. Please try again.', 'danger')
        return redirect(url_for('reset_password'))

    if request.method == 'POST':
        entered_otp = request.form['otp']

        if str(session['otp']) == entered_otp:
            flash('OTP verified successfully! You can now set a new password.', 'success')
            return redirect(url_for('set_new_password'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('verify_otp.html')

@app.route('/set-new-password', methods=['GET', 'POST'])
def set_new_password():
    if 'email' not in session:
        flash('Invalid request. Please try again.', 'danger')
        return redirect(url_for('reset_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('set_new_password'))

        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (new_password, session['email']))
        mysql.connection.commit()
        cursor.close()

        session.pop('otp', None)
        session.pop('email', None)

        flash('Your password has been updated successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('set_new_password.html')

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session:
        flash('Please log in to change your password.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('New passwords do not match!', 'danger')
            return redirect(url_for('change_password'))

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (session['username'],))
        user = cursor.fetchone()

        if user and user[0] == current_password:
            cursor.execute("UPDATE users SET password = %s WHERE username = %s", (new_password, session['username']))
            mysql.connection.commit()
            flash('Password changed successfully!', 'success')
        else:
            flash('Current password is incorrect.', 'danger')

        cursor.close()
        return redirect(url_for('home'))

    return render_template('change_password.html')


@app.route('/update-profile', methods=['GET', 'POST'])
def update_profile():
    if 'username' not in session:
        flash('Please log in to update your profile.', 'warning')
        return redirect(url_for('login'))

    if 'otp_verified' not in session:
        flash('Please verify your identity to update your profile.', 'danger')
        return redirect(url_for('request_profile_otp'))

    if request.method == 'POST':
        email = request.form['email']
        profession = request.form['profession']
        city = request.form['city']
        area = request.form['area']
        road = request.form['road']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE users 
            SET email=%s, profession=%s, city=%s, area=%s, road=%s 
            WHERE username=%s
        """, (email, profession, city, area, road, session['username']))
        mysql.connection.commit()
        cursor.close()

        session.pop('otp_verified', None)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('home'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT email, profession, city, area, road FROM users WHERE username=%s", (session['username'],))
    user = cursor.fetchone()
    cursor.close()

    return render_template('update_profile.html', user=user)


@app.route('/delete-profile', methods=['POST'])
def delete_profile():
    if 'username' not in session:
        flash('Please log in to delete your profile.', 'warning')
        return redirect(url_for('login'))

    password = request.form['password']

    # Verify the password
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT password FROM users WHERE username=%s", (session['username'],))
    user = cursor.fetchone()

    if user and user[0] == password:  # Replace with hashed password check if applicable
        cursor.execute("DELETE FROM users WHERE username=%s", (session['username'],))
        mysql.connection.commit()
        cursor.close()

        session.pop('username', None)
        flash('Your profile has been deleted successfully.', 'info')
        return redirect(url_for('register'))
    else:
        flash('Incorrect password. Please try again.', 'danger')
        cursor.close()
        return redirect(url_for('confirm_delete_profile'))


@app.route('/request-profile-otp', methods=['GET', 'POST'])
def request_profile_otp():
    if 'username' not in session:
        flash('Please log in to update your profile.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Get user email from the database
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT email FROM users WHERE username = %s", (session['username'],))
        user = cursor.fetchone()
        cursor.close()

        if user:
            email = user[0]
            otp = send_otp(email)
            if otp:
                session['otp'] = otp
                session['otp_email'] = email
                flash('An OTP has been sent to your email. Please verify to proceed.', 'info')
                return redirect(url_for('verify_profile_otp'))
            else:
                flash('Failed to send OTP. Please try again later.', 'danger')

    return render_template('request_profile_otp.html')

@app.route('/verify-profile-otp', methods=['GET', 'POST'])
def verify_profile_otp():
    if 'otp' not in session or 'otp_email' not in session:
        flash('Invalid request. Please request a new OTP.', 'danger')
        return redirect(url_for('request_profile_otp'))

    if request.method == 'POST':
        entered_otp = request.form['otp']

        if str(session['otp']) == entered_otp:
            session.pop('otp', None)
            session['otp_verified'] = True
            flash('OTP verified successfully! You can now update your profile.', 'success')
            return redirect(url_for('update_profile'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('verify_profile_otp.html')



@app.route('/confirm-delete-profile')
def confirm_delete_profile():
    if 'username' not in session:
        flash('Please log in to delete your profile.', 'warning')
        return redirect(url_for('login'))
    return render_template('confirm_delete_profile.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/create-listing', methods=['GET', 'POST'])
def create_listing():
    if 'username' not in session:
        flash('Please log in to create a property listing.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Collect form data
        name = request.form['name']
        description = request.form['description']
        starting_price = request.form['starting_price']
        starting_date = request.form['starting_date']
        starting_time = request.form['starting_time']
        ending_date = request.form['ending_date']
        ending_time = request.form['ending_time']
        city = request.form['city']
        area = request.form['area']
        road = request.form['road']
        contact_info = request.form['contact_info']
        files = request.files.getlist('images')

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username=%s", (session['username'],))
        user = cursor.fetchone()

        if user:
            user_id = user[0]

            # Insert property details
            cursor.execute("""
                INSERT INTO properties (user_id, name, description, starting_price, starting_date, starting_time, ending_date, ending_time, city, area, road, contact_info)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, name, description, starting_price, starting_date, starting_time, ending_date, ending_time, city, area, road, contact_info))
            mysql.connection.commit()

            property_id = cursor.lastrowid

            # Add to auction_items
            cursor.execute("INSERT INTO auction_items (property_id, status) VALUES (%s, 'Upcoming')", (property_id,))
            mysql.connection.commit()

            # Handle image uploads
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    cursor.execute("INSERT INTO property_images (property_id, image_url) VALUES (%s, %s)", (property_id, file_path))
            mysql.connection.commit()

            flash('Property listing created successfully!', 'success')
        cursor.close()

        return redirect(url_for('view_listings'))

    return render_template('create_listing.html')



from flask import render_template, request
import mysql.connector

@app.route('/search', methods=['GET'])
def search_properties():
    # Extract filter values from the request
    name_query = request.args.get('name', '')
    city_query = request.args.get('city', '')
    area_query = request.args.get('area', '')
    road_query = request.args.get('road', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    # Create the search conditions
    search_conditions = []
    search_params = []

    # Add conditions based on the provided filters
    if name_query:
        search_conditions.append("p.name LIKE %s")
        search_params.append(f"%{name_query}%")
    if city_query:
        search_conditions.append("p.city LIKE %s")
        search_params.append(f"%{city_query}%")
    if area_query:
        search_conditions.append("p.area LIKE %s")
        search_params.append(f"%{area_query}%")
    if road_query:
        search_conditions.append("p.road LIKE %s")
        search_params.append(f"%{road_query}%")
    if min_price is not None:
        search_conditions.append("p.starting_price >= %s")
        search_params.append(min_price)
    if max_price is not None:
        search_conditions.append("p.starting_price <= %s")
        search_params.append(max_price)

    # If no filters are provided, default to a name search
    if not search_conditions:
        search_conditions.append("p.name LIKE %s")
        search_params.append(f"%{name_query}%")
    
    # Build the query with dynamic conditions
    query = """
        SELECT p.id, p.name, p.description, p.starting_price, p.starting_date, p.starting_time,
               p.ending_date, p.ending_time, p.city, p.area, p.road, pi.image_url
        FROM properties p
        LEFT JOIN property_images pi ON p.id = pi.property_id
        WHERE """ + " AND ".join(search_conditions)
    
    # Execute the query
    cursor = mysql.connection.cursor()
    cursor.execute(query, tuple(search_params))
    results = cursor.fetchall()

    # Fetch cities and areas for the filter dropdowns
    cursor.execute("SELECT DISTINCT city FROM properties")
    cities = [city[0] for city in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT area FROM properties")
    areas = [area[0] for area in cursor.fetchall()]

    cursor.close()

    # Pass the results and filter options to the template
    return render_template('search_properties.html', search_results=results,
                           cities=cities, areas=areas, query=name_query,
                           city=city_query, area=area_query, road=road_query,
                           min_price=min_price, max_price=max_price)






@app.route('/property/<int:property_id>', methods=['GET', 'POST'])
def view_property(property_id):
    if 'username' not in session:
        flash('Please log in to view property details.', 'warning')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()

    # Fetch user ID from session
    cursor.execute("SELECT id FROM users WHERE username=%s", (session['username'],))
    user = cursor.fetchone()

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    user_id = user[0]

    # Fetch property details
    cursor.execute("""
        SELECT id, name, description, starting_price, starting_date, starting_time, ending_date, ending_time, city, area, road, contact_info, user_id 
        FROM properties WHERE id=%s
    """, (property_id,))
    property_details = cursor.fetchone()

    if not property_details:
        cursor.close()
        flash('Property not found.', 'danger')
        return redirect(url_for('view_listings'))

    # Check if the logged-in user owns the property
    is_owner = property_details[-1] == user_id

    # Fetch associated images
    cursor.execute("SELECT image_url FROM property_images WHERE property_id=%s", (property_id,))
    images = cursor.fetchall()

    if request.method == 'POST':
        if is_owner:
            # Handle property deletion
            try:
                # Delete property images
                cursor.execute("DELETE FROM property_images WHERE property_id=%s", (property_id,))
                # Delete the property
                cursor.execute("DELETE FROM properties WHERE id=%s", (property_id,))
                mysql.connection.commit()
                flash('Property deleted successfully!', 'success')
            except Exception as e:
                flash(f"Error deleting property: {e}", 'danger')
            finally:
                cursor.close()
                return redirect(url_for('view_listings'))
        else:
            flash('You are not authorized to delete this property.', 'danger')
            cursor.close()
            return redirect(url_for('view_property', property_id=property_id))

    cursor.close()
    return render_template('view_property.html', property=property_details, images=images, is_owner=is_owner)









@app.route('/delete-property/<int:property_id>', methods=['POST'])
def delete_property(property_id):
    if 'username' not in session:
        flash('Please log in to delete your property.', 'warning')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()

    # Fetch the user ID from the session
    cursor.execute("SELECT id FROM users WHERE username=%s", (session['username'],))
    user = cursor.fetchone()

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    user_id = user[0]

    # Verify if the property belongs to the logged-in user
    cursor.execute("SELECT user_id FROM properties WHERE id=%s", (property_id,))
    property_owner = cursor.fetchone()

    if not property_owner or property_owner[0] != user_id:
        flash('You are not authorized to delete this property.', 'danger')
        return redirect(url_for('view_listings'))

    # Delete the property and associated images
    cursor.execute("DELETE FROM property_images WHERE property_id=%s", (property_id,))
    cursor.execute("DELETE FROM properties WHERE id=%s", (property_id,))
    mysql.connection.commit()

    cursor.close()

    flash('Property deleted successfully!', 'success')
    return redirect(url_for('view_listings'))



@app.route('/view-listings')
def view_listings():
    if 'username' not in session:
        flash('Please log in to view your listings.', 'warning')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()

    # Fetch the user ID based on the session username
    cursor.execute("SELECT id FROM users WHERE username=%s", (session['username'],))
    user = cursor.fetchone()

    if user:
        user_id = user[0]

        # Fetch the listings created by this user, including the first image URL and updated location details
        cursor.execute("""
            SELECT 
                p.id, p.name, p.description, p.starting_price, p.starting_date, p.starting_time, 
                p.ending_date, p.ending_time, CONCAT(p.city, ', ', p.area, ', ', p.road) AS location, 
                p.contact_info, 
                COALESCE((SELECT image_url FROM property_images WHERE property_id = p.id LIMIT 1), '/static/uploads/placeholder.png') AS image_url
            FROM properties p 
            WHERE p.user_id=%s
        """, (user_id,))
        listings = cursor.fetchall()
    else:
        listings = []

    cursor.close()

    return render_template('view_listings.html', listings=listings)



@app.route('/property/<int:property_id>/bids', methods=['GET', 'POST'])
def property_bids(property_id):
    if 'username' not in session:
        flash('Please log in to place a bid.', 'warning')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()

    # Fetch user ID based on session
    cursor.execute("SELECT id FROM users WHERE username=%s", (session['username'],))
    user = cursor.fetchone()

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    user_id = user[0]

    # Fetch property details
    cursor.execute("SELECT id, name, description, starting_price FROM properties WHERE id=%s", (property_id,))
    property_details = cursor.fetchone()

    if not property_details:
        flash('Property not found.', 'danger')
        return redirect(url_for('view_listings'))

    if request.method == 'POST':
        bid_amount = float(request.form['bid_amount'])

        # Validate bid amount
        cursor.execute("SELECT MAX(bid_amount) FROM bids WHERE property_id=%s", (property_id,))
        highest_bid = cursor.fetchone()[0] or property_details[3]  # Use starting price if no bids

        if bid_amount <= highest_bid:
            flash('Your bid must be higher than the current highest bid.', 'danger')
        else:
            # Insert new bid
            cursor.execute(
                "INSERT INTO bids (property_id, user_id, bid_amount) VALUES (%s, %s, %s)",
                (property_id, user_id, bid_amount)
            )
            mysql.connection.commit()
            flash('Your bid has been placed successfully!', 'success')

    # Fetch all bids for the property
    cursor.execute("""
        SELECT b.bid_amount, b.bid_time, u.username 
        FROM bids b 
        JOIN users u ON b.user_id = u.id 
        WHERE b.property_id=%s 
        ORDER BY b.bid_amount DESC
    """, (property_id,))
    bids = cursor.fetchall()

    cursor.close()

    return render_template('property_bids.html', property=property_details, bids=bids)



if __name__ == '__main__':
    app.run(debug=True)
