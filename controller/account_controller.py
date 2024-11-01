from flask import Blueprint, request, jsonify, flash, redirect, url_for, render_template
from models.account import Account
from connector.db import Session
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from

account_controller = Blueprint('account_controller', __name__)

# GET /accounts: List all accounts for the authenticated user
@account_controller.route('/accounts', methods=['GET'])
@jwt_required()
@swag_from({
    'summary': 'List all accounts',
    'description': 'Retrieve all accounts associated with the authenticated user.',
    'responses': {
        200: {
            'description': 'List of accounts',
            'examples': {
                'application/json': {
                    'accounts': [
                        {'id': 1, 'account_type': 'savings', 'account_number': '12345', 'balance': 1000.00}
                    ]
                }
            }
        }
    }
})
def get_accounts():
    user_id = get_jwt_identity()
    with Session() as session:
        accounts = session.query(Account).filter_by(user_id=user_id).all()
    return render_template('/dashboard/accounts.html', accounts=accounts)


# GET /accounts/<id>: Retrieve a specific account by ID
@account_controller.route('/accounts/<int:account_id>', methods=['GET'])
@jwt_required()
@swag_from({
    'summary': 'Get account details',
    'description': 'Retrieve details of a specific account by its ID.',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID of the account to retrieve'
        }
    ],
    'responses': {
        200: {
            'description': 'Account details',
            'examples': {
                'application/json': {
                    'account_type': 'savings',
                    'account_number': '12345',
                    'balance': 1000.00
                }
            }
        },
        404: {
            'description': 'Account not found'
        }
    }
})
def get_account(account_id):
    user_id = get_jwt_identity()
    session = Session()
    account = session.query(Account).filter_by(id=account_id, user_id=user_id).first()
    session.close()
    if account:
        return jsonify({
            'account_type': account.account_type,
            'account_number': account.account_number,
            'balance': account.balance
        }), 200
    else:
        flash("Account not found or you are not authorized", "danger")
        return redirect(url_for('account_controller.get_accounts'))


# GET /accounts/<id>/edit: Retrieve an account by ID for editing
@account_controller.route('/accounts/<int:account_id>/edit', methods=['GET'])
@jwt_required()
@swag_from({
    'summary': 'Edit account',
    'description': 'Retrieve a specific account by ID for editing.',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID of the account to edit'
        }
    ],
    'responses': {
        200: {
            'description': 'Account edit page'
        },
        404: {
            'description': 'Account not found'
        }
    }
})
def edit_account(account_id):
    user_id = get_jwt_identity()
    session = Session()
    account = session.query(Account).filter_by(id=account_id, user_id=user_id).first()
    session.close()
    
    if account:
        return render_template('/dashboard/edit_account.html', account=account)
    else:
        flash("Account not found or you are not authorized", "danger")
        return redirect(url_for('account_controller.get_accounts'))


# POST /accounts: Create a new account for the user
@account_controller.route('/accounts', methods=['POST'])
@jwt_required()
@swag_from({
    'summary': 'Create a new account',
    'description': 'Create a new account for the authenticated user.',
    'parameters': [
        {
            'name': 'account_type',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'Type of the account (e.g., savings, checking)'
        },
        {
            'name': 'account_number',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'Unique account number'
        },
        {
            'name': 'balance',
            'in': 'formData',
            'type': 'number',
            'required': True,
            'description': 'Initial balance for the account'
        }
    ],
    'responses': {
        201: {
            'description': 'Account created successfully'
        },
        400: {
            'description': 'Invalid input data'
        }
    }
})
def create_account():
    user_id = get_jwt_identity()
    account_type = request.form.get('account_type')
    account_number = request.form.get('account_number')
    balance = request.form.get('balance')

    session = Session()
    new_account = Account(user_id=user_id, account_type=account_type, account_number=account_number, balance=balance)
    session.add(new_account)
    session.commit()
    session.close()
    flash("Account created successfully!", "success")
    return redirect(url_for('account_controller.get_accounts'))


# PUT /accounts/<id>: Update an account
@account_controller.route('/accounts/<int:account_id>', methods=['POST'])
@jwt_required()
@swag_from({
    'summary': 'Update account',
    'description': 'Update details of a specific account by its ID.',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID of the account to update'
        },
        {
            'name': 'account_type',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'New account type'
        },
        {
            'name': 'account_number',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'New account number'
        },
        {
            'name': 'balance',
            'in': 'formData',
            'type': 'number',
            'required': False,
            'description': 'New account balance'
        }
    ],
    'responses': {
        200: {
            'description': 'Account updated successfully'
        },
        404: {
            'description': 'Account not found'
        }
    }
})
def update_account(account_id):
    if request.form.get('_method') == 'PUT':
        user_id = get_jwt_identity()
        session = Session()
        account = session.query(Account).filter_by(id=account_id, user_id=user_id).first()

        if account:
            account.account_type = request.form.get('account_type', account.account_type)
            account.account_number = request.form.get('account_number', account.account_number)
            account.balance = request.form.get('balance', account.balance)
            session.commit()
            flash("Account updated successfully!", "success")
        else:
            flash("Account not found or you are not authorized", "danger")
        session.close()
    return redirect(url_for('account_controller.get_accounts'))


# DELETE /accounts/<id>: Delete an account
@account_controller.route('/accounts/accounts/<int:account_id>', methods=['POST'])
@jwt_required()
@swag_from({
    'summary': 'Delete account',
    'description': 'Delete a specific account by its ID.',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID of the account to delete'
        }
    ],
    'responses': {
        200: {
            'description': 'Account deleted successfully'
        },
        404: {
            'description': 'Account not found'
        }
    }
})
def delete_account(account_id):
    user_id = get_jwt_identity()
    session = Session()

    # Check if the method is actually DELETE
    if request.method == 'POST':
        account = session.query(Account).filter_by(id=account_id, user_id=user_id).first()
        if account:
            session.delete(account)
            session.commit()
            flash("Account deleted successfully", "success")
        else:
            flash("Account not found or you are not authorized", "danger")
        session.close()

    return redirect(url_for('account_controller.get_accounts'))
