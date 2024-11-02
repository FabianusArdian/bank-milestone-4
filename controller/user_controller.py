from flask import Blueprint, request, jsonify, redirect, url_for, flash, render_template, make_response
from sqlalchemy.exc import IntegrityError
from models.user import User
from connector.db import Session
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from werkzeug.security import generate_password_hash, check_password_hash
from flasgger import swag_from

user_controller = Blueprint('user_controller', __name__)

@user_controller.route('/register_user', methods=['GET', 'POST'])
@swag_from({
    'summary': 'Register a new user',
    'description': 'Allows a new user to register with a username, email, and password.',
    'parameters': [
        {
            'name': 'username',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'Username for the new user'
        },
        {
            'name': 'email',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'Email address for the new user'
        },
        {
            'name': 'password',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'Password for the new user'
        }
    ],
    'responses': {
        200: {
            'description': 'Registration successful, redirect to login'
        },
        400: {
            'description': 'All fields are required or email/username already exists'
        }
    }
})
def register_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not (username and email and password):
            flash("All fields are required.", "danger")
            return redirect(url_for('user_controller.register_user'))

        session = Session()
        try:
            if session.query(User).filter((User.email == email) | (User.username == username)).first():
                flash("Email or username already exists.", "danger")
                return redirect(url_for('user_controller.register_user'))

            user = User(username=username, email=email)
            user.set_password(password)
            session.add(user)
            session.commit()

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('user_controller.login'))
        except IntegrityError:
            session.rollback()
            flash("An error occurred. Please try again.", "danger")
        finally:
            session.close()

    return render_template('register.html')

@user_controller.route('/login', methods=['GET', 'POST'])
@swag_from({
    'summary': 'User login',
    'description': 'Logs in an existing user with email and password.',
    'parameters': [
        {
            'name': 'email',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'Email address of the user'
        },
        {
            'name': 'password',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'Password for the user'
        }
    ],
    'responses': {
        200: {
            'description': 'Login successful, redirect to dashboard'
        },
        401: {
            'description': 'Invalid email or password'
        }
    }
})
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        session = Session()
        user = session.query(User).filter_by(email=email).first()
        session.close()

        if user and user.check_password(password):
            access_token = create_access_token(identity=user.id)
            response = make_response(redirect(url_for('dashboard')))
            set_access_cookies(response, access_token)
            flash("Login successful!", "success")
            return response
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for('user_controller.login'))

    return render_template('login.html')

@user_controller.route('/users/me', methods=['GET'])
@jwt_required()
@swag_from({
    'summary': 'Get user profile',
    'description': 'Retrieves the profile of the authenticated user.',
    'responses': {
        200: {
            'description': 'User profile details',
            'examples': {
                'application/json': {
                    'username': 'john_doe',
                    'email': 'john@example.com'
                }
            }
        },
        404: {
            'description': 'User not found'
        }
    }
})
def get_profile():
    user_id = get_jwt_identity()
    session = Session()
    user = session.query(User).filter_by(id=user_id).first()
    session.close()

    if not user:
        flash("User not found", "danger")
        return redirect(url_for('user_controller.login'))

    return render_template('/dashboard/profile.html', username=user.username, email=user.email)

@user_controller.route('/users/me', methods=['POST', 'PUT'])
@jwt_required()
@swag_from({
    'summary': 'Update user profile',
    'description': 'Allows the authenticated user to update their profile information.',
    'parameters': [
        {
            'name': 'username',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'New username for the user'
        },
        {
            'name': 'email',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'New email address for the user'
        },
        {
            'name': 'old_password',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'Current password of the user (for validation)'
        },
        {
            'name': 'new_password',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'New password for the user'
        }
    ],
    'responses': {
        200: {
            'description': 'Profile updated successfully'
        },
        404: {
            'description': 'User not found'
        },
        403: {
            'description': 'Old password is incorrect'
        }
    }
})
def update_profile():
    user_id = get_jwt_identity()
    session = Session()
    user = session.query(User).filter_by(id=user_id).first()

    if not user:
        flash("User not found", "danger")
        return redirect(url_for('dashboard'))

    user.username = request.form.get('username', user.username)
    user.email = request.form.get('email', user.email)

    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')

    # Check if the old password is provided and validate it
    if old_password and not user.check_password(old_password):
        flash("Old password is incorrect.", "danger")
        return redirect(url_for('user_controller.get_profile'))

    if new_password:
        user.set_password(new_password)

    session.commit()
    session.close()

    flash("Profile updated successfully", "success")
    return redirect(url_for('user_controller.get_profile'))


@user_controller.route('/logout')
@swag_from({
    'summary': 'User logout',
    'description': 'Logs out the authenticated user, invalidating their session.',
    'responses': {
        200: {
            'description': 'Successfully logged out'
        }
    }
})
def logout():
    response = make_response(redirect(url_for('home')))
    unset_jwt_cookies(response)
    flash("You have been logged out.", "info")
    return response
