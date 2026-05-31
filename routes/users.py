# hms_web/routes/users.py
# Full user management — admin only
# Handles: list, create, edit, toggle active for ALL roles

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from middleware.auth_middleware import admin_required
from models.user import (
    get_all_users, get_user_by_id,
    create_user, update_password,
    toggle_user_active, get_all_roles,
    get_all_departments
)

users_bp = Blueprint("users", __name__, url_prefix="/users")


# ─────────────────────────────────────────────
#  LIST ALL USERS
# ─────────────────────────────────────────────

@users_bp.route("/")
@admin_required
def list_users():
    users = get_all_users()
    return render_template("users/list.html", users=users)


# ─────────────────────────────────────────────
#  CREATE NEW USER  (any role)
# ─────────────────────────────────────────────

@users_bp.route("/new", methods=["GET", "POST"])
@admin_required
def new_user():
    roles = get_all_roles()
    depts = get_all_departments()

    if request.method == "POST":
        username  = request.form.get("username",  "").strip()
        full_name = request.form.get("full_name", "").strip()
        email     = request.form.get("email",     "").strip()
        phone     = request.form.get("phone",     "").strip()
        password  = request.form.get("password",  "")
        confirm   = request.form.get("confirm",   "")
        role_id   = request.form.get("role_id",   type=int)
        dept_id   = request.form.get("dept_id",   type=int) or None

        # ── Validation ────────────────────────────────────────────
        errors = []
        if not username:           errors.append("Username is required.")
        if not full_name:          errors.append("Full name is required.")
        if not password:           errors.append("Password is required.")
        if len(password) < 8:      errors.append("Password must be at least 8 characters.")
        if password != confirm:    errors.append("Passwords do not match.")
        if not role_id:            errors.append("Role is required.")

        if errors:
            for e in errors:
                flash(e, "warning")
            return render_template("users/form.html",
                                   roles=roles, depts=depts,
                                   action="new", form=request.form)

        try:
            user_id = create_user(
                username, password, full_name,
                email, phone, role_id, dept_id
            )
            flash(f"User '{username}' created successfully! (ID: {user_id})", "success")

            # If doctor role → redirect to create doctor profile
            doctor_role_id = next(
                (r["role_id"] for r in roles if r["role_name"] == "doctor"), None
            )
            if role_id == doctor_role_id:
                flash("Don't forget to create a Doctor Profile for this user.", "info")
                return redirect(url_for("doctors.new_doctor"))

            return redirect(url_for("users.list_users"))

        except Exception as e:
            error_msg = str(e)
            if "Duplicate entry" in error_msg and "username" in error_msg:
                flash(f"Username '{username}' is already taken.", "danger")
            elif "Duplicate entry" in error_msg and "email" in error_msg:
                flash(f"Email '{email}' is already registered.", "danger")
            else:
                flash(f"Failed to create user: {error_msg}", "danger")
            return render_template("users/form.html",
                                   roles=roles, depts=depts,
                                   action="new", form=request.form)

    return render_template("users/form.html",
                           roles=roles, depts=depts,
                           action="new", form={})


# ─────────────────────────────────────────────
#  RESET PASSWORD
# ─────────────────────────────────────────────

@users_bp.route("/<int:user_id>/reset-password", methods=["GET", "POST"])
@admin_required
def reset_password(user_id):
    user = get_user_by_id(user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("users.list_users"))

    if request.method == "POST":
        new_pwd = request.form.get("new_password", "")
        confirm = request.form.get("confirm",      "")

        if len(new_pwd) < 8:
            flash("Password must be at least 8 characters.", "warning")
            return render_template("users/reset_password.html", user=user)
        if new_pwd != confirm:
            flash("Passwords do not match.", "warning")
            return render_template("users/reset_password.html", user=user)

        update_password(user_id, new_pwd)
        flash(f"Password for '{user['username']}' reset successfully.", "success")
        return redirect(url_for("users.list_users"))

    return render_template("users/reset_password.html", user=user)


# ─────────────────────────────────────────────
#  TOGGLE ACTIVE / DISABLE
# ─────────────────────────────────────────────

@users_bp.route("/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(user_id):
    # Prevent admin disabling themselves
    if user_id == session.get("user_id"):
        flash("You cannot disable your own account.", "warning")
        return redirect(url_for("users.list_users"))

    current_status = request.form.get("is_active", "1") == "1"
    toggle_user_active(user_id, not current_status)
    state = "disabled" if current_status else "enabled"
    flash(f"User account {state} successfully.", "success")
    return redirect(url_for("users.list_users"))
