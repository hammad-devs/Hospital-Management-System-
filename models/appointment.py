# hms_web/models/appointment.py

from database.db import execute_query


# ─────────────────────────────────────────────
#  CREATE
# ─────────────────────────────────────────────

def create_appointment(patient_id, doctor_id, dept_id,
                       appt_date, appt_time, appt_type, complaint):
    """
    Book a new appointment after a slot conflict check.
    Returns (appt_id, None) on success or (None, error_msg).
    """
    # Conflict check — same doctor, date, time, not cancelled
    conflict = execute_query(
        """
        SELECT appt_id
        FROM appointments
        WHERE doctor_id = %s
          AND appt_date = %s
          AND appt_time = %s
          AND status    = 'Scheduled'
        """,
        (doctor_id, appt_date, appt_time),
        fetch=True,
    )
    if conflict:
        return None, "That time slot is already booked. Choose a different time."

    appt_id, _ = execute_query(
        """
        INSERT INTO appointments
            (patient_id, doctor_id, dept_id,
             appt_date, appt_time, appt_type, chief_complaint)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            patient_id, doctor_id, dept_id,
            appt_date,  appt_time, appt_type,
            complaint or None,
        ),
    )
    return appt_id, None


# ─────────────────────────────────────────────
#  BASE SELECT  — matches appointments table in schema
# ─────────────────────────────────────────────

def _base_select():
    return """
        SELECT
            a.appt_id,
            a.appt_date,
            a.appt_time,
            a.appt_type,
            a.status,
            a.chief_complaint,
            a.notes,
            p.patient_id,
            p.full_name   AS patient,
            p.patient_code,
            dr.doctor_id,
            u.full_name   AS doctor,
            d.dept_id,
            d.name        AS department
        FROM appointments a
        JOIN patients    p  ON a.patient_id = p.patient_id
        JOIN doctors     dr ON a.doctor_id  = dr.doctor_id
        JOIN users       u  ON dr.user_id   = u.user_id
        JOIN departments d  ON a.dept_id    = d.dept_id
    """


# ─────────────────────────────────────────────
#  READ
# ─────────────────────────────────────────────

def get_appointments_today():
    """All appointments scheduled for today."""
    return execute_query(
        _base_select() +
        "WHERE a.appt_date = CURDATE() ORDER BY a.appt_time",
        fetch=True,
    )


def get_appointments_by_date(date: str):
    """Appointments for a specific date string YYYY-MM-DD."""
    return execute_query(
        _base_select() +
        "WHERE a.appt_date = %s ORDER BY a.appt_time",
        (date,),
        fetch=True,
    )


def get_appointments_by_doctor(doctor_id: int):
    """30 most recent appointments for one doctor."""
    return execute_query(
        _base_select() +
        "WHERE a.doctor_id = %s ORDER BY a.appt_date DESC, a.appt_time DESC LIMIT 30",
        (doctor_id,),
        fetch=True,
    )


def get_appointments_by_patient(patient_id: int):
    """All appointments for one patient."""
    return execute_query(
        _base_select() +
        "WHERE a.patient_id = %s ORDER BY a.appt_date DESC, a.appt_time DESC",
        (patient_id,),
        fetch=True,
    )


def get_appointment_by_id(appt_id: int):
    """Single appointment dict or None."""
    rows = execute_query(
        _base_select() + "WHERE a.appt_id = %s",
        (appt_id,),
        fetch=True,
    )
    return rows[0] if rows else None


# ─────────────────────────────────────────────
#  UPDATE
# ─────────────────────────────────────────────

def update_appointment_status(appt_id: int, status: str, notes: str = None):
    """Update appointment status and optional notes."""
    execute_query(
        """
        UPDATE appointments
        SET status = %s,
            notes  = %s
        WHERE appt_id = %s
        """,
        (status, notes or None, appt_id),
    )


# ─────────────────────────────────────────────
#  STATS
# ─────────────────────────────────────────────

def count_today_appointments():
    """Count of today's appointments for dashboard."""
    rows = execute_query(
        """
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE appt_date = CURDATE()
        """,
        fetch=True,
    )
    return rows[0]["total"] if rows else 0