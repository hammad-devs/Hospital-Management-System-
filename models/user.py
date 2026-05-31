# hms_web/models/user.py

import bcrypt
from database.db import execute_query


# ─────────────────────────────────────────────
#  PASSWORD HELPERS
# ─────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Return bcrypt hash of a plaintext password."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ─────────────────────────────────────────────
#  LOOKUP
# ─────────────────────────────────────────────

def get_user_by_username(username: str):
    """
    Fetch full user record (with role name and doctor_id) by username.
    Returns a dict or None.
    """
    rows = execute_query(
        """
        SELECT
            u.user_id,
            u.username,
            u.full_name,
            u.password_hash,
            u.email,
            u.phone,
            u.dept_id,
            u.is_active,
            r.role_name AS role,
            d.doctor_id
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        LEFT JOIN doctors d ON d.user_id = u.user_id
        WHERE u.username = %s
        """,
        (username,),
        fetch=True,
    )
    return rows[0] if rows else None


def get_user_by_id(user_id: int):
    """Fetch a user record by primary key. Returns a dict or None."""
    rows = execute_query(
        """
        SELECT
            u.user_id,
            u.username,
            u.full_name,
            u.email,
            u.phone,
            u.dept_id,
            u.is_active,
            r.role_name AS role,
            d.doctor_id
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        LEFT JOIN doctors d ON d.user_id = u.user_id
        WHERE u.user_id = %s
        """,
        (user_id,),
        fetch=True,
    )
    return rows[0] if rows else None


def get_all_users():
    """Return all users with role name — for admin user management."""
    return execute_query(
        """
        SELECT
            u.user_id,
            u.username,
            u.full_name,
            u.email,
            u.phone,
            r.role_name AS role,
            u.is_active,
            u.created_at
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        ORDER BY u.created_at DESC
        """,
        fetch=True,
    )


# ─────────────────────────────────────────────
#  CREATE / UPDATE
# ─────────────────────────────────────────────

def create_user(username, plain_password, full_name,
                email, phone, role_id, dept_id=None):
    """
    Insert a new user row.
    Returns the new user_id.
    """
    hashed = hash_password(plain_password)
    user_id, _ = execute_query(
        """
        INSERT INTO users
            (username, password_hash, full_name, email, phone, role_id, dept_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            username,
            hashed,
            full_name,
            email   or None,
            phone   or None,
            role_id,
            dept_id or None,
        ),
    )
    return user_id


def update_password(user_id: int, plain_password: str):
    """Hash and save a new password for the given user."""
    hashed = hash_password(plain_password)
    execute_query(
        "UPDATE users SET password_hash = %s WHERE user_id = %s",
        (hashed, user_id),
    )


def toggle_user_active(user_id: int, is_active: bool):
    """Enable or disable a user account."""
    execute_query(
        "UPDATE users SET is_active = %s WHERE user_id = %s",
        (int(is_active), user_id),
    )


# ─────────────────────────────────────────────
#  ROLES & DEPARTMENTS  (used by forms)
# ─────────────────────────────────────────────

def get_all_roles():
    """Return all roles for dropdown population."""
    return execute_query("SELECT role_id, role_name FROM roles", fetch=True)


def get_all_departments():
    """Return all departments for dropdown population."""
    return execute_query(
        "SELECT dept_id, name FROM departments ORDER BY name",
        fetch=True,
    )