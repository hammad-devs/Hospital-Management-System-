# Doctor model queries
# hms_web/models/doctor.py

from database.db import execute_query


# ─────────────────────────────────────────────
#  CREATE
# ─────────────────────────────────────────────

def create_doctor(user_id, dept_id, specialization, qualification,
                  experience, license_no, fee, joined_date):
    """Insert a new doctor record. Returns new doctor_id."""
    doctor_id, _ = execute_query(
        """
        INSERT INTO doctors
            (user_id, dept_id, specialization, qualification,
             experience_years, license_no, consultation_fee, joined_date)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            user_id       or None,
            dept_id,
            specialization,
            qualification,
            int(experience),
            license_no,
            float(fee),
            joined_date   or None,
        ),
    )
    return doctor_id


# ─────────────────────────────────────────────
#  READ
# ─────────────────────────────────────────────

def get_all_doctors(dept_id=None):
    """
    Return all active doctors.
    Optionally filter by dept_id.
    """
    if dept_id:
        return execute_query(
            """
            SELECT
                d.doctor_id,
                u.full_name,
                dept.name        AS department,
                d.specialization,
                d.qualification,
                d.experience_years,
                d.consultation_fee,
                d.license_no,
                d.joined_date
            FROM doctors d
            JOIN users       u ON d.user_id  = u.user_id
            JOIN departments dept ON d.dept_id = dept.dept_id
            WHERE d.is_active = 1
              AND d.dept_id   = %s
            ORDER BY u.full_name
            """,
            (dept_id,),
            fetch=True,
        )
    return execute_query(
        """
        SELECT
            d.doctor_id,
            u.full_name,
            dept.name        AS department,
            d.specialization,
            d.qualification,
            d.experience_years,
            d.consultation_fee,
            d.license_no,
            d.joined_date
        FROM doctors d
        JOIN users       u ON d.user_id  = u.user_id
        JOIN departments dept ON d.dept_id = dept.dept_id
        WHERE d.is_active = 1
        ORDER BY dept.name, u.full_name
        """,
        fetch=True,
    )


def get_doctor_by_id(doctor_id: int):
    """Return a single doctor dict or None."""
    rows = execute_query(
        """
        SELECT
            d.*,
            u.full_name,
            u.email,
            u.phone,
            dept.name AS department
        FROM doctors d
        JOIN users       u ON d.user_id  = u.user_id
        JOIN departments dept ON d.dept_id = dept.dept_id
        WHERE d.doctor_id = %s
        """,
        (doctor_id,),
        fetch=True,
    )
    return rows[0] if rows else None


def get_doctor_by_user_id(user_id: int):
    """Return doctor record linked to a user_id, or None."""
    rows = execute_query(
        "SELECT * FROM doctors WHERE user_id = %s",
        (user_id,),
        fetch=True,
    )
    return rows[0] if rows else None


def get_doctors_for_dropdown(dept_id=None):
    """Lightweight list for <select> dropdowns."""
    if dept_id:
        return execute_query(
            """
            SELECT d.doctor_id, u.full_name, d.consultation_fee
            FROM doctors d
            JOIN users u ON d.user_id = u.user_id
            WHERE d.is_active = 1 AND d.dept_id = %s
            ORDER BY u.full_name
            """,
            (dept_id,),
            fetch=True,
        )
    return execute_query(
        """
        SELECT d.doctor_id, u.full_name, d.consultation_fee
        FROM doctors d
        JOIN users u ON d.user_id = u.user_id
        WHERE d.is_active = 1
        ORDER BY u.full_name
        """,
        fetch=True,
    )


def get_doctor_patients(doctor_id: int):
    """
    Return all patients who have an appointment or
    admission under this doctor — used for doctor
    role-based access (doctors see only their patients).
    """
    return execute_query(
        """
        SELECT DISTINCT
            p.patient_id,
            p.patient_code,
            p.full_name,
            p.gender,
            p.phone,
            p.blood_group
        FROM patients p
        WHERE p.patient_id IN (
            SELECT patient_id FROM appointments WHERE doctor_id = %s
            UNION
            SELECT patient_id FROM admissions   WHERE doctor_id = %s
        )
        ORDER BY p.full_name
        """,
        (doctor_id, doctor_id),
        fetch=True,
    )


# ─────────────────────────────────────────────
#  SCHEDULE
# ─────────────────────────────────────────────

def upsert_schedule(doctor_id, day, start_time, end_time, max_patients):
    """Insert or update a doctor's schedule for a given day."""
    execute_query(
        """
        INSERT INTO doctor_schedule
            (doctor_id, day_of_week, start_time, end_time, max_patients)
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            start_time   = VALUES(start_time),
            end_time     = VALUES(end_time),
            max_patients = VALUES(max_patients)
        """,
        (doctor_id, day, start_time, end_time, max_patients),
    )


def get_schedule(doctor_id: int):
    """Return all schedule rows for a doctor."""
    return execute_query(
        """
        SELECT day_of_week, start_time, end_time, max_patients
        FROM doctor_schedule
        WHERE doctor_id = %s
        ORDER BY FIELD(day_of_week,'Mon','Tue','Wed','Thu','Fri','Sat','Sun')
        """,
        (doctor_id,),
        fetch=True,
    )


# ─────────────────────────────────────────────
#  STATS
# ─────────────────────────────────────────────

def count_doctors():
    """Return total active doctor count for dashboard."""
    rows = execute_query(
        "SELECT COUNT(*) AS total FROM doctors WHERE is_active = 1",
        fetch=True,
    )
    return rows[0]["total"] if rows else 0