# 🏥 Hospital Management System — Web Edition

A fully modular, web-based HMS built with Flask + MySQL.
Converted from a monolithic JSX/CLI structure into a clean,
role-based web application.

---

## 🗂️ Complete Project Structure

hms_web/
│
├── app.py                          ← Flask entry point
├── config.py                       ← DB config + secret key
├── requirements.txt                ← pip packages
├── README.md                       ← This file
│
├── database/
│   ├── __init__.py                 ← Empty
│   ├── db.py                       ← MySQL connection + execute_query
│   └── schema.sql                  ← Full DB schema (run once)
│
├── middleware/
│   ├── __init__.py                 ← Empty
│   └── auth_middleware.py          ← login_required, role_required, admin_required
│
├── models/
│   ├── __init__.py                 ← Empty
│   ├── user.py                     ← Auth queries, password hashing
│   ├── patient.py                  ← Patient CRUD
│   ├── doctor.py                   ← Doctor CRUD + schedule
│   ├── appointment.py              ← Appointment booking + status
│   ├── admission.py                ← Ward admissions + discharge
│   ├── icu.py                      ← ICU admissions
│   ├── ot.py                       ← Operation theatre bookings
│   ├── lab.py                      ← Lab test orders + results
│   ├── pharmacy.py                 ← Medicines + prescriptions
│   └── billing.py                  ← Bills + payments
│
├── routes/
│   ├── __init__.py                 ← Empty
│   ├── auth.py                     ← /login  /logout  /change-password
│   ├── dashboard.py                ← /  /dashboard
│   ├── patients.py                 ← /patients/*
│   ├── doctors.py                  ← /doctors/*
│   ├── appointments.py             ← /appointments/*
│   ├── admissions.py               ← /admissions/*
│   ├── icu.py                      ← /icu/*
│   ├── ot.py                       ← /ot/*
│   ├── lab.py                      ← /lab/*
│   ├── pharmacy.py                 ← /pharmacy/*
│   └── billing.py                  ← /billing/*
│
├── flask_session/                  ← Auto-created on first run
│
└── templates/
    ├── base.html                   ← Master layout
    ├── auth/
    │   ├── login.html
    │   └── change_password.html
    ├── dashboard/
    │   └── index.html
    ├── patients/
    │   ├── list.html
    │   ├── detail.html
    │   └── form.html
    ├── doctors/
    │   ├── list.html
    │   ├── detail.html
    │   ├── form.html
    │   ├── schedule.html
    │   └── users.html
    ├── appointments/
    │   ├── list.html
    │   └── form.html
    ├── admissions/
    │   ├── list.html
    │   ├── detail.html
    │   └── form.html
    ├── icu/
    │   ├── list.html
    │   └── form.html
    ├── ot/
    │   ├── list.html
    │   └── form.html
    ├── lab/
    │   ├── list.html
    │   └── form.html
    ├── pharmacy/
    │   ├── medicines.html
    │   ├── medicine_form.html
    │   ├── prescriptions.html
    │   └── prescription_form.html
    ├── billing/
    │   ├── list.html
    │   ├── form.html
    │   ├── items.html
    │   └── detail.html
    └── errors/
        ├── 403.html
        ├── 404.html
        └── 500.html