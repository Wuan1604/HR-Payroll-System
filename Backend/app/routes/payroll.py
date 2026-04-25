from flask import Blueprint, jsonify, request
from app.database import get_mysql_connection, get_sqlserver_connection 
from ..config import Config
from app.auth import login_required
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

payroll_bp = Blueprint('payroll', __name__)


def send_email_logic(to_email, subject, content):
    try:
        msg = MIMEMultipart()
        msg['From'] = Config.SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(Config.SENDER_EMAIL, Config.SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True

    except Exception as e:
        print(f"Lỗi gửi mail: {e}")
        return False


# ---------------------------
# 1. HIỂN THỊ BẢNG LƯƠNG
# ---------------------------
@payroll_bp.route('/show-salaries', methods=['GET'])
@login_required
def show_salaries():
    mysql_conn = get_mysql_connection()

    if not mysql_conn:
        return jsonify({"error": "Lỗi kết nối MySQL"}), 500

    try:
        cursor = mysql_conn.cursor(dictionary=True)

        """
        Lấy nhân viên từ employees_payroll.
        Nếu nhân viên chưa có dữ liệu trong salaries thì vẫn hiển thị,
        SalaryID = 0 và các giá trị lương = 0.
        """
        cursor.execute("""
            SELECT 
                e.EmployeeID,
                e.FullName,
                e.DepartmentID,
                e.PositionID,
                e.Status,

                COALESCE(d.DepartmentName, 'N/A') AS DepartmentName,
                COALESCE(p.PositionName, 'N/A') AS PositionName,

                COALESCE(s.SalaryID, 0) AS SalaryID,
                COALESCE(s.SalaryMonth, DATE_FORMAT(CURDATE(), '%Y-%m-01')) AS SalaryMonth,
                COALESCE(s.BaseSalary, 0) AS BaseSalary,
                COALESCE(s.Bonus, 0) AS Bonus,
                COALESCE(s.Deductions, 0) AS Deductions,
                COALESCE(s.NetSalary, 0) AS NetSalary,
                s.CreatedAt

            FROM employees_payroll e
            LEFT JOIN salaries s 
                ON e.EmployeeID = s.EmployeeID
            LEFT JOIN departments_payroll d
                ON e.DepartmentID = d.DepartmentID
            LEFT JOIN positions_payroll p
                ON e.PositionID = p.PositionID

            ORDER BY 
                e.EmployeeID DESC,
                s.SalaryMonth DESC,
                s.SalaryID DESC
        """)

        salaries = cursor.fetchall()

        for s in salaries:
            s['SalaryID'] = int(s['SalaryID']) if s['SalaryID'] is not None else 0
            s['EmployeeID'] = int(s['EmployeeID'])
            s['BaseSalary'] = float(s['BaseSalary'] or 0)
            s['Bonus'] = float(s['Bonus'] or 0)
            s['Deductions'] = float(s['Deductions'] or 0)
            s['NetSalary'] = float(s['NetSalary'] or 0)
            s['SalaryMonth'] = str(s['SalaryMonth']) if s['SalaryMonth'] else None
            s['CreatedAt'] = str(s['CreatedAt']) if s.get('CreatedAt') else None

        return jsonify(salaries), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        mysql_conn.close()


# ---------------------------
# 2. HIỂN THỊ CHẤM CÔNG
# ---------------------------
@payroll_bp.route('/timekeeping', methods=['GET'])
@login_required
def get_timekeeping():
    my_conn = get_mysql_connection()
    sql_conn = get_sqlserver_connection()
    
    if not my_conn or not sql_conn: 
        return jsonify({"error": "Lỗi kết nối DB"}), 500
    
    try:
        my_cursor = my_conn.cursor(dictionary=True)
        my_cursor.execute("""
            SELECT 
                a.AttendanceID,
                a.EmployeeID,
                a.WorkDays,
                a.AbsentDays,
                a.LeaveDays,
                a.AttendanceMonth
            FROM attendance a
            ORDER BY a.AttendanceMonth DESC
        """)
        attendances = my_cursor.fetchall()

        sql_cursor = sql_conn.cursor()
        sql_cursor.execute("SELECT EmployeeID, FullName FROM Employees")
        emps = {row[0]: row[1] for row in sql_cursor.fetchall()}

        for a in attendances:
            a['FullName'] = emps.get(a['EmployeeID'], "N/A")
            a['AttendanceMonth'] = str(a['AttendanceMonth']) if a['AttendanceMonth'] else None

        return jsonify(attendances), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        my_conn.close()
        sql_conn.close()


# ---------------------------
# 3. CẬP NHẬT LƯƠNG
# ---------------------------
@payroll_bp.route('/update-salary', methods=['POST'])
@login_required
def update_salary():
    data = request.json or {}

    conn = get_mysql_connection()
    if not conn:
        return jsonify({"error": "Lỗi kết nối MySQL"}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        salary_id = data.get('SalaryID')
        employee_id = data.get('EmployeeID')
        salary_month = data.get('SalaryMonth')

        base = float(data.get('BaseSalary') or 0)
        bonus = float(data.get('Bonus') or 0)
        deduct = float(data.get('Deductions') or 0)
        net_salary = base + bonus - deduct

        if not employee_id and not salary_id:
            return jsonify({"error": "Thiếu EmployeeID hoặc SalaryID"}), 400

        # Nếu frontend không gửi SalaryMonth thì lấy tháng hiện tại
        if not salary_month:
            cursor.execute("SELECT DATE_FORMAT(CURDATE(), '%Y-%m-01') AS current_month")
            salary_month = cursor.fetchone()["current_month"]

        # Trường hợp 1: Có SalaryID thật thì UPDATE theo SalaryID
        if salary_id and int(salary_id) > 0:
            cursor.execute("""
                UPDATE salaries 
                SET 
                    BaseSalary = %s,
                    Bonus = %s,
                    Deductions = %s,
                    NetSalary = %s,
                    SalaryMonth = %s
                WHERE SalaryID = %s
            """, (
                base,
                bonus,
                deduct,
                net_salary,
                salary_month,
                salary_id
            ))

            conn.commit()

            return jsonify({
                "message": "Cập nhật lương thành công",
                "SalaryID": int(salary_id),
                "EmployeeID": employee_id,
                "SalaryMonth": str(salary_month),
                "BaseSalary": base,
                "Bonus": bonus,
                "Deductions": deduct,
                "NetSalary": net_salary
            }), 200

        # Trường hợp 2: Nhân viên chưa có dòng lương
        # Kiểm tra nhân viên có tồn tại trong employees_payroll không
        cursor.execute("""
            SELECT EmployeeID
            FROM employees_payroll
            WHERE EmployeeID = %s
        """, (employee_id,))

        employee = cursor.fetchone()

        if not employee:
            return jsonify({"error": "Nhân viên chưa tồn tại trong hệ thống payroll"}), 404

        # Kiểm tra tháng lương đã có chưa
        cursor.execute("""
            SELECT SalaryID
            FROM salaries
            WHERE EmployeeID = %s AND SalaryMonth = %s
            LIMIT 1
        """, (employee_id, salary_month))

        existing_salary = cursor.fetchone()

        if existing_salary:
            # Nếu tháng này đã có lương thì UPDATE
            cursor.execute("""
                UPDATE salaries 
                SET 
                    BaseSalary = %s,
                    Bonus = %s,
                    Deductions = %s,
                    NetSalary = %s
                WHERE SalaryID = %s
            """, (
                base,
                bonus,
                deduct,
                net_salary,
                existing_salary["SalaryID"]
            ))

            final_salary_id = existing_salary["SalaryID"]

        else:
            # Nếu chưa có lương tháng này thì INSERT mới
            cursor.execute("""
                INSERT INTO salaries 
                    (EmployeeID, SalaryMonth, BaseSalary, Bonus, Deductions, NetSalary)
                VALUES 
                    (%s, %s, %s, %s, %s, %s)
            """, (
                employee_id,
                salary_month,
                base,
                bonus,
                deduct,
                net_salary
            ))

            final_salary_id = cursor.lastrowid

        conn.commit()

        return jsonify({
            "message": "Cập nhật lương thành công",
            "SalaryID": final_salary_id,
            "EmployeeID": int(employee_id),
            "SalaryMonth": str(salary_month),
            "BaseSalary": base,
            "Bonus": bonus,
            "Deductions": deduct,
            "NetSalary": net_salary
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


# ---------------------------
# 4. GỬI EMAIL PHIẾU LƯƠNG
# ---------------------------
@payroll_bp.route('/send-salary-emails', methods=['GET'])
@login_required
def send_emails():
    my_conn = get_mysql_connection()
    sql_conn = get_sqlserver_connection()
    
    if not my_conn or not sql_conn:
        return jsonify({"error": "Lỗi kết nối cơ sở dữ liệu"}), 500

    try:
        my_cursor = my_conn.cursor(dictionary=True)

        my_cursor.execute("""
            SELECT EmployeeID, NetSalary, SalaryMonth
            FROM salaries
            ORDER BY SalaryMonth DESC
        """)
        salaries = my_cursor.fetchall()
        
        sql_cursor = sql_conn.cursor()
        sql_cursor.execute("SELECT EmployeeID, FullName, Email FROM Employees")
        emps = {
            r[0]: {
                "name": r[1],
                "email": r[2]
            }
            for r in sql_cursor.fetchall()
        }
        
        sent_count = 0

        for s in salaries:
            emp = emps.get(s['EmployeeID'])

            if emp and emp['email'] and float(s['NetSalary'] or 0) > 0:
                formatted_salary = "{:,.0f}".format(float(s['NetSalary']))
                salary_month = str(s['SalaryMonth'])

                html = f"""
                    <h3>Chào {emp['name']},</h3>
                    <p>Lương tháng {salary_month} của bạn là:</p>
                    <h2>{formatted_salary} VND</h2>
                """
                
                if send_email_logic(emp['email'], "Phiếu lương", html):
                    sent_count += 1
                    
        return jsonify({"message": f"Đã gửi {sent_count} email"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        my_conn.close()
        sql_conn.close()


# ---------------------------
# 5. LỊCH SỬ LƯƠNG THEO NHÂN VIÊN
# ---------------------------
@payroll_bp.route('/history-salaries/<int:employee_id>', methods=['GET'])
@login_required
def history_salaries(employee_id):
    my_conn = get_mysql_connection()
    sql_conn = get_sqlserver_connection()

    if not my_conn or not sql_conn:
        return jsonify({"error": "Lỗi kết nối cơ sở dữ liệu"}), 500

    try:
        my_cursor = my_conn.cursor(dictionary=True)
        sql_cursor = sql_conn.cursor()

        # Lấy thông tin nhân viên từ SQL Server
        sql_cursor.execute(
            """
            SELECT e.EmployeeID, e.FullName, e.Email, e.Status,
                   d.DepartmentName, p.PositionName
            FROM Employees e
            LEFT JOIN Departments d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN Positions p ON e.PositionID = p.PositionID
            WHERE e.EmployeeID = ?
            """,
            (employee_id,)
        )

        employee_row = sql_cursor.fetchone()

        if not employee_row:
            return jsonify({"error": f"Không tìm thấy nhân viên có mã {employee_id}"}), 404

        employee = {
            "EmployeeID": employee_row[0],
            "FullName": employee_row[1],
            "Email": employee_row[2],
            "Status": employee_row[3],
            "DepartmentName": employee_row[4],
            "PositionName": employee_row[5],
        }

        # Lấy lịch sử lương nếu có
        my_cursor.execute(
            """
            SELECT 
                SalaryID,
                EmployeeID,
                SalaryMonth,
                BaseSalary,
                Bonus,
                Deductions,
                NetSalary,
                CreatedAt
            FROM salaries
            WHERE EmployeeID = %s
            ORDER BY SalaryMonth DESC, CreatedAt DESC, SalaryID DESC
            """,
            (employee_id,)
        )

        salary_rows = my_cursor.fetchall()

        history = []

        for row in salary_rows:
            history.append({
                "SalaryID": row["SalaryID"],
                "EmployeeID": row["EmployeeID"],
                "SalaryMonth": str(row["SalaryMonth"]) if row["SalaryMonth"] else None,
                "BaseSalary": float(row["BaseSalary"] or 0),
                "Bonus": float(row["Bonus"] or 0),
                "Deductions": float(row["Deductions"] or 0),
                "NetSalary": float(row["NetSalary"] or 0),
                "CreatedAt": str(row["CreatedAt"]) if row.get("CreatedAt") else None,
            })

        latest_salary = history[0] if history else None

        return jsonify({
            "employee": employee,
            "history": history,
            "count": len(history),
            "latest_salary": latest_salary,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        my_conn.close()
        sql_conn.close()