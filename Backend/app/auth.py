from functools import wraps
from flask import jsonify, request
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from app.config import Config

TOKEN_MAX_AGE_SECONDS = 60 * 60 * 8


def _serializer():
    return URLSafeTimedSerializer(Config.SECRET_KEY, salt='hr-payroll-auth')


def generate_token(user):
    payload = {
        'UserID': user.get('UserID'),
        'EmployeeID': user.get('EmployeeID'),
        'FullName': user.get('FullName'),
        'Email': user.get('Email'),
        'Username': user.get('Username'),
        'Role': user.get('RoleName') or user.get('Role'),
    }
    return _serializer().dumps(payload)


def get_current_user():
    auth_header = request.headers.get('Authorization', '')
    token = None

    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '', 1).strip()

    if not token:
        token = request.cookies.get('token')

    if not token:
        return None

    try:
        return _serializer().loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
    except (SignatureExpired, BadSignature, Exception):
        return None


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Bạn cần đăng nhập để sử dụng chức năng này'}), 401
        request.current_user = user
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Bạn cần đăng nhập để sử dụng chức năng này'}), 401
            if user.get('Role') not in allowed_roles:
                return jsonify({'error': 'Bạn không có quyền sử dụng chức năng này'}), 403
            request.current_user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def is_employee_requesting_other_employee(employee_id):
    user = getattr(request, 'current_user', None) or get_current_user()
    if not user or user.get('Role') != 'Employee':
        return False
    return str(user.get('EmployeeID')) != str(employee_id)
