import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-secret-key')
    
    # Default XAMPP MySQL Database URL: root with no password on localhost:3306
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'mysql+pymysql://root:@localhost:3306/stratlearn'
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Optional debug flag
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
