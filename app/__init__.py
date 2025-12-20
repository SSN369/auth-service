# In app/__init__.py

from flask import Flask
from flask_cors import CORS
from config import Config
from .extension import db, bcrypt, jwt, ma # <-- Import from new file

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)

    # Configure CORS
    CORS(app, supports_credentials=True)

    with app.app_context():
        # Import and register blueprints
        from .routes.auth_routes import auth_bp
        # You can also import models here if needed for db.create_all() etc.
        # from . import models

        app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
