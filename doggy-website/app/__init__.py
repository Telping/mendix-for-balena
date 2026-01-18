from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix
import os

db = SQLAlchemy()
migrate = Migrate()

class ReverseProxied:
    """Middleware to handle reverse proxy with URL prefix.

    Sets SCRIPT_NAME so Flask's url_for() generates correct URLs with prefix.
    Nginx strips the prefix before forwarding, so we just set SCRIPT_NAME
    without modifying PATH_INFO.
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Get X-Script-Name header from nginx (e.g., /doggy)
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
        return self.app(environ, start_response)

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///boxty.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

    # Handle reverse proxy - order matters!
    # 1. First apply ProxyFix to handle X-Forwarded-* headers
    # 2. Then apply ReverseProxied to set SCRIPT_NAME for url_for()
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.wsgi_app = ReverseProxied(app.wsgi_app)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)

    # Create tables
    with app.app_context():
        db.create_all()

    return app
