# hms_web/routes/doctors.py

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from middleware.auth_middleware import login_required, admin_required, role_required
from models.doctor import (
    create_doctor, get_all_doctors, get_doctor_by_id,
    get_doctors_for_dropdown, upsert_schedule, get_schedule,
    get_doctor_by_user_id
)
from models.user import (
    create_user, get_all_users, get_all_roles,
    get_all_departments, toggle_user_active
)

doctors_bp = Blueprint("doctors", __name__, url_prefix="/doctors")


# ─────────────────────────────────────────────
#  LIST DOCTORS
# ─────────────────────────────────────────────

@doctors_bp.route("/")
@login_required
def list_doctors():
    dept_id = request.args.get("dept_id", type=int)
    doctors = get_all_doctors(dept_id=dept_id)
    depts   = get_all_departments()

    return render_template(
        "doctors/list.html",
        doctors         = doctors,
        departments     = depts,
        selected_dept   = dept_id,
    )


# ─────────────────────────────────────────────
#  DOCTOR DETAIL
# ─────────────────────────────────────────────

@doctors_bp.route("/<int:doctor_id>")
@login_required
def doctor_detail(doctor_id):
    role           = session.get("role")
    session_doc_id = session.get("doctor_id")

    # ── Doctor can only view their own profile ────────────────────
    if role == "doctor" and session_doc_id != doctor_id:
        flash("Access denied — you can only view your own profile.", "danger")
        return redirect(url_for("doctors.list_doctors"))

    doctor   = get_doctor_by_id(doctor_id)
    schedule = get_schedule(doctor_id)

    if not doctor:
        flash("Doctor not found.", "warning")
        return redirect(url_for("doctors.list_doctors"))

    return render_template(
        "doctors/detail.html",
        doctor   = doctor,
        schedule = schedule,
    )


# ─────────────────────────────────────────────
#  ADD DOCTOR  (admin only)
# ─────────────────────────────────────────────

@doctors_bp.route("/new", methods=["GET", "POST"])
@admin_required
def new_doctor():
    depts = get_all_departments()
    roles = get_all_roles()

    # Users with doctor role not yet assigned a doctor record
    all_users      = get_all_users()
    available_users = [
        u for u in all_users
        if u["role"] == "doctor"
        and get_doctor_by_user_id(u["user_id"]) is None
    ]

    if request.method == "POST":
        action = request.form.get("action", "existing")

        # ── Step A: create brand-new user then attach doctor ──────
        if action == "new_user":
            username  = request.form.get("username",  "").strip()
            full_name = request.form.get("full_name", "").strip()
            email     = request.form.get("email",     "").strip()
            phone     = request.form.get("phone",     "").strip()
            password  = request.form.get("password",  "")
            dept_id   = request.form.get("dept_id",   type=int)

            if not username or not full_name or not password:
                flash("Username, full name and password are required.", "warning")
                return render_template("doctors/form.html",
                                       depts=depts, roles=roles,
                                       available_users=available_users)
            try:
                doctor_role_id = next(
                    r["role_id"] for r in roles if r["role_name"] == "doctor"
                )
                user_id = create_user(
                    username, password, full_name,
                    email, phone, doctor_role_id, dept_id
                )
            except Exception as e:
                flash(f"Could not create user: {e}", "danger")
                return render_template("doctors/form.html",
                                       depts=depts, roles=roles,
                                       available_users=available_users)
        else:
            # ── Step B: link existing user ─────────────────────────
            user_id = request.form.get("user_id", type=int)
            if not user_id:
                flash("Please select a user account.", "warning")
                return render_template("doctors/form.html",
                                       depts=depts, roles=roles,
                                       available_users=available_users)

        # ── Common doctor fields ───────────────────────────────────
        dept_id        = request.form.get("dept_id",        type=int)
        specialization = request.form.get("specialization", "").strip()
        qualification  = request.form.get("qualification",  "").strip()
        experience     = request.form.get("experience",     0)
        license_no     = request.form.get("license_no",     "").strip()
        fee            = request.form.get("fee",            500)
        joined_date    = request.form.get("joined_date",    "").strip() or None

        if not dept_id or not license_no:
            flash("Department and license number are required.", "warning")
            return render_template("doctors/form.html",
                                   depts=depts, roles=roles,
                                   available_users=available_users)
        try:
            doctor_id = create_doctor(
                user_id, dept_id, specialization, qualification,
                experience, license_no, fee, joined_date
            )
            flash(f"Doctor added successfully! (ID: {doctor_id})", "success")
            return redirect(url_for("doctors.doctor_detail",
                                    doctor_id=doctor_id))
        except Exception as e:
            flash(f"Failed to add doctor: {e}", "danger")

    return render_template(
        "doctors/form.html",
        depts           = depts,
        roles           = roles,
        available_users = available_users,
    )


# ─────────────────────────────────────────────
#  SET SCHEDULE
# ─────────────────────────────────────────────

@doctors_bp.route("/<int:doctor_id>/schedule", methods=["GET", "POST"])
@login_required
def set_schedule(doctor_id):
    role           = session.get("role")
    session_doc_id = session.get("doctor_id")

    # ── Doctor can only edit their own schedule ───────────────────
    if role == "doctor" and session_doc_id != doctor_id:
        flash("Access denied — you can only manage your own schedule.", "danger")
        return redirect(url_for("doctors.list_doctors"))

    doctor   = get_doctor_by_id(doctor_id)
    schedule = get_schedule(doctor_id)

    if not doctor:
        flash("Doctor not found.", "warning")
        return redirect(url_for("doctors.list_doctors"))

    if request.method == "POST":
        day          = request.form.get("day")
        start_time   = request.form.get("start_time")
        end_time     = request.form.get("end_time")
        max_patients = request.form.get("max_patients", 20, type=int)

        if not day or not start_time or not end_time:
            flash("Day, start time and end time are required.", "warning")
            return render_template("doctors/schedule.html",
                                   doctor=doctor, schedule=schedule)
        try:
            upsert_schedule(doctor_id, day, start_time, end_time, max_patients)
            flash(f"Schedule for {day} saved.", "success")
            return redirect(url_for("doctors.set_schedule",
                                    doctor_id=doctor_id))
        except Exception as e:
            flash(f"Failed to save schedule: {e}", "danger")

    return render_template(
        "doctors/schedule.html",
        doctor   = doctor,
        schedule = schedule,
    )


# ─────────────────────────────────────────────
#  USER MANAGEMENT  (admin only)
# ─────────────────────────────────────────────

@doctors_bp.route("/users")
@admin_required
def manage_users():
    users = get_all_users()
    return render_template("doctors/users.html", users=users)


@doctors_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(user_id):
    current_status = request.form.get("is_active", "1") == "1"
    toggle_user_active(user_id, not current_status)
    state = "disabled" if current_status else "enabled"
    flash(f"User account {state}.", "success")
    return redirect(url_for("doctors.manage_users"))