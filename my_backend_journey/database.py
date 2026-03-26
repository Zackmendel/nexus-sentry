from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Create the Database URL
# For SQLite, it's just a file path.
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# 2. Create the Engine
# The "check_same_thread" arg is needed only for SQLite.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Create a SessionLocal class
# Each instance of this class will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create a Base class
# All your database models will inherit from this class.
Base = declarative_base()