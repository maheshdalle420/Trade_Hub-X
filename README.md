# TRADE HUBX
A feature-rich auctions platform built with Flask, featuring user subscriptions, tier-based privileges, and dynamic auction functionality. The application allows users to participate in auctions, manage subscriptions, maintain a wishlist, and receive notifications based on their subscription tier.

## Features

### General Features
- User registration and login system with email verification.
- User dashboard to manage profiles, subscriptions, and actions.
- Wallet system to handle balances and payments.

### Auction Features
- Live, upcoming, and past auction categories.
- Ability to bid on properties and manage bidding history.
- Countdown timer for live auctions.
- Wishlist functionality to keep track of preferred items.

### Subscription Tiers
- **None/Bronze:** Standard functionality.
- **Silver:** Extended checkout time, auction-ending notifications via email.
- **Gold:** Wishlist live notifications, payment discounts, and all Silver tier features.

## Installation

### Prerequisites
- Python 3.8+
- Flask
- Flask extensions:
  - Flask-SQLAlchemy
  - Flask-Mail
  - Flask-WTF
- SQLite (or any preferred database backend)
- A mail server for email notifications

### Setup
1. Clone the repository:
    ```bash
    git clone https://github.com/maheshdalle420/Trade_Hub-X
    cd TradehubX
    ```
2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Set up environment variables for configuration:
    ```bash
    export FLASK_APP=app.py
    export FLASK_ENV=development
    export MAIL_SERVER=smtp.yourmail.com
    export MAIL_PORT=587
    export MAIL_USERNAME=your-email@example.com
    export MAIL_PASSWORD=your-password
    ```
5. Initialize the database:
    ```bash
    flask db init
    flask db migrate
    flask db upgrade
    ```
6. Run the application:
    ```bash
    flask run
    ```

## Usage

### User Roles
- **Buyers:**
  - View auctions and place bids.
  - Manage wishlist items.
  - Receive notifications based on subscription tier.

- **Sellers:**
  - List properties for auction.
  - View and manage property listings.

### Admin Features
- Approve or reject auction listings.
- Manage users and auction properties.

## Subscription System
Users can subscribe to tiers that provide added benefits:
- **Silver:** Email reminders for auction closings, extended checkout time.
- **Gold:** Includes Silver features plus wishlist notifications and payment discounts.

## Contribution
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m 'Add feature-name'`).
4. Push to the branch (`git push origin feature-name`).
5. Open a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contact
For questions or suggestions, please contact:
Email : juhayer.rahman@g.bracu.ac.bd ,md.mohaiminul.islam2@g.bracu.ac.bd,rifat.sanjida@g.bracu.ac.bd



 
 
