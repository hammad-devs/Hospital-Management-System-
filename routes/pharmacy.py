# hms_web/routes/pharmacy.py

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from middleware.auth_middleware import login_required, role_required, admin_required
from models.pharmacy import (
    get_all_medicines, add_medicine, update_stock,
    get_low_stock_medicines, create_prescription,
    get_all_prescriptions, get_prescriptions_by_doctor,
    dispense_prescription
)
from models.patient import get_patients_for_dropdown
from models.doctor  import get_doctors_for_dropdown

pharmacy_bp = Blueprint("pharmacy", __name__, url_prefix="/pharmacy")


# ── Medicines ──────────────────────────────────────────────────────

@pharmacy_bp.route("/medicines")
@login_required
def medicines():
    meds      = get_all_medicines()
    low_stock = get_low_stock_medicines()
    return render_template(
        "pharmacy/medicines.html",
        medicines  = meds,
        low_stock  = low_stock,
        role       = session.get("role"),
    )


@pharmacy_bp.route("/medicines/new", methods=["GET", "POST"])
@admin_required
def new_medicine():
    if request.method == "POST":
        name        = request.form.get("name",        "").strip()
        category    = request.form.get("category",    "").strip()
        stock_qty   = request.form.get("stock_qty",   0)
        unit        = request.form.get("unit",        "tablets")
        unit_price  = request.form.get("unit_price",  0)
        reorder_lvl = request.form.get("reorder_lvl", 20)

        if not name:
            flash("Medicine name is required.", "warning")
            return render_template("pharmacy/medicine_form.html")
        try:
            med_id = add_medicine(name, category, stock_qty,
                                  unit, unit_price, reorder_lvl)
            flash(f"Medicine added successfully. ID: {med_id}", "success")
            return redirect(url_for("pharmacy.medicines"))
        except Exception as e:
            flash(f"Failed to add medicine: {e}", "danger")

    return render_template("pharmacy/medicine_form.html")


@pharmacy_bp.route("/medicines/<int:medicine_id>/stock", methods=["POST"])
@admin_required
def adjust_stock(medicine_id):
    qty_change = request.form.get("qty_change", type=int, default=0)
    if qty_change == 0:
        flash("Please enter a non-zero quantity change.", "warning")
        return redirect(url_for("pharmacy.medicines"))
    update_stock(medicine_id, qty_change)
    action = "added to" if qty_change > 0 else "removed from"
    flash(f"{abs(qty_change)} units {action} stock.", "success")
    return redirect(url_for("pharmacy.medicines"))


# ── Prescriptions ──────────────────────────────────────────────────

@pharmacy_bp.route("/prescriptions")
@login_required
def prescriptions():
    role      = session.get("role")
    doctor_id = session.get("doctor_id")
    status    = request.args.get("status", "")

    if role == "doctor":
        rxs = get_prescriptions_by_doctor(doctor_id)
        if status:
            rxs = [r for r in rxs if r["status"] == status]
        return render_template(
            "pharmacy/prescriptions.html",
            prescriptions  = rxs,
            status_filter  = status,
            is_doctor_view = True,
            role           = role,
        )

    rxs = get_all_prescriptions(status=status if status else None)
    return render_template(
        "pharmacy/prescriptions.html",
        prescriptions  = rxs,
        status_filter  = status,
        is_doctor_view = False,
        role           = role,
    )


@pharmacy_bp.route("/prescriptions/new", methods=["GET", "POST"])
@role_required("admin", "doctor")
def new_prescription():
    role      = session.get("role")
    doctor_id = session.get("doctor_id")

    patients  = get_patients_for_dropdown()
    medicines = get_all_medicines()

    if role == "doctor":
        doctors = get_doctors_for_dropdown()
        doctors = [d for d in doctors if d["doctor_id"] == doctor_id]
    else:
        doctors = get_doctors_for_dropdown()

    if request.method == "POST":
        patient_id   = request.form.get("patient_id",   type=int)
        medicine_id  = request.form.get("medicine_id",  type=int)
        quantity     = request.form.get("quantity",      type=int)
        dosage       = request.form.get("dosage",        "").strip()
        instructions = request.form.get("instructions",  "").strip()

        if role == "doctor":
            selected_doctor_id = doctor_id
        else:
            selected_doctor_id = request.form.get("doctor_id", type=int)

        errors = []
        if not patient_id:         errors.append("Patient is required.")
        if not selected_doctor_id: errors.append("Doctor is required.")
        if not medicine_id:        errors.append("Medicine is required.")
        if not quantity or quantity < 1:
            errors.append("Quantity must be at least 1.")

        if errors:
            for e in errors: flash(e, "warning")
            return render_template(
                "pharmacy/prescription_form.html",
                patients=patients, doctors=doctors, medicines=medicines
            )
        try:
            rx_id = create_prescription(
                patient_id, selected_doctor_id, medicine_id,
                quantity, dosage, instructions
            )
            flash(f"Prescription created. ID: {rx_id}", "success")
            return redirect(url_for("pharmacy.prescriptions"))
        except Exception as e:
            flash(f"Failed to create prescription: {e}", "danger")

    return render_template(
        "pharmacy/prescription_form.html",
        patients=patients, doctors=doctors, medicines=medicines
    )


@pharmacy_bp.route("/prescriptions/<int:prescription_id>/dispense",
                   methods=["POST"])
@role_required("admin")
def dispense(prescription_id):
    ok, msg = dispense_prescription(prescription_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("pharmacy.prescriptions"))