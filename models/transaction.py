from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from connector.db import Base

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    from_account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    to_account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    type = Column(String(255), nullable=False)  # e.g., deposit, withdrawal, transfer
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Define relationships
    from_account = relationship("Account", foreign_keys=[from_account_id], back_populates="transactions_from")
    to_account = relationship("Account", foreign_keys=[to_account_id], back_populates="transactions_to")
