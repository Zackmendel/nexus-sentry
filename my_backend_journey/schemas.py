from pydantic import BaseModel

# 1. The Base Schema
# These are the fields that are common to creating and reading
class TransactionBase(BaseModel):
    symbol: str  # e.g., "BTC"
    price: float
    quantity: float

# 2. The Create Schema
# This is exactly what we expect the user to send us when creating a transaction.
# It looks just like the Base for now.
class TransactionCreate(TransactionBase):
    pass

# 3. The Response Schema
# This is what we send BACK to the user.
# It includes the 'id' because the database has created it by now.
class Transaction(TransactionBase):
    id: int

    class Config:
        # This config line tells Pydantic to read the data even if it's 
        # coming from an ORM (SQLAlchemy) object, not just a dict.
        orm_mode = True