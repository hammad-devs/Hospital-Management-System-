# hms_web/middleware/auth_middleware.py

from functools import wraps
from flask import session, redirect, url_for, flash, abort


def login_required(f):
    """
    Decorator — blocks any unauthenticated request.
    Redirects to /login with a flash message.
    Usage:
        @login_required
        def my_route(): ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """
    Decorator — allows only users whose role is in `roles`.
    Admin always passes regardless of what roles are listed.
    Usage:
        @role_required("admin")
        def admin_only(): ...

        @role_required("admin", "doctor")
        def admin_or_doctor(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login"))

            user_role = session.get("role", "")

            # Admin bypasses every role check
            if user_role == "admin":
                return f(*args, **kwargs)

            if user_role not in roles:
                flash("Access denied — you do not have permission for this page.", "danger")
                abort(403)

            return f(*args, **kwargs)
        return decorated
    return decorator


def admin_required(f):
    """
    Shorthand decorator — admin only.
    Usage:
        @admin_required
        def admin_page(): ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))

        if session.get("role") != "admin":
            flash("Access denied — admin only.", "danger")
            abort(403)

        return f(*args, **kwargs)
    return decorated


def get_current_user():
    """
    Helper — returns a dict of the logged-in user from session.
    Returns None if not logged in.
    """
    if not session.get("user_id"):
        return None
    return {
        "user_id"  : session.get("user_id"),
        "username" : session.get("username"),
        "full_name": session.get("full_name"),
        "role"     : session.get("role"),
        "dept_id"  : session.get("dept_id"),
        "doctor_id": session.get("doctor_id"),
    }