# hms_web/routes/patients.py

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from middleware.auth_middleware import login_required, role_required
from models.patient import (
    create_patient, get_all_patients, search_patients,
    get_patient_by_id, update_patient,
    get_patient_admissions, get_patient_appointments,
    get_patient_bills
)
from models.doctor import get_doctor_by_user_id, get_doctor_patients

patients_bp = Blueprint("patients", __name__, url_prefix="/patients")


# ─────────────────────────────────────────────
#  LIST / SEARCH
# ─────────────────────────────────────────────

@patients_bp.route("/")
@login_required
def list_patients():
    role      = session.get("role")
    doctor_id = session.get("doctor_id")
    query     = request.args.get("q", "").strip()

    # ── Doctor sees only their own patients ───────────────────────
    if role == "doctor":
        if query:
            all_results = search_patients(query)
            # Filter to only patients linked to this doctor
            doctor_patient_ids = {
                p["patient_id"] for p in get_doctor_patients(doctor_id)
            }
            patients = [p for p in all_results
                        if p["patient_id"] in doctor_patient_ids]
        else:
            patients = get_doctor_patients(doctor_id)

        return render_template(
            "patients/list.html",
            patients = patients,
            query    = query,
            is_doctor_view = True,
        )

    # ── Admin / receptionist sees all ─────────────────────────────
    if query:
        patients = search_patients(query)
    else:
        patients = get_all_patients(limit=50)

    return render_template(
        "patients/list.html",
        patients       = patients,
        query          = query,
        is_doctor_view = False,
    )


# ─────────────────────────────────────────────
#  DETAIL
# ─────────────────────────────────────────────

@patients_bp.route("/<int:patient_id>")
@login_required
def patient_detail(patient_id):
    role      = session.get("role")
    doctor_id = session.get("doctor_id")

    # ── RBAC: doctor can only view their own patients ─────────────
    if role == "doctor":
        allowed_ids = {
            p["patient_id"] for p in get_doctor_patients(doctor_id)
        }
        if patient_id not in allowed_ids:
            flash("Access denied — this patient is not under your care.", "danger")
            return redirect(url_for("patients.list_patients"))

    patient = get_patient_by_id(patient_id)
    if not patient:
        flash("Patient not found.", "warning")
        return redirect(url_for("patients.list_patients"))

    admissions   = get_patient_admissions(patient_id)
    appointments = get_patient_appointments(patient_id)
    bills        = get_patient_bills(patient_id)

    return render_template(
        "patients/detail.html",
        patient      = patient,
        admissions   = admissions,
        appointments = appointments,
        bills        = bills,
    )


# ─────────────────────────────────────────────
#  REGISTER NEW PATIENT
# ─────────────────────────────────────────────

@patients_bp.route("/new", methods=["GET", "POST"])
@role_required("admin", "receptionist", "doctor")
def new_patient():
    if request.method == "POST":
        full_name   = request.form.get("full_name",   "").strip()
        dob         = request.form.get("dob",         "").strip() or None
        gender      = request.form.get("gender",      "")
        blood_group = request.form.get("blood_group", "Unknown")
        phone       = request.form.get("phone",       "").strip()
        email       = request.form.get("email",       "").strip()
        address     = request.form.get("address",     "").strip()
        ec_name     = request.form.get("ec_name",     "").strip()
        ec_phone    = request.form.get("ec_phone",    "").strip()
        allergies   = request.form.get("allergies",   "None").strip()
        chronic     = request.form.get("chronic",     "None").strip()
        insurance   = request.form.get("insurance",   "").strip()

        # ── Basic validation ──────────────────────────────────────
        if not full_name:
            flash("Patient full name is required.", "warning")
            return render_template("patients/form.html", action="new")
        if not phone:
            flash("Phone number is required.", "warning")
            return render_template("patients/form.html", action="new")
        if not gender:
            flash("Gender is required.", "warning")
            return render_template("patients/form.html", action="new")

        try:
            patient_id, code = create_patient(
                full_name, dob, gender, blood_group, phone,
                email, address, ec_name, ec_phone,
                allergies, chronic, insurance
            )
            flash(f"Patient registered successfully! Code: {code}", "success")
            return redirect(url_for("patients.patient_detail",
                                    patient_id=patient_id))
        except Exception as e:
            flash(f"Registration failed: {e}", "danger")
            return render_template("patients/form.html", action="new")

    return render_template("patients/form.html", action="new")


# ─────────────────────────────────────────────
#  EDIT PATIENT
# ─────────────────────────────────────────────

@patients_bp.route("/<int:patient_id>/edit", methods=["GET", "POST"])
@role_required("admin", "receptionist", "doctor")
def edit_patient(patient_id):
    role      = session.get("role")
    doctor_id = session.get("doctor_id")

    # ── RBAC: doctor can only edit their own patients ─────────────
    if role == "doctor":
        allowed_ids = {
            p["patient_id"] for p in get_doctor_patients(doctor_id)
        }
        if patient_id not in allowed_ids:
            flash("Access denied — this patient is not under your care.", "danger")
            return redirect(url_for("patients.list_patients"))

    patient = get_patient_by_id(patient_id)
    if not patient:
        flash("Patient not found.", "warning")
        return redirect(url_for("patients.list_patients"))

    if request.method == "POST":
        phone     = request.form.get("phone",     "").strip()
        email     = request.form.get("email",     "").strip()
        address   = request.form.get("address",   "").strip()
        allergies = request.form.get("allergies", "None").strip()
        chronic   = request.form.get("chronic",   "None").strip()
        insurance = request.form.get("insurance", "").strip()

        if not phone:
            flash("Phone number is required.", "warning")
            return render_template("patients/form.html",
                                   action="edit", patient=patient)
        try:
            update_patient(patient_id, phone, email,
                           address, allergies, chronic, insurance)
            flash("Patient record updated successfully.", "success")
            return redirect(url_for("patients.patient_detail",
                                    patient_id=patient_id))
        except Exception as e:
            flash(f"Update failed: {e}", "danger")
            return render_template("patients/form.html",
                                   action="edit", patient=patient)

    return render_template("patients/form.html",
                           action="edit", patient=patient)