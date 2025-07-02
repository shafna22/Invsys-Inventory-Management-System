import os

# Base directory (absolute path of the project)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')

# Ensure the instance directory exists
os.makedirs(INSTANCE_DIR, exist_ok=True)  # `exist_ok=True` prevents errors

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback_secret_key_change_this!')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(INSTANCE_DIR, 'inventory.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ✅ Set upload folder path (correct format)
    PROFILE_PICTURE_FOLDER = os.path.join('static', 'uploads', 'profile_pics')