from flask import Blueprint, jsonify, request
from app.database import get_mysql_connection, get_sqlserver_connection
from ..config import Config
from app.auth import roles_required, is_employee_requesting_other_employee
from datetime import datetime, date, time, timedelta
import calendar
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

payroll_bp = Blueprint('payroll', __name__)


# =========================================================
# COMMON HELPERS
# =========================================================
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
                COALESCE(s.Bonus, 0) AS Bonus,
                COALESCE(s.Deductions, 0) AS Deductions,
                COALESCE(s.NetSalary, 0) AS NetSalary,
                s.CreatedAt
            FROM employees_payroll e
            LEFT JOIN salaries s ON e.EmployeeID = s.EmployeeID
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
# 4. GỬI EMAIL PHIẾU LƯƠNG
# =========================================================
@payroll_bp.route('/send-salary-emails', methods=['GET'])
@roles_required('Admin', 'Manager')
def send_emails():
    my_conn = get_mysql_connection()
    sql_conn = get_sqlserver_connection()
    if not my_conn or not sql_conn:
        return jsonify({"error": "Lỗi kết nối cơ sở dữ liệu"}), 500

    try:
        my_cursor = my_conn.cursor(dictionary=True)
        my_cursor.execute("SELECT EmployeeID, NetSalary, SalaryMonth FROM salaries ORDER BY SalaryMonth DESC")
        salaries = my_cursor.fetchall()

        sql_cursor = sql_conn.cursor()
        sql_cursor.execute("SELECT EmployeeID, FullName, Email FROM Employees")
        emps = {r[0]: {"name": r[1], "email": r[2]} for r in sql_cursor.fetchall()}

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
