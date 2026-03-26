from sqlalchemy import Column, Integer, String, Float
from database import Base

class Transaction(Base):
    # 1. Name the table in the database
    __tablename__ = "transactions"

    # 2. Define Columns
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True) # e.g., "BTC"
    price = Column(Float)               # e.g., 50000.50
    quantity = Column(Float)            # e.g., 0.5
    
    # You don't need to write "CREATE TABLE..." 
    # SQLAlchemy will read this and do it for you.