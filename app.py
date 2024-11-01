from flask import Flask, render_template, redirect, url_for, flash
from flask_jwt_extended import JWTManager, set_access_cookies, unset_jwt_cookies, jwt_required
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flasgger import Swagger
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default_secret_key")
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "jwt_secret_key")
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = False  # Change to True for production with HTTPS
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///bank.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
swagger = Swagger(app)

# Initialize database and JWT
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Import blueprints and routes
from controller.user_controller import user_controller
from controller.account_controller import account_controller
from controller.transaction_controller import transaction_controller

# Register blueprints
app.register_blueprint(user_controller, url_prefix='/users')
app.register_blueprint(account_controller, url_prefix='/accounts')
app.register_blueprint(transaction_controller, url_prefix='/transactions')

# Home Route
@app.route('/')
def home():
    return render_template('index.html')

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    return render_template('/dashboard/dashboard.html')

# Error Handling
@app.errorhandler(404)
def page_not_found(e):
    flash("Page not found", "danger")
    return redirect(url_for('home'))

# Run app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
