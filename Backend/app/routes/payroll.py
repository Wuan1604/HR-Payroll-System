from flask import Blueprint, jsonify, request, Response
from app.database import get_mysql_connection, get_sqlserver_connection
from ..config import Config
from app.auth import roles_required, is_employee_requesting_other_employee
from datetime import datetime, date, time, timedelta
import calendar
import csv
import os
import unicodedata
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
except Exception:
    colors = None
    A4 = None
    landscape = None
    getSampleStyleSheet = None
    mm = None
    pdfmetrics = None
    TTFont = None
    SimpleDocTemplate = None
    Table = None
    TableStyle = None
    Paragraph = None
    Spacer = None
from email.header import Header

payroll_bp = Blueprint('payroll', __name__)


# =========================================================
# COMMON HELPERS
# =========================================================
def send_email_logic(to_email, subject, content):
    """Gửi email và trả về (thành_công, lỗi).

    Gmail App Password thường được hiển thị có khoảng trắng.
    Khi đăng nhập SMTP cần bỏ khoảng trắng để tránh lỗi xác thực.
    """
    server = None
    try:
        sender_email = (Config.SENDER_EMAIL or '').strip()
        sender_password = (Config.SENDER_PASSWORD or '').replace(' ', '').strip()
        receiver_email = (to_email or '').strip()

        if not sender_email:
            return False, 'Chưa cấu hình SENDER_EMAIL trong file .env'
        if not sender_password:
            return False, 'Chưa cấu hình SENDER_PASSWORD trong file .env'
        if not receiver_email:
            return False, 'Người nhận chưa có email'

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = str(Header(subject, 'utf-8'))
        msg.attach(MIMEText(content, 'html', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [receiver_email], msg.as_string())
        return True, None

    except smtplib.SMTPAuthenticationError:
        error = 'Không đăng nhập được Gmail SMTP. Kiểm tra SENDER_EMAIL và App Password trong .env'
        print(f"Lỗi gửi mail: {error}")
        return False, error
    except Exception as e:
        error = str(e)
        print(f"Lỗi gửi mail tới {to_email}: {error}")
        return False, error
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass


def ensure_attendance_details_table(cursor):
    """Tạo bảng chấm công chi tiết nếu database hiện tại chưa có."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_details (
            DetailID INT NOT NULL AUTO_INCREMENT,
            EmployeeID INT NOT NULL,
            WorkDate DATE NOT NULL,
            CheckIn TIME NULL,
            CheckOut TIME NULL,
            TotalHours DECIMAL(5,2) DEFAULT 0,
            WorkUnit DECIMAL(4,2) DEFAULT 0,
            Status VARCHAR(50) DEFAULT 'Đi làm',
            Note TEXT NULL,
            CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (DetailID),
            UNIQUE KEY unique_employee_date (EmployeeID, WorkDate)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)




def ensure_employee_base_salaries_table(cursor):
    """Tạo bảng lưu lương cơ bản hiện tại của từng nhân viên nếu chưa có."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_base_salaries (
            BaseSalaryID INT NOT NULL AUTO_INCREMENT,
            EmployeeID INT NOT NULL,
            BaseSalary DECIMAL(12,2) NOT NULL DEFAULT 0.00,
            EffectiveDate DATE NULL,
            Note TEXT NULL,
            CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (BaseSalaryID),
            UNIQUE KEY unique_employee_base_salary (EmployeeID)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)


def row_to_base_salary_json(row):
    return {
        'BaseSalaryID': int(row.get('BaseSalaryID') or 0),
        'EmployeeID': int(row.get('EmployeeID') or 0),
        'FullName': row.get('FullName') or '',
        'DepartmentName': row.get('DepartmentName') or 'N/A',
        'PositionName': row.get('PositionName') or 'N/A',
        'Status': row.get('Status') or '',
        'BaseSalary': float(row.get('BaseSalary') or 0),
        'EffectiveDate': to_json_date(row.get('EffectiveDate')),
        'Note': row.get('Note') or '',
        'CreatedAt': str(row.get('CreatedAt')) if row.get('CreatedAt') else None,
        'UpdatedAt': str(row.get('UpdatedAt')) if row.get('UpdatedAt') else None,
        'HasBaseSalary': bool(row.get('BaseSalaryID')),
    }

def parse_date_value(value):
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()


def parse_time_value(value):
    if not value:
        return None
    if isinstance(value, time):
        return value
    return datetime.strptime(str(value)[:5], '%H:%M').time()


def to_json_date(value):
    if value is None:
        return None
    return str(value)[:10]


def to_json_time(value):
    if value is None:
        return None
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f'{hours:02d}:{minutes:02d}'
    return str(value)[:5]


def month_range(month_value):
    month_text = str(month_value or '')[:7]
    start = datetime.strptime(month_text + '-01', '%Y-%m-%d').date()
    end = date(start.year, start.month, calendar.monthrange(start.year, start.month)[1])
    return start, end


def standard_work_dates(month_value):
    """Công ty làm từ thứ 2 đến thứ 7. Chủ nhật không tính công."""
    start, end = month_range(month_value)
    current = start
    days = []
    while current <= end:
        if current.weekday() != 6:
            days.append(current)
        current += timedelta(days=1)
    return days


def calculate_total_hours(check_in, check_out):
    if not check_in or not check_out:
        return 0.0

    today = date.today()
    start = datetime.combine(today, check_in)
    end = datetime.combine(today, check_out)
    if end <= start:
        return 0.0

    hours = (end - start).total_seconds() / 3600
    # Làm quá 5 tiếng thì trừ 1 tiếng nghỉ trưa.
    if hours > 5:
        hours -= 1
    return round(max(hours, 0), 2)


def calculate_work_unit(total_hours, status):
    if status in ['Nghỉ phép', 'Nghỉ không phép']:
        return 0.0
    if total_hours >= 8:
        return 1.0
    if total_hours >= 4:
        return 0.5
    if total_hours > 0:
        return 0.25
    return 0.0


def build_attendance_summary(detail_rows, month_value, base_salary=0):
    work_dates = standard_work_dates(month_value)
    standard_days = len(work_dates)
    work_date_set = {d.isoformat() for d in work_dates}

    details = []
    recorded_work_dates = set()
    total_hours = 0.0
    work_units = 0.0
    leave_days = 0
    unpaid_absent_days = 0
    short_days = 0

    for row in detail_rows:
        work_date = to_json_date(row.get('WorkDate'))
        status = row.get('Status') or 'Đi làm'
        total = float(row.get('TotalHours') or 0)
        unit = float(row.get('WorkUnit') or 0)

        if work_date in work_date_set:
            recorded_work_dates.add(work_date)

        if status == 'Nghỉ phép':
            leave_days += 1
        elif status == 'Nghỉ không phép':
            unpaid_absent_days += 1
        elif 0 < unit < 1:
            short_days += 1

        total_hours += total
        work_units += unit

        details.append({
            'DetailID': row.get('DetailID'),
            'EmployeeID': row.get('EmployeeID'),
            'WorkDate': work_date,
            'CheckIn': to_json_time(row.get('CheckIn')),
            'CheckOut': to_json_time(row.get('CheckOut')),
            'TotalHours': total,
            'WorkUnit': unit,
            'Status': status,
            'Note': row.get('Note') or '',
            'CreatedAt': str(row.get('CreatedAt')) if row.get('CreatedAt') else None,
            'UpdatedAt': str(row.get('UpdatedAt')) if row.get('UpdatedAt') else None,
        })

    missing_record_days = max(0, standard_days - len(recorded_work_dates))
    missing_work_units = max(0, standard_days - work_units - leave_days)
    daily_rate = float(base_salary or 0) / standard_days if standard_days else 0

    return {
        'month': str(month_value)[:7],
        'standardWorkDays': standard_days,
        'totalHours': round(total_hours, 2),
        'workDays': round(work_units, 2),
        'leaveDays': leave_days,
        'absentDays': missing_record_days + unpaid_absent_days,
        'shortDays': short_days,
        'missingRecordDays': missing_record_days,
        'missingWorkUnits': round(missing_work_units, 2),
        'suggestedDeductions': round(daily_rate * missing_work_units, 2),
        'details': details,
    }


def refresh_monthly_attendance_summary(cursor, employee_id, month_value):
    start, end = month_range(month_value)
    ensure_attendance_details_table(cursor)
    cursor.execute("""
        SELECT DetailID, EmployeeID, WorkDate, CheckIn, CheckOut, TotalHours,
               WorkUnit, Status, Note, CreatedAt, UpdatedAt
        FROM attendance_details
        WHERE EmployeeID = %s AND WorkDate BETWEEN %s AND %s
        ORDER BY WorkDate DESC
    """, (employee_id, start, end))
    rows = cursor.fetchall()
    summary = build_attendance_summary(rows, month_value)

    # Đồng bộ về bảng attendance tổng hợp cũ để không làm hỏng màn hình/API cũ.
    work_days_int = int(round(float(summary['workDays'])))
    absent_days_int = int(round(float(summary['absentDays'])))
    leave_days_int = int(round(float(summary['leaveDays'])))

    cursor.execute("""
        SELECT AttendanceID
        FROM attendance
        WHERE EmployeeID = %s AND AttendanceMonth = %s
        ORDER BY AttendanceID DESC
        LIMIT 1
    """, (employee_id, start))
    old = cursor.fetchone()

    if old:
        cursor.execute("""
            UPDATE attendance
            SET WorkDays = %s, AbsentDays = %s, LeaveDays = %s
            WHERE AttendanceID = %s
        """, (work_days_int, absent_days_int, leave_days_int, old['AttendanceID']))
    else:
        cursor.execute("""
            INSERT INTO attendance (EmployeeID, WorkDays, AbsentDays, LeaveDays, AttendanceMonth)
            VALUES (%s, %s, %s, %s, %s)
        """, (employee_id, work_days_int, absent_days_int, leave_days_int, start))

    return summary




def format_seniority_by_work_units(total_valid_days):
    """
    Quy đổi thâm niên theo công chuẩn của hệ thống:
    - 26 công = 1 tháng
    - 12 tháng = 1 năm = 312 công

    Chỉ nhận vào số công hợp lệ để tính thâm niên.
    Công hợp lệ = ngày/công đã làm + ngày nghỉ phép được chấm.
    Không cộng ngày nghỉ không phép hoặc ngày thiếu bản ghi chấm công.
    """
    total_valid_days = float(total_valid_days or 0)

    years = int(total_valid_days // 312)
    remaining_days = total_valid_days % 312
    months = int(remaining_days // 26)
    days = remaining_days % 26

    parts = []
    if years > 0:
        parts.append(f"{years} năm")
    if months > 0:
        parts.append(f"{months} tháng")

    if days > 0 or not parts:
        if float(days).is_integer():
            parts.append(f"{int(days)} ngày")
        else:
            parts.append(f"{days:.1f} ngày")

    return {
        'years': years,
        'months': months,
        'days': round(days, 2),
        'text': ' '.join(parts)
    }



# =========================================================
# 0. QUẢN LÝ LƯƠNG CƠ BẢN NHÂN VIÊN
# =========================================================
@payroll_bp.route('/base-salaries', methods=['GET'])
@roles_required('Admin', 'Manager')
def get_base_salaries():
    conn = get_mysql_connection()
    if not conn:
        return jsonify({"error": "Lỗi kết nối MySQL"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        ensure_employee_base_salaries_table(cursor)
        cursor.execute("""
            SELECT
                e.EmployeeID,
                e.FullName,
                e.DepartmentID,
                e.PositionID,
                e.Status,
                COALESCE(d.DepartmentName, 'N/A') AS DepartmentName,
                COALESCE(p.PositionName, 'N/A') AS PositionName,
                b.BaseSalaryID,
                b.BaseSalary,
                b.EffectiveDate,
                b.Note,
                b.CreatedAt,
                b.UpdatedAt
            FROM employees_payroll e
            LEFT JOIN employee_base_salaries b ON e.EmployeeID = b.EmployeeID
            LEFT JOIN departments_payroll d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN positions_payroll p ON e.PositionID = p.PositionID
            ORDER BY e.EmployeeID DESC
        """)
        rows = cursor.fetchall()
        return jsonify([row_to_base_salary_json(row) for row in rows]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@payroll_bp.route('/base-salaries', methods=['POST'])
@roles_required('Admin', 'Manager')
def create_base_salary():
    data = request.json or {}
    conn = get_mysql_connection()
    if not conn:
        return jsonify({"error": "Lỗi kết nối MySQL"}), 500

    try:
        employee_id = data.get('EmployeeID')
        base_salary = data.get('BaseSalary')
        effective_date = data.get('EffectiveDate') or None
        note = data.get('Note') or ''

        if not employee_id:
            return jsonify({"error": "Vui lòng chọn nhân viên"}), 400
        if base_salary is None or str(base_salary).strip() == '':
            return jsonify({"error": "Vui lòng nhập lương cơ bản"}), 400

        base_salary = float(base_salary)
        if base_salary < 0:
            return jsonify({"error": "Lương cơ bản không được âm"}), 400

        cursor = conn.cursor(dictionary=True)
        ensure_employee_base_salaries_table(cursor)
        cursor.execute("SELECT EmployeeID FROM employees_payroll WHERE EmployeeID = %s", (employee_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Không tìm thấy nhân viên"}), 404

        cursor.execute("""
            INSERT INTO employee_base_salaries (EmployeeID, BaseSalary, EffectiveDate, Note)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                BaseSalary = VALUES(BaseSalary),
                EffectiveDate = VALUES(EffectiveDate),
                Note = VALUES(Note),
                UpdatedAt = CURRENT_TIMESTAMP
        """, (employee_id, base_salary, effective_date, note))
        conn.commit()

        cursor.execute("""
            SELECT e.EmployeeID, e.FullName, e.Status,
                   COALESCE(d.DepartmentName, 'N/A') AS DepartmentName,
                   COALESCE(p.PositionName, 'N/A') AS PositionName,
                   b.BaseSalaryID, b.BaseSalary, b.EffectiveDate, b.Note, b.CreatedAt, b.UpdatedAt
            FROM employees_payroll e
            LEFT JOIN employee_base_salaries b ON e.EmployeeID = b.EmployeeID
            LEFT JOIN departments_payroll d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN positions_payroll p ON e.PositionID = p.PositionID
            WHERE e.EmployeeID = %s
        """, (employee_id,))
        return jsonify(row_to_base_salary_json(cursor.fetchone())), 200
    except ValueError:
        return jsonify({"error": "Lương cơ bản phải là số hợp lệ"}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@payroll_bp.route('/base-salaries/<int:employee_id>', methods=['PUT'])
@roles_required('Admin', 'Manager')
def update_base_salary(employee_id):
    data = request.json or {}
    conn = get_mysql_connection()
    if not conn:
        return jsonify({"error": "Lỗi kết nối MySQL"}), 500

    try:
        base_salary = data.get('BaseSalary')
        effective_date = data.get('EffectiveDate') or None
        note = data.get('Note') or ''

        if base_salary is None or str(base_salary).strip() == '':
            return jsonify({"error": "Vui lòng nhập lương cơ bản"}), 400

        base_salary = float(base_salary)
        if base_salary < 0:
            return jsonify({"error": "Lương cơ bản không được âm"}), 400

        cursor = conn.cursor(dictionary=True)
        ensure_employee_base_salaries_table(cursor)
        cursor.execute("SELECT EmployeeID FROM employees_payroll WHERE EmployeeID = %s", (employee_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Không tìm thấy nhân viên"}), 404

        cursor.execute("""
            INSERT INTO employee_base_salaries (EmployeeID, BaseSalary, EffectiveDate, Note)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                BaseSalary = VALUES(BaseSalary),
                EffectiveDate = VALUES(EffectiveDate),
                Note = VALUES(Note),
                UpdatedAt = CURRENT_TIMESTAMP
        """, (employee_id, base_salary, effective_date, note))
        conn.commit()
        return jsonify({"message": "Cập nhật lương cơ bản thành công", "EmployeeID": employee_id}), 200
    except ValueError:
        return jsonify({"error": "Lương cơ bản phải là số hợp lệ"}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@payroll_bp.route('/base-salaries/<int:employee_id>', methods=['DELETE'])
@roles_required('Admin', 'Manager')
def delete_base_salary(employee_id):
    conn = get_mysql_connection()
    if not conn:
        return jsonify({"error": "Lỗi kết nối MySQL"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        ensure_employee_base_salaries_table(cursor)
        cursor.execute("DELETE FROM employee_base_salaries WHERE EmployeeID = %s", (employee_id,))
        conn.commit()
        return jsonify({"message": "Đã xóa lương cơ bản của nhân viên", "EmployeeID": employee_id}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# =========================================================
# 1. HIỂN THỊ BẢNG LƯƠNG
# =========================================================
@payroll_bp.route('/show-salaries', methods=['GET'])
@roles_required('Admin', 'Manager', 'Employee')
def show_salaries():
    mysql_conn = get_mysql_connection()
    if not mysql_conn:
        return jsonify({"error": "Lỗi kết nối MySQL"}), 500

    try:
        cursor = mysql_conn.cursor(dictionary=True)
        ensure_employee_base_salaries_table(cursor)
        user = getattr(request, 'current_user', {})
        employee_filter = ''
        params = ()
        if user.get('Role') == 'Employee':
            employee_filter = 'WHERE e.EmployeeID = %s'
            params = (user.get('EmployeeID'),)

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
                COALESCE(b.BaseSalary, 0) AS DefaultBaseSalary,
                b.EffectiveDate AS DefaultBaseSalaryEffectiveDate,
                COALESCE(s.Bonus, 0) AS Bonus,
                COALESCE(s.Deductions, 0) AS Deductions,
                COALESCE(s.NetSalary, 0) AS NetSalary,
                s.CreatedAt
            FROM employees_payroll e
            LEFT JOIN salaries s ON e.EmployeeID = s.EmployeeID
            LEFT JOIN employee_base_salaries b ON e.EmployeeID = b.EmployeeID
            LEFT JOIN departments_payroll d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN positions_payroll p ON e.PositionID = p.PositionID
            {employee_filter}
            ORDER BY e.EmployeeID DESC, s.SalaryMonth DESC, s.SalaryID DESC
        """.format(employee_filter=employee_filter), params)
        salaries = cursor.fetchall()
        for s in salaries:
            s['SalaryID'] = int(s['SalaryID'] or 0)
            s['EmployeeID'] = int(s['EmployeeID'])
            s['BaseSalary'] = float(s['BaseSalary'] or 0)
            s['DefaultBaseSalary'] = float(s.get('DefaultBaseSalary') or 0)
            s['DefaultBaseSalaryEffectiveDate'] = str(s.get('DefaultBaseSalaryEffectiveDate')) if s.get('DefaultBaseSalaryEffectiveDate') else None
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


# =========================================================
# 2. CHẤM CÔNG
# =========================================================
@payroll_bp.route('/timekeeping', methods=['GET'])
@roles_required('Admin', 'Manager', 'Employee')
def get_timekeeping():
    my_conn = get_mysql_connection()
    if not my_conn:
        return jsonify({"error": "Lỗi kết nối DB"}), 500

    try:
        my_cursor = my_conn.cursor(dictionary=True)
        user = getattr(request, 'current_user', {})
        attendance_filter = ''
        params = ()
        if user.get('Role') == 'Employee':
            attendance_filter = 'WHERE a.EmployeeID = %s'
            params = (user.get('EmployeeID'),)

        my_cursor.execute("""
            SELECT 
                a.AttendanceID,
                a.EmployeeID,
                e.FullName,
                a.WorkDays,
                a.AbsentDays,
                a.LeaveDays,
                a.AttendanceMonth,
                a.CreatedAt
            FROM attendance a
            LEFT JOIN employees_payroll e ON a.EmployeeID = e.EmployeeID
            {attendance_filter}
            ORDER BY a.AttendanceMonth DESC, a.EmployeeID DESC
        """.format(attendance_filter=attendance_filter), params)
        attendances = my_cursor.fetchall()
        for a in attendances:
            a['AttendanceMonth'] = str(a['AttendanceMonth']) if a['AttendanceMonth'] else None
            a['CreatedAt'] = str(a['CreatedAt']) if a.get('CreatedAt') else None
        return jsonify(attendances), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        my_conn.close()


@payroll_bp.route('/attendance/employees', methods=['GET'])
@roles_required('Admin', 'Manager', 'Employee')
def attendance_employees():
    conn = get_mysql_connection()
    if not conn:
        return jsonify({"error": "Lỗi kết nối MySQL"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        user = getattr(request, 'current_user', {})
        employee_filter = ''
        params = ()
        if user.get('Role') == 'Employee':
            employee_filter = 'WHERE e.EmployeeID = %s'
            params = (user.get('EmployeeID'),)

        cursor.execute("""
            SELECT e.EmployeeID, e.FullName, e.DepartmentID, e.PositionID, e.Status,
                   COALESCE(d.DepartmentName, 'N/A') AS DepartmentName,
                   COALESCE(p.PositionName, 'N/A') AS PositionName
            FROM employees_payroll e
            LEFT JOIN departments_payroll d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN positions_payroll p ON e.PositionID = p.PositionID
            {employee_filter}
            ORDER BY e.EmployeeID DESC
        """.format(employee_filter=employee_filter), params)
        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@payroll_bp.route('/attendance/check', methods=['POST'])
@roles_required('Admin', 'Manager')
def save_attendance_check():
    data = request.json or {}
    conn = get_mysql_connection()
    if not conn:
        return jsonify({"error": "Lỗi kết nối MySQL"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        ensure_attendance_details_table(cursor)

        employee_id = data.get('EmployeeID')
        work_date_raw = data.get('WorkDate')
        status = data.get('Status') or 'Đi làm'
        note = data.get('Note') or ''

        if not employee_id:
            return jsonify({"error": "Vui lòng chọn nhân viên"}), 400
        if not work_date_raw:
            return jsonify({"error": "Vui lòng chọn ngày chấm công"}), 400

        work_date = parse_date_value(work_date_raw)
        check_in = parse_time_value(data.get('CheckIn'))
        check_out = parse_time_value(data.get('CheckOut'))

        if status == 'Đi làm' and (not check_in or not check_out):
            return jsonify({"error": "Đi làm thì phải nhập đủ giờ vào và giờ ra"}), 400

        total_hours = calculate_total_hours(check_in, check_out)
        work_unit = calculate_work_unit(total_hours, status)

        if status == 'Đi làm' and work_unit < 1 and not note.strip():
            note = 'Thiếu công do tổng giờ làm chưa đủ 8 tiếng'

        cursor.execute("""
            INSERT INTO attendance_details
                (EmployeeID, WorkDate, CheckIn, CheckOut, TotalHours, WorkUnit, Status, Note)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                CheckIn = VALUES(CheckIn),
                CheckOut = VALUES(CheckOut),
                TotalHours = VALUES(TotalHours),
                WorkUnit = VALUES(WorkUnit),
                Status = VALUES(Status),
                Note = VALUES(Note),
                UpdatedAt = CURRENT_TIMESTAMP
        """, (employee_id, work_date, check_in, check_out, total_hours, work_unit, status, note))

        summary = refresh_monthly_attendance_summary(cursor, employee_id, work_date.strftime('%Y-%m'))
        conn.commit()

        return jsonify({
            "message": "Lưu chấm công thành công",
            "EmployeeID": int(employee_id),
            "WorkDate": work_date.isoformat(),
            "CheckIn": to_json_time(check_in),
            "CheckOut": to_json_time(check_out),
            "TotalHours": total_hours,
            "WorkUnit": work_unit,
            "Status": status,
            "Note": note,
            "summary": summary,
        }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@payroll_bp.route('/attendance/details', methods=['GET'])
@roles_required('Admin', 'Manager', 'Employee')
def attendance_details():
    employee_id = request.args.get('employee_id')
    month_value = request.args.get('month')
    base_salary = float(request.args.get('base_salary') or 0)

    if not employee_id:
        return jsonify({"error": "Thiếu employee_id"}), 400
    if is_employee_requesting_other_employee(employee_id):
        return jsonify({"error": "Bạn chỉ được xem chấm công của chính mình"}), 403
    if not month_value:
        return jsonify({"error": "Thiếu month"}), 400

    conn = get_mysql_connection()
    if not conn:
        return jsonify({"error": "Lỗi kết nối MySQL"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        ensure_attendance_details_table(cursor)
        start, end = month_range(month_value)
        cursor.execute("""
            SELECT DetailID, EmployeeID, WorkDate, CheckIn, CheckOut, TotalHours,
                   WorkUnit, Status, Note, CreatedAt, UpdatedAt
            FROM attendance_details
            WHERE EmployeeID = %s AND WorkDate BETWEEN %s AND %s
            ORDER BY WorkDate DESC
        """, (employee_id, start, end))
        rows = cursor.fetchall()
        return jsonify(build_attendance_summary(rows, month_value, base_salary)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@payroll_bp.route('/attendance/summary', methods=['GET'])
@roles_required('Admin', 'Manager', 'Employee')
def attendance_summary():
    return attendance_details()




@payroll_bp.route('/attendance/seniority', methods=['GET'])
@roles_required('Admin', 'Manager', 'Employee')
def attendance_seniority():
    """Xem thâm niên theo công được ghi nhận trong chấm công.

    Công thức theo yêu cầu:
    - 26 công = 1 tháng.
    - 12 tháng = 1 năm.
    - Công tính thâm niên = công/ngày đã làm + ngày nghỉ phép được chấm.
    - Không cộng ngày nghỉ không phép hoặc ngày chưa có bản ghi chấm công.

    Nguồn ưu tiên:
    - attendance_details: lấy WorkUnit cho ngày đi làm và Status = 'Nghỉ phép'.
    - Nếu chưa có attendance_details thì fallback sang attendance.WorkDays + attendance.LeaveDays.
    """
    employee_id = request.args.get('employee_id')
    user = getattr(request, 'current_user', {})

    if user.get('Role') == 'Employee':
        employee_id = user.get('EmployeeID')

    if employee_id and is_employee_requesting_other_employee(employee_id):
        return jsonify({"error": "Bạn chỉ được xem thâm niên của chính mình"}), 403

    conn = get_mysql_connection()
    if not conn:
        return jsonify({"error": "Lỗi kết nối MySQL"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        ensure_attendance_details_table(cursor)

        where_sql = ''
        params = []
        if employee_id:
            where_sql = 'WHERE e.EmployeeID = %s'
            params.append(employee_id)

        cursor.execute(f"""
            SELECT
                e.EmployeeID,
                e.FullName,
                e.DepartmentID,
                e.PositionID,
                e.Status,
                COALESCE(d.DepartmentName, 'N/A') AS DepartmentName,
                COALESCE(p.PositionName, 'N/A') AS PositionName,
                COALESCE(SUM(a.WorkDays), 0) AS FallbackWorkDays,
                COALESCE(SUM(a.AbsentDays), 0) AS FallbackAbsentDays,
                COALESCE(SUM(a.LeaveDays), 0) AS FallbackLeaveDays,
                COUNT(a.AttendanceID) AS AttendanceMonthCount,
                MIN(a.AttendanceMonth) AS FirstAttendanceMonth,
                MAX(a.AttendanceMonth) AS LastAttendanceMonth
            FROM employees_payroll e
            LEFT JOIN departments_payroll d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN positions_payroll p ON e.PositionID = p.PositionID
            LEFT JOIN attendance a ON e.EmployeeID = a.EmployeeID
            {where_sql}
            GROUP BY e.EmployeeID, e.FullName, e.DepartmentID, e.PositionID, e.Status,
                     d.DepartmentName, p.PositionName
            ORDER BY e.EmployeeID ASC
        """, tuple(params))
        rows = cursor.fetchall()

        employee_ids = [int(row['EmployeeID']) for row in rows]
        detail_map = {}
        if employee_ids:
            placeholders = ','.join(['%s'] * len(employee_ids))
            cursor.execute(f"""
                SELECT
                    EmployeeID,
                    MIN(WorkDate) AS FirstWorkDate,
                    MAX(WorkDate) AS LastWorkDate,
                    COALESCE(SUM(TotalHours), 0) AS TotalHours,
                    COALESCE(SUM(CASE WHEN Status = 'Đi làm' THEN WorkUnit ELSE 0 END), 0) AS DetailWorkUnits,
                    COALESCE(SUM(CASE WHEN Status = 'Nghỉ phép' THEN 1 ELSE 0 END), 0) AS DetailLeaveDays,
                    COALESCE(SUM(CASE WHEN Status = 'Nghỉ không phép' THEN 1 ELSE 0 END), 0) AS DetailUnpaidAbsentDays,
                    COALESCE(SUM(CASE WHEN Status = 'Đi làm' AND WorkUnit > 0 THEN 1 ELSE 0 END), 0) AS RecordedWorkDays,
                    COALESCE(SUM(CASE WHEN Status = 'Đi làm' AND WorkUnit > 0 AND WorkUnit < 1 THEN 1 ELSE 0 END), 0) AS RecordedShortDays,
                    COUNT(*) AS DetailRecordCount
                FROM attendance_details
                WHERE EmployeeID IN ({placeholders})
                GROUP BY EmployeeID
            """, tuple(employee_ids))
            for detail in cursor.fetchall():
                detail_map[int(detail['EmployeeID'])] = detail

        seniority = []
        total_work_days_all = 0.0
        total_leave_days_all = 0.0
        total_absent_days_all = 0.0
        total_hours_all = 0.0
        total_valid_days_all = 0.0

        for row in rows:
            emp_id = int(row['EmployeeID'])
            detail = detail_map.get(emp_id, {})
            has_detail = int(detail.get('DetailRecordCount') or 0) > 0

            fallback_work_days = float(row.get('FallbackWorkDays') or 0)
            fallback_leave_days = float(row.get('FallbackLeaveDays') or 0)
            fallback_absent_days = float(row.get('FallbackAbsentDays') or 0)

            if has_detail:
                total_work_days = float(detail.get('DetailWorkUnits') or 0)
                total_leave_days = float(detail.get('DetailLeaveDays') or 0)
                total_absent_days = float(detail.get('DetailUnpaidAbsentDays') or 0)
                total_hours = float(detail.get('TotalHours') or 0)
                first_attendance = detail.get('FirstWorkDate')
                last_attendance = detail.get('LastWorkDate')
                recorded_work_days = int(detail.get('RecordedWorkDays') or 0)
                recorded_short_days = int(detail.get('RecordedShortDays') or 0)
            else:
                total_work_days = fallback_work_days
                total_leave_days = fallback_leave_days
                total_absent_days = fallback_absent_days
                total_hours = 0.0
                first_attendance = row.get('FirstAttendanceMonth')
                last_attendance = row.get('LastAttendanceMonth')
                recorded_work_days = int(round(fallback_work_days))
                recorded_short_days = 0

            # Công hợp lệ để tính thâm niên: công đã làm + nghỉ phép được chấm.
            total_valid_days = total_work_days + total_leave_days
            duration = format_seniority_by_work_units(total_valid_days)

            total_work_days_all += total_work_days
            total_leave_days_all += total_leave_days
            total_absent_days_all += total_absent_days
            total_hours_all += total_hours
            total_valid_days_all += total_valid_days

            seniority.append({
                'EmployeeID': emp_id,
                'FullName': row.get('FullName'),
                'DepartmentID': row.get('DepartmentID'),
                'PositionID': row.get('PositionID'),
                'DepartmentName': row.get('DepartmentName') or 'N/A',
                'PositionName': row.get('PositionName') or 'N/A',
                'Status': row.get('Status'),
                'FirstAttendanceDate': to_json_date(first_attendance),
                'LastAttendanceDate': to_json_date(last_attendance),
                'AttendanceMonthCount': int(row.get('AttendanceMonthCount') or 0),
                'TotalWorkDays': round(total_work_days, 2),
                'TotalLeaveDays': round(total_leave_days, 2),
                'TotalAbsentDays': round(total_absent_days, 2),
                'TotalValidDays': round(total_valid_days, 2),
                'TotalHours': round(total_hours, 2),
                'RecordedWorkDays': recorded_work_days,
                'RecordedShortDays': recorded_short_days,
                'SeniorityYears': duration['years'],
                'SeniorityMonths': duration['months'],
                'SeniorityDays': duration['days'],
                'SeniorityText': duration['text'],
                'SalaryRaiseSuggestion': build_salary_raise_suggestion(total_valid_days),
            })

        return jsonify({
            'employees': seniority,
            'summary': {
                'EmployeeCount': len(seniority),
                'TotalWorkDays': round(total_work_days_all, 2),
                'TotalLeaveDays': round(total_leave_days_all, 2),
                'TotalAbsentDays': round(total_absent_days_all, 2),
                'TotalValidDays': round(total_valid_days_all, 2),
                'TotalHours': round(total_hours_all, 2),
                'RuleText': 'Thâm niên = Tổng công đã làm + nghỉ phép được chấm; 26 công = 1 tháng.'
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


def build_salary_raise_suggestion(total_valid_days, base_salary=0):
    total_valid_days = float(total_valid_days or 0)
    years = int(total_valid_days // 312)
    if years <= 0:
        return {
            'Eligible': False,
            'Level': 'none',
            'SuggestedPercent': 0,
            'SuggestedAmount': 0,
            'Text': 'Chưa đủ 1 năm thâm niên'
        }

    if years >= 5:
        percent, level = 10, 'high'
    elif years >= 3:
        percent, level = 7, 'medium'
    else:
        percent, level = 5, 'low'

    return {
        'Eligible': True,
        'Level': level,
        'SuggestedPercent': percent,
        'SuggestedAmount': round(float(base_salary or 0) * percent / 100, 2),
        'Text': f'Gợi ý tăng {percent}% lương cơ bản vì đã đạt {years} năm thâm niên'
    }


def salary_report_rows(cursor, month_value=None, employee_id=None):
    where = []
    params = []
    if month_value:
        where.append("DATE_FORMAT(s.SalaryMonth, '%Y-%m') = %s")
        params.append(str(month_value)[:7])
    if employee_id:
        where.append('s.EmployeeID = %s')
        params.append(employee_id)
    where_sql = 'WHERE ' + ' AND '.join(where) if where else ''

    cursor.execute(f"""
        SELECT
            s.SalaryID, s.EmployeeID, e.FullName,
            COALESCE(d.DepartmentName, 'N/A') AS DepartmentName,
            COALESCE(p.PositionName, 'N/A') AS PositionName,
            e.Status, s.SalaryMonth, s.BaseSalary, s.Bonus, s.Deductions,
            s.NetSalary, s.CreatedAt
        FROM salaries s
        LEFT JOIN employees_payroll e ON s.EmployeeID = e.EmployeeID
        LEFT JOIN departments_payroll d ON e.DepartmentID = d.DepartmentID
        LEFT JOIN positions_payroll p ON e.PositionID = p.PositionID
        {where_sql}
        ORDER BY s.SalaryMonth DESC, s.EmployeeID ASC, s.SalaryID DESC
    """, tuple(params))
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            'SalaryID': int(row.get('SalaryID') or 0),
            'EmployeeID': int(row.get('EmployeeID') or 0),
            'FullName': row.get('FullName') or 'N/A',
            'DepartmentName': row.get('DepartmentName') or 'N/A',
            'PositionName': row.get('PositionName') or 'N/A',
            'Status': row.get('Status') or 'N/A',
            'SalaryMonth': to_json_date(row.get('SalaryMonth')),
            'BaseSalary': float(row.get('BaseSalary') or 0),
            'Bonus': float(row.get('Bonus') or 0),
            'Deductions': float(row.get('Deductions') or 0),
            'NetSalary': float(row.get('NetSalary') or 0),
            'CreatedAt': str(row.get('CreatedAt')) if row.get('CreatedAt') else None,
        })
    return result




def _salary_pdf_font_name():
    if pdfmetrics is None or TTFont is None:
        return 'Helvetica'

    candidates = [
        os.path.join(os.getcwd(), 'DejaVuSans.ttf'),
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/calibri.ttf',
    ]

    for path in candidates:
        try:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('PayrollUnicode', path))
                return 'PayrollUnicode'
        except Exception:
            continue

    return 'Helvetica'


def _pdf_text(value):
    text = '' if value is None else str(value)
    if _salary_pdf_font_name() != 'Helvetica':
        return text
    # Fallback khi máy chưa có font unicode: bỏ dấu để PDF không lỗi encoding.
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')


def _format_money_vnd(value):
    try:
        return f"{float(value or 0):,.0f} VND".replace(',', '.')
    except Exception:
        return '0 VND'


def build_salary_report_pdf(rows, summary):
    if SimpleDocTemplate is None:
        raise RuntimeError('Thiếu thư viện reportlab. Hãy cài: pip install reportlab')

    font_name = _salary_pdf_font_name()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=8 * mm,
        leftMargin=8 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
    )

    styles = getSampleStyleSheet()
    styles['Title'].fontName = font_name
    styles['Normal'].fontName = font_name

    month_label = summary.get('Month') or 'Tat ca'
    employee_label = summary.get('EmployeeID') or 'Tat ca nhan vien'
    story = [
        Paragraph(_pdf_text(f"BAO CAO BANG LUONG - {month_label}"), styles['Title']),
        Spacer(1, 4 * mm),
        Paragraph(_pdf_text(
            f"Nhan vien: {employee_label} | So ban ghi: {summary.get('RecordCount', 0)} | "
            f"Tong thuc nhan: {_format_money_vnd(summary.get('TotalNetSalary'))}"
        ), styles['Normal']),
        Spacer(1, 5 * mm),
    ]

    table_data = [[
        _pdf_text('Ma NV'), _pdf_text('Ho va ten'), _pdf_text('Phong ban'),
        _pdf_text('Chuc vu'), _pdf_text('Thang'), _pdf_text('Luong co ban'),
        _pdf_text('Thuong'), _pdf_text('Khau tru'), _pdf_text('Thuc nhan'), _pdf_text('Trang thai')
    ]]

    for row in rows:
        table_data.append([
            row.get('EmployeeID'),
            _pdf_text(row.get('FullName')),
            _pdf_text(row.get('DepartmentName')),
            _pdf_text(row.get('PositionName')),
            _pdf_text(str(row.get('SalaryMonth') or '')[:10]),
            _format_money_vnd(row.get('BaseSalary')),
            _format_money_vnd(row.get('Bonus')),
            _format_money_vnd(row.get('Deductions')),
            _format_money_vnd(row.get('NetSalary')),
            _pdf_text(row.get('Status')),
        ])

    table = Table(table_data, repeatRows=1, colWidths=[16*mm, 36*mm, 34*mm, 28*mm, 22*mm, 27*mm, 23*mm, 23*mm, 28*mm, 25*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#d1d5db')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (5, 1), (8, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
@payroll_bp.route('/report-salaries', methods=['GET'])
@roles_required('Admin', 'Manager', 'Employee')
def report_salaries():
    user = getattr(request, 'current_user', {})
    month_value = request.args.get('month') or request.args.get('salary_month')
    employee_id = request.args.get('employee_id')
    export_format = (request.args.get('format') or 'json').lower()

    if user.get('Role') == 'Employee':
        employee_id = user.get('EmployeeID')
    elif employee_id:
        try:
            employee_id = int(employee_id)
        except Exception:
            return jsonify({'error': 'employee_id không hợp lệ'}), 400

    conn = get_mysql_connection()
    if not conn:
        return jsonify({'error': 'Lỗi kết nối MySQL'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        rows = salary_report_rows(cursor, month_value, employee_id)
        summary = {
            'EmployeeCount': len({r['EmployeeID'] for r in rows}),
            'RecordCount': len(rows),
            'TotalBaseSalary': round(sum(r['BaseSalary'] for r in rows), 2),
            'TotalBonus': round(sum(r['Bonus'] for r in rows), 2),
            'TotalDeductions': round(sum(r['Deductions'] for r in rows), 2),
            'TotalNetSalary': round(sum(r['NetSalary'] for r in rows), 2),
            'Month': str(month_value)[:7] if month_value else None,
            'EmployeeID': int(employee_id) if employee_id else None,
        }

        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Ma NV', 'Ho va ten', 'Phong ban', 'Chuc vu', 'Thang luong', 'Luong co ban', 'Thuong', 'Khau tru', 'Thuc nhan', 'Trang thai'])
            for row in rows:
                writer.writerow([row['EmployeeID'], row['FullName'], row['DepartmentName'], row['PositionName'], row['SalaryMonth'], row['BaseSalary'], row['Bonus'], row['Deductions'], row['NetSalary'], row['Status']])
            filename = f"bao-cao-luong-{summary['Month'] or 'tat-ca'}"
            if summary['EmployeeID']:
                filename += f"-nv-{summary['EmployeeID']}"
            filename += '.csv'
            return Response('\ufeff' + output.getvalue(), mimetype='text/csv; charset=utf-8', headers={'Content-Disposition': f'attachment; filename="{filename}"'})

        if export_format == 'pdf':
            pdf_bytes = build_salary_report_pdf(rows, summary)
            filename = f"bao-cao-luong-{summary['Month'] or 'tat-ca'}"
            if summary['EmployeeID']:
                filename += f"-nv-{summary['EmployeeID']}"
            filename += '.pdf'
            return Response(
                pdf_bytes,
                mimetype='application/pdf',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )

        return jsonify({'salaries': rows, 'summary': summary}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@payroll_bp.route('/employee-anniversary-warning', methods=['GET'])
@roles_required('Admin', 'Manager')
def employee_anniversary_warning():
    conn = get_mysql_connection()
    if not conn:
        return jsonify({'error': 'Lỗi kết nối MySQL'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        ensure_attendance_details_table(cursor)
        cursor.execute("""
            SELECT
                e.EmployeeID, e.FullName, e.Status,
                COALESCE(d.DepartmentName, 'N/A') AS DepartmentName,
                COALESCE(p.PositionName, 'N/A') AS PositionName,
                COALESCE(SUM(CASE WHEN ad.Status = 'Đi làm' THEN ad.WorkUnit ELSE 0 END), 0) AS WorkUnits,
                COALESCE(SUM(CASE WHEN ad.Status = 'Nghỉ phép' THEN 1 ELSE 0 END), 0) AS LeaveDays,
                COALESCE(MAX(s.BaseSalary), 0) AS BaseSalary
            FROM employees_payroll e
            LEFT JOIN departments_payroll d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN positions_payroll p ON e.PositionID = p.PositionID
            LEFT JOIN attendance_details ad ON e.EmployeeID = ad.EmployeeID
            LEFT JOIN salaries s ON e.EmployeeID = s.EmployeeID
            GROUP BY e.EmployeeID, e.FullName, e.Status, d.DepartmentName, p.PositionName
            ORDER BY e.EmployeeID ASC
        """)
        warnings = []
        for row in cursor.fetchall():
            total_valid_days = float(row.get('WorkUnits') or 0) + float(row.get('LeaveDays') or 0)
            suggestion = build_salary_raise_suggestion(total_valid_days, row.get('BaseSalary'))
            if suggestion['Eligible']:
                duration = format_seniority_by_work_units(total_valid_days)
                warnings.append({
                    'EmployeeID': int(row['EmployeeID']),
                    'FullName': row.get('FullName'),
                    'DepartmentName': row.get('DepartmentName'),
                    'PositionName': row.get('PositionName'),
                    'Status': row.get('Status'),
                    'TotalValidDays': round(total_valid_days, 2),
                    'SeniorityText': duration['text'],
                    'BaseSalary': float(row.get('BaseSalary') or 0),
                    'RaiseSuggestion': suggestion,
                })
        return jsonify({'warnings': warnings, 'total': len(warnings)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@payroll_bp.route('/leave-days-warning', methods=['GET'])
@roles_required('Admin', 'Manager')
def leave_days_warning():
    month_value = request.args.get('month') or datetime.now().strftime('%Y-%m')
    leave_threshold = int(request.args.get('leave_threshold') or 3)
    absent_threshold = int(request.args.get('absent_threshold') or 1)
    conn = get_mysql_connection()
    if not conn:
        return jsonify({'error': 'Lỗi kết nối MySQL'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        ensure_attendance_details_table(cursor)
        cursor.execute("""
            SELECT
                e.EmployeeID, e.FullName, e.Status,
                COALESCE(d.DepartmentName, 'N/A') AS DepartmentName,
                COALESCE(p.PositionName, 'N/A') AS PositionName,
                COALESCE(SUM(CASE WHEN ad.Status = 'Nghỉ phép' THEN 1 ELSE 0 END), 0) AS LeaveDays,
                COALESCE(SUM(CASE WHEN ad.Status = 'Nghỉ không phép' THEN 1 ELSE 0 END), 0) AS UnpaidAbsentDays,
                COALESCE(SUM(CASE WHEN ad.Status = 'Đi làm' AND ad.WorkUnit > 0 AND ad.WorkUnit < 1 THEN 1 ELSE 0 END), 0) AS ShortDays
            FROM employees_payroll e
            LEFT JOIN departments_payroll d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN positions_payroll p ON e.PositionID = p.PositionID
            LEFT JOIN attendance_details ad ON e.EmployeeID = ad.EmployeeID AND DATE_FORMAT(ad.WorkDate, '%Y-%m') = %s
            GROUP BY e.EmployeeID, e.FullName, e.Status, d.DepartmentName, p.PositionName
            HAVING LeaveDays >= %s OR UnpaidAbsentDays >= %s OR ShortDays > 0
            ORDER BY UnpaidAbsentDays DESC, LeaveDays DESC, ShortDays DESC, e.EmployeeID ASC
        """, (month_value[:7], leave_threshold, absent_threshold))
        warnings = []
        for row in cursor.fetchall():
            reasons = []
            if int(row.get('LeaveDays') or 0) >= leave_threshold:
                reasons.append(f"Nghỉ phép {int(row.get('LeaveDays') or 0)} ngày")
            if int(row.get('UnpaidAbsentDays') or 0) >= absent_threshold:
                reasons.append(f"Nghỉ không phép {int(row.get('UnpaidAbsentDays') or 0)} ngày")
            if int(row.get('ShortDays') or 0) > 0:
                reasons.append(f"Thiếu công {int(row.get('ShortDays') or 0)} ngày")
            warnings.append({
                'EmployeeID': int(row['EmployeeID']),
                'FullName': row.get('FullName'),
                'DepartmentName': row.get('DepartmentName'),
                'PositionName': row.get('PositionName'),
                'Status': row.get('Status'),
                'Month': month_value[:7],
                'LeaveDays': int(row.get('LeaveDays') or 0),
                'UnpaidAbsentDays': int(row.get('UnpaidAbsentDays') or 0),
                'ShortDays': int(row.get('ShortDays') or 0),
                'Reasons': reasons,
            })
        return jsonify({'warnings': warnings, 'total': len(warnings), 'month': month_value[:7]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@payroll_bp.route('/salary-alerts', methods=['GET'])
@roles_required('Admin', 'Manager')
def salary_alerts():
    month_value = request.args.get('month') or datetime.now().strftime('%Y-%m')
    conn = get_mysql_connection()
    if not conn:
        return jsonify({'error': 'Lỗi kết nối MySQL'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        alerts = []
        cursor.execute("""
            SELECT e.EmployeeID, e.FullName,
                   COALESCE(d.DepartmentName, 'N/A') AS DepartmentName,
                   COALESCE(p.PositionName, 'N/A') AS PositionName,
                   e.Status, s.SalaryID, s.SalaryMonth, s.BaseSalary, s.Bonus, s.Deductions, s.NetSalary
            FROM employees_payroll e
            LEFT JOIN departments_payroll d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN positions_payroll p ON e.PositionID = p.PositionID
            LEFT JOIN salaries s ON e.EmployeeID = s.EmployeeID AND DATE_FORMAT(s.SalaryMonth, '%Y-%m') = %s
            ORDER BY e.EmployeeID ASC
        """, (month_value[:7],))
        for row in cursor.fetchall():
            base = float(row.get('BaseSalary') or 0)
            bonus = float(row.get('Bonus') or 0)
            deductions = float(row.get('Deductions') or 0)
            net = float(row.get('NetSalary') or 0)
            expected_net = base + bonus - deductions
            reasons = []
            severity = 'medium'
            if not row.get('SalaryID'):
                reasons.append('Chưa có bảng lương tháng này')
                severity = 'high'
            else:
                if base <= 0:
                    reasons.append('Lương cơ bản bằng 0')
                    severity = 'high'
                if abs(expected_net - net) > 1:
                    reasons.append('Thực nhận không khớp lương cơ bản + thưởng - khấu trừ')
                    severity = 'high'
                if net < 0:
                    reasons.append('Thực nhận âm')
                    severity = 'high'
                if deductions > base * 0.5 and base > 0:
                    reasons.append('Khấu trừ vượt 50% lương cơ bản')
            if reasons:
                alerts.append({
                    'EmployeeID': int(row['EmployeeID']),
                    'FullName': row.get('FullName'),
                    'DepartmentName': row.get('DepartmentName'),
                    'PositionName': row.get('PositionName'),
                    'Status': row.get('Status'),
                    'Month': month_value[:7],
                    'SalaryID': row.get('SalaryID'),
                    'BaseSalary': base,
                    'Bonus': bonus,
                    'Deductions': deductions,
                    'NetSalary': net,
                    'Severity': severity,
                    'Reasons': reasons,
                })
        return jsonify({'alerts': alerts, 'total': len(alerts), 'month': month_value[:7]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# =========================================================
# 3. CẬP NHẬT/TẠO BẢNG LƯƠNG
# =========================================================
@payroll_bp.route('/update-salary', methods=['POST'])
@roles_required('Admin', 'Manager')
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

        if not salary_month:
            cursor.execute("SELECT DATE_FORMAT(CURDATE(), '%Y-%m-01') AS current_month")
            salary_month = cursor.fetchone()["current_month"]

        if salary_id and int(salary_id) > 0:
            cursor.execute("""
                UPDATE salaries
                SET BaseSalary=%s, Bonus=%s, Deductions=%s, NetSalary=%s, SalaryMonth=%s
                WHERE SalaryID=%s
            """, (base, bonus, deduct, net_salary, salary_month, salary_id))
            final_salary_id = int(salary_id)
        else:
            cursor.execute("SELECT EmployeeID FROM employees_payroll WHERE EmployeeID = %s", (employee_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Nhân viên chưa tồn tại trong hệ thống payroll"}), 404

            cursor.execute("""
                SELECT SalaryID FROM salaries
                WHERE EmployeeID = %s AND SalaryMonth = %s
                LIMIT 1
            """, (employee_id, salary_month))
            existing_salary = cursor.fetchone()

            if existing_salary:
                cursor.execute("""
                    UPDATE salaries
                    SET BaseSalary=%s, Bonus=%s, Deductions=%s, NetSalary=%s
                    WHERE SalaryID=%s
                """, (base, bonus, deduct, net_salary, existing_salary["SalaryID"]))
                final_salary_id = existing_salary["SalaryID"]
            else:
                cursor.execute("""
                    INSERT INTO salaries (EmployeeID, SalaryMonth, BaseSalary, Bonus, Deductions, NetSalary)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (employee_id, salary_month, base, bonus, deduct, net_salary))
                final_salary_id = cursor.lastrowid

        conn.commit()
        return jsonify({
            "message": "Cập nhật lương thành công",
            "SalaryID": final_salary_id,
            "EmployeeID": int(employee_id) if employee_id else None,
            "SalaryMonth": str(salary_month),
            "BaseSalary": base,
            "Bonus": bonus,
            "Deductions": deduct,
            "NetSalary": net_salary,
        }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# =========================================================
# 4. GỬI EMAIL THÔNG TIN NHÂN VIÊN / CHẤM CÔNG / PHIẾU LƯƠNG
# =========================================================
def format_vnd(value):
    try:
        return f"{float(value or 0):,.0f}".replace(',', '.') + ' VNĐ'
    except Exception:
        return '0 VNĐ'


def normalize_month_value(month_value):
    if not month_value:
        return datetime.now().strftime('%Y-%m')
    return str(month_value)[:7]


def salary_month_date(month_value):
    return normalize_month_value(month_value) + '-01'


def build_employee_email_html(employee, salary=None, attendance=None, options=None, month_value=None):
    options = options or {}
    month_text = normalize_month_value(month_value)

    html = f'''
    <div style="font-family: Arial, sans-serif; color: #0f172a; line-height: 1.5;">
        <h2 style="margin-bottom: 4px;">HR & Payroll</h2>
        <p style="margin-top: 0; color: #64748b;">Thông tin nhân viên tháng {month_text}</p>
        <p>Chào <b>{employee.get('FullName') or 'nhân viên'}</b>,</p>
    '''

    if options.get('sendProfile'):
        html += f'''
        <h3 style="margin-top: 24px;">1. Thông tin cá nhân</h3>
        <table cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; border: 1px solid #e5e7eb;">
            <tr><td style="border:1px solid #e5e7eb;"><b>Mã nhân viên</b></td><td style="border:1px solid #e5e7eb;">{employee.get('EmployeeID') or ''}</td></tr>
            <tr><td style="border:1px solid #e5e7eb;"><b>Họ và tên</b></td><td style="border:1px solid #e5e7eb;">{employee.get('FullName') or ''}</td></tr>
            <tr><td style="border:1px solid #e5e7eb;"><b>Email</b></td><td style="border:1px solid #e5e7eb;">{employee.get('Email') or ''}</td></tr>
            <tr><td style="border:1px solid #e5e7eb;"><b>Ngày sinh</b></td><td style="border:1px solid #e5e7eb;">{employee.get('DateOfBirth') or ''}</td></tr>
            <tr><td style="border:1px solid #e5e7eb;"><b>Giới tính</b></td><td style="border:1px solid #e5e7eb;">{employee.get('Gender') or ''}</td></tr>
            <tr><td style="border:1px solid #e5e7eb;"><b>Số điện thoại</b></td><td style="border:1px solid #e5e7eb;">{employee.get('PhoneNumber') or ''}</td></tr>
            <tr><td style="border:1px solid #e5e7eb;"><b>Ngày vào làm</b></td><td style="border:1px solid #e5e7eb;">{employee.get('HireDate') or ''}</td></tr>
            <tr><td style="border:1px solid #e5e7eb;"><b>Phòng ban</b></td><td style="border:1px solid #e5e7eb;">{employee.get('DepartmentName') or 'Chưa có'}</td></tr>
            <tr><td style="border:1px solid #e5e7eb;"><b>Chức vụ</b></td><td style="border:1px solid #e5e7eb;">{employee.get('PositionName') or 'Chưa có'}</td></tr>
            <tr><td style="border:1px solid #e5e7eb;"><b>Trạng thái</b></td><td style="border:1px solid #e5e7eb;">{employee.get('Status') or 'Chưa có'}</td></tr>
        </table>
        '''

    if options.get('sendAttendance'):
        if attendance:
            html += f'''
            <h3 style="margin-top: 24px;">2. Bảng chấm công tháng {month_text}</h3>
            <table cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; border: 1px solid #e5e7eb;">
                <tr><td style="border:1px solid #e5e7eb;"><b>Công chuẩn</b></td><td style="border:1px solid #e5e7eb;">{attendance.get('standardWorkDays')}</td></tr>
                <tr><td style="border:1px solid #e5e7eb;"><b>Công thực tế</b></td><td style="border:1px solid #e5e7eb;">{attendance.get('workDays')}</td></tr>
                <tr><td style="border:1px solid #e5e7eb;"><b>Tổng giờ làm</b></td><td style="border:1px solid #e5e7eb;">{attendance.get('totalHours')} giờ</td></tr>
                <tr><td style="border:1px solid #e5e7eb;"><b>Nghỉ phép</b></td><td style="border:1px solid #e5e7eb;">{attendance.get('leaveDays')}</td></tr>
                <tr><td style="border:1px solid #e5e7eb;"><b>Ngày nghỉ/thiếu ghi nhận</b></td><td style="border:1px solid #e5e7eb;">{attendance.get('absentDays')}</td></tr>
                <tr><td style="border:1px solid #e5e7eb;"><b>Khấu trừ đề xuất</b></td><td style="border:1px solid #e5e7eb;">{format_vnd(attendance.get('suggestedDeductions'))}</td></tr>
            </table>
            '''
            details = attendance.get('details') or []
            if details:
                html += '''
                <table cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; border: 1px solid #e5e7eb; margin-top: 10px; font-size: 13px;">
                    <thead>
                        <tr style="background:#f8fafc;">
                            <th style="border:1px solid #e5e7eb; text-align:left;">Ngày</th>
                            <th style="border:1px solid #e5e7eb; text-align:left;">Giờ vào</th>
                            <th style="border:1px solid #e5e7eb; text-align:left;">Giờ ra</th>
                            <th style="border:1px solid #e5e7eb; text-align:left;">Tổng giờ</th>
                            <th style="border:1px solid #e5e7eb; text-align:left;">Công</th>
                            <th style="border:1px solid #e5e7eb; text-align:left;">Trạng thái</th>
                            <th style="border:1px solid #e5e7eb; text-align:left;">Ghi chú</th>
                        </tr>
                    </thead><tbody>
                '''
                for d in details:
                    html += f'''
                    <tr>
                        <td style="border:1px solid #e5e7eb;">{d.get('WorkDate') or ''}</td>
                        <td style="border:1px solid #e5e7eb;">{d.get('CheckIn') or ''}</td>
                        <td style="border:1px solid #e5e7eb;">{d.get('CheckOut') or ''}</td>
                        <td style="border:1px solid #e5e7eb;">{d.get('TotalHours') or 0}</td>
                        <td style="border:1px solid #e5e7eb;">{d.get('WorkUnit') or 0}</td>
                        <td style="border:1px solid #e5e7eb;">{d.get('Status') or ''}</td>
                        <td style="border:1px solid #e5e7eb;">{d.get('Note') or ''}</td>
                    </tr>
                    '''
                html += '</tbody></table>'
        else:
            html += f'<h3 style="margin-top: 24px;">2. Bảng chấm công tháng {month_text}</h3><p>Chưa có dữ liệu chấm công.</p>'

    if options.get('sendSalary'):
        if salary:
            html += f'''
            <h3 style="margin-top: 24px;">3. Bảng lương tháng {month_text}</h3>
            <table cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; border: 1px solid #e5e7eb;">
                <tr><td style="border:1px solid #e5e7eb;"><b>Lương cơ bản</b></td><td style="border:1px solid #e5e7eb;">{format_vnd(salary.get('BaseSalary'))}</td></tr>
                <tr><td style="border:1px solid #e5e7eb;"><b>Thưởng</b></td><td style="border:1px solid #e5e7eb;">{format_vnd(salary.get('Bonus'))}</td></tr>
                <tr><td style="border:1px solid #e5e7eb;"><b>Khấu trừ</b></td><td style="border:1px solid #e5e7eb;">{format_vnd(salary.get('Deductions'))}</td></tr>
                <tr><td style="border:1px solid #e5e7eb;"><b>Lương thực nhận</b></td><td style="border:1px solid #e5e7eb;"><b style="color:#047857;">{format_vnd(salary.get('NetSalary'))}</b></td></tr>
            </table>
            '''
        else:
            html += f'<h3 style="margin-top: 24px;">3. Bảng lương tháng {month_text}</h3><p>Chưa có dữ liệu lương.</p>'

    html += '''
        <p style="margin-top: 24px; color: #64748b;">Email này được gửi tự động từ hệ thống HR & Payroll.</p>
    </div>
    '''
    return html


@payroll_bp.route('/send-salary-emails', methods=['GET', 'POST'])
@roles_required('Admin', 'Manager')
def send_emails():
    my_conn = get_mysql_connection()
    sql_conn = get_sqlserver_connection()
    if not my_conn or not sql_conn:
        return jsonify({"error": "Lỗi kết nối cơ sở dữ liệu"}), 500

    try:
        data = (request.json or {}) if request.method == 'POST' else {}
        month_value = normalize_month_value(data.get('month'))
        selected_ids = data.get('employeeIds') or []
        select_all = bool(data.get('selectAll')) or request.method == 'GET'

        options = {
            'sendProfile': bool(data.get('sendProfile')) or request.method == 'GET',
            'sendAttendance': bool(data.get('sendAttendance')),
            'sendSalary': bool(data.get('sendSalary')) or request.method == 'GET',
        }

        if not any(options.values()):
            return jsonify({"error": "Vui lòng chọn ít nhất một nội dung email cần gửi"}), 400

        sql_cursor = sql_conn.cursor()
        if select_all:
            sql_cursor.execute("""
                SELECT e.EmployeeID, e.FullName, e.DateOfBirth, e.Gender, e.PhoneNumber, e.Email, e.HireDate,
                       e.DepartmentID, e.PositionID, e.Status,
                       d.DepartmentName, p.PositionName
                FROM Employees e
                LEFT JOIN Departments d ON e.DepartmentID = d.DepartmentID
                LEFT JOIN Positions p ON e.PositionID = p.PositionID
                WHERE e.Email IS NOT NULL AND LTRIM(RTRIM(e.Email)) <> ''
                ORDER BY e.EmployeeID
            """)
        else:
            ids = [int(x) for x in selected_ids if str(x).strip().isdigit()]
            if not ids:
                return jsonify({"error": "Vui lòng chọn ít nhất một nhân viên"}), 400
            placeholders = ','.join(['?'] * len(ids))
            sql_cursor.execute(f"""
                SELECT e.EmployeeID, e.FullName, e.DateOfBirth, e.Gender, e.PhoneNumber, e.Email, e.HireDate,
                       e.DepartmentID, e.PositionID, e.Status,
                       d.DepartmentName, p.PositionName
                FROM Employees e
                LEFT JOIN Departments d ON e.DepartmentID = d.DepartmentID
                LEFT JOIN Positions p ON e.PositionID = p.PositionID
                WHERE e.EmployeeID IN ({placeholders})
                ORDER BY e.EmployeeID
            """, tuple(ids))

        employee_rows = sql_cursor.fetchall()
        employees = []
        for r in employee_rows:
            employees.append({
                'EmployeeID': int(r[0]),
                'FullName': r[1],
                'DateOfBirth': str(r[2])[:10] if r[2] else None,
                'Gender': r[3],
                'PhoneNumber': r[4],
                'Email': r[5],
                'HireDate': str(r[6])[:10] if r[6] else None,
                'DepartmentID': r[7],
                'PositionID': r[8],
                'Status': r[9],
                'DepartmentName': r[10],
                'PositionName': r[11],
            })

        if not employees:
            return jsonify({"error": "Không tìm thấy nhân viên phù hợp để gửi email"}), 404

        employee_ids = [e['EmployeeID'] for e in employees]
        my_cursor = my_conn.cursor(dictionary=True)

        salaries_by_employee = {}
        if options.get('sendSalary'):
            placeholders = ','.join(['%s'] * len(employee_ids))
            my_cursor.execute(f"""
                SELECT SalaryID, EmployeeID, SalaryMonth, BaseSalary, Bonus, Deductions, NetSalary, CreatedAt
                FROM salaries
                WHERE EmployeeID IN ({placeholders}) AND SalaryMonth = %s
            """, tuple(employee_ids + [salary_month_date(month_value)]))
            for s in my_cursor.fetchall():
                salaries_by_employee[int(s['EmployeeID'])] = s

        attendance_by_employee = {}
        if options.get('sendAttendance'):
            ensure_attendance_details_table(my_cursor)
            start, end = month_range(month_value)
            placeholders = ','.join(['%s'] * len(employee_ids))
            my_cursor.execute(f"""
                SELECT DetailID, EmployeeID, WorkDate, CheckIn, CheckOut, TotalHours,
                       WorkUnit, Status, Note, CreatedAt, UpdatedAt
                FROM attendance_details
                WHERE EmployeeID IN ({placeholders}) AND WorkDate BETWEEN %s AND %s
                ORDER BY WorkDate DESC
            """, tuple(employee_ids + [start, end]))
            grouped = {emp_id: [] for emp_id in employee_ids}
            for row in my_cursor.fetchall():
                grouped.setdefault(int(row['EmployeeID']), []).append(row)

            for emp in employees:
                base_salary = 0
                salary_row = salaries_by_employee.get(emp['EmployeeID'])
                if salary_row:
                    base_salary = salary_row.get('BaseSalary') or 0
                attendance_by_employee[emp['EmployeeID']] = build_attendance_summary(
                    grouped.get(emp['EmployeeID'], []),
                    month_value,
                    base_salary,
                )

        sent_count = 0
        failed = []
        skipped = []
        results = []
        for emp in employees:
            email = (emp.get('Email') or '').strip()
            if not email:
                skipped.append({
                    'EmployeeID': emp.get('EmployeeID'),
                    'FullName': emp.get('FullName'),
                    'reason': 'Nhân viên chưa có email',
                })
                continue

            salary = salaries_by_employee.get(emp['EmployeeID'])
            attendance = attendance_by_employee.get(emp['EmployeeID'])
            subject_parts = []
            if options.get('sendProfile'):
                subject_parts.append('thông tin cá nhân')
            if options.get('sendAttendance'):
                subject_parts.append('chấm công')
            if options.get('sendSalary'):
                subject_parts.append('bảng lương')
            subject = 'HR & Payroll - ' + ', '.join(subject_parts).capitalize() + f' tháng {month_value}'
            html = build_employee_email_html(emp, salary, attendance, options, month_value)

            success, send_error = send_email_logic(email, subject, html)
            if success:
                sent_count += 1
                results.append({
                    'EmployeeID': emp.get('EmployeeID'),
                    'FullName': emp.get('FullName'),
                    'Email': email,
                    'status': 'Đã gửi',
                })
            else:
                failed.append({
                    'EmployeeID': emp.get('EmployeeID'),
                    'FullName': emp.get('FullName'),
                    'Email': email,
                    'reason': send_error or 'Gửi email thất bại',
                })

        return jsonify({
            'message': f'Đã gửi {sent_count}/{len(employees)} email',
            'sent_count': sent_count,
            'total_selected': len(employees),
            'month': month_value,
            'options': options,
            'results': results,
            'failed': failed,
            'skipped': skipped,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        my_conn.close()
        sql_conn.close()


# =========================================================
# 5. LỊCH SỬ LƯƠNG THEO NHÂN VIÊN
# =========================================================
@payroll_bp.route('/history-salaries/<int:employee_id>', methods=['GET'])
@roles_required('Admin', 'Manager', 'Employee')
def history_salaries(employee_id):
    if is_employee_requesting_other_employee(employee_id):
        return jsonify({"error": "Bạn chỉ được xem lịch sử lương của chính mình"}), 403

    my_conn = get_mysql_connection()
    sql_conn = get_sqlserver_connection()
    if not my_conn or not sql_conn:
        return jsonify({"error": "Lỗi kết nối cơ sở dữ liệu"}), 500

    try:
        my_cursor = my_conn.cursor(dictionary=True)
        sql_cursor = sql_conn.cursor()
        sql_cursor.execute("""
            SELECT e.EmployeeID, e.FullName, e.Email, e.Status,
                   d.DepartmentName, p.PositionName
            FROM Employees e
            LEFT JOIN Departments d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN Positions p ON e.PositionID = p.PositionID
            WHERE e.EmployeeID = ?
        """, (employee_id,))
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

        my_cursor.execute("""
            SELECT SalaryID, EmployeeID, SalaryMonth, BaseSalary, Bonus, Deductions,
                   NetSalary, CreatedAt
            FROM salaries
            WHERE EmployeeID = %s
            ORDER BY SalaryMonth DESC, CreatedAt DESC, SalaryID DESC
        """, (employee_id,))
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

        return jsonify({
            "employee": employee,
            "history": history,
            "count": len(history),
            "latest_salary": history[0] if history else None,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        my_conn.close()
        sql_conn.close()
