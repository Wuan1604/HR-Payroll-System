import pyodbc
import mysql.connector
from .config import Config


def get_sqlserver_connection():
    try:
        return pyodbc.connect(Config.SQL_SERVER_CONN)
    except Exception as e:
        print(f"❌ Lỗi kết nối SQL Server (Human): {e}")
        return None


def get_mysql_connection():
    try:
        return mysql.connector.connect(**Config.MYSQL_CONFIG)
    except Exception as e:
        print(f"❌ Lỗi kết nối MySQL (Payroll): {e}")
        return None


def get_auth_connection():
    try:
        return mysql.connector.connect(**Config.AUTH_MYSQL_CONFIG)
    except Exception as e:
        print(f"❌ Lỗi kết nối MySQL (Auth): {e}")
        return None
