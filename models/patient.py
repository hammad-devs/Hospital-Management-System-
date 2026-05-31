# Patient model queries
# hms_web/models/patient.py

from database.db import execute_query


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _generate_patient_code(patient_id: int) -> str:
    """Generate a zero-padded patient code e.g. PAT-00042"""
    return f"PAT-{patient_id:05d}"


# ─────────────────────────────────────────────
#  CREATE
# ─────────────────────────────────────────────

def create_patient(full_name, dob, gender, blood_group, phone,
                   email, address, ec_name, ec_phone,
                   allergies, chronic, insurance):
    """
    Insert a new patient and immediately write back
    the generated patient_code.
    Returns (patient_id, patient_code).
    """
    patient_id, _ = execute_query(
        """
        INSERT INTO patients
            (full_name, dob, gender, blood_group, phone, email,
             address, emergency_contact_name, emergency_contact_phone,
             allergies, chronic_conditions, insurance_no)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            full_name,
            dob       or None,
            gender,
            blood_group,
            phone,
            email     or None,
            address   or None,
            ec_name   or None,
            ec_phone  or None,
            allergies or "None",
            chronic   or "None",
            insurance or None,
        ),
    )
    code = _generate_patient_code(patient_id)
    execute_query(
        "UPDATE patients SET patient_code = %s WHERE patient_id = %s",
        (code, patient_id),
    )
    return patient_id, code


# ─────────────────────────────────────────────
#  READ
# ─────────────────────────────────────────────

def get_all_patients(limit=50):
    """Return the most recently registered patients."""
    return execute_query(
        """
        SELECT patient_id, patient_code, full_name,
               gender, phone, blood_group, registered_at
        FROM patients
        ORDER BY patient_id DESC
        LIMIT %s
        """,
        (limit,),
        fetch=True,
    )


def search_patients(query: str):
    """
    Search by name (partial), patient_code, or phone.
    Returns up to 30 matches.
    """
    like = f"%{query}%"
    return execute_query(
        """
        SELECT patient_id, patient_code, full_name,
               gender, phone, blood_group, registered_at
        FROM patients
        WHERE full_name    LIKE %s
           OR patient_code LIKE %s
           OR phone        LIKE %s
        ORDER BY full_name
        LIMIT 30
        """,
        (like, like, like),
        fetch=True,
    )


def get_patient_by_id(patient_id: int):
    """Return a single patient row as a dict, or None."""
    rows = execute_query(
        "SELECT * FROM patients WHERE patient_id = %s",
        (patient_id,),
        fetch=True,
    )
    return rows[0] if rows else None


def get_patient_admissions(patient_id: int):
    """Return the 5 most recent admissions for a patient."""
    return execute_query(
        """
        SELECT
            a.admission_id,
            a.admission_date,
            a.discharge_date,
            a.status,
            d.name      AS department,
            a.diagnosis,
            u.full_name AS doctor
        FROM admissions a
        JOIN departments d ON a.dept_id   = d.dept_id
        JOIN doctors    dr ON a.doctor_id = dr.doctor_id
        JOIN users       u ON dr.user_id  = u.user_id
        WHERE a.patient_id = %s
        ORDER BY a.admission_date DESC
        LIMIT 5
        """,
        (patient_id,),
        fetch=True,
    )


def get_patient_appointments(patient_id: int):
    """Return the 5 most recent appointments for a patient."""
    return execute_query(
        """
        SELECT
            a.appt_id,
            a.appt_date,
            a.appt_time,
            a.appt_type,
            a.status,
            u.full_name AS doctor,
            d.name      AS department
        FROM appointments a
        JOIN doctors    dr ON a.doctor_id = dr.doctor_id
        JOIN users       u ON dr.user_id  = u.user_id
        JOIN departments d ON a.dept_id   = d.dept_id
        WHERE a.patient_id = %s
        ORDER BY a.appt_date DESC, a.appt_time DESC
        LIMIT 5
        """,
        (patient_id,),
        fetch=True,
    )


def get_patient_bills(patient_id: int):
    """Return all bills for a patient."""
    return execute_query(
        """
        SELECT
            bill_id, bill_no, total_amount,
            paid_amount, status, created_at
        FROM bills
        WHERE patient_id = %s
        ORDER BY created_at DESC
        """,
        (patient_id,),
        fetch=True,
    )


def get_patients_for_dropdown():
    """Lightweight list for <select> dropdowns — id + name + code."""
    return execute_query(
        """
        SELECT patient_id, patient_code, full_name
        FROM patients
        ORDER BY full_name
        """,
        fetch=True,
    )


# ─────────────────────────────────────────────
#  UPDATE
# ─────────────────────────────────────────────

def update_patient(patient_id, phone, email, address,
                   allergies, chronic, insurance):
    """Update the editable fields of a patient record."""
    execute_query(
        """
        UPDATE patients
        SET phone              = %s,
            email              = %s,
            address            = %s,
            allergies          = %s,
            chronic_conditions = %s,
            insurance_no       = %s
        WHERE patient_id = %s
        """,
        (
            phone,
            email     or None,
            address   or None,
            allergies or "None",
            chronic   or "None",
            insurance or None,
            patient_id,
        ),
    )


# ─────────────────────────────────────────────
#  DASHBOARD STATS
# ─────────────────────────────────────────────

def count_patients():
    """Return total registered patient count."""
    rows = execute_query(
        "SELECT COUNT(*) AS total FROM patients",
        fetch=True,
    )
    return rows[0]["total"] if rows else 0


def count_active_admissions():
    """Return number of currently admitted (active) patients."""
    rows = execute_query(
        "SELECT COUNT(*) AS total FROM admissions WHERE status = 'Active'",
        fetch=True,
    )
    return rows[0]["total"] if rows else 0