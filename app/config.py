# app/config.py
import os
from dotenv import load_dotenv

# load environment variables from a .env file if present
load_dotenv()

class Config:
    DEBUG = True
    
    # use environment variables for database configuration
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'kiwi_app')

    # SQLAlchemy database URI
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    # other configurations
    SQLALCHEMY_TRACK_MODIFICATIONS = False
