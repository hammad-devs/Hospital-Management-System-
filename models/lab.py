# Lab model queries
# hms_web/models/lab.py

from database.db import execute_query


def order_test(patient_id, doctor_id, test_name, notes=None):
    test_id, _ = execute_query(
        """
        INSERT INTO lab_tests (patient_id, doctor_id, test_name, notes)
        VALUES (%s,%s,%s,%s)
        """,
        (patient_id, doctor_id, test_name, notes or None),
    )
    return test_id


def get_all_tests(status=None):
    q = """
        SELECT
            t.test_id, t.test_name, t.ordered_at,
            t.result,  t.result_at, t.status,
            p.full_name  AS patient, p.patient_code,
            u.full_name  AS ordered_by
        FROM lab_tests t
        JOIN patients p ON t.patient_id = p.patient_id
        JOIN doctors  d ON t.doctor_id  = d.doctor_id
        JOIN users    u ON d.user_id    = u.user_id
    """
    if status:
        return execute_query(
            q + " WHERE t.status = %s ORDER BY t.ordered_at DESC",
            (status,), fetch=True,
        )
    return execute_query(q + " ORDER BY t.ordered_at DESC", fetch=True)


def get_tests_by_doctor(doctor_id: int):
    return execute_query(
        """
        SELECT
            t.test_id, t.test_name, t.ordered_at,
            t.result, t.status,
            p.full_name AS patient, p.patient_code
        FROM lab_tests t
        JOIN patients p ON t.patient_id = p.patient_id
        WHERE t.doctor_id = %s
        ORDER BY t.ordered_at DESC
        """,
        (doctor_id,), fetch=True,
    )


def update_test_result(test_id: int, result: str, status: str):
    execute_query(
        """
        UPDATE lab_tests
        SET result    = %s,
            status    = %s,
            result_at = IF(%s='Completed', NOW(), result_at)
        WHERE test_id = %s
        """,
        (result, status, status, test_id),
    )


def count_pending_tests():
    rows = execute_query(
        "SELECT COUNT(*) AS total FROM lab_tests WHERE status = 'Pending'",
        fetch=True,
    )
    return rows[0]["total"] if rows else 0