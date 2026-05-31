# Admission model queries
# hms_web/models/admission.py

from database.db import execute_query


def create_admission(patient_id, doctor_id, dept_id,
                     ward, bed_no, admission_type, diagnosis):
    admission_id, _ = execute_query(
        """
        INSERT INTO admissions
            (patient_id, doctor_id, dept_id, ward,
             bed_no, admission_type, diagnosis)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
        (patient_id, doctor_id, dept_id, ward or None,
         bed_no or None, admission_type, diagnosis or None),
    )
    return admission_id


def get_all_admissions(status=None):
    q = """
        SELECT
            a.admission_id,
            a.admission_date,
            a.discharge_date,
            a.admission_type,
            a.ward,
            a.bed_no,
            a.status,
            a.diagnosis,
            p.full_name  AS patient,
            p.patient_id,
            p.patient_code,
            u.full_name  AS doctor,
            d.name       AS department
        FROM admissions a
        JOIN patients    p  ON a.patient_id = p.patient_id
        JOIN doctors     dr ON a.doctor_id  = dr.doctor_id
        JOIN users       u  ON dr.user_id   = u.user_id
        JOIN departments d  ON a.dept_id    = d.dept_id
    """
    if status:
        return execute_query(q + " WHERE a.status = %s ORDER BY a.admission_date DESC",
                             (status,), fetch=True)
    return execute_query(q + " ORDER BY a.admission_date DESC", fetch=True)


def get_admission_by_id(admission_id: int):
    rows = execute_query(
        """
        SELECT
            a.*,
            p.full_name  AS patient,
            p.patient_code,
            u.full_name  AS doctor,
            d.name       AS department
        FROM admissions a
        JOIN patients    p  ON a.patient_id = p.patient_id
        JOIN doctors     dr ON a.doctor_id  = dr.doctor_id
        JOIN users       u  ON dr.user_id   = u.user_id
        JOIN departments d  ON a.dept_id    = d.dept_id
        WHERE a.admission_id = %s
        """,
        (admission_id,), fetch=True,
    )
    return rows[0] if rows else None


def get_admissions_by_doctor(doctor_id: int):
    return execute_query(
        """
        SELECT
            a.admission_id, a.admission_date, a.status,
            a.ward, a.bed_no, a.diagnosis,
            p.full_name AS patient, p.patient_code,
            d.name      AS department
        FROM admissions a
        JOIN patients    p ON a.patient_id = p.patient_id
        JOIN departments d ON a.dept_id    = d.dept_id
        WHERE a.doctor_id = %s
        ORDER BY a.admission_date DESC
        """,
        (doctor_id,), fetch=True,
    )


def discharge_patient(admission_id: int, notes: str = None):
    execute_query(
        """
        UPDATE admissions
        SET status         = 'Discharged',
            discharge_date = NOW(),
            notes          = %s
        WHERE admission_id = %s
        """,
        (notes or None, admission_id),
    )