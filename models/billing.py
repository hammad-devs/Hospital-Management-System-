# Billing model queries
# hms_web/models/billing.py

from database.db import execute_query


def _generate_bill_no(bill_id: int) -> str:
    return f"BILL-{bill_id:05d}"


def create_bill(patient_id, admission_id, generated_by):
    bill_id, _ = execute_query(
        """
        INSERT INTO bills
            (patient_id, admission_id, generated_by,
             due_date, status)
        VALUES (%s,%s,%s, DATE_ADD(CURDATE(), INTERVAL 7 DAY), 'Draft')
        """,
        (patient_id, admission_id or None, generated_by),
    )
    bill_no = _generate_bill_no(bill_id)
    execute_query(
        "UPDATE bills SET bill_no = %s WHERE bill_id = %s",
        (bill_no, bill_id),
    )
    return bill_id, bill_no


def add_bill_item(bill_id, item_type, description, quantity, unit_price):
    total = float(quantity) * float(unit_price)
    execute_query(
        """
        INSERT INTO bill_items
            (bill_id, item_type, description, quantity, unit_price, total_price)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (bill_id, item_type, description, quantity, unit_price, total),
    )
    return total


def finalise_bill(bill_id, discount, tax, notes):
    rows = execute_query(
        "SELECT SUM(total_price) AS sub FROM bill_items WHERE bill_id = %s",
        (bill_id,), fetch=True,
    )
    subtotal     = float(rows[0]["sub"] or 0)
    total_amount = subtotal - float(discount) + float(tax)
    execute_query(
        """
        UPDATE bills
        SET subtotal = %s, discount = %s, tax = %s,
            total_amount = %s, status = 'Pending', notes = %s
        WHERE bill_id = %s
        """,
        (subtotal, discount, tax, total_amount, notes or None, bill_id),
    )
    return total_amount


def record_payment(bill_id, amount):
    execute_query(
        """
        UPDATE bills
        SET paid_amount = paid_amount + %s,
            status = CASE
                WHEN paid_amount + %s >= total_amount THEN 'Paid'
                ELSE 'Partial'
            END
        WHERE bill_id = %s
        """,
        (amount, amount, bill_id),
    )


def get_all_bills():
    return execute_query(
        """
        SELECT
            b.bill_id, b.bill_no, b.status,
            b.total_amount, b.paid_amount, b.created_at,
            p.full_name AS patient, p.patient_code
        FROM bills b
        JOIN patients p ON b.patient_id = p.patient_id
        ORDER BY b.created_at DESC
        """,
        fetch=True,
    )


def get_bill_by_id(bill_id: int):
    rows = execute_query(
        """
        SELECT
            b.*,
            p.full_name  AS patient,
            p.patient_code
        FROM bills b
        JOIN patients p ON b.patient_id = p.patient_id
        WHERE b.bill_id = %s
        """,
        (bill_id,), fetch=True,
    )
    if not rows:
        return None, []
    items = execute_query(
        "SELECT * FROM bill_items WHERE bill_id = %s",
        (bill_id,), fetch=True,
    )
    return rows[0], items


def count_pending_bills():
    rows = execute_query(
        "SELECT COUNT(*) AS total FROM bills WHERE status IN ('Pending','Partial')",
        fetch=True,
    )
    return rows[0]["total"] if rows else 0