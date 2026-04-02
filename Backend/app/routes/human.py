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
       
# ---------------------------------------------------------
# 6.QUẢN LÝ PHÒNG BAN (DEPARTMENTS) - CRUD & SYNC
# ---------------------------------------------------------

@human_bp.route('/show-department', methods=['GET'])
@login_required
def show_departments():
    conn = get_sqlserver_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DepartmentID, DepartmentName FROM [HUMAN_2025].[dbo].[Departments]")
    data = [{"DepartmentID": r[0], "DepartmentName": r[1]} for r in cursor.fetchall()]
    conn.close()
    return jsonify(data), 200

@human_bp.route('/add-department', methods=['POST'])
@login_required
def add_department():
    name = request.json.get('DepartmentName')
    sql_conn = get_sqlserver_connection()
    my_conn = get_mysql_connection()
    sql_cursor = sql_conn.cursor()
    my_cursor = my_conn.cursor()
    try:
        # 1. Thêm vào SQL Server
        sql_cursor.execute("INSERT INTO [HUMAN_2025].[dbo].[Departments] (DepartmentName) VALUES (?)", (name))
        sql_cursor.execute("SELECT @@IDENTITY")
        new_id = int(sql_cursor.fetchone()[0])
        sql_conn.commit()

        # 2. Đồng bộ sang MySQL (Bảng departments_payroll)
        my_cursor.execute("INSERT INTO departments_payroll (DepartmentID, DepartmentName) VALUES (%s, %s)", (new_id, name))
        my_conn.commit()
        return jsonify({"message": "Thêm thành công", "id": new_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        sql_conn.close()
        my_conn.close()

@human_bp.route('/update-department', methods=['PUT'])
@login_required
def update_department():
    data = request.json # {DepartmentID, DepartmentName}
    sql_conn = get_sqlserver_connection()
    my_conn = get_mysql_connection()
    try:
        # Update SQL Server
        sql_conn.cursor().execute("UPDATE [HUMAN_2025].[dbo].[Departments] SET DepartmentName = ? WHERE DepartmentID = ?", 
                                   (data['DepartmentName'], data['DepartmentID']))
        sql_conn.commit()
        # Update MySQL
        my_conn.cursor().execute("UPDATE departments_payroll SET DepartmentName = %s WHERE DepartmentID = %s", 
                                  (data['DepartmentName'], data['DepartmentID']))
        my_conn.commit()
        return jsonify({"message": "Cập nhật thành công"}), 200
    finally:
        sql_conn.close()
        my_conn.close()

@human_bp.route('/delete-department/<int:id>', methods=['DELETE'])
@login_required
def delete_department(id):
    sql_conn = get_sqlserver_connection()
    my_conn = get_mysql_connection()
    sql_cursor = sql_conn.cursor()
    try:
        # Kiểm tra ràng buộc nhân viên trước khi xóa
        sql_cursor.execute("SELECT COUNT(*) FROM [HUMAN_2025].[dbo].[Employees] WHERE DepartmentID = ?", (id))
        if sql_cursor.fetchone()[0] > 0:
            return jsonify({"error": "Không thể xóa phòng ban đang có nhân viên"}), 400
        
        sql_cursor.execute("DELETE FROM [HUMAN_2025].[dbo].[Departments] WHERE DepartmentID = ?", (id))
        sql_conn.commit()
        # Xóa bên MySQL
        my_conn.cursor().execute("DELETE FROM departments_payroll WHERE DepartmentID = %s", (id))
        my_conn.commit()
        return jsonify({"message": "Xóa thành công"}), 200
    finally:
        sql_conn.close()
        my_conn.close()

# ---------------------------------------------------------
# 7.QUẢN LÝ CHỨC VỤ (POSITIONS) - CRUD & SYNC
# ---------------------------------------------------------

@human_bp.route('/show-human', methods=['GET'])
@login_required
def show_positions():
    conn = get_sqlserver_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT PositionID, PositionName FROM [HUMAN_2025].[dbo].[Positions]")
    data = [{"PositionID": r[0], "PositionName": r[1]} for r in cursor.fetchall()]
    conn.close()
    return jsonify(data), 200

@human_bp.route('/add-position', methods=['POST'])
@login_required
def add_position():
    name = request.json.get('PositionName')
    sql_conn = get_sqlserver_connection()
    my_conn = get_mysql_connection()
    sql_cursor = sql_conn.cursor()
    try:
        # SQL Server
        sql_cursor.execute("INSERT INTO [HUMAN_2025].[dbo].[Positions] (PositionName) VALUES (?)", (name))
        sql_cursor.execute("SELECT @@IDENTITY")
        new_id = int(sql_cursor.fetchone()[0])
        sql_conn.commit()
        # MySQL
        my_conn.cursor().execute("INSERT INTO positions_payroll (PositionID, PositionName) VALUES (%s, %s)", (new_id, name))
        my_conn.commit()
        return jsonify({"message": "Thêm chức vụ thành công"}), 201
    finally:
        sql_conn.close()
        my_conn.close()