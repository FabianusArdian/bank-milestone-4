from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from connector.db import Base

class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    account_type = Column(String(255), nullable=False)
    account_number = Column(String(255), unique=True, nullable=False)
    balance = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="accounts")
    transactions_from = relationship("Transaction", foreign_keys='Transaction.from_account_id', back_populates="from_account")
    transactions_to = relationship("Transaction", foreign_keys='Transaction.to_account_id', back_populates="to_account")
