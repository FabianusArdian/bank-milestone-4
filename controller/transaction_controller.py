from flask import Blueprint, request, flash, redirect, url_for, render_template
from models.transaction import Transaction
from models.account import Account
from models.user import User
from connector.db import Session
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from decimal import Decimal
from sqlalchemy import or_
from flasgger import swag_from

transaction_controller = Blueprint('transaction_controller', __name__)

# GET /transactions: Retrieve all transactions for the user's accounts
@transaction_controller.route('/transactions', methods=['GET'])
@jwt_required()
@swag_from({
    'summary': 'Retrieve all transactions',
    'description': 'Retrieve all transactions for the authenticated user\'s accounts, with optional filters.',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'description': 'Optional filter to retrieve transactions for a specific account'
        },
        {
            'name': 'start_date',
            'in': 'query',
            'type': 'string',
            'format': 'date-time',
            'required': False,
            'description': 'Optional filter to specify the start date for transactions'
        },
        {
            'name': 'end_date',
            'in': 'query',
            'type': 'string',
            'format': 'date-time',
            'required': False,
            'description': 'Optional filter to specify the end date for transactions'
        },
        {
            'name': 'type',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Optional filter to retrieve transactions of a specific type'
        }
    ],
    'responses': {
        200: {
            'description': 'List of transactions for the authenticated user'
        }
    }
})
def get_transactions():
    user_id = get_jwt_identity()
    account_id = request.args.get('account_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    transaction_type = request.args.get('type')  # Get transaction type from query parameters

    session = Session()
    query = session.query(Transaction).join(
        Account, or_(
            Transaction.from_account_id == Account.id,
            Transaction.to_account_id == Account.id
        )
    ).filter(Account.user_id == user_id)

    if account_id:
        query = query.filter(
            or_(
                Transaction.from_account_id == account_id,
                Transaction.to_account_id == account_id
            )
        )
    if start_date and end_date:
        query = query.filter(Transaction.created_at.between(start_date, end_date))
    if transaction_type:  # Filter by transaction type if provided
        query = query.filter(Transaction.type == transaction_type)

    transactions = query.all()
    accounts = session.query(Account).filter_by(user_id=user_id).all()
    session.close()

    return render_template('/dashboard/transactions.html', transactions=transactions, accounts=accounts)


# GET /transactions/<id>: Retrieve details of a specific transaction
@transaction_controller.route('/transactions/<int:transaction_id>', methods=['GET'])
@jwt_required()
@swag_from({
    'summary': 'Retrieve transaction details',
    'description': 'Retrieve details of a specific transaction by its ID.',
    'parameters': [
        {
            'name': 'transaction_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID of the transaction to retrieve'
        }
    ],
    'responses': {
        200: {
            'description': 'Details of the specified transaction',
            'examples': {
                'application/json': {
                    'id': 1,
                    'type': 'transfer',
                    'from_account_id': 1,
                    'to_account_id': 2,
                    'amount': 50.00,
                    'description': 'Transfer to account 2',
                    'created_at': '2024-01-01T10:00:00'
                }
            }
        },
        404: {
            'description': 'Transaction not found or unauthorized access'
        }
    }
})
def get_transaction(transaction_id):
    user_id = get_jwt_identity()
    session = Session()
    transaction = session.query(Transaction).join(Account).filter(
        Transaction.id == transaction_id,
        (Transaction.from_account_id == Account.id) | (Transaction.to_account_id == Account.id),
        Account.user_id == user_id
    ).first()
    session.close()

    if transaction:
        return render_template('/dashboard/view_transaction.html', transaction=transaction)
    else:
        flash("Transaction not found or you are not authorized", "danger")
        return redirect(url_for('transaction_controller.get_transactions'))

# POST /transactions: Initiate a new transaction
@transaction_controller.route('/transactions', methods=['POST'])
@jwt_required()
@swag_from({
    'summary': 'Initiate a new transaction',
    'description': 'Create a new transaction (deposit, withdrawal, or transfer) for the authenticated user.',
    'parameters': [
        {
            'name': 'type',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'Type of transaction (deposit, withdrawal, transfer)'
        },
        {
            'name': 'from_account_id',
            'in': 'formData',
            'type': 'integer',
            'required': True,
            'description': 'Account ID from which funds will be withdrawn or deposited'
        },
        {
            'name': 'to_account_id',
            'in': 'formData',
            'type': 'integer',
            'required': False,
            'description': 'Account ID to which funds will be transferred or deposited (if applicable)'
        },
        {
            'name': 'amount',
            'in': 'formData',
            'type': 'number',
            'format': 'float',
            'required': True,
            'description': 'Amount of money to be transacted'
        },
        {
            'name': 'description',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'Description of the transaction'
        },
        {
            'name': 'confirm_password',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'Confirm password for transaction'
        }
    ],
    'responses': {
        201: {
            'description': 'Transaction completed successfully'
        },
        400: {
            'description': 'Invalid transaction request'
        }
    }
})
def create_transaction():
    user_id = get_jwt_identity()
    transaction_type = request.form.get('type')
    from_account_id = request.form.get('from_account_id')
    to_account_id = request.form.get('to_account_id') if transaction_type in ["transfer", "deposit"] else None
    amount = Decimal(request.form.get('amount'))
    description = request.form.get('description', '')
    confirm_password = request.form.get('confirm_password')

    session = Session()

    user = session.query(User).filter_by(id=user_id).first()
    if not user or not user.check_password(confirm_password):
        flash("Password confirmation failed.", "danger")
        session.close()
        return redirect(url_for('transaction_controller.get_transactions'))

    from_account = session.query(Account).filter_by(id=from_account_id, user_id=user_id).first() if from_account_id else None
    to_account = session.query(Account).filter_by(id=to_account_id, user_id=user_id).first() if to_account_id else None

    if transaction_type == "deposit" and to_account:
        to_account.balance += amount

    elif transaction_type == "withdrawal" and from_account:
        if from_account.balance >= amount:
            from_account.balance -= amount
        else:
            flash("Insufficient funds for withdrawal", "danger")
            session.close()
            return redirect(url_for('transaction_controller.get_transactions'))

    elif transaction_type == "transfer" and from_account and to_account:
        if from_account.balance >= amount:
            from_account.balance -= amount
            to_account.balance += amount
        else:
            flash("Insufficient funds for transfer", "danger")
            session.close()
            return redirect(url_for('transaction_controller.get_transactions'))

    else:
        flash("Invalid accounts selected or unauthorized access", "danger")
        session.close()
        return redirect(url_for('transaction_controller.get_transactions'))

    transaction = Transaction(
        type=transaction_type,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        amount=amount,
        description=description,
        created_at=datetime.utcnow()
    )
    session.add(transaction)
    session.commit()
    flash("Transaction completed successfully", "success")

    session.close()
    return redirect(url_for('transaction_controller.get_transactions'))
