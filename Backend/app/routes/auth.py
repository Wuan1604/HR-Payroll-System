import os

import bcrypt
from flask import Blueprint, jsonify, request, session

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return jsonify({'error': 'Thiếu username hoặc password'}), 400

    # strip() để tránh lỗi do `.env` có khoảng trắng đầu/cuối
    admin_username = (os.getenv('ADMIN_USERNAME', '') or '').strip()
    admin_password_hash = (os.getenv('ADMIN_PASSWORD_HASH', '') or '').strip()

    if not admin_username or not admin_password_hash:
        return (
            jsonify(
                {
                    'error': 'Chưa cấu hình ADMIN_USERNAME/ADMIN_PASSWORD_HASH trong .env',
                }
            ),
            500,
        )

    # So khớp bcrypt theo hash trong .env (ADMIN_PASSWORD_HASH)
    try:
        ok = bcrypt.checkpw(
            password.encode('utf-8'),
            admin_password_hash.encode('utf-8'),
        )
    except Exception:
        return jsonify({'error': 'ADMIN_PASSWORD_HASH không đúng định dạng bcrypt'}), 500

    if username != admin_username or not ok:
        return jsonify({'error': 'Sai tài khoản hoặc mật khẩu'}), 401

    session.clear()
    session['admin_authenticated'] = True
    session['admin_username'] = username
    return jsonify({'message': 'Đăng nhập thành công'}), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Đăng xuất thành công'}), 200


@auth_bp.route('/me', methods=['GET'])
def me():
    if session.get('admin_authenticated'):
        return jsonify({'authenticated': True, 'username': session.get('admin_username')}), 200
    return jsonify({'authenticated': False}), 401

