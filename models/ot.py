# hms_web/models/ot.py

from database.db import execute_query


# ─────────────────────────────────────────────
# CREATE OT BOOKING
# ─────────────────────────────────────────────
def create_ot_booking(
    patient_id,
    doctor_id,
    ot_no,
    scheduled_date,
    scheduled_time,
    procedure_name,
    anesthesia,
    duration_hrs
):
    execute_query(
        """
        INSERT INTO ot_bookings
            (patient_id, doctor_id, ot_no, scheduled_date,
             scheduled_time, procedure_name, anesthesia, duration_hrs)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            patient_id,
            doctor_id,
            ot_no,
            scheduled_date,
            scheduled_time,
            procedure_name,
            anesthesia,
            float(duration_hrs)
        ),
    )


# ─────────────────────────────────────────────
# GET ALL OT BOOKINGS
# ─────────────────────────────────────────────
def get_all_ot_bookings(status=None):
    query = """
        SELECT
            o.ot_booking_id,
            o.ot_no,
            o.scheduled_date,
            o.scheduled_time,
            o.procedure_name,
            o.anesthesia,
            o.duration_hrs,
            o.status,
            p.full_name AS patient,
            p.patient_code,
            u.full_name AS surgeon
        FROM ot_bookings o
        JOIN patients p ON o.patient_id = p.patient_id
        JOIN doctors d ON o.doctor_id = d.doctor_id
        JOIN users u ON d.user_id = u.user_id
    """

    params = ()

    if status:
        query += " WHERE o.status = %s"
        params = (status,)

    query += " ORDER BY o.scheduled_date, o.scheduled_time"

    return execute_query(query, params, fetch=True)


# ─────────────────────────────────────────────
# UPDATE OT STATUS
# ─────────────────────────────────────────────
def update_ot_status(ot_booking_id: int, status: str, notes: str = None):
    execute_query(
        """
        UPDATE ot_bookings
        SET status = %s,
            notes = %s
        WHERE ot_booking_id = %s
        """,
        (status, notes, ot_booking_id),
    )