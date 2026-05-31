# hms_web/routes/dashboard.py

from flask import Blueprint, render_template, session
from middleware.auth_middleware import login_required

# ── Model imports for stats ────────────────────────────────────────
from models.patient     import count_patients, count_active_admissions
from models.doctor      import count_doctors, get_all_doctors
from models.appointment import count_today_appointments, get_appointments_today
from models.icu         import count_active_icu, get_active_icu
from models.lab         import count_pending_tests
from models.billing     import count_pending_bills
from models.admission   import get_all_admissions
from models.pharmacy    import get_low_stock_medicines

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    role      = session.get("role")
    doctor_id = session.get("doctor_id")

    # ── Stats cards (admin sees all, doctor sees own) ──────────────
    if role == "admin":
        stats = {
            "total_patients"      : count_patients(),
            "active_admissions"   : count_active_admissions(),
            "total_doctors"       : count_doctors(),
            "today_appointments"  : count_today_appointments(),
            "icu_patients"        : count_active_icu(),
            "pending_lab_tests"   : count_pending_tests(),
            "pending_bills"       : count_pending_bills(),
        }
        # ── Recent data widgets ────────────────────────────────────
        today_appts   = get_appointments_today()
        icu_patients  = get_active_icu()
        recent_admits = get_all_admissions(status="Active")[:8]
        low_stock     = get_low_stock_medicines()

        return render_template(
            "dashboard/index.html",
            stats         = stats,
            today_appts   = today_appts,
            icu_patients  = icu_patients,
            recent_admits = recent_admits,
            low_stock     = low_stock,
        )

    # ── Doctor dashboard ───────────────────────────────────────────
    else:
        from models.appointment import get_appointments_by_doctor
        from models.admission   import get_admissions_by_doctor
        from models.lab         import get_tests_by_doctor
        from models.pharmacy    import get_prescriptions_by_doctor

        my_appts   = get_appointments_by_doctor(doctor_id)
        my_admits  = get_admissions_by_doctor(doctor_id)
        my_tests   = get_tests_by_doctor(doctor_id)[:10]
        my_rx      = get_prescriptions_by_doctor(doctor_id)[:10]

        stats = {
            "my_appointments" : len(my_appts),
            "my_admissions"   : len([a for a in my_admits if a["status"] == "Active"]),
            "my_lab_tests"    : len(my_tests),
            "my_prescriptions": len(my_rx),
        }

        return render_template(
            "dashboard/index.html",
            stats      = stats,
            my_appts   = my_appts[:8],
            my_admits  = my_admits[:8],
            my_tests   = my_tests,
            my_rx      = my_rx,
        )