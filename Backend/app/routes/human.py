from flask import Blueprint, jsonify, request
from app.database import get_sqlserver_connection, get_mysql_connection
from app.auth import login_required
import pyodbc

human_bp = Blueprint('human', __name__)

# ---------------------------
# 1. LẤY DANH SÁCH NHÂN VIÊN
# ---------------------------
@human_bp.route('/employees-page', methods=['GET'])
@login_required
def get_employees():
    conn = get_sqlserver_connection()
    if not conn: 
        return jsonify({"error": "Không thể kết nối SQL Server"}), 500
    
    cursor = conn.cursor()
    try:
        
        cursor.execute("""
            SELECT e.EmployeeID, e.FullName, e.DateOfBirth, e.Gender, e.PhoneNumber, e.Email, e.HireDate,
                   e.DepartmentID, e.PositionID, e.Status, e.CreatedAt, e.UpdatedAt,
                   d.DepartmentName, p.PositionName
            FROM [HUMAN_2025].[dbo].[Employees] e
            LEFT JOIN [HUMAN_2025].[dbo].[Departments] d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN [HUMAN_2025].[dbo].[Positions] p ON e.PositionID = p.PositionID
        """)
        rows = cursor.fetchall()
        employees = [{
            "EmployeeID": r[0], "FullName": r[1],
            "DateOfBirth": r[2].isoformat() if r[2] else None,
            "Gender": r[3], "PhoneNumber": r[4], "Email": r[5],
            "HireDate": r[6].isoformat() if r[6] else None,
            "DepartmentID": r[7], "PositionID": r[8], "Status": r[9],
            "DepartmentName": r[12], "PositionName": r[13]
        } for r in rows]
        return jsonify({"employees": employees}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------
# 2. THÊM NHÂN VIÊN & ĐỒNG BỘ
# ---------------------------
@human_bp.route('/add-employee', methods=['POST'])
@login_required
def add_employee():
    data = request.json
    sql_conn = get_sqlserver_connection()
    my_conn = get_mysql_connection()
    
    if not sql_conn or not my_conn:
        return jsonify({"error": "Kết nối Database thất bại"}), 500

    sql_cursor = sql_conn.cursor()
    my_cursor = my_conn.cursor()
    
    try:
        # Bước 1: Lưu vào SQL Server [HUMAN_2025]
        sql_cursor.execute("""
            INSERT INTO [HUMAN_2025].[dbo].[Employees] 
            (FullName, DateOfBirth, Gender, PhoneNumber, Email, HireDate, DepartmentID, PositionID, Status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data.get("FullName"), data.get("DateOfBirth"), data.get("Gender"), data.get("PhoneNumber"), 
              data.get("Email"), data.get("HireDate"), data.get("DepartmentID"), data.get("PositionID"), data.get("Status")))
        sql_conn.commit()

        # Bước 2: Đồng bộ qua MySQL (payrol)
        # Lưu ý: MySQL không dùng [dbo], chỉ dùng tên bảng
        my_cursor.execute("""
            INSERT INTO employees (FullName, DepartmentID, PositionID, Status)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE FullName = VALUES(FullName), Status = VALUES(Status)
        """, (data.get("FullName"), data.get("DepartmentID"), data.get("PositionID"), data.get("Status")))
        my_conn.commit()
        
        return jsonify({"message": "Thêm mới và đồng bộ thành công!"}), 200
    except Exception as e:
        if sql_conn: sql_conn.rollback()
        if my_conn: my_conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        sql_conn.close()
        my_conn.close()

# ---------------------------
# 3. BÁO CÁO NHÂN SỰ
# ---------------------------
@human_bp.route('/report-human', methods=['GET'])
@login_required
def report_human():
    conn = get_sqlserver_connection()
    if not conn: return jsonify({"error": "DB Error"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM [HUMAN_2025].[dbo].[Employees]")
        total = cursor.fetchone()[0]
        return jsonify({"total_employees": total}), 200
    finally:
        cursor.close()
        conn.close()