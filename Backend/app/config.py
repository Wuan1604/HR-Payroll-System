import os
from dotenv import load_dotenv

# Load các biến từ file .env
load_dotenv()

class Config:
    # 1. SQL Server - Lấy hoàn toàn từ ENV, nếu không có thì để chuỗi rỗng
    SQL_SERVER_CONN = os.getenv('SQL_SERVER_CONN', "")

    # 2. MySQL - Tất cả các key đều lấy từ ENV
    MYSQL_CONFIG = {
        'host':     os.getenv('MYSQL_HOST'),
        'user':     os.getenv('MYSQL_USER'),
        'password': os.getenv('MYSQL_PASSWORD'),
        'database': os.getenv('MYSQL_DB'),
      'port':     int(os.getenv('MYSQL_PORT'))
    }

    # 3. Email & Security
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', "")
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', "")
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_default_key')