# Icu model queries
# hms_web/models/icu.py

from database.db import execute_query


def admit_to_icu(patient_id, doctor_id, bed_no,
                 diagnosis, ventilator, nurse_name):
    icu_id, _ = execute_query(
        """
        INSERT INTO icu_admissions
            (patient_id, doctor_id, bed_no, diagnosis, ventilator, nurse_name)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (patient_id, doctor_id, bed_no,
         diagnosis or None, int(ventilator), nurse_name or None),
    )
    return icu_id


def get_active_icu():
    return execute_query(
        """
        SELECT
            i.icu_id,
            i.bed_no,
            i.admitted_at,
            i.diagnosis,
            i.ventilator,
            i.nurse_name,
            i.status,
            p.full_name  AS patient,
            p.patient_id,
            p.patient_code,
            u.full_name  AS doctor
        FROM icu_admissions i
        JOIN patients p  ON i.patient_id = p.patient_id
        JOIN doctors  d  ON i.doctor_id  = d.doctor_id
        JOIN users    u  ON d.user_id    = u.user_id
        WHERE i.status != 'Discharged'
        ORDER BY i.admitted_at DESC
        """,
        fetch=True,
    )


def get_all_icu():
    return execute_query(
        """
        SELECT
            i.icu_id, i.bed_no, i.admitted_at, i.discharged_at,
            i.diagnosis, i.ventilator, i.nurse_name, i.status,
            p.full_name AS patient, p.patient_code,
            u.full_name AS doctor
        FROM icu_admissions i
        JOIN patients p ON i.patient_id = p.patient_id
        JOIN doctors  d ON i.doctor_id  = d.doctor_id
        JOIN users    u ON d.user_id    = u.user_id
        ORDER BY i.admitted_at DESC
        """,
        fetch=True,
    )


def update_icu_status(icu_id: int, status: str, notes: str = None):
    if status == "Discharged":
        execute_query(
            """
            UPDATE icu_admissions
            SET status = 'Discharged', discharged_at = NOW(), notes = %s
            WHERE icu_id = %s
            """,
            (notes or None, icu_id),
        )
    else:
        execute_query(
            "UPDATE icu_admissions SET status = %s WHERE icu_id = %s",
            (status, icu_id),
        )


def count_active_icu():
    rows = execute_query(
        "SELECT COUNT(*) AS total FROM icu_admissions WHERE status != 'Discharged'",
        fetch=True,
    )
    return rows[0]["total"] if rows else 0