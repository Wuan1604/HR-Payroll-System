import bcrypt
import hashlib
import secrets
from datetime import datetime, timedelta
from urllib.parse import quote

from flask import Blueprint, jsonify, request, make_response
from app.database import get_auth_connection
from app.auth import generate_token, login_required, roles_required, get_current_user
from app.config import Config
from app.utils import send_email

auth_bp = Blueprint('auth', __name__)


def _check_password(stored_password, raw_password):
    if stored_password is None:
        return False
    stored = str(stored_password)
    raw = str(raw_password)

    # Hỗ trợ cả mật khẩu đang lưu dạng text tạm thời trong database mẫu
    if stored == raw:
        return True

    try:
        return bcrypt.checkpw(raw.encode('utf-8'), stored.encode('utf-8'))
    except Exception:
        return False


def _hash_password(raw_password):
    return bcrypt.hashpw(str(raw_password).encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _hash_reset_token(raw_token):
    return hashlib.sha256(str(raw_token).encode('utf-8')).hexdigest()


def _ensure_password_reset_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            TokenID INT AUTO_INCREMENT PRIMARY KEY,
            UserID INT NOT NULL,
            TokenHash VARCHAR(64) NOT NULL UNIQUE,
            ExpiresAt DATETIME NOT NULL,
            UsedAt DATETIME NULL,
            CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_password_reset_user
                FOREIGN KEY (UserID) REFERENCES users(UserID)
                ON UPDATE CASCADE
                ON DELETE CASCADE
        )
        """
    )


def _build_reset_email(full_name, reset_link, expires_minutes):
    safe_name = full_name or 'bạn'
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 620px; margin: 0 auto; color: #0f172a;">
      <h2 style="margin-bottom: 8px;">Đặt lại mật khẩu HR & Payroll</h2>
      <p>Xin chào <b>{safe_name}</b>,</p>
      <p>Hệ thống nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn.</p>
      <p>Vui lòng bấm nút bên dưới để tạo mật khẩu mới. Liên kết này có hiệu lực trong <b>{expires_minutes} phút</b>.</p>
      <p style="margin: 28px 0;">
        <a href="{reset_link}" style="background:#0f172a;color:#ffffff;text-decoration:none;padding:12px 18px;border-radius:10px;font-weight:700;display:inline-block;">
          Đặt lại mật khẩu
        </a>
      </p>
      <p>Nếu nút không hoạt động, bạn có thể sao chép liên kết này vào trình duyệt:</p>
      <p style="word-break:break-all;background:#f1f5f9;padding:12px;border-radius:10px;">{reset_link}</p>
      <p style="color:#64748b;font-size:13px;">Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này.</p>
    </div>
    """


def _log_login(cursor, user_id, email, status, message):
    try:
        cursor.execute(
            """
            INSERT INTO user_login_logs (UserID, Email, LoginStatus, Message)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, email, status, message)
        )
    except Exception:
        pass


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    account = (data.get('email') or data.get('Email') or data.get('username') or data.get('Username') or '').strip()
    password = data.get('password') or data.get('Password') or ''

    if not account or not password:
        return jsonify({'error': 'Vui lòng nhập email/tên đăng nhập và mật khẩu'}), 400

    conn = get_auth_connection()
    if not conn:
        return jsonify({'error': 'Không thể kết nối database đăng nhập'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT u.UserID, u.EmployeeID, u.FullName, u.Email, u.Username,
                   u.PasswordHash, u.Status, r.RoleName
            FROM users u
            JOIN roles r ON u.RoleID = r.RoleID
            WHERE u.Email = %s OR u.Username = %s
            LIMIT 1
            """,
            (account, account)
        )
        user = cursor.fetchone()

        if not user:
            _log_login(cursor, None, account, 'Failed', 'Tài khoản không tồn tại')
            conn.commit()
            return jsonify({'error': 'Email/tên đăng nhập hoặc mật khẩu không đúng'}), 401

        if user.get('Status') != 'Active':
            _log_login(cursor, user['UserID'], user['Email'], 'Failed', 'Tài khoản không hoạt động')
            conn.commit()
            return jsonify({'error': 'Tài khoản đã bị khóa hoặc ngừng hoạt động'}), 403

        if not _check_password(user.get('PasswordHash'), password):
            _log_login(cursor, user['UserID'], user['Email'], 'Failed', 'Sai mật khẩu')
            conn.commit()
            return jsonify({'error': 'Email/tên đăng nhập hoặc mật khẩu không đúng'}), 401

        cursor.execute('UPDATE users SET LastLogin = NOW() WHERE UserID = %s', (user['UserID'],))
        _log_login(cursor, user['UserID'], user['Email'], 'Success', 'Đăng nhập thành công')
        conn.commit()

        token = generate_token(user)
        safe_user = {
            'UserID': user['UserID'],
            'EmployeeID': user['EmployeeID'],
            'FullName': user['FullName'],
            'Email': user['Email'],
            'Username': user['Username'],
            'Role': user['RoleName'],
        }
        resp = make_response(jsonify({'message': 'Đăng nhập thành công', 'token': token, 'user': safe_user}), 200)
        resp.delete_cookie('token')
        return resp
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route('/logout', methods=['POST'])
def logout():
    resp = make_response(jsonify({'message': 'Đăng xuất thành công'}), 200)
    resp.delete_cookie('token')
    return resp


@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    return jsonify({'user': get_current_user()}), 200




@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    full_name = (data.get('FullName') or '').strip()
    email = (data.get('Email') or '').strip()
    username = (data.get('Username') or '').strip()
    password = data.get('Password') or ''
    employee_id = data.get('EmployeeID') or None

    if not full_name or not email or not username or not password:
        return jsonify({'error': 'Vui lòng nhập đủ họ tên, email, username và mật khẩu'}), 400

    conn = get_auth_connection()
    if not conn:
        return jsonify({'error': 'Không thể kết nối database đăng nhập'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('SELECT RoleID FROM roles WHERE RoleName = %s', ('Employee',))
        role = cursor.fetchone()
        if not role:
            return jsonify({'error': 'Chưa có role Employee trong database hr_auth'}), 400

        cursor.execute(
            """
            INSERT INTO users (EmployeeID, FullName, Email, Username, PasswordHash, RoleID, Status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Active')
            """,
            (employee_id, full_name, email, username, _hash_password(password), role['RoleID'])
        )
        conn.commit()
        return jsonify({'message': 'Đăng ký tài khoản thành công. Bạn có thể đăng nhập ngay.', 'UserID': cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()




@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json or {}
    account = (data.get('email') or data.get('Email') or data.get('account') or '').strip()

    if not account:
        return jsonify({'error': 'Vui lòng nhập email tài khoản'}), 400

    # Không tiết lộ email có tồn tại hay không để tránh dò tài khoản.
    generic_message = 'Nếu email tồn tại trong hệ thống, liên kết đặt lại mật khẩu đã được gửi.'

    conn = get_auth_connection()
    if not conn:
        return jsonify({'error': 'Không thể kết nối database đăng nhập'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        _ensure_password_reset_table(cursor)
        cursor.execute(
            """
            SELECT UserID, FullName, Email, Status
            FROM users
            WHERE Email = %s
            LIMIT 1
            """,
            (account,)
        )
        user = cursor.fetchone()

        if not user or user.get('Status') != 'Active':
            conn.commit()
            return jsonify({'message': generic_message}), 200

        raw_token = secrets.token_urlsafe(48)
        token_hash = _hash_reset_token(raw_token)
        expires_minutes = int(getattr(Config, 'PASSWORD_RESET_EXPIRES_MINUTES', 30))
        expires_at = datetime.now() + timedelta(minutes=expires_minutes)

        cursor.execute(
            """
            UPDATE password_reset_tokens
            SET UsedAt = NOW()
            WHERE UserID = %s AND UsedAt IS NULL
            """,
            (user['UserID'],)
        )
        cursor.execute(
            """
            INSERT INTO password_reset_tokens (UserID, TokenHash, ExpiresAt)
            VALUES (%s, %s, %s)
            """,
            (user['UserID'], token_hash, expires_at)
        )
        conn.commit()

        frontend_url = (Config.FRONTEND_URL or 'http://localhost:5173').rstrip('/')
        reset_link = f"{frontend_url}/reset-password?token={quote(raw_token)}"
        html = _build_reset_email(user.get('FullName'), reset_link, expires_minutes)
        sent = send_email(user['Email'], 'Đặt lại mật khẩu HR & Payroll', html)
        if not sent:
            return jsonify({'error': 'Không thể gửi email đặt lại mật khẩu. Vui lòng kiểm tra cấu hình Gmail.'}), 500

        return jsonify({'message': generic_message}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json or {}
    token = (data.get('token') or data.get('Token') or '').strip()
    password = data.get('password') or data.get('Password') or ''
    confirm_password = data.get('confirmPassword') or data.get('ConfirmPassword') or password

    if not token:
        return jsonify({'error': 'Thiếu mã đặt lại mật khẩu'}), 400
    if not password:
        return jsonify({'error': 'Vui lòng nhập mật khẩu mới'}), 400
    if password != confirm_password:
        return jsonify({'error': 'Mật khẩu xác nhận không khớp'}), 400
    if len(str(password)) < 6:
        return jsonify({'error': 'Mật khẩu mới phải có ít nhất 6 ký tự'}), 400

    conn = get_auth_connection()
    if not conn:
        return jsonify({'error': 'Không thể kết nối database đăng nhập'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        _ensure_password_reset_table(cursor)
        token_hash = _hash_reset_token(token)
        cursor.execute(
            """
            SELECT pr.TokenID, pr.UserID, pr.ExpiresAt, pr.UsedAt, u.Status
            FROM password_reset_tokens pr
            JOIN users u ON pr.UserID = u.UserID
            WHERE pr.TokenHash = %s
            LIMIT 1
            """,
            (token_hash,)
        )
        row = cursor.fetchone()

        if not row or row.get('UsedAt') is not None:
            return jsonify({'error': 'Liên kết đặt lại mật khẩu không hợp lệ hoặc đã được sử dụng'}), 400
        if row.get('Status') != 'Active':
            return jsonify({'error': 'Tài khoản đã bị khóa hoặc ngừng hoạt động'}), 403

        expires_at = row.get('ExpiresAt')
        if expires_at and datetime.now() > expires_at:
            cursor.execute('UPDATE password_reset_tokens SET UsedAt = NOW() WHERE TokenID = %s', (row['TokenID'],))
            conn.commit()
            return jsonify({'error': 'Liên kết đặt lại mật khẩu đã hết hạn'}), 400

        cursor.execute(
            'UPDATE users SET PasswordHash = %s WHERE UserID = %s',
            (_hash_password(password), row['UserID'])
        )
        cursor.execute('UPDATE password_reset_tokens SET UsedAt = NOW() WHERE TokenID = %s', (row['TokenID'],))
        conn.commit()
        return jsonify({'message': 'Đặt lại mật khẩu thành công. Bạn có thể đăng nhập bằng mật khẩu mới.'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route('/roles', methods=['GET'])
@roles_required('Admin')
def roles():
    conn = get_auth_connection()
    if not conn:
        return jsonify({'error': 'Không thể kết nối database đăng nhập'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('SELECT RoleID, RoleName, Description FROM roles ORDER BY RoleID')
        return jsonify(cursor.fetchall()), 200
    finally:
        cursor.close()
        conn.close()


@auth_bp.route('/users', methods=['GET'])
@roles_required('Admin')
def list_users():
    conn = get_auth_connection()
    if not conn:
        return jsonify({'error': 'Không thể kết nối database đăng nhập'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT u.UserID, u.EmployeeID, u.FullName, u.Email, u.Username,
                   u.RoleID, r.RoleName, u.Status, u.LastLogin, u.CreatedAt, u.UpdatedAt
            FROM users u
            JOIN roles r ON u.RoleID = r.RoleID
            ORDER BY u.UserID DESC
            """
        )
        rows = cursor.fetchall()
        for row in rows:
            row['LastLogin'] = str(row['LastLogin']) if row.get('LastLogin') else None
            row['CreatedAt'] = str(row['CreatedAt']) if row.get('CreatedAt') else None
            row['UpdatedAt'] = str(row['UpdatedAt']) if row.get('UpdatedAt') else None
        return jsonify(rows), 200
    finally:
        cursor.close()
        conn.close()


@auth_bp.route('/users', methods=['POST'])
@roles_required('Admin')
def create_user():
    data = request.json or {}
    full_name = (data.get('FullName') or '').strip()
    email = (data.get('Email') or '').strip()
    username = (data.get('Username') or '').strip()
    password = data.get('Password') or ''
    employee_id = data.get('EmployeeID') or None
    role_name = data.get('RoleName') or 'Employee'
    status = data.get('Status') or 'Active'

    if not full_name or not email or not username or not password:
        return jsonify({'error': 'Vui lòng nhập đủ họ tên, email, username và mật khẩu'}), 400

    conn = get_auth_connection()
    if not conn:
        return jsonify({'error': 'Không thể kết nối database đăng nhập'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('SELECT RoleID FROM roles WHERE RoleName = %s', (role_name,))
        role = cursor.fetchone()
        if not role:
            return jsonify({'error': 'Role không hợp lệ'}), 400

        cursor.execute(
            """
            INSERT INTO users (EmployeeID, FullName, Email, Username, PasswordHash, RoleID, Status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (employee_id, full_name, email, username, _hash_password(password), role['RoleID'], status)
        )
        conn.commit()
        return jsonify({'message': 'Tạo tài khoản thành công', 'UserID': cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@roles_required('Admin')
def update_user(user_id):
    data = request.json or {}
    conn = get_auth_connection()
    if not conn:
        return jsonify({'error': 'Không thể kết nối database đăng nhập'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        role_id = None
        if data.get('RoleName'):
            cursor.execute('SELECT RoleID FROM roles WHERE RoleName = %s', (data.get('RoleName'),))
            role = cursor.fetchone()
            if not role:
                return jsonify({'error': 'Role không hợp lệ'}), 400
            role_id = role['RoleID']

        fields = []
        values = []
        mapping = {
            'EmployeeID': data.get('EmployeeID'),
            'FullName': data.get('FullName'),
            'Email': data.get('Email'),
            'Username': data.get('Username'),
            'Status': data.get('Status'),
        }
        for key, value in mapping.items():
            if value is not None:
                fields.append(f'{key} = %s')
                values.append(value or None if key == 'EmployeeID' else value)
        if role_id is not None:
            fields.append('RoleID = %s')
            values.append(role_id)
        if data.get('Password'):
            fields.append('PasswordHash = %s')
            values.append(_hash_password(data.get('Password')))

        if not fields:
            return jsonify({'message': 'Không có dữ liệu cần cập nhật'}), 200

        values.append(user_id)
        cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE UserID = %s", values)
        conn.commit()
        return jsonify({'message': 'Cập nhật tài khoản thành công'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@roles_required('Admin')
def delete_user(user_id):
    current = get_current_user()
    if current and int(current.get('UserID') or 0) == int(user_id):
        return jsonify({'error': 'Không thể xóa chính tài khoản đang đăng nhập'}), 400

    conn = get_auth_connection()
    if not conn:
        return jsonify({'error': 'Không thể kết nối database đăng nhập'}), 500
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM users WHERE UserID = %s', (user_id,))
        conn.commit()
        return jsonify({'message': 'Xóa tài khoản thành công'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
