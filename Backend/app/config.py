import os
from dotenv import load_dotenv

# Load các biến từ file .env nếu có
load_dotenv()

class Config:
    # 1. Cấu hình SQL Server (Lấy từ chuỗi kết nối cũ của bạn)
  
    SQL_SERVER_CONN = os.getenv(
        'SQL_SERVER_CONN', 
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-QURO3OM;DATABASE=HUMAN_2025;trusted_connection=yes"
    )
    
    # 2. Cấu hình MySQL
    
    MYSQL_CONFIG = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DB', 'payroll'),
        'port': 3306
    }

    # 3. Cấu hình Email 
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', "16.nguyenquan2004@gmail.com")
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', "dasw ctzo hzwe oyqg")

    # 4. Các cấu hình khác của Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key_hr_payroll')

  