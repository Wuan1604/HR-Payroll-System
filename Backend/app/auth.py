from functools import wraps

from flask import jsonify, session


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Auth bypass - allow all requests
        return fn(*args, **kwargs)

    return wrapper

