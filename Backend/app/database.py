import pyodbc
import mysql.connector
from .config import Config

# Hàm kết nối SQL Server (Lấy thông tin nhân sự)
def get_sqlserver_connection():
    try:
        return pyodbc.connect(Config.SQL_SERVER_CONN)
    except Exception as e:
        print(f"❌ Lỗi kết nối SQL Server (Human): {e}")
        return None

# Hàm kết nối MySQL (Lấy thông tin lương)
def get_mysql_connection():
    try:
        # Giải nén dictionary MYSQL_CONFIG vào hàm connect
        return mysql.connector.connect(**Config.MYSQL_CONFIG)
    except Exception as e:
        print(f"❌ Lỗi kết nối MySQL (Payroll): {e}")
        return None