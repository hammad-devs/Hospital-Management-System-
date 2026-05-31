# hms_web/routes/appointments.py

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from middleware.auth_middleware import login_required, role_required
from models.appointment import (
    create_appointment, get_appointments_today,
    get_appointments_by_date, get_appointments_by_doctor,
    get_appointments_by_patient, get_appointment_by_id,
    update_appointment_status
)
from models.patient import get_patients_for_dropdown
from models.doctor  import get_doctors_for_dropdown
from models.user    import get_all_departments

appointments_bp = Blueprint("appointments", __name__, url_prefix="/appointments")


# ─────────────────────────────────────────────
#  LIST / FILTER
# ─────────────────────────────────────────────

@appointments_bp.route("/")
@login_required
def list_appointments():
    role      = session.get("role")
    doctor_id = session.get("doctor_id")

    filter_by  = request.args.get("filter",     "today")
    date_param = request.args.get("date",        "")
    doc_param  = request.args.get("doctor_id",   type=int)
    pat_param  = request.args.get("patient_id",  type=int)

    # ── Doctor sees only their own appointments ───────────────────
    if role == "doctor":
        appointments = get_appointments_by_doctor(doctor_id)
        return render_template(
            "appointments/list.html",
            appointments   = appointments,
            filter_by      = "doctor",
            is_doctor_view = True,
        )

    # ── Admin / receptionist — full filter controls ───────────────
    if filter_by == "today":
        appointments = get_appointments_today()

    elif filter_by == "date" and date_param:
        appointments = get_appointments_by_date(date_param)

    elif filter_by == "doctor" and doc_param:
        appointments = get_appointments_by_doctor(doc_param)

    elif filter_by == "patient" and pat_param:
        appointments = get_appointments_by_patient(pat_param)

    else:
        appointments = get_appointments_today()
        filter_by    = "today"

    doctors  = get_doctors_for_dropdown()
    patients = get_patients_for_dropdown()

    return render_template(
        "appointments/list.html",
        appointments   = appointments,
        filter_by      = filter_by,
        date_param     = date_param,
        doc_param      = doc_param,
        pat_param      = pat_param,
        doctors        = doctors,
        patients       = patients,
        is_doctor_view = False,
    )


# ─────────────────────────────────────────────
#  DETAIL
# ─────────────────────────────────────────────

@appointments_bp.route("/<int:appt_id>")
@login_required
def appointment_detail(appt_id):
    role      = session.get("role")
    doctor_id = session.get("doctor_id")

    appt = get_appointment_by_id(appt_id)
    if not appt:
        flash("Appointment not found.", "warning")
        return redirect(url_for("appointments.list_appointments"))

    # ── RBAC: doctor can only view their own appointments ─────────
    if role == "doctor":
        doc = get_appointments_by_doctor(doctor_id)
        allowed_ids = {a["appt_id"] for a in doc}
        if appt_id not in allowed_ids:
            flash("Access denied — this appointment is not yours.", "danger")
            return redirect(url_for("appointments.list_appointments"))

    return render_template("appointments/detail.html", appt=appt)


# ─────────────────────────────────────────────
#  BOOK NEW APPOINTMENT
# ─────────────────────────────────────────────

@appointments_bp.route("/new", methods=["GET", "POST"])
@role_required("admin", "receptionist", "doctor")
def new_appointment():
    role      = session.get("role")
    doctor_id = session.get("doctor_id")

    patients = get_patients_for_dropdown()
    depts    = get_all_departments()

    # Doctor pre-selects themselves
    if role == "doctor":
        doctors = get_doctors_for_dropdown()
        doctors = [d for d in doctors if d["doctor_id"] == doctor_id]
    else:
        doctors = get_doctors_for_dropdown()

    if request.method == "POST":
        patient_id  = request.form.get("patient_id",  type=int)
        dept_id     = request.form.get("dept_id",     type=int)
        appt_type   = request.form.get("appt_type",   "OPD")
        appt_date   = request.form.get("appt_date",   "").strip()
        appt_time   = request.form.get("appt_time",   "").strip()
        complaint   = request.form.get("complaint",   "").strip()

        # Doctor role forces their own doctor_id
        if role == "doctor":
            selected_doctor_id = doctor_id
        else:
            selected_doctor_id = request.form.get("doctor_id", type=int)

        # ── Validation ────────────────────────────────────────────
        errors = []
        if not patient_id:        errors.append("Patient is required.")
        if not selected_doctor_id:errors.append("Doctor is required.")
        if not dept_id:           errors.append("Department is required.")
        if not appt_date:         errors.append("Appointment date is required.")
        if not appt_time:         errors.append("Appointment time is required.")

        if errors:
            for e in errors:
                flash(e, "warning")
            return render_template(
                "appointments/form.html",
                patients = patients,
                doctors  = doctors,
                depts    = depts,
            )

        appt_id, err = create_appointment(
            patient_id, selected_doctor_id, dept_id,
            appt_date, appt_time, appt_type, complaint
        )

        if err:
            flash(err, "danger")
            return render_template(
                "appointments/form.html",
                patients = patients,
                doctors  = doctors,
                depts    = depts,
            )

        flash(f"Appointment booked successfully! ID: {appt_id}", "success")
        return redirect(url_for("appointments.list_appointments"))

    return render_template(
        "appointments/form.html",
        patients = patients,
        doctors  = doctors,
        depts    = depts,
    )


# ─────────────────────────────────────────────
#  UPDATE STATUS
# ─────────────────────────────────────────────

@appointments_bp.route("/<int:appt_id>/status", methods=["POST"])
@login_required
def update_status(appt_id):
    role      = session.get("role")
    doctor_id = session.get("doctor_id")

    appt = get_appointment_by_id(appt_id)
    if not appt:
        flash("Appointment not found.", "warning")
        return redirect(url_for("appointments.list_appointments"))

    # ── RBAC ──────────────────────────────────────────────────────
    if role == "doctor":
        if appt["doctor_id"] if "doctor_id" in appt else None:
            pass
        doc_appts   = get_appointments_by_doctor(doctor_id)
        allowed_ids = {a["appt_id"] for a in doc_appts}
        if appt_id not in allowed_ids:
            flash("Access denied.", "danger")
            return redirect(url_for("appointments.list_appointments"))

    new_status = request.form.get("status", "")
    notes      = request.form.get("notes",  "").strip()

    valid_statuses = ["Scheduled", "Completed", "Cancelled", "No-Show"]
    if new_status not in valid_statuses:
        flash("Invalid status value.", "warning")
        return redirect(url_for("appointments.appointment_detail",
                                appt_id=appt_id))

    update_appointment_status(appt_id, new_status, notes)
    flash(f"Appointment status updated to '{new_status}'.", "success")
    return redirect(url_for("appointments.list_appointments"))