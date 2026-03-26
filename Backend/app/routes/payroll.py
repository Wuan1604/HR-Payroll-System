from flask import Blueprint, jsonify, request
from app.database import get_mysql_connection, get_sqlserver_connection
from ..config import Config
from app.auth import login_required
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

payroll_bp = Blueprint('payroll', __name__)

# ---------------------------
# HÀM LOGIC GỬI EMAIL (Dùng Config)
# ---------------------------
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
# 1. HIỂN THỊ BẢNG LƯƠNG (MySQL)
# ---------------------------
@payroll_bp.route('/show-salaries', methods=['GET'])
@login_required
def show_salaries():
    conn = get_mysql_connection()
    if not conn: return jsonify({"error": "Không thể kết nối MySQL"}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Join bảng salaries và employees trong MySQL để lấy tên
        cursor.execute("""
            SELECT s.*, e.FullName 
            FROM salaries s 
            JOIN employees e ON s.EmployeeID = e.EmployeeID
            ORDER BY s.SalaryMonth DESC
        """)
        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
# ---------------------------
# 4. HIỂN THỊ CHẤM CÔNG (MySQL)
# ---------------------------
@payroll_bp.route('/timekeeping', methods=['GET'])
@login_required
def get_timekeeping():
    conn = get_mysql_connection()
    if not conn: return jsonify({"error": "Lỗi kết nối MySQL"}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Lấy dữ liệu từ bảng attendance
        cursor.execute("""
            SELECT a.*, e.FullName 
            FROM attendance a
            JOIN employees e ON a.EmployeeID = e.EmployeeID
            ORDER BY a.AttendanceMonth DESC
        """)
        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
# ---------------------------
# 2. CẬP NHẬT LƯƠNG (MySQL)
# ---------------------------
@payroll_bp.route('/update-salary', methods=['POST'])
@login_required
def update_salary():
    data = request.json
    try:
        # Tính toán lại NetSalary để đảm bảo chính xác
        base = float(data.get('BaseSalary', 0))
        bonus = float(data.get('Bonus', 0))
        deduct = float(data.get('Deductions', 0))
        net_salary = base + bonus - deduct
        
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE salaries 
            SET BaseSalary=%s, Bonus=%s, Deductions=%s, NetSalary=%s 
            WHERE SalaryID=%s
        """, (base, bonus, deduct, net_salary, data['SalaryID']))
        conn.commit()
        
        return jsonify({
            "message": "Cập nhật lương thành công",
            "NetSalary": net_salary
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals(): conn.close()

# ---------------------------
# 3. GỬI EMAIL PHIẾU LƯƠNG (KẾT HỢP SQL Server + MySQL)
# ---------------------------
@payroll_bp.route('/send-salary-emails', methods=['GET'])
@login_required
def send_emails():
    my_conn = get_mysql_connection()
    sql_conn = get_sqlserver_connection()
    
    if not my_conn or not sql_conn:
        return jsonify({"error": "Lỗi kết nối một trong hai Database"}), 500
    
    try:
        # Bước A: Lấy dữ liệu lương từ MySQL
        my_cursor = my_conn.cursor(dictionary=True)
        my_cursor.execute("SELECT EmployeeID, NetSalary, SalaryMonth FROM salaries")
        salaries = my_cursor.fetchall()
        
        # Bước B: Lấy Email nhân viên từ SQL Server [HUMAN_2025]
        sql_cursor = sql_conn.cursor()
        sql_cursor.execute("SELECT EmployeeID, FullName, Email FROM [HUMAN_2025].[dbo].[Employees]")
        emps = {r[0]: {"name": r[1], "email": r[2]} for r in sql_cursor.fetchall()}
        
        sent_count = 0
        for s in salaries:
            emp = emps.get(s['EmployeeID'])
            # Kiểm tra nếu nhân viên có email và NetSalary > 0
            if emp and emp['email'] and s['NetSalary'] > 0:
                # Format tiền: 10,000,000 VND
                formatted_salary = "{:,.0f}".format(s['NetSalary'])
                
                html_content = f"""
                <div style="font-family: Arial; border: 1px solid #ddd; padding: 20px;">
                    <h2 style="color: #2c3e50;">PHIẾU LƯƠNG NHÂN VIÊN</h2>
                    <p>Xin chào: <b>{emp['name']}</b></p>
                    <p>Mã nhân viên: <b>{s['EmployeeID']}</b></p>
                    <hr>
                    <p style="font-size: 16px;">Tổng lương thực nhận tháng này:</p>
                    <h1 style="color: #e74c3c;">{formatted_salary} VND</h1>
                    <p><i>Vui lòng phản hồi nếu có sai sót.</i></p>
                </div>
                """
                if send_email_logic(emp['email'], f"Thông báo lương - {datetime.now().strftime('%m/%Y')}", html_content):
                    sent_count += 1
                    
        return jsonify({"message": f"Đã gửi thành công {sent_count} email phiếu lương"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        my_conn.close()
        sql_conn.close()