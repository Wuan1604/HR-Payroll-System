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
    mssql_conn = get_sqlserver_connection() # Sửa tên hàm cho đúng import
    
    if not mysql_conn or not mssql_conn:
        return jsonify({"error": "Lỗi kết nối cơ sở dữ liệu"}), 500

    try:
        mysql_cursor = mysql_conn.cursor(dictionary=True)
        mssql_cursor = mssql_conn.cursor()

        # Lấy lương từ MySQL
        mysql_cursor.execute("SELECT * FROM salaries ORDER BY SalaryMonth DESC")
        salaries = mysql_cursor.fetchall()

        # Lấy nhân viên từ SQL Server
        mssql_cursor.execute("SELECT EmployeeID, FullName, DepartmentID FROM Employees")
        employees = {row[0]: {"FullName": row[1], "Dept": row[2]} for row in mssql_cursor.fetchall()}

        for s in salaries:
            emp = employees.get(s['EmployeeID'])
            s['FullName'] = emp['FullName'] if emp else "N/A"
            # ÉP KIỂU ĐỂ TRÁNH LỖI JSON 500
            s['BaseSalary'] = float(s['BaseSalary'])
            s['Bonus'] = float(s['Bonus'])
            s['Deductions'] = float(s['Deductions'])
            s['NetSalary'] = float(s['NetSalary'])
            s['SalaryMonth'] = str(s['SalaryMonth']) 

        return jsonify(salaries), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        mysql_conn.close()
        mssql_conn.close()

# ---------------------------
# 2. HIỂN THỊ CHẤM CÔNG (Sửa logic lấy tên từ SQL Server)
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
        my_cursor.execute("SELECT * FROM attendance ORDER BY AttendanceMonth DESC")
        attendances = my_cursor.fetchall()

        sql_cursor = sql_conn.cursor()
        sql_cursor.execute("SELECT EmployeeID, FullName FROM Employees")
        emps = {row[0]: row[1] for row in sql_cursor.fetchall()}

        for a in attendances:
            a['FullName'] = emps.get(a['EmployeeID'], "N/A")
            a['AttendanceMonth'] = str(a['AttendanceMonth'])

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
    data = request.json
    conn = get_mysql_connection()
    if not conn: return jsonify({"error": "Lỗi kết nối"}), 500
    
    try:
        base = float(data.get('BaseSalary', 0))
        bonus = float(data.get('Bonus', 0))
        deduct = float(data.get('Deductions', 0))
        net_salary = base + bonus - deduct
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE salaries 
            SET BaseSalary=%s, Bonus=%s, Deductions=%s, NetSalary=%s 
            WHERE SalaryID=%s
        """, (base, bonus, deduct, net_salary, data['SalaryID']))
        conn.commit()
        return jsonify({"message": "Thành công", "NetSalary": net_salary}), 200
    except Exception as e:
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
    
    try:
        my_cursor = my_conn.cursor(dictionary=True)
        my_cursor.execute("SELECT EmployeeID, NetSalary FROM salaries")
        salaries = my_cursor.fetchall()
        
        sql_cursor = sql_conn.cursor()
        sql_cursor.execute("SELECT EmployeeID, FullName, Email FROM Employees")
        emps = {r[0]: {"name": r[1], "email": r[2]} for r in sql_cursor.fetchall()}
        
        sent_count = 0
        for s in salaries:
            emp = emps.get(s['EmployeeID'])
            if emp and emp['email'] and float(s['NetSalary']) > 0:
                formatted_salary = "{:,.0f}".format(float(s['NetSalary']))
                html = f"<h3>Chào {emp['name']}, lương tháng này của bạn là {formatted_salary} VND</h3>"
                
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

        my_cursor.execute(
            """
            SELECT SalaryID, EmployeeID, SalaryMonth, BaseSalary, Bonus, Deductions,
                   NetSalary, CreatedAt
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
                "SalaryMonth": str(row["SalaryMonth"]),
                "BaseSalary": float(row["BaseSalary"]),
                "Bonus": float(row["Bonus"]),
                "Deductions": float(row["Deductions"]),
                "NetSalary": float(row["NetSalary"]),
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
