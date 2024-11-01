from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define Base
Base = declarative_base()

# Database Configuration
DB_CONFIG = {
    "host": os.getenv('DB_HOST', 'localhost'),
    "port": os.getenv('DB_PORT', '3306'),
    "user": os.getenv('DB_USER', 'root'),
    "password": os.getenv('DB_PASSWORD', 'password'),
    "name": os.getenv('DB_NAME', 'bank-flask'),
}

# Create engine
engine = create_engine(
    f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['name']}"
)
Session = sessionmaker(bind=engine)

# Test connection
def test_connection():
    try:
        with engine.connect() as connection:
            print("Database connection successful!")
    except SQLAlchemyError as e:
        print(f"Failed to connect to the database: {e}")

if __name__ == "__main__":
    test_connection()
