# hms_web/routes/admissions.py

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from middleware.auth_middleware import login_required, role_required, admin_required
from models.admission import (
    create_admission, get_all_admissions,
    get_admission_by_id, get_admissions_by_doctor,
    discharge_patient
)
from models.patient import get_patients_for_dropdown
from models.doctor  import get_doctors_for_dropdown
from models.user    import get_all_departments

admissions_bp = Blueprint("admissions", __name__, url_prefix="/admissions")


# ─────────────────────────────────────────────
#  LIST
# ─────────────────────────────────────────────

@admissions_bp.route("/")
@login_required
def list_admissions():
    role      = session.get("role")
    doctor_id = session.get("doctor_id")
    status    = request.args.get("status", "")

    # ── Doctor sees only their own admitted patients ───────────────
    if role == "doctor":
        admissions = get_admissions_by_doctor(doctor_id)
        if status:
            admissions = [a for a in admissions if a["status"] == status]
        return render_template(
            "admissions/list.html",
            admissions     = admissions,
            status_filter  = status,
            is_doctor_view = True,
        )

    # ── Admin sees all ────────────────────────────────────────────
    admissions = get_all_admissions(status=status if status else None)
    return render_template(
        "admissions/list.html",
        admissions     = admissions,
        status_filter  = status,
        is_doctor_view = False,
    )


# ─────────────────────────────────────────────
#  DETAIL
# ─────────────────────────────────────────────

@admissions_bp.route("/<int:admission_id>")
@login_required
def admission_detail(admission_id):
    role      = session.get("role")
    doctor_id = session.get("doctor_id")

    admission = get_admission_by_id(admission_id)
    if not admission:
        flash("Admission record not found.", "warning")
        return redirect(url_for("admissions.list_admissions"))

    # ── RBAC: doctor can only view their own admissions ───────────
    if role == "doctor":
        my_admits   = get_admissions_by_doctor(doctor_id)
        allowed_ids = {a["admission_id"] for a in my_admits}
        if admission_id not in allowed_ids:
            flash("Access denied — this admission is not under your care.", "danger")
            return redirect(url_for("admissions.list_admissions"))

    return render_template("admissions/detail.html", admission=admission)


# ─────────────────────────────────────────────
#  NEW ADMISSION
# ─────────────────────────────────────────────

@admissions_bp.route("/new", methods=["GET", "POST"])
@role_required("admin", "doctor", "receptionist")
def new_admission():
    role      = session.get("role")
    doctor_id = session.get("doctor_id")

    patients = get_patients_for_dropdown()
    depts    = get_all_departments()

    if role == "doctor":
        doctors = get_doctors_for_dropdown()
        doctors = [d for d in doctors if d["doctor_id"] == doctor_id]
    else:
        doctors = get_doctors_for_dropdown()

    if request.method == "POST":
        patient_id     = request.form.get("patient_id",     type=int)
        dept_id        = request.form.get("dept_id",        type=int)
        ward           = request.form.get("ward",           "").strip()
        bed_no         = request.form.get("bed_no",         "").strip()
        admission_type = request.form.get("admission_type", "Elective")
        diagnosis      = request.form.get("diagnosis",      "").strip()

        if role == "doctor":
            selected_doctor_id = doctor_id
        else:
            selected_doctor_id = request.form.get("doctor_id", type=int)

        # ── Validation ────────────────────────────────────────────
        errors = []
        if not patient_id:         errors.append("Patient is required.")
        if not selected_doctor_id: errors.append("Doctor is required.")
        if not dept_id:            errors.append("Department is required.")

        if errors:
            for e in errors:
                flash(e, "warning")
            return render_template(
                "admissions/form.html",
                patients = patients,
                doctors  = doctors,
                depts    = depts,
            )

        try:
            admission_id = create_admission(
                patient_id, selected_doctor_id, dept_id,
                ward, bed_no, admission_type, diagnosis
            )
            flash(f"Patient admitted successfully! Admission ID: {admission_id}", "success")
            return redirect(url_for("admissions.admission_detail",
                                    admission_id=admission_id))
        except Exception as e:
            flash(f"Admission failed: {e}", "danger")
            return render_template(
                "admissions/form.html",
                patients = patients,
                doctors  = doctors,
                depts    = depts,
            )

    return render_template(
        "admissions/form.html",
        patients = patients,
        doctors  = doctors,
        depts    = depts,
    )


# ─────────────────────────────────────────────
#  DISCHARGE
# ─────────────────────────────────────────────

@admissions_bp.route("/<int:admission_id>/discharge", methods=["POST"])
@role_required("admin", "doctor")
def discharge(admission_id):
    role      = session.get("role")
    doctor_id = session.get("doctor_id")

    admission = get_admission_by_id(admission_id)
    if not admission:
        flash("Admission record not found.", "warning")
        return redirect(url_for("admissions.list_admissions"))

    # ── RBAC: doctor can only discharge their own patients ────────
    if role == "doctor":
        my_admits   = get_admissions_by_doctor(doctor_id)
        allowed_ids = {a["admission_id"] for a in my_admits}
        if admission_id not in allowed_ids:
            flash("Access denied — this admission is not under your care.", "danger")
            return redirect(url_for("admissions.list_admissions"))

    if admission["status"] == "Discharged":
        flash("Patient has already been discharged.", "warning")
        return redirect(url_for("admissions.admission_detail",
                                admission_id=admission_id))

    notes = request.form.get("notes", "").strip()
    discharge_patient(admission_id, notes)
    flash("Patient discharged successfully.", "success")
    return redirect(url_for("admissions.list_admissions"))