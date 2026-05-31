# hms_web/routes/lab.py

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from middleware.auth_middleware import login_required, role_required
from models.lab     import (
    order_test, get_all_tests,
    get_tests_by_doctor, update_test_result
)
from models.patient import get_patients_for_dropdown
from models.doctor  import get_doctors_for_dropdown

lab_bp = Blueprint("lab", __name__, url_prefix="/lab")


@lab_bp.route("/")
@login_required
def list_tests():
    role      = session.get("role")
    doctor_id = session.get("doctor_id")
    status    = request.args.get("status", "")

    # Doctor sees only tests they ordered
    if role == "doctor":
        tests = get_tests_by_doctor(doctor_id)
        if status:
            tests = [t for t in tests if t["status"] == status]
        return render_template(
            "lab/list.html",
            tests          = tests,
            status_filter  = status,
            is_doctor_view = True,
        )

    tests = get_all_tests(status=status if status else None)
    return render_template(
        "lab/list.html",
        tests          = tests,
        status_filter  = status,
        is_doctor_view = False,
    )


@lab_bp.route("/new", methods=["GET", "POST"])
@role_required("admin", "doctor")
def new_test():
    role      = session.get("role")
    doctor_id = session.get("doctor_id")

    patients = get_patients_for_dropdown()

    if role == "doctor":
        doctors = get_doctors_for_dropdown()
        doctors = [d for d in doctors if d["doctor_id"] == doctor_id]
    else:
        doctors = get_doctors_for_dropdown()

    if request.method == "POST":
        patient_id = request.form.get("patient_id", type=int)
        test_name  = request.form.get("test_name",  "").strip()
        notes      = request.form.get("notes",      "").strip()

        if role == "doctor":
            selected_doctor_id = doctor_id
        else:
            selected_doctor_id = request.form.get("doctor_id", type=int)

        errors = []
        if not patient_id:         errors.append("Patient is required.")
        if not selected_doctor_id: errors.append("Doctor is required.")
        if not test_name:          errors.append("Test name is required.")

        if errors:
            for e in errors: flash(e, "warning")
            return render_template("lab/form.html",
                                   patients=patients, doctors=doctors)
        try:
            test_id = order_test(patient_id, selected_doctor_id,
                                 test_name, notes)
            flash(f"Lab test ordered successfully. Test ID: {test_id}", "success")
            return redirect(url_for("lab.list_tests"))
        except Exception as e:
            flash(f"Failed to order test: {e}", "danger")

    return render_template("lab/form.html",
                           patients=patients, doctors=doctors)


@lab_bp.route("/<int:test_id>/result", methods=["POST"])
@role_required("admin", "doctor")
def update_result(test_id):
    result = request.form.get("result", "").strip()
    status = request.form.get("status", "Completed")

    valid = ["Pending", "In Progress", "Completed", "Cancelled"]
    if status not in valid:
        flash("Invalid status.", "warning")
        return redirect(url_for("lab.list_tests"))

    if not result:
        flash("Result text is required.", "warning")
        return redirect(url_for("lab.list_tests"))

    update_test_result(test_id, result, status)
    flash("Lab test result updated.", "success")
    return redirect(url_for("lab.list_tests"))