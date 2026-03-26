from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import pandas as pd

import models
import schemas
from database import engine, SessionLocal

import requests
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

# Create tables
models.Base.metadata.create_all(bind=engine)

def fetch_bitcoin_price():
    print(f"Tick... Fetching Bitcoin price at {datetime.datetime.now()}")
    
    # --- CHANGE START ---
    # We are switching to CoinGecko
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    
    try:
        response = requests.get(url, timeout=10) # Added timeout so it doesn't freeze forever
        data = response.json()
        
        # CoinGecko returns: {'bitcoin': {'usd': 96500}}
        price = data['bitcoin']['usd'] 
    # --- CHANGE END ---

    except Exception as e:
        print(f"Error fetching price: {e}")
        return

    # ... (Rest of the database saving code stays the same) ...
    db = SessionLocal()
    try:
        price_record = models.Transaction(
            symbol="BTC", 
            price=price, 
            quantity=0.0 
        )
        db.add(price_record)
        db.commit()
        print(f"Saved BTC Price: ${price}")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        db.close()

# app = FastAPI()

# 1. Create the Scheduler
scheduler = BackgroundScheduler()

# 2. Define the Lifespan Context Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    print("Starting Scheduler...")
    # Add the job: Run 'fetch_bitcoin_price' every 10 seconds (for testing)
    # In production, you would change this to: hours=1
    scheduler.add_job(fetch_bitcoin_price, 'interval', hours=1)
    scheduler.start()
    
    yield # The app runs here
    
    # --- SHUTDOWN LOGIC ---
    print("Stopping Scheduler...")
    scheduler.shutdown()

# 3. Initialize App with Lifespan
app = FastAPI(lifespan=lifespan)


# Database Dependency (The Boilerplate)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- THE CRUD ENDPOINTS ---

# 1. CREATE (POST): Add a new transaction
@app.post("/transactions/", response_model=schemas.Transaction)
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    # Step A: Create the SQLAlchemy Model instance
    # We unpack the Pydantic data (**transaction.dict()) into the Model
    db_transaction = models.Transaction(**transaction.dict())
    
    # Step B: Add to the session
    db.add(db_transaction)
    
    # Step C: Commit (Save) to the DB
    db.commit()
    
    # Step D: Refresh (Get the ID that the DB just assigned)
    db.refresh(db_transaction)
    
    return db_transaction

# 2. READ (GET): Get all transactions
@app.get("/transactions/", response_model=List[schemas.Transaction])
def read_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Query the database using SQLAlchemy syntax
    # This is equivalent to: SELECT * FROM transactions LIMIT 100 OFFSET 0
    transactions = db.query(models.Transaction).offset(skip).limit(limit).all()
    return transactions


# 3. ANALYTICS (GET): The "Analyst Special"
@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    # Step A: Read data from SQL directly into Pandas
    # We use 'db.bind' to access the connection engine
    # We use a raw SQL query string because you are comfortable with SQL
    stmt = "SELECT * FROM transactions"
    df = pd.read_sql(stmt, db.bind)

    # Step B: Handle empty database case
    if df.empty:
        return {"message": "No data available for analysis"}

    # Step C: Perform Analysis (The "Analyst Logic")
    # Let's calculate the current value of each holding
    df['current_value'] = df['price'] * df['quantity']

    # Aggregate metrics
    total_portfolio_value = df['current_value'].sum()
    average_buy_price = df['price'].mean()
    most_traded_asset = df['symbol'].mode()[0]

    # Step D: Return JSON
    # We round the numbers to make them pretty for the API
    return {
        "total_portfolio_value": round(total_portfolio_value, 2),
        "average_buy_price": round(average_buy_price, 2),
        "most_traded_asset": most_traded_asset,
        "transaction_count": int(len(df)) # Convert numpy int to python int for JSON
    }