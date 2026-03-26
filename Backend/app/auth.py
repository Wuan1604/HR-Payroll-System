from functools import wraps

from flask import jsonify, session


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return jsonify({'error': 'Bạn chưa đăng nhập'}), 401
        return fn(*args, **kwargs)

    return wrapper

