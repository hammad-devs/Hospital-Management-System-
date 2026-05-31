# hms_web/routes/auth.py

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from models.user import (
    get_user_by_username, get_user_by_id,
    update_password, check_password
)
from middleware.auth_middleware import login_required

auth_bp = Blueprint("auth", __name__)


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Already logged in → go to dashboard
    if session.get("user_id"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "warning")
            return render_template("auth/login.html")

        user = get_user_by_username(username)

        if not user:
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html")

        if not user["is_active"]:
            flash("Your account has been disabled. Contact the administrator.", "danger")
            return render_template("auth/login.html")

        if not check_password(password, user["password_hash"]):
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html")

        # ── Write session ──────────────────────────────
        session.permanent = False
        session["user_id"]   = user["user_id"]
        session["username"]  = user["username"]
        session["full_name"] = user["full_name"]
        session["role"]      = user["role"]
        session["dept_id"]   = user["dept_id"]
        session["doctor_id"] = user["doctor_id"]

        flash(f"Welcome back, {user['full_name']}!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html")


# ─────────────────────────────────────────────
#  LOGOUT
# ─────────────────────────────────────────────

@auth_bp.route("/logout")
@login_required
def logout():
    full_name = session.get("full_name", "User")
    session.clear()
    flash(f"Goodbye, {full_name}. You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# ─────────────────────────────────────────────
#  CHANGE PASSWORD
# ─────────────────────────────────────────────

@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_pwd = request.form.get("current_password", "")
        new_pwd     = request.form.get("new_password", "")
        confirm_pwd = request.form.get("confirm_password", "")

        user = get_user_by_id(session["user_id"])

        if not check_password(current_pwd, user["password_hash"] if user else ""):
            flash("Current password is incorrect.", "danger")
            return render_template("auth/change_password.html")

        if len(new_pwd) < 8:
            flash("New password must be at least 8 characters.", "warning")
            return render_template("auth/change_password.html")

        if new_pwd != confirm_pwd:
            flash("New passwords do not match.", "warning")
            return render_template("auth/change_password.html")

        update_password(session["user_id"], new_pwd)
        flash("Password changed successfully.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/change_password.html")