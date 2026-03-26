from flask import Flask
from flask_cors import CORS

from .config import Config
from .routes import human_bp, payroll_bp, auth_bp

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    CORS(app, supports_credentials=True)

    # Đăng ký các Blueprint
    app.register_blueprint(human_bp, url_prefix='/api/human')
    app.register_blueprint(payroll_bp, url_prefix='/api/payroll')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    return app