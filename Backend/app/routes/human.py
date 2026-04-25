from flask import Blueprint, jsonify, request
from app.database import get_sqlserver_connection, get_mysql_connection, get_auth_connection
from app.auth import roles_required
import pyodbc

human_bp = Blueprint('human', __name__)

# ---------------------------------------------------------
# 0. EMPLOYEE - XEM / SỬA THÔNG TIN CÁ NHÂN
# ---------------------------------------------------------
def _employee_profile_response(row):
    return {
        "EmployeeID": row[0],
        "FullName": row[1],
        "DateOfBirth": row[2].isoformat() if row[2] else None,
        "Gender": row[3],
        "PhoneNumber": row[4],
        "Email": row[5],
        "HireDate": row[6].isoformat() if row[6] else None,
        "DepartmentID": row[7],
        "PositionID": row[8],
        "Status": row[9],
        "DepartmentName": row[10],
        "PositionName": row[11]
    }


@human_bp.route('/my-profile', methods=['GET'])
@roles_required('Employee')
def get_my_profile():
    user = getattr(request, 'current_user', {})
    employee_id = user.get('EmployeeID')

    if not employee_id:
        return jsonify({"error": "Tài khoản Employee chưa liên kết EmployeeID"}), 400

    conn = get_sqlserver_connection()
    if not conn:
        return jsonify({"error": "Không thể kết nối SQL Server"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT e.EmployeeID, e.FullName, e.DateOfBirth, e.Gender, e.PhoneNumber, e.Email, e.HireDate,
                   e.DepartmentID, e.PositionID, e.Status,
                   d.DepartmentName, p.PositionName
            FROM [HUMAN_2025].[dbo].[Employees] e
            LEFT JOIN [HUMAN_2025].[dbo].[Departments] d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN [HUMAN_2025].[dbo].[Positions] p ON e.PositionID = p.PositionID
            WHERE e.EmployeeID = ?
        """, (employee_id,))

        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Không tìm thấy hồ sơ nhân viên của tài khoản này"}), 404

        return jsonify({"employee": _employee_profile_response(row)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@human_bp.route('/my-profile', methods=['PUT'])
@roles_required('Employee')
def update_my_profile():
    user = getattr(request, 'current_user', {})
    employee_id = user.get('EmployeeID')

    if not employee_id:
        return jsonify({"error": "Tài khoản Employee chưa liên kết EmployeeID"}), 400

    data = request.json or {}

    def none_if_blank(value):
        if value is None:
            return None
        value = str(value).strip()
        return value if value else None

    full_name = none_if_blank(data.get("FullName"))
    date_of_birth = none_if_blank(data.get("DateOfBirth"))
    gender = none_if_blank(data.get("Gender"))
    phone_number = none_if_blank(data.get("PhoneNumber"))
    email = none_if_blank(data.get("Email"))

    if full_name is not None and not str(full_name).strip():
        return jsonify({"error": "Họ tên không được để trống"}), 400

    sql_conn = get_sqlserver_connection()
    my_conn = get_mysql_connection()
    auth_conn = get_auth_connection()

    if not sql_conn:
        return jsonify({"error": "Không thể kết nối SQL Server"}), 500

    sql_cursor = sql_conn.cursor()
    my_cursor = my_conn.cursor() if my_conn else None
    auth_cursor = auth_conn.cursor() if auth_conn else None

    try:
        sql_cursor.execute("""
            SELECT EmployeeID
            FROM [HUMAN_2025].[dbo].[Employees]
            WHERE EmployeeID = ?
        """, (employee_id,))

        if not sql_cursor.fetchone():
            return jsonify({"error": "Không tìm thấy hồ sơ nhân viên của tài khoản này"}), 404

        sql_cursor.execute("""
            UPDATE [HUMAN_2025].[dbo].[Employees]
            SET
                FullName = COALESCE(?, FullName),
                DateOfBirth = COALESCE(?, DateOfBirth),
                Gender = COALESCE(?, Gender),
                PhoneNumber = COALESCE(?, PhoneNumber),
                Email = COALESCE(?, Email),
                UpdatedAt = GETDATE()
            WHERE EmployeeID = ?
        """, (
            full_name,
            date_of_birth,
            gender,
            phone_number,
            email,
            employee_id
        ))

        if my_cursor:
            my_cursor.execute("""
                UPDATE employees_payroll
                SET FullName = COALESCE(%s, FullName)
                WHERE EmployeeID = %s
            """, (full_name, employee_id))

        if auth_cursor:
            auth_cursor.execute("""
                UPDATE users
                SET FullName = COALESCE(%s, FullName),
                    Email = COALESCE(%s, Email)
                WHERE UserID = %s
            """, (full_name, email, user.get('UserID')))

        sql_conn.commit()
        if my_conn:
            my_conn.commit()
        if auth_conn:
            auth_conn.commit()

        sql_cursor.execute("""
            SELECT e.EmployeeID, e.FullName, e.DateOfBirth, e.Gender, e.PhoneNumber, e.Email, e.HireDate,
                   e.DepartmentID, e.PositionID, e.Status,
                   d.DepartmentName, p.PositionName
            FROM [HUMAN_2025].[dbo].[Employees] e
            LEFT JOIN [HUMAN_2025].[dbo].[Departments] d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN [HUMAN_2025].[dbo].[Positions] p ON e.PositionID = p.PositionID
            WHERE e.EmployeeID = ?
        """, (employee_id,))

        row = sql_cursor.fetchone()
        return jsonify({
            "message": "Cập nhật thông tin cá nhân thành công",
            "employee": _employee_profile_response(row)
        }), 200

    except Exception as e:
        sql_conn.rollback()
        if my_conn:
            my_conn.rollback()
        if auth_conn:
            auth_conn.rollback()
        return jsonify({"error": f"Lỗi hệ thống: {str(e)}"}), 500

    finally:
        sql_cursor.close()
        if my_cursor:
            my_cursor.close()
        if auth_cursor:
            auth_cursor.close()
        sql_conn.close()
        if my_conn:
            my_conn.close()
        if auth_conn:
            auth_conn.close()


# ---------------------------------------------------------
# 1. LẤY DANH SÁCH NHÂN VIÊN (SQL Server)
# ---------------------------------------------------------
@human_bp.route('/employees-page', methods=['GET'])
@roles_required('Admin', 'Manager')
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
@roles_required('Admin')
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
@roles_required('Admin')
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
@roles_required('Admin')
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
        
        sql_cursor.execute("SELECT @@IDENTITY")
        new_employee_id = int(sql_cursor.fetchone()[0])
        
        sql_conn.commit()

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
# 4.1. SỬA NHÂN VIÊN & ĐỒNG BỘ SQL Server -> MySQL
# ---------------------------------------------------------
@human_bp.route('/update-employee', methods=['PUT'])
@roles_required('Admin')
def update_employee():
    data = request.json or {}

    employee_id = data.get("EmployeeID")
    full_name = data.get("FullName")
    date_of_birth = data.get("DateOfBirth")
    gender = data.get("Gender")
    phone_number = data.get("PhoneNumber")
    email = data.get("Email")
    hire_date = data.get("HireDate")
    department_id = data.get("DepartmentID")
    position_id = data.get("PositionID")
    status = data.get("Status")

    VALID_STATUSES = ["Đang làm việc", "Thử việc", "Đã nghỉ việc", "Tạm hoãn"]

    if not employee_id:
        return jsonify({"error": "Thiếu EmployeeID"}), 400

    if full_name is not None and not str(full_name).strip():
        return jsonify({"error": "Họ tên không được để trống"}), 400

    if status is not None and status not in VALID_STATUSES:
        return jsonify({"error": "Trạng thái không hợp lệ"}), 400

    sql_conn = get_sqlserver_connection()
    my_conn = get_mysql_connection()

    if not sql_conn or not my_conn:
        return jsonify({"error": "Kết nối Database thất bại"}), 500

    sql_cursor = sql_conn.cursor()
    my_cursor = my_conn.cursor()

    try:
        sql_cursor.execute("""
            SELECT EmployeeID
            FROM [HUMAN_2025].[dbo].[Employees]
            WHERE EmployeeID = ?
        """, (employee_id,))

        if not sql_cursor.fetchone():
            return jsonify({"error": "Nhân viên không tồn tại"}), 404

        # SQL Server: field nào không gửi thì giữ nguyên giá trị cũ
        sql_cursor.execute("""
            UPDATE [HUMAN_2025].[dbo].[Employees]
            SET 
                FullName = COALESCE(?, FullName),
                DateOfBirth = COALESCE(?, DateOfBirth),
                Gender = COALESCE(?, Gender),
                PhoneNumber = COALESCE(?, PhoneNumber),
                Email = COALESCE(?, Email),
                HireDate = COALESCE(?, HireDate),
                DepartmentID = COALESCE(?, DepartmentID),
                PositionID = COALESCE(?, PositionID),
                Status = COALESCE(?, Status)
            WHERE EmployeeID = ?
        """, (
            full_name,
            date_of_birth,
            gender,
            phone_number,
            email,
            hire_date,
            department_id,
            position_id,
            status,
            employee_id
        ))

        # MySQL: field nào không gửi thì giữ nguyên giá trị cũ
        my_cursor.execute("""
            UPDATE employees_payroll
            SET 
                FullName = COALESCE(%s, FullName),
                DepartmentID = COALESCE(%s, DepartmentID),
                PositionID = COALESCE(%s, PositionID),
                Status = COALESCE(%s, Status)
            WHERE EmployeeID = %s
        """, (
            full_name,
            department_id,
            position_id,
            status,
            employee_id
        ))

        # Nếu MySQL chưa có employee này thì tự thêm lại để đồng bộ
        if my_cursor.rowcount == 0:
            sql_cursor.execute("""
                SELECT FullName, DepartmentID, PositionID, Status
                FROM [HUMAN_2025].[dbo].[Employees]
                WHERE EmployeeID = ?
            """, (employee_id,))
            emp = sql_cursor.fetchone()

            my_cursor.execute("""
                INSERT INTO employees_payroll 
                    (EmployeeID, FullName, DepartmentID, PositionID, Status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                employee_id,
                emp[0],
                emp[1],
                emp[2],
                emp[3]
            ))

        sql_conn.commit()
        my_conn.commit()

        return jsonify({"message": "Cập nhật nhân viên thành công"}), 200

    except Exception as e:
        sql_conn.rollback()
        my_conn.rollback()
        return jsonify({"error": f"Lỗi hệ thống: {str(e)}"}), 500

    finally:
        sql_cursor.close()
        my_cursor.close()
        sql_conn.close()
        my_conn.close()

# ---------------------------------------------------------
# 4.2. XÓA NHÂN VIÊN & ĐỒNG BỘ SQL Server -> MySQL
# ---------------------------------------------------------
@human_bp.route('/delete-employee/<int:employee_id>', methods=['DELETE'])
@roles_required('Admin')
def delete_employee(employee_id):
    sql_conn = get_sqlserver_connection()
    my_conn = get_mysql_connection()

    if not sql_conn or not my_conn:
        return jsonify({"error": "Kết nối Database thất bại"}), 500

    sql_cursor = sql_conn.cursor()
    my_cursor = my_conn.cursor()

    try:
        # Kiểm tra nhân viên có tồn tại không
        sql_cursor.execute("""
            SELECT COUNT(*) 
            FROM [HUMAN_2025].[dbo].[Employees] 
            WHERE EmployeeID = ?
        """, (employee_id,))

        if sql_cursor.fetchone()[0] == 0:
            return jsonify({"error": "Nhân viên không tồn tại"}), 404

        # Kiểm tra nhân viên đã có dữ liệu lương/chấm công chưa
        my_cursor.execute("""
            SELECT COUNT(*) 
            FROM salaries 
            WHERE EmployeeID = %s
        """, (employee_id,))

        salary_count = my_cursor.fetchone()[0]

        my_cursor.execute("""
            SELECT COUNT(*) 
            FROM timekeeping 
            WHERE EmployeeID = %s
        """, (employee_id,))

        timekeeping_count = my_cursor.fetchone()[0]

        if salary_count > 0 or timekeeping_count > 0:
            return jsonify({
                "error": "Không thể xóa nhân viên vì đã có dữ liệu lương hoặc chấm công"
            }), 400

        # Xóa bên MySQL trước
        my_cursor.execute("""
            DELETE FROM employees_payroll 
            WHERE EmployeeID = %s
        """, (employee_id,))

        # Xóa bên SQL Server
        sql_cursor.execute("""
            DELETE FROM [HUMAN_2025].[dbo].[Employees] 
            WHERE EmployeeID = ?
        """, (employee_id,))

        my_conn.commit()
        sql_conn.commit()

        return jsonify({"message": "Xóa nhân viên thành công"}), 200

    except Exception as e:
        sql_conn.rollback()
        my_conn.rollback()
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
@roles_required('Admin', 'Manager')
def report_human():
    conn = get_sqlserver_connection()
    if not conn: return jsonify({"error": "DB Error"}), 500
    cursor = conn.cursor()
    try:
        # 1. Tổng số nhân viên
        cursor.execute("SELECT COUNT(*) FROM [HUMAN_2025].[dbo].[Employees]")
        total_employees = cursor.fetchone()[0]

        # 2. Tổng số phòng ban
        cursor.execute("SELECT COUNT(*) FROM [HUMAN_2025].[dbo].[Departments]")
        total_depts = cursor.fetchone()[0]

        # 3. Tổng số chức vụ
        cursor.execute("SELECT COUNT(*) FROM [HUMAN_2025].[dbo].[Positions]")
        total_positions = cursor.fetchone()[0]

        # 4. Thống kê theo trạng thái (Status)
        cursor.execute("SELECT Status, COUNT(*) FROM [HUMAN_2025].[dbo].[Employees] GROUP BY Status")
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        return jsonify({
            "total_employees": total_employees,
            "total_departments": total_depts,
            "total_positions": total_positions,
            "status_distribution": status_counts
        }), 200
    finally:
        cursor.close()
        conn.close()
# ---------------------------------------------------------
# 6.QUẢN LÝ PHÒNG BAN (DEPARTMENTS) - CRUD & SYNC
# ---------------------------------------------------------

@human_bp.route('/show-department', methods=['GET'])
@roles_required('Admin')
def show_departments():
    conn = get_sqlserver_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DepartmentID, DepartmentName FROM [HUMAN_2025].[dbo].[Departments]")
    data = [{"DepartmentID": r[0], "DepartmentName": r[1]} for r in cursor.fetchall()]
    conn.close()
    return jsonify(data), 200

@human_bp.route('/add-department', methods=['POST'])
@roles_required('Admin')
def add_department():
    name = request.json.get('DepartmentName')
    sql_conn = get_sqlserver_connection()
    my_conn = get_mysql_connection()
    sql_cursor = sql_conn.cursor()
    my_cursor = my_conn.cursor()
    try:
        # 1. Thêm vào SQL Server
        sql_cursor.execute("INSERT INTO [HUMAN_2025].[dbo].[Departments] (DepartmentName) VALUES (?)", (name,))
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
@roles_required('Admin')
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
@roles_required('Admin')
def delete_department(id):
    sql_conn = get_sqlserver_connection()
    my_conn = get_mysql_connection()
    sql_cursor = sql_conn.cursor()
    try:
        # Kiểm tra ràng buộc nhân viên trước khi xóa
        sql_cursor.execute("SELECT COUNT(*) FROM [HUMAN_2025].[dbo].[Employees] WHERE DepartmentID = ?", (id,))
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
# 7.1. CẬP NHẬT CHỨC VỤ & ĐỒNG BỘ SQL Server -> MySQL
# ---------------------------------------------------------
@human_bp.route('/update-position', methods=['PUT'])
@roles_required('Admin')
def update_position():
    data = request.json or {}

    position_id = data.get("PositionID")
    position_name = data.get("PositionName")

    if not position_id:
        return jsonify({"error": "Thiếu PositionID"}), 400

    if not position_name or not str(position_name).strip():
        return jsonify({"error": "Tên chức vụ không được để trống"}), 400

    sql_conn = get_sqlserver_connection()
    my_conn = get_mysql_connection()

    if not sql_conn or not my_conn:
        return jsonify({"error": "Kết nối Database thất bại"}), 500

    sql_cursor = sql_conn.cursor()
    my_cursor = my_conn.cursor()

    try:
        sql_cursor.execute("""
            SELECT COUNT(*)
            FROM [HUMAN_2025].[dbo].[Positions]
            WHERE PositionID = ?
        """, (position_id,))

        if sql_cursor.fetchone()[0] == 0:
            return jsonify({"error": "Chức vụ không tồn tại"}), 404

        sql_cursor.execute("""
            UPDATE [HUMAN_2025].[dbo].[Positions]
            SET PositionName = ?
            WHERE PositionID = ?
        """, (position_name, position_id))

        my_cursor.execute("""
            UPDATE positions_payroll
            SET PositionName = %s
            WHERE PositionID = %s
        """, (position_name, position_id))

        if my_cursor.rowcount == 0:
            my_cursor.execute("""
                INSERT INTO positions_payroll (PositionID, PositionName)
                VALUES (%s, %s)
            """, (position_id, position_name))

        sql_conn.commit()
        my_conn.commit()

        return jsonify({"message": "Cập nhật chức vụ thành công"}), 200

    except Exception as e:
        sql_conn.rollback()
        my_conn.rollback()
        return jsonify({"error": f"Lỗi hệ thống: {str(e)}"}), 500

    finally:
        sql_cursor.close()
        my_cursor.close()
        sql_conn.close()
        my_conn.close()


# ---------------------------------------------------------
# 7.2. XÓA CHỨC VỤ & ĐỒNG BỘ SQL Server -> MySQL
# ---------------------------------------------------------
@human_bp.route('/show-human', methods=['GET'])
@roles_required('Admin')
def show_positions():
    conn = get_sqlserver_connection()

    if not conn:
        return jsonify({"error": "Không thể kết nối SQL Server"}), 500

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT PositionID, PositionName
            FROM [HUMAN_2025].[dbo].[Positions]
            ORDER BY PositionID
        """)

        data = [
            {
                "PositionID": row[0],
                "PositionName": row[1]
            }
            for row in cursor.fetchall()
        ]

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": f"Lỗi hệ thống: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()


@human_bp.route('/add-position', methods=['POST'])
@roles_required('Admin')
def add_position():
    data = request.json or {}
    name = data.get('PositionName')

    if not name or not str(name).strip():
        return jsonify({"error": "Tên chức vụ không được để trống"}), 400

    sql_conn = get_sqlserver_connection()
    my_conn = get_mysql_connection()

    if not sql_conn or not my_conn:
        return jsonify({"error": "Kết nối Database thất bại"}), 500

    sql_cursor = sql_conn.cursor()
    my_cursor = my_conn.cursor()

    try:
        sql_cursor.execute("""
            INSERT INTO [HUMAN_2025].[dbo].[Positions] (PositionName)
            VALUES (?)
        """, (name,))

        sql_cursor.execute("SELECT @@IDENTITY")
        new_id = int(sql_cursor.fetchone()[0])

        my_cursor.execute("""
            INSERT INTO positions_payroll (PositionID, PositionName)
            VALUES (%s, %s)
        """, (new_id, name))

        sql_conn.commit()
        my_conn.commit()

        return jsonify({
            "message": "Thêm chức vụ thành công",
            "id": new_id
        }), 201

    except Exception as e:
        sql_conn.rollback()
        my_conn.rollback()
        return jsonify({"error": f"Lỗi hệ thống: {str(e)}"}), 500

    finally:
        sql_cursor.close()
        my_cursor.close()
        sql_conn.close()
        my_conn.close()