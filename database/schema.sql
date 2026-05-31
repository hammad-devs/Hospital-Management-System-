-- ============================================================
--  HOSPITAL MANAGEMENT SYSTEM — COMPLETE SCHEMA
--  MySQL 5.7+ / 8.0+ compatible
--  Run: mysql -u root -p < database/schema.sql
-- ============================================================

DROP DATABASE IF EXISTS hospital_db;
CREATE DATABASE hospital_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE hospital_db;

-- ─────────────────────────────────────────────
--  ROLES
-- ─────────────────────────────────────────────
CREATE TABLE roles (
    role_id   INT          AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50)  NOT NULL UNIQUE
);

INSERT INTO roles (role_name) VALUES
    ('admin'),
    ('doctor'),
    ('nurse'),
    ('receptionist');

-- ─────────────────────────────────────────────
--  DEPARTMENTS
-- ─────────────────────────────────────────────
CREATE TABLE departments (
    dept_id     INT          AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO departments (name) VALUES
    ('Cardiology'),
    ('Orthopedics'),
    ('Neurology'),
    ('General Surgery'),
    ('Emergency'),
    ('Pediatrics'),
    ('Gynecology'),
    ('Radiology'),
    ('Pharmacy'),
    ('Laboratory');

-- ─────────────────────────────────────────────
--  USERS
--  password for admin  = Admin@123
--  password for dr_ali = Pass@123
-- ─────────────────────────────────────────────
CREATE TABLE users (
    user_id       INT          AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(150) NOT NULL,
    email         VARCHAR(150) UNIQUE,
    phone         VARCHAR(20),
    role_id       INT          NOT NULL,
    dept_id       INT,
    is_active     TINYINT(1)   DEFAULT 1,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(role_id),
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

INSERT INTO users
    (username, password_hash, full_name, email, role_id, dept_id)
VALUES
    (
        'admin',
        '$2b$12$KIXiDPFuFDR6V5TfNRMfROcBvAFpBNgbhFt3eomn9K/dqJEG2PViq',
        'System Administrator',
        'admin@hospital.com',
        1,
        NULL
    ),
    (
        'dr_ali',
        '$2b$12$92sR5jWCBpBqSp.RpWjlhO3SzmVB1z4LM6oXi2s6tPdH3sFQXONEO',
        'Dr. Ali Hassan',
        'dr.ali@hospital.com',
        2,
        1
    );

-- ─────────────────────────────────────────────
--  DOCTORS
-- ─────────────────────────────────────────────
CREATE TABLE doctors (
    doctor_id        INT           AUTO_INCREMENT PRIMARY KEY,
    user_id          INT           UNIQUE,
    dept_id          INT           NOT NULL,
    specialization   VARCHAR(150),
    qualification    VARCHAR(150),
    experience_years INT           DEFAULT 0,
    license_no       VARCHAR(100)  UNIQUE,
    consultation_fee DECIMAL(10,2) DEFAULT 500.00,
    joined_date      DATE,
    is_active        TINYINT(1)    DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

INSERT INTO doctors
    (user_id, dept_id, specialization, qualification,
     experience_years, license_no, consultation_fee, joined_date)
VALUES
    (2, 1, 'Interventional Cardiology', 'MBBS, FCPS', 12, 'LIC-001', 1500.00, '2015-01-01');

-- ─────────────────────────────────────────────
--  DOCTOR SCHEDULE
-- ─────────────────────────────────────────────
CREATE TABLE doctor_schedule (
    schedule_id  INT  AUTO_INCREMENT PRIMARY KEY,
    doctor_id    INT  NOT NULL,
    day_of_week  ENUM('Mon','Tue','Wed','Thu','Fri','Sat','Sun') NOT NULL,
    start_time   TIME NOT NULL,
    end_time     TIME NOT NULL,
    max_patients INT  DEFAULT 20,
    UNIQUE KEY uq_doc_day (doctor_id, day_of_week),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
--  PATIENTS
-- ─────────────────────────────────────────────
CREATE TABLE patients (
    patient_id              INT          AUTO_INCREMENT PRIMARY KEY,
    patient_code            VARCHAR(20)  UNIQUE,
    full_name               VARCHAR(150) NOT NULL,
    dob                     DATE,
    gender                  ENUM('Male','Female','Other') NOT NULL,
    blood_group             ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-','Unknown')
                            DEFAULT 'Unknown',
    phone                   VARCHAR(20)  NOT NULL,
    email                   VARCHAR(150),
    address                 TEXT,
    emergency_contact_name  VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    allergies               TEXT,
    chronic_conditions      TEXT,
    insurance_no            VARCHAR(100),
    registered_at           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
--  WARDS
-- ─────────────────────────────────────────────
CREATE TABLE wards (
    ward_id    INT          AUTO_INCREMENT PRIMARY KEY,
    dept_id    INT          NOT NULL,
    ward_name  VARCHAR(100) NOT NULL,
    ward_type  ENUM('General','Semi-Private','Private','VIP') DEFAULT 'General',
    total_beds INT          DEFAULT 20,
    floor      INT          DEFAULT 1,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

INSERT INTO wards (dept_id, ward_name, ward_type, total_beds, floor) VALUES
    (1, 'Ward A', 'General',      20, 1),
    (2, 'Ward B', 'General',      15, 2),
    (4, 'Ward C', 'Semi-Private', 10, 2),
    (6, 'Ward D', 'General',      12, 3),
    (7, 'Ward E', 'Private',       8, 3);

-- ─────────────────────────────────────────────
--  BEDS
-- ─────────────────────────────────────────────
CREATE TABLE beds (
    bed_id     INT         AUTO_INCREMENT PRIMARY KEY,
    ward_id    INT         NOT NULL,
    bed_number VARCHAR(20) NOT NULL,
    status     ENUM('Available','Occupied','Maintenance') DEFAULT 'Available',
    UNIQUE KEY uq_ward_bed (ward_id, bed_number),
    FOREIGN KEY (ward_id) REFERENCES wards(ward_id) ON DELETE CASCADE
);

INSERT INTO beds (ward_id, bed_number) VALUES
    (1,'A-001'),(1,'A-002'),(1,'A-003'),(1,'A-004'),(1,'A-005'),
    (2,'B-001'),(2,'B-002'),(2,'B-003'),(2,'B-004'),(2,'B-005'),
    (3,'C-001'),(3,'C-002'),(3,'C-003'),(3,'C-004'),(3,'C-005'),
    (4,'D-001'),(4,'D-002'),(4,'D-003'),(4,'D-004'),(4,'D-005'),
    (5,'E-001'),(5,'E-002'),(5,'E-003'),(5,'E-004'),(5,'E-005');

-- ─────────────────────────────────────────────
--  ADMISSIONS
-- ─────────────────────────────────────────────
CREATE TABLE admissions (
    admission_id   INT  AUTO_INCREMENT PRIMARY KEY,
    patient_id     INT  NOT NULL,
    doctor_id      INT  NOT NULL,
    dept_id        INT  NOT NULL,
    bed_id         INT,
    ward           VARCHAR(100),
    bed_no         VARCHAR(20),
    admission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    discharge_date TIMESTAMP NULL,
    admission_type ENUM('Elective','Emergency','Transfer','Planned') DEFAULT 'Elective',
    diagnosis      TEXT,
    status         ENUM('Active','Discharged','Transferred')         DEFAULT 'Active',
    notes          TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)  REFERENCES doctors(doctor_id),
    FOREIGN KEY (dept_id)    REFERENCES departments(dept_id),
    FOREIGN KEY (bed_id)     REFERENCES beds(bed_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
--  ICU BEDS
-- ─────────────────────────────────────────────
CREATE TABLE icu_beds (
    icu_bed_id INT         AUTO_INCREMENT PRIMARY KEY,
    bed_number VARCHAR(20) NOT NULL UNIQUE,
    bed_type   ENUM('Standard','Isolation','Pediatric') DEFAULT 'Standard',
    ventilator TINYINT(1)  DEFAULT 0,
    monitor    TINYINT(1)  DEFAULT 1,
    status     ENUM('Available','Occupied','Maintenance') DEFAULT 'Available'
);

INSERT INTO icu_beds (bed_number, bed_type, ventilator, monitor, status) VALUES
    ('ICU-01', 'Standard',  1, 1, 'Available'),
    ('ICU-02', 'Standard',  1, 1, 'Available'),
    ('ICU-03', 'Isolation', 0, 1, 'Available'),
    ('ICU-04', 'Standard',  1, 1, 'Available'),
    ('ICU-05', 'Pediatric', 0, 1, 'Available');

-- ─────────────────────────────────────────────
--  ICU ADMISSIONS
-- ─────────────────────────────────────────────
CREATE TABLE icu_admissions (
    icu_id          INT          AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT          NOT NULL,
    doctor_id       INT          NOT NULL,
    icu_bed_id      INT,
    bed_no          VARCHAR(20),
    admitted_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    discharged_at   TIMESTAMP    NULL,
    diagnosis       TEXT,
    reason          TEXT,
    gcs_score       INT,
    ventilator      TINYINT(1)   DEFAULT 0,
    ventilator_used TINYINT(1)   DEFAULT 0,
    nurse_name      VARCHAR(100),
    status          ENUM('Critical','Stable','Improving','Discharged') DEFAULT 'Critical',
    notes           TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)  REFERENCES doctors(doctor_id),
    FOREIGN KEY (icu_bed_id) REFERENCES icu_beds(icu_bed_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
--  OT ROOMS
-- ─────────────────────────────────────────────
CREATE TABLE ot_rooms (
    ot_room_id INT         AUTO_INCREMENT PRIMARY KEY,
    room_name  VARCHAR(50) NOT NULL UNIQUE,
    room_type  ENUM('General','Cardiac','Neuro','Orthopedic','Emergency') DEFAULT 'General',
    status     ENUM('Available','In Use','Maintenance') DEFAULT 'Available'
);

INSERT INTO ot_rooms (room_name, room_type, status) VALUES
    ('OT-1', 'General',    'Available'),
    ('OT-2', 'Cardiac',    'Available'),
    ('OT-3', 'Orthopedic', 'Available'),
    ('OT-4', 'Emergency',  'Available');

-- ─────────────────────────────────────────────
--  OT BOOKINGS
-- ─────────────────────────────────────────────
CREATE TABLE ot_bookings (
    ot_booking_id   INT           AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT           NOT NULL,
    doctor_id       INT           NOT NULL,
    anesthetist_id  INT,
    ot_room_id      INT,
    ot_no           VARCHAR(20),
    scheduled_date  DATE,
    scheduled_time  TIME,
    procedure_name  VARCHAR(200),
    surgery_type    VARCHAR(200),
    anesthesia      ENUM('General','Local','Spinal','Epidural') DEFAULT 'General',
    anesthesia_type ENUM('General','Local','Spinal','Epidural') DEFAULT 'General',
    duration_hrs    DECIMAL(4,1)  DEFAULT 1.0,
    pre_op_notes    TEXT,
    post_op_notes   TEXT,
    status          ENUM('Scheduled','Completed','Cancelled','Postponed') DEFAULT 'Scheduled',
    notes           TEXT,
    created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id)     REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)      REFERENCES doctors(doctor_id),
    FOREIGN KEY (anesthetist_id) REFERENCES doctors(doctor_id) ON DELETE SET NULL,
    FOREIGN KEY (ot_room_id)     REFERENCES ot_rooms(ot_room_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
--  APPOINTMENTS
-- ─────────────────────────────────────────────
CREATE TABLE appointments (
    appt_id         INT  AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT  NOT NULL,
    doctor_id       INT  NOT NULL,
    dept_id         INT  NOT NULL,
    appt_date       DATE NOT NULL,
    appt_time       TIME NOT NULL,
    appt_type       ENUM('OPD','Follow-up','Emergency','Teleconsult') DEFAULT 'OPD',
    chief_complaint TEXT,
    status          ENUM('Scheduled','Completed','Cancelled','No-Show') DEFAULT 'Scheduled',
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)  REFERENCES doctors(doctor_id),
    FOREIGN KEY (dept_id)    REFERENCES departments(dept_id)
);

-- ─────────────────────────────────────────────
--  LAB TEST CATALOG
-- ─────────────────────────────────────────────
CREATE TABLE lab_test_catalog (
    catalog_id       INT           AUTO_INCREMENT PRIMARY KEY,
    test_code        VARCHAR(30)   UNIQUE,
    test_name        VARCHAR(200)  NOT NULL,
    category         VARCHAR(100),
    price            DECIMAL(10,2) DEFAULT 0.00,
    turnaround_hours INT           DEFAULT 24,
    normal_range     VARCHAR(200),
    unit             VARCHAR(50),
    created_at       TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lab_test_catalog
    (test_code, test_name, category, price, turnaround_hours) VALUES
    ('CBC',     'Complete Blood Count',       'Hematology',    500,   4),
    ('HBA1C',   'HbA1c',                      'Biochemistry',  800,   6),
    ('LFT',     'Liver Function Test',         'Biochemistry',  900,   6),
    ('KFT',     'Kidney Function Test',        'Biochemistry',  900,   6),
    ('LIPID',   'Lipid Profile',              'Biochemistry', 1000,   6),
    ('ECG',     'Electrocardiogram',           'Cardiology',    500,   1),
    ('XRAY',    'Chest X-Ray',               'Radiology',      800,   2),
    ('URINE',   'Urine Complete Examination', 'Microbiology',   400,   4),
    ('THYROID', 'Thyroid Function Test',       'Biochemistry', 1200,   8),
    ('COVID',   'COVID-19 PCR',              'Microbiology',  2500,  12);

-- ─────────────────────────────────────────────
--  LAB TESTS  (ordered per patient)
-- ─────────────────────────────────────────────
CREATE TABLE lab_tests (
    test_id      INT          AUTO_INCREMENT PRIMARY KEY,
    patient_id   INT          NOT NULL,
    doctor_id    INT          NOT NULL,
    admission_id INT,
    catalog_id   INT,
    test_name    VARCHAR(200) NOT NULL,
    priority     ENUM('Routine','Urgent','Stat') DEFAULT 'Routine',
    sample_type  VARCHAR(50)  DEFAULT 'Blood',
    ordered_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    result       TEXT,
    result_at    TIMESTAMP    NULL,
    normal_range VARCHAR(200),
    status       ENUM('Pending','Sample Collected','In Progress','Completed','Cancelled')
                 DEFAULT 'Pending',
    notes        TEXT,
    FOREIGN KEY (patient_id)   REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)    REFERENCES doctors(doctor_id),
    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)   ON DELETE SET NULL,
    FOREIGN KEY (catalog_id)   REFERENCES lab_test_catalog(catalog_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
--  MEDICINES
-- ─────────────────────────────────────────────
CREATE TABLE medicines (
    medicine_id   INT           AUTO_INCREMENT PRIMARY KEY,
    medicine_code VARCHAR(30)   UNIQUE,
    name          VARCHAR(200)  NOT NULL UNIQUE,
    generic_name  VARCHAR(200),
    category      VARCHAR(100),
    dosage_form   VARCHAR(50)   DEFAULT 'Tablet',
    strength      VARCHAR(50),
    manufacturer  VARCHAR(150),
    stock_qty     INT           DEFAULT 0,
    unit          VARCHAR(50)   DEFAULT 'tablets',
    unit_price    DECIMAL(10,2) DEFAULT 0.00,
    reorder_lvl   INT           DEFAULT 20,
    min_stock     INT           DEFAULT 10,
    expiry_date   DATE,
    is_active     TINYINT(1)    DEFAULT 1,
    created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO medicines
    (name, generic_name, category, dosage_form, strength,
     stock_qty, unit, unit_price, reorder_lvl, min_stock) VALUES
    ('Metformin 500mg',        'Metformin',        'Antidiabetic',     'Tablet',    '500mg',  200, 'tablets',    5.00, 20, 10),
    ('Atorvastatin 20mg',      'Atorvastatin',     'Lipid-lowering',   'Tablet',    '20mg',   150, 'tablets',    8.00, 20, 10),
    ('Amlodipine 5mg',         'Amlodipine',       'Antihypertensive', 'Tablet',    '5mg',    300, 'tablets',    6.00, 20, 10),
    ('IV Normal Saline 500ml', 'Sodium Chloride',  'IV Fluid',         'Injection', '0.9%',    50, 'bags',     120.00, 10,  5),
    ('Paracetamol 500mg',      'Paracetamol',      'Analgesic',        'Tablet',    '500mg',  500, 'tablets',    3.00, 50, 20),
    ('Amoxicillin 250mg',      'Amoxicillin',      'Antibiotic',       'Capsule',   '250mg',  180, 'capsules',  12.00, 30, 15),
    ('Omeprazole 20mg',        'Omeprazole',       'PPI',              'Capsule',   '20mg',   200, 'capsules',  10.00, 20, 10),
    ('Aspirin 75mg',           'Aspirin',          'Antiplatelet',     'Tablet',    '75mg',   400, 'tablets',    2.00, 50, 20);

-- ─────────────────────────────────────────────
--  PRESCRIPTIONS
-- ─────────────────────────────────────────────
CREATE TABLE prescriptions (
    prescription_id INT       AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT       NOT NULL,
    doctor_id       INT       NOT NULL,
    medicine_id     INT       NOT NULL,
    admission_id    INT,
    quantity        INT       NOT NULL,
    dosage          VARCHAR(100),
    instructions    TEXT,
    prescribed_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dispensed_at    TIMESTAMP NULL,
    dispensed_by    INT,
    status          ENUM('Pending','Dispensed','Cancelled') DEFAULT 'Pending',
    FOREIGN KEY (patient_id)   REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)    REFERENCES doctors(doctor_id),
    FOREIGN KEY (medicine_id)  REFERENCES medicines(medicine_id),
    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id) ON DELETE SET NULL,
    FOREIGN KEY (dispensed_by) REFERENCES users(user_id)           ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
--  BILLS
-- ─────────────────────────────────────────────
CREATE TABLE bills (
    bill_id      INT           AUTO_INCREMENT PRIMARY KEY,
    bill_no      VARCHAR(30)   UNIQUE,
    patient_id   INT           NOT NULL,
    admission_id INT,
    generated_by INT,
    subtotal     DECIMAL(12,2) DEFAULT 0,
    discount     DECIMAL(12,2) DEFAULT 0,
    tax          DECIMAL(12,2) DEFAULT 0,
    total_amount DECIMAL(12,2) DEFAULT 0,
    paid_amount  DECIMAL(12,2) DEFAULT 0,
    status       ENUM('Draft','Pending','Partial','Paid','Cancelled') DEFAULT 'Draft',
    due_date     DATE,
    notes        TEXT,
    generated_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id)   REFERENCES patients(patient_id),
    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id) ON DELETE SET NULL,
    FOREIGN KEY (generated_by) REFERENCES users(user_id)           ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
--  BILL ITEMS
-- ─────────────────────────────────────────────
CREATE TABLE bill_items (
    item_id     INT           AUTO_INCREMENT PRIMARY KEY,
    bill_id     INT           NOT NULL,
    item_type   ENUM('Consultation','Lab Test','Medicine',
                     'Bed Charge','Surgery','Radiology','Other') DEFAULT 'Other',
    description VARCHAR(255),
    quantity    INT           DEFAULT 1,
    unit_price  DECIMAL(10,2) DEFAULT 0,
    total_price DECIMAL(10,2) DEFAULT 0,
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
--  PAYMENTS
-- ─────────────────────────────────────────────
CREATE TABLE payments (
    payment_id      INT           AUTO_INCREMENT PRIMARY KEY,
    bill_id         INT           NOT NULL,
    amount          DECIMAL(12,2) NOT NULL,
    payment_mode    ENUM('Cash','Card','Bank Transfer','Insurance','Cheque') DEFAULT 'Cash',
    transaction_ref VARCHAR(100),
    payment_date    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    received_by     INT,
    notes           TEXT,
    FOREIGN KEY (bill_id)     REFERENCES bills(bill_id),
    FOREIGN KEY (received_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
--  MEDICAL NOTES
-- ─────────────────────────────────────────────
CREATE TABLE medical_notes (
    note_id      INT       AUTO_INCREMENT PRIMARY KEY,
    patient_id   INT       NOT NULL,
    doctor_id    INT       NOT NULL,
    admission_id INT,
    note_type    ENUM('Progress Note','Discharge Summary',
                      'Referral','Consultation','Nursing Note'),
    note_text    TEXT      NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id)   REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)    REFERENCES doctors(doctor_id),
    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
--  VERIFY  (quick row count check after import)
-- ─────────────────────────────────────────────
SELECT 'roles'           AS tbl, COUNT(*) AS total FROM roles
UNION ALL
SELECT 'departments',             COUNT(*)           FROM departments
UNION ALL
SELECT 'users',                   COUNT(*)           FROM users
UNION ALL
SELECT 'doctors',                 COUNT(*)           FROM doctors
UNION ALL
SELECT 'wards',                   COUNT(*)           FROM wards
UNION ALL
SELECT 'beds',                    COUNT(*)           FROM beds
UNION ALL
SELECT 'icu_beds',                COUNT(*)           FROM icu_beds
UNION ALL
SELECT 'ot_rooms',                COUNT(*)           FROM ot_rooms
UNION ALL
SELECT 'lab_test_catalog',        COUNT(*)           FROM lab_test_catalog
UNION ALL
SELECT 'medicines',               COUNT(*)           FROM medicines;


USE hospital_db;

UPDATE users 
SET password_hash = '$2b$12$JwEti5/CX2J1bLDIYJi.2OtjvXIsd83fUlDqfLPzg3Cc/6PVcsxJS' 
WHERE username = 'admin';

UPDATE users 
SET password_hash = '$2b$12$vEhgB6GzbZsRnQM9dOxG8O5fIZA8NI.ZVMTeKCbUXZzgkGRr.S4qq' 
WHERE username = 'dr_ali';