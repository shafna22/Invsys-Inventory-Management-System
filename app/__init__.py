from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    """Application factory function."""
    app = Flask(__name__, static_folder='static', template_folder='templates')

    # ✅ Load configurations safely
    try:
        app.config.from_object(Config)
    except Exception as e:
        app.logger.error(f"Error loading configuration: {e}")

    # ✅ Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # ✅ Set login view
    login_manager.login_view = "main.login"
    login_manager.login_message_category = "info"

    # ✅ Import Blueprints inside the function to avoid circular imports
    from app.routes import main_bp, admin_bp, staff_bp

    # ✅ Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')  # ✅ Admin routes
    app.register_blueprint(staff_bp, url_prefix='/staff')  # ✅ Staff routes

    # ✅ Set up user loader within app context
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    return app
