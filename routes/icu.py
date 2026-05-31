# hms_web/routes/icu.py

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from middleware.auth_middleware import login_required, role_required
from models.icu     import admit_to_icu, get_active_icu, get_all_icu, update_icu_status
from models.patient import get_patients_for_dropdown
from models.doctor  import get_doctors_for_dropdown

icu_bp = Blueprint("icu", __name__, url_prefix="/icu")


@icu_bp.route("/")
@login_required
def list_icu():
    role      = session.get("role")
    show_all  = request.args.get("show_all", "0") == "1"

    # Doctors get read-only view of active ICU patients
    if role == "doctor":
        patients = get_active_icu()
        return render_template(
            "icu/list.html",
            icu_patients   = patients,
            is_doctor_view = True,
            show_all       = False,
        )

    icu_patients = get_all_icu() if show_all else get_active_icu()
    return render_template(
        "icu/list.html",
        icu_patients   = icu_patients,
        is_doctor_view = False,
        show_all       = show_all,
    )


@icu_bp.route("/new", methods=["GET", "POST"])
@role_required("admin")
def new_icu_admission():
    patients = get_patients_for_dropdown()
    doctors  = get_doctors_for_dropdown()

    if request.method == "POST":
        patient_id  = request.form.get("patient_id",  type=int)
        doctor_id   = request.form.get("doctor_id",   type=int)
        bed_no      = request.form.get("bed_no",      "").strip()
        diagnosis   = request.form.get("diagnosis",   "").strip()
        ventilator  = request.form.get("ventilator",  "0") == "1"
        nurse_name  = request.form.get("nurse_name",  "").strip()

        errors = []
        if not patient_id: errors.append("Patient is required.")
        if not doctor_id:  errors.append("Doctor is required.")
        if not bed_no:     errors.append("ICU bed number is required.")

        if errors:
            for e in errors: flash(e, "warning")
            return render_template("icu/form.html",
                                   patients=patients, doctors=doctors)
        try:
            icu_id = admit_to_icu(
                patient_id, doctor_id, bed_no,
                diagnosis, ventilator, nurse_name
            )
            flash(f"Patient admitted to ICU. ICU ID: {icu_id}", "success")
            return redirect(url_for("icu.list_icu"))
        except Exception as e:
            flash(f"ICU admission failed: {e}", "danger")

    return render_template("icu/form.html", patients=patients, doctors=doctors)


@icu_bp.route("/<int:icu_id>/status", methods=["POST"])
@role_required("admin")
def update_status(icu_id):
    status = request.form.get("status", "")
    notes  = request.form.get("notes",  "").strip()

    valid = ["Critical", "Stable", "Discharged"]
    if status not in valid:
        flash("Invalid status.", "warning")
        return redirect(url_for("icu.list_icu"))

    update_icu_status(icu_id, status, notes)
    flash(f"ICU patient status updated to '{status}'.", "success")
    return redirect(url_for("icu.list_icu"))