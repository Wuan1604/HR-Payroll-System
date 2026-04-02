from flask import Blueprint, jsonify, request
from app.database import get_sqlserver_connection, get_mysql_connection
from app.auth import login_required
import pyodbc

human_bp = Blueprint('human', __name__)

# ---------------------------------------------------------
# 1. LẤY DANH SÁCH NHÂN VIÊN (SQL Server)
# ---------------------------------------------------------
@human_bp.route('/employees-page', methods=['GET'])
@login_required
def get_employees():
    conn = get_sqlserver_connection()
    if not conn: 
        return jsonify({"error": "Không thể kết nối SQL Server"}), 500
    
    cursor = conn.cursor()
    try:
        # Join để lấy tên phòng ban và chức vụ hiển thị lên bảng
        cursor.execute("""
            SELECT e.EmployeeID, e.FullName, e.DateOfBirth, e.Gender, e.PhoneNumber, e.Email, e.HireDate,
                   e.DepartmentID, e.PositionID, e.Status,
                   d.DepartmentName, p.PositionName
            FROM [HUMAN_2025].[dbo].[Employees] e
            LEFT JOIN [HUMAN_2025].[dbo].[Departments] d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN [HUMAN_2025].[dbo].[Positions] p ON e.PositionID = p.PositionID
        """)
        rows = cursor.fetchall()
        employees = [{
            "EmployeeID": r[0], 
            "FullName": r[1],
            "DateOfBirth": r[2].isoformat() if r[2] else None,
            "Gender": r[3], 
            "PhoneNumber": r[4], 
            "Email": r[5],
            "HireDate": r[6].isoformat() if r[6] else None,
            "DepartmentID": r[7], 
            "PositionID": r[8], 
            "Status": r[9],
            "DepartmentName": r[10], 
            "PositionName": r[11]
        } for r in rows]
        return jsonify({"employees": employees}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 2. LẤY PHÒNG BAN (Từ SQL Server - HUMAN_2025)
# ---------------------------------------------------------
@human_bp.route('/departments', methods=['GET'])
@login_required
def get_departments():
    conn = get_sqlserver_connection()
    if not conn: return jsonify({"error": "Lỗi kết nối SQL Server"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DepartmentID, DepartmentName FROM [HUMAN_2025].[dbo].[Departments]")
        data = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        return jsonify(data), 200
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 3. LẤY CHỨC VỤ (Từ SQL Server - HUMAN_2025)
# ---------------------------------------------------------
@human_bp.route('/positions', methods=['GET'])
@login_required
def get_positions():
    conn = get_sqlserver_connection()
    if not conn: return jsonify({"error": "Lỗi kết nối SQL Server"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT PositionID, PositionName FROM [HUMAN_2025].[dbo].[Positions]")
        data = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        return jsonify(data), 200
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 4. THÊM NHÂN VIÊN & ĐỒNG BỘ (SQL Server -> MySQL)
# ---------------------------------------------------------
@human_bp.route('/add-employee', methods=['POST'])
@login_required
def add_employee():
    data = request.json
    
    # Kiểm tra Status hợp lệ
    VALID_STATUSES = ["Đang làm việc", "Thử việc", "Đã nghỉ việc", "Tạm hoãn"]
    user_status = data.get("Status")
    if user_status not in VALID_STATUSES:
        return jsonify({"error": "Trạng thái không hợp lệ"}), 400

    sql_conn = get_sqlserver_connection()
    my_conn = get_mysql_connection()
    
    if not sql_conn or not my_conn:
        return jsonify({"error": "Kết nối Database thất bại"}), 500

    sql_cursor = sql_conn.cursor()
    my_cursor = my_conn.cursor()
    
    try:
        # Bước 1: Chèn vào SQL Server
        sql_query = """
            INSERT INTO [HUMAN_2025].[dbo].[Employees] 
            (FullName, DateOfBirth, Gender, PhoneNumber, Email, HireDate, DepartmentID, PositionID, Status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        sql_values = (
            data.get("FullName"), data.get("DateOfBirth"), data.get("Gender"), 
            data.get("PhoneNumber"), data.get("Email"), data.get("HireDate"), 
            data.get("DepartmentID"), data.get("PositionID"), user_status
        )
        sql_cursor.execute(sql_query, sql_values)
        
        # Lấy EmployeeID vừa tự động sinh ra trong SQL Server
        sql_cursor.execute("SELECT @@IDENTITY")
        new_employee_id = int(sql_cursor.fetchone()[0])
        
        sql_conn.commit()

        # Bước 2: Đồng bộ sang MySQL (Bảng employees_payroll)
        # Lưu ý dùng đúng tên bảng 'employees_payroll' theo file sql của bạn
        my_query = """
            INSERT INTO employees_payroll (EmployeeID, FullName, DepartmentID, PositionID, Status)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                FullName = VALUES(FullName), 
                Status = VALUES(Status),
                DepartmentID = VALUES(DepartmentID),
                PositionID = VALUES(PositionID)
        """
        my_values = (
            new_employee_id, # Dùng ID từ SQL Server để đồng nhất
            data.get("FullName"), 
            data.get("DepartmentID"), 
            data.get("PositionID"), 
            user_status
        )
        my_cursor.execute(my_query, my_values)
        my_conn.commit()
        
        return jsonify({"message": "Thêm mới và đồng bộ thành công!", "id": new_employee_id}), 200

    except Exception as e:
        if sql_conn: sql_conn.rollback()
        if my_conn: my_conn.rollback()
        return jsonify({"error": f"Lỗi hệ thống: {str(e)}"}), 500
    finally:
        sql_cursor.close()
        my_cursor.close()
        sql_conn.close()
        my_conn.close()

# ---------------------------------------------------------
# 5. BÁO CÁO NHÂN SỰ
# ---------------------------------------------------------
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