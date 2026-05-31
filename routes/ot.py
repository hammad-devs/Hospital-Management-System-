# hms_web/routes/ot.py

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from middleware.auth_middleware import login_required, role_required
from models.ot      import create_ot_booking, get_all_ot_bookings, update_ot_status
from models.patient import get_patients_for_dropdown
from models.doctor  import get_doctors_for_dropdown

ot_bp = Blueprint("ot", __name__, url_prefix="/ot")


@ot_bp.route("/")
@login_required
def list_ot():
    role      = session.get("role")
    doctor_id = session.get("doctor_id")
    status    = request.args.get("status", "")

    bookings = get_all_ot_bookings(status=status if status else None)

    # Doctor sees only their own OT bookings (read only)
    if role == "doctor":
        bookings = [b for b in bookings
                    if b.get("doctor_id") == doctor_id
                    or b.get("surgeon_id") == doctor_id]
        return render_template(
            "ot/list.html",
            bookings       = bookings,
            status_filter  = status,
            is_doctor_view = True,
        )

    return render_template(
        "ot/list.html",
        bookings       = bookings,
        status_filter  = status,
        is_doctor_view = False,
    )


@ot_bp.route("/new", methods=["GET", "POST"])
@role_required("admin")
def new_ot_booking():
    patients = get_patients_for_dropdown()
    doctors  = get_doctors_for_dropdown()

    if request.method == "POST":
        patient_id     = request.form.get("patient_id",     type=int)
        doctor_id      = request.form.get("doctor_id",      type=int)
        ot_no          = request.form.get("ot_no",          "").strip()
        scheduled_date = request.form.get("scheduled_date", "").strip()
        scheduled_time = request.form.get("scheduled_time", "").strip()
        procedure_name = request.form.get("procedure_name", "").strip()
        anesthesia     = request.form.get("anesthesia",     "General")
        duration_hrs   = request.form.get("duration_hrs",   1.0)

        errors = []
        if not patient_id:     errors.append("Patient is required.")
        if not doctor_id:      errors.append("Surgeon is required.")
        if not ot_no:          errors.append("OT number is required.")
        if not scheduled_date: errors.append("Scheduled date is required.")
        if not scheduled_time: errors.append("Scheduled time is required.")
        if not procedure_name: errors.append("Procedure name is required.")

        if errors:
            for e in errors: flash(e, "warning")
            return render_template("ot/form.html",
                                   patients=patients, doctors=doctors)
        try:
            ot_id = create_ot_booking(
                patient_id, doctor_id, ot_no,
                scheduled_date, scheduled_time,
                procedure_name, anesthesia, duration_hrs
            )
            flash(f"OT booking created. OT ID: {ot_id}", "success")
            return redirect(url_for("ot.list_ot"))
        except Exception as e:
            flash(f"OT booking failed: {e}", "danger")

    return render_template("ot/form.html", patients=patients, doctors=doctors)


@ot_bp.route("/<int:ot_id>/status", methods=["POST"])
@role_required("admin")
def update_status(ot_id):
    status = request.form.get("status", "")
    notes  = request.form.get("notes",  "").strip()

    valid = ["Scheduled", "Completed", "Cancelled", "Postponed"]
    if status not in valid:
        flash("Invalid status.", "warning")
        return redirect(url_for("ot.list_ot"))

    update_ot_status(ot_id, status, notes)
    flash(f"OT booking status updated to '{status}'.", "success")
    return redirect(url_for("ot.list_ot"))