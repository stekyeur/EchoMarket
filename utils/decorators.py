from functools import wraps
from flask import session, redirect, jsonify, request


def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Check if it's an AJAX request
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'status': 'error', 'message': 'Giris yapin'}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


def json_response(f):
    """Decorator to ensure JSON response format."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            if isinstance(result, dict):
                return jsonify(result)
            return result
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    return decorated_function
