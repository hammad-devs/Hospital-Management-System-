# hms_web/routes/billing.py

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from middleware.auth_middleware import login_required, admin_required
from models.billing import (
    create_bill, add_bill_item, finalise_bill,
    record_payment, get_all_bills, get_bill_by_id
)
from models.patient   import get_patients_for_dropdown
from models.admission import get_all_admissions

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")


@billing_bp.route("/")
@admin_required
def list_bills():
    status = request.args.get("status", "")
    bills  = get_all_bills()
    if status:
        bills = [b for b in bills if b["status"] == status]
    return render_template(
        "billing/list.html",
        bills         = bills,
        status_filter = status,
    )


@billing_bp.route("/<int:bill_id>")
@admin_required
def bill_detail(bill_id):
    bill, items = get_bill_by_id(bill_id)
    if not bill:
        flash("Bill not found.", "warning")
        return redirect(url_for("billing.list_bills"))
    return render_template("billing/detail.html", bill=bill, items=items)


@billing_bp.route("/new", methods=["GET", "POST"])
@admin_required
def new_bill():
    patients   = get_patients_for_dropdown()
    admissions = get_all_admissions(status="Active")

    if request.method == "POST":
        patient_id   = request.form.get("patient_id",   type=int)
        admission_id = request.form.get("admission_id", type=int) or None
        generated_by = session["user_id"]

        if not patient_id:
            flash("Patient is required.", "warning")
            return render_template("billing/form.html",
                                   patients=patients, admissions=admissions)
        try:
            bill_id, bill_no = create_bill(patient_id, admission_id, generated_by)
            flash(f"Bill {bill_no} created. Now add items.", "success")
            return redirect(url_for("billing.add_items", bill_id=bill_id))
        except Exception as e:
            flash(f"Failed to create bill: {e}", "danger")

    return render_template("billing/form.html",
                           patients=patients, admissions=admissions)


@billing_bp.route("/<int:bill_id>/items", methods=["GET", "POST"])
@admin_required
def add_items(bill_id):
    bill, items = get_bill_by_id(bill_id)
    if not bill:
        flash("Bill not found.", "warning")
        return redirect(url_for("billing.list_bills"))

    item_types = [
        "Consultation", "Lab Test", "Medicine",
        "Bed Charge", "Surgery", "Radiology", "Other"
    ]

    if request.method == "POST":
        action = request.form.get("action", "add_item")

        if action == "add_item":
            item_type   = request.form.get("item_type",   "Other")
            description = request.form.get("description", "").strip()
            quantity    = request.form.get("quantity",    1,   type=int)
            unit_price  = request.form.get("unit_price",  0.0, type=float)

            if not description:
                flash("Item description is required.", "warning")
            elif quantity < 1:
                flash("Quantity must be at least 1.", "warning")
            elif unit_price < 0:
                flash("Unit price cannot be negative.", "warning")
            else:
                line_total = add_bill_item(
                    bill_id, item_type, description, quantity, unit_price
                )
                flash(f"Item added — PKR {line_total:,.2f}", "success")
            return redirect(url_for("billing.add_items", bill_id=bill_id))

        elif action == "finalise":
            discount = request.form.get("discount", 0.0, type=float)
            tax      = request.form.get("tax",      0.0, type=float)
            notes    = request.form.get("notes",    "").strip()

            if not items:
                flash("Add at least one item before finalising.", "warning")
                return redirect(url_for("billing.add_items", bill_id=bill_id))

            total = finalise_bill(bill_id, discount, tax, notes)
            flash(f"Bill finalised. Total: PKR {total:,.2f}", "success")
            return redirect(url_for("billing.bill_detail", bill_id=bill_id))

    # Refresh items after POST
    bill, items = get_bill_by_id(bill_id)
    return render_template(
        "billing/items.html",
        bill       = bill,
        items      = items,
        item_types = item_types,
    )


@billing_bp.route("/<int:bill_id>/payment", methods=["POST"])
@admin_required
def record_payment_route(bill_id):
    amount = request.form.get("amount", 0.0, type=float)
    if amount <= 0:
        flash("Payment amount must be greater than zero.", "warning")
        return redirect(url_for("billing.bill_detail", bill_id=bill_id))

    record_payment(bill_id, amount)
    flash(f"Payment of PKR {amount:,.2f} recorded.", "success")
    return redirect(url_for("billing.bill_detail", bill_id=bill_id))