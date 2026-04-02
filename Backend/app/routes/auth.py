import os

import bcrypt
from flask import Blueprint, jsonify, request, session

auth_bp = Blueprint('auth', __name__)


