import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQL_SERVER_CONN = os.getenv('SQL_SERVER_CONN', '')

    MYSQL_CONFIG = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DB', 'payroll'),
        'port': int(os.getenv('MYSQL_PORT', '3306')),
    }

    AUTH_MYSQL_CONFIG = {
        'host': os.getenv('AUTH_MYSQL_HOST', os.getenv('MYSQL_HOST', 'localhost')),
        'user': os.getenv('AUTH_MYSQL_USER', os.getenv('MYSQL_USER', 'root')),
        'password': os.getenv('AUTH_MYSQL_PASSWORD', os.getenv('MYSQL_PASSWORD', '')),
        'database': os.getenv('AUTH_MYSQL_DB', 'hr_auth'),
        'port': int(os.getenv('AUTH_MYSQL_PORT', os.getenv('MYSQL_PORT', '3306'))),
    }

    SENDER_EMAIL = os.getenv('SENDER_EMAIL', '')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_default_key')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    PASSWORD_RESET_EXPIRES_MINUTES = int(os.getenv('PASSWORD_RESET_EXPIRES_MINUTES', '30'))
