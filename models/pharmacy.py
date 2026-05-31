# Pharmacy model queries
# hms_web/models/pharmacy.py

from database.db import execute_query


# ── Medicines ──────────────────────────────────────────────────────

def get_all_medicines():
    return execute_query(
        """
        SELECT medicine_id, name, category,
               stock_qty, unit, unit_price, reorder_lvl
        FROM medicines ORDER BY name
        """,
        fetch=True,
    )


def get_medicine_by_id(medicine_id: int):
    rows = execute_query(
        "SELECT * FROM medicines WHERE medicine_id = %s",
        (medicine_id,), fetch=True,
    )
    return rows[0] if rows else None


def add_medicine(name, category, stock_qty, unit, unit_price, reorder_lvl):
    med_id, _ = execute_query(
        """
        INSERT INTO medicines
            (name, category, stock_qty, unit, unit_price, reorder_lvl)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (name, category or None, int(stock_qty),
         unit, float(unit_price), int(reorder_lvl)),
    )
    return med_id


def update_stock(medicine_id: int, qty_change: int):
    """Add (positive) or subtract (negative) from stock."""
    execute_query(
        "UPDATE medicines SET stock_qty = stock_qty + %s WHERE medicine_id = %s",
        (qty_change, medicine_id),
    )


def get_low_stock_medicines():
    return execute_query(
        "SELECT * FROM medicines WHERE stock_qty <= reorder_lvl ORDER BY stock_qty",
        fetch=True,
    )


# ── Prescriptions ──────────────────────────────────────────────────

def create_prescription(patient_id, doctor_id, medicine_id,
                        quantity, dosage, instructions):
    pid, _ = execute_query(
        """
        INSERT INTO prescriptions
            (patient_id, doctor_id, medicine_id,
             quantity, dosage, instructions)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (patient_id, doctor_id, medicine_id,
         int(quantity), dosage or None, instructions or None),
    )
    return pid


def get_all_prescriptions(status=None):
    q = """
        SELECT
            pr.prescription_id, pr.quantity, pr.dosage,
            pr.prescribed_at, pr.dispensed_at, pr.status,
            p.full_name  AS patient, p.patient_code,
            u.full_name  AS doctor,
            m.name       AS medicine
        FROM prescriptions pr
        JOIN patients  p ON pr.patient_id  = p.patient_id
        JOIN doctors   d ON pr.doctor_id   = d.doctor_id
        JOIN users     u ON d.user_id      = u.user_id
        JOIN medicines m ON pr.medicine_id = m.medicine_id
    """
    if status:
        return execute_query(
            q + " WHERE pr.status = %s ORDER BY pr.prescribed_at DESC",
            (status,), fetch=True,
        )
    return execute_query(q + " ORDER BY pr.prescribed_at DESC", fetch=True)


def get_prescriptions_by_doctor(doctor_id: int):
    return execute_query(
        """
        SELECT
            pr.prescription_id, pr.quantity, pr.dosage,
            pr.prescribed_at, pr.status,
            p.full_name AS patient,
            m.name      AS medicine
        FROM prescriptions pr
        JOIN patients  p ON pr.patient_id  = p.patient_id
        JOIN medicines m ON pr.medicine_id = m.medicine_id
        WHERE pr.doctor_id = %s
        ORDER BY pr.prescribed_at DESC
        """,
        (doctor_id,), fetch=True,
    )


def dispense_prescription(prescription_id: int):
    """Mark as dispensed and deduct stock."""
    rows = execute_query(
        "SELECT medicine_id, quantity FROM prescriptions WHERE prescription_id = %s",
        (prescription_id,), fetch=True,
    )
    if not rows:
        return False, "Prescription not found."
    med_id  = rows[0]["medicine_id"]
    qty     = rows[0]["quantity"]
    med     = get_medicine_by_id(med_id)
    if not med or med["stock_qty"] < qty:
        return False, "Insufficient stock."
    update_stock(med_id, -qty)
    execute_query(
        """
        UPDATE prescriptions
        SET status = 'Dispensed', dispensed_at = NOW()
        WHERE prescription_id = %s
        """,
        (prescription_id,),
    )
    return True, "Dispensed successfully."