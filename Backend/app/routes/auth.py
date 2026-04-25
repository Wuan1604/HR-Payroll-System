import bcrypt
from flask import Blueprint, jsonify, request, make_response
from app.database import get_auth_connection
from app.auth import generate_token, login_required, roles_required, get_current_user

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
        resp.set_cookie('token', token, httponly=True, samesite='Lax')
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
