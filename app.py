# hms_web/app.py

import os
from flask import Flask, render_template, session
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ─────────────────────────────────────────────
    #  SESSION — filesystem-backed
    # ─────────────────────────────────────────────
    from flask_session import Session
    os.makedirs("flask_session", exist_ok=True)
    app.config["SESSION_FILE_DIR"] = os.path.join(
        os.path.dirname(__file__), "flask_session"
    )
    Session(app)

    # ─────────────────────────────────────────────
    #  BLUEPRINTS
    # ─────────────────────────────────────────────
    from routes.auth         import auth_bp
    from routes.dashboard    import dashboard_bp
    from routes.patients     import patients_bp
    from routes.doctors      import doctors_bp
    from routes.appointments import appointments_bp
    from routes.admissions   import admissions_bp
    from routes.icu          import icu_bp
    from routes.ot           import ot_bp
    from routes.lab          import lab_bp
    from routes.pharmacy     import pharmacy_bp
    from routes.billing      import billing_bp
    from routes.users        import users_bp          # ← NEW

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(doctors_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(admissions_bp)
    app.register_blueprint(icu_bp)
    app.register_blueprint(ot_bp)
    app.register_blueprint(lab_bp)
    app.register_blueprint(pharmacy_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(users_bp)                 # ← NEW

    # ─────────────────────────────────────────────
    #  CONTEXT PROCESSOR
    #  Makes current user available in every template
    #  as {{ current_user }}
    # ─────────────────────────────────────────────
    @app.context_processor
    def inject_user():
        return {
            "current_user": {
                "user_id"  : session.get("user_id"),
                "username" : session.get("username"),
                "full_name": session.get("full_name"),
                "role"     : session.get("role"),
                "dept_id"  : session.get("dept_id"),
                "doctor_id": session.get("doctor_id"),
            }
            if session.get("user_id")
            else None
        }

    # ─────────────────────────────────────────────
    #  TEMPLATE FILTERS
    # ─────────────────────────────────────────────
    @app.template_filter("currency")
    def currency_filter(value):
        """{{ value | currency }}  →  PKR 1,500.00"""
        try:
            return f"PKR {float(value):,.2f}"
        except (TypeError, ValueError):
            return "PKR 0.00"

    @app.template_filter("yesno")
    def yesno_filter(value):
        """{{ value | yesno }}  →  Yes / No"""
        return "Yes" if value else "No"

    @app.template_filter("status_badge")
    def status_badge_filter(status):
        """
        {{ status | status_badge }}
        Returns an HTML badge string — safe to use with | safe in templates.
        """
        mapping = {
            # Green
            "Active"          : "badge-green",
            "Completed"       : "badge-green",
            "Paid"            : "badge-green",
            "Dispensed"       : "badge-green",
            "Stable"          : "badge-green",
            "Improving"       : "badge-green",
            # Blue
            "Scheduled"       : "badge-blue",
            "In Progress"     : "badge-blue",
            "Draft"           : "badge-blue",
            "Sample Collected": "badge-blue",
            # Amber
            "Pending"         : "badge-amber",
            "Partial"         : "badge-amber",
            "Postponed"       : "badge-amber",
            "Follow-up"       : "badge-amber",
            "Routine"         : "badge-amber",
            # Red
            "Cancelled"       : "badge-red",
            "Critical"        : "badge-red",
            "No-Show"         : "badge-red",
            "Urgent"          : "badge-red",
            "Stat"            : "badge-red",
            # Grey
            "Discharged"      : "badge-gray",
            "Transferred"     : "badge-gray",
        }
        css = mapping.get(status, "badge-gray")
        return f'<span class="badge {css}">{status}</span>'

    # ─────────────────────────────────────────────
    #  ERROR HANDLERS
    # ─────────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # ─────────────────────────────────────────────
    #  DB HEALTH CHECK  (runs once on startup)
    # ─────────────────────────────────────────────
    with app.app_context():
        try:
            from database.db import get_connection
            conn = get_connection()
            conn.close()
            print("\n✅  MySQL connection OK")
        except Exception as ex:
            print(f"\n❌  MySQL connection FAILED: {ex}")
            print("    → Check config.py credentials and ensure MySQL is running.\n")

    return app


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    print("\n🏥  Hospital Management System")
    print("    Running at  →  http://127.0.0.1:5000")
    print("    Admin login →  admin / Admin@123")
    print("    Doctor login→  dr_ali / Pass@123\n")
    app.run(
        host  = "0.0.0.0",
        port  = 5000,
        debug = Config.DEBUG,
    )