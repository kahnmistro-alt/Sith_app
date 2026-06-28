"""
Flask backend – local SQLite + CSV, with all demographic fields.
Includes automatic schema migration to add new columns.
"""

import csv
import os
import re
import sqlite3
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ---------- constants ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "submissions.csv")
DB_PATH = os.path.join(BASE_DIR, "submissions.db")

# Updated CSV headers – all fields (including new ones)
CSV_HEADERS = [
    "timestamp", "name", "email", "phone", "message",
    "nationality", "employment_status", "education_level",
    # Demographic fields (optional)
    "dob", "gender", "sex", "ethnicity", "disability",
    "marital_status", "household_size", "family_structure",
    "occupation", "income", "net_worth",
    "language", "religion", "geographic_location",
    "housing_tenure", "birth_rate", "death_rate", "migration_status"
]

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s()]{7,20}$")

# Validations for dropdowns
VALID_GENDERS = {"female", "male", "non_binary", "other", "prefer_not_to_say", None}
VALID_SEX = {"female", "male", "other", "prefer_not_to_say", None}
VALID_ETHNICITIES = {"black_african", "coloured", "indian_asian", "white", "other", "prefer_not_to_say", None}
VALID_DISABILITY = {"no_disability", "has_disability", "prefer_not_to_say", None}
VALID_EMPLOYMENT = {"employed", "unemployed", "self_employed", "student"}
VALID_EDUCATION = {"level_1_highschool", "level_2_matric", "level_3_n4_n6"}
VALID_MARITAL = {"single", "married", "divorced", "widowed", "separated", "prefer_not_to_say", None}
VALID_FAMILY = {"single_person", "couple_no_kids", "nuclear_family", "extended_family", "other", None}
VALID_HOUSING = {"own", "rent", "live_with_family", "other", None}
VALID_MIGRATION = {"citizen", "permanent_resident", "temporary_visa", "other", None}

# ---------- database helpers ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # Main applications table (core fields)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submitted_at TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                message TEXT NOT NULL,
                nationality TEXT NOT NULL,
                employment_status TEXT NOT NULL,
                education_level TEXT NOT NULL
            )
        """)
        # Demographics table – base schema
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applicant_demographics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                submitted_at TEXT NOT NULL,
                dob TEXT,
                gender TEXT,
                ethnicity TEXT,
                disability TEXT,
                FOREIGN KEY (application_id) REFERENCES job_applications(id)
            )
        """)
    # Now migrate to add any missing columns
    migrate_db()

def migrate_db():
    """Add missing columns to applicant_demographics if they don't exist."""
    with get_db() as conn:
        columns_to_add = [
            ("sex", "TEXT"),
            ("marital_status", "TEXT"),
            ("household_size", "INTEGER"),
            ("family_structure", "TEXT"),
            ("occupation", "TEXT"),
            ("income", "REAL"),
            ("net_worth", "REAL"),
            ("language", "TEXT"),
            ("religion", "TEXT"),
            ("geographic_location", "TEXT"),
            ("housing_tenure", "TEXT"),
            ("birth_rate", "REAL"),
            ("death_rate", "REAL"),
            ("migration_status", "TEXT"),
        ]
        # Get existing columns
        cur = conn.execute("PRAGMA table_info(applicant_demographics)")
        existing = [row[1] for row in cur.fetchall()]
        for col, col_type in columns_to_add:
            if col not in existing:
                conn.execute(f"ALTER TABLE applicant_demographics ADD COLUMN {col} {col_type}")
        conn.commit()

def insert_into_db(row):
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO job_applications
                (submitted_at, name, email, phone, message, nationality, employment_status, education_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["timestamp"], row["name"], row["email"], row["phone"], row["message"],
                row["nationality"], row["employment_status"], row["education_level"],
            )
        )
        app_id = cur.lastrowid

        # Insert demographics (always, with NULLs for empty)
        conn.execute(
            """
            INSERT INTO applicant_demographics
                (application_id, submitted_at, dob, gender, sex, ethnicity, disability,
                 marital_status, household_size, family_structure, occupation, income, net_worth,
                 language, religion, geographic_location, housing_tenure, birth_rate, death_rate, migration_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                app_id, row["timestamp"],
                row.get("dob"), row.get("gender"), row.get("sex"), row.get("ethnicity"), row.get("disability"),
                row.get("marital_status"), row.get("household_size"), row.get("family_structure"),
                row.get("occupation"), row.get("income"), row.get("net_worth"),
                row.get("language"), row.get("religion"), row.get("geographic_location"),
                row.get("housing_tenure"), row.get("birth_rate"), row.get("death_rate"), row.get("migration_status")
            )
        )

def get_db_submissions():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                a.id,
                a.submitted_at,
                a.name,
                a.email,
                a.phone,
                a.message,
                a.nationality,
                a.employment_status,
                a.education_level,
                d.dob,
                d.gender,
                d.sex,
                d.ethnicity,
                d.disability,
                d.marital_status,
                d.household_size,
                d.family_structure,
                d.occupation,
                d.income,
                d.net_worth,
                d.language,
                d.religion,
                d.geographic_location,
                d.housing_tenure,
                d.birth_rate,
                d.death_rate,
                d.migration_status
            FROM job_applications a
            LEFT JOIN applicant_demographics d ON a.id = d.application_id
            ORDER BY a.submitted_at DESC
        """).fetchall()
    return [dict(row) for row in rows]

# ---------- CSV helpers ----------
def ensure_csv_header():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(CSV_HEADERS)

def append_to_csv(row):
    ensure_csv_header()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Build row in CSV_HEADERS order
        csv_row = [row.get(h, "") or "" for h in CSV_HEADERS]
        writer.writerow(csv_row)

def get_csv_submissions():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            clean = {h: row.get(h, "") for h in CSV_HEADERS}
            rows.append(clean)
    return rows

# ---------- validation ----------
def validate_payload(data):
    if not data:
        return False, "No data received."

    # Core required fields
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    message = (data.get("message") or "").strip()
    nationality = (data.get("nationality") or "").strip()
    employment_status = (data.get("employmentStatus") or "").strip()
    education_level = (data.get("educationLevel") or "").strip()

    # Optional fields (normalise to None if empty)
    def optional_str(key):
        val = (data.get(key) or "").strip()
        return val if val else None

    gender = optional_str("gender")
    sex = optional_str("sex")
    ethnicity = optional_str("ethnicity")
    disability = optional_str("disability")
    dob = optional_str("dob")
    marital_status = optional_str("maritalStatus")
    family_structure = optional_str("familyStructure")
    occupation = optional_str("occupation")
    language = optional_str("language")
    religion = optional_str("religion")
    geographic_location = optional_str("geographicLocation")
    housing_tenure = optional_str("housingTenure")
    migration_status = optional_str("migrationStatus")

    # Numeric fields
    household_size = data.get("householdSize")
    if household_size is not None and household_size != "":
        try:
            household_size = int(household_size)
            if household_size < 0:
                return False, "Household size cannot be negative."
        except ValueError:
            return False, "Household size must be a number."
    else:
        household_size = None

    income = data.get("income")
    if income is not None and income != "":
        try:
            income = float(income)
            if income < 0:
                return False, "Income cannot be negative."
        except ValueError:
            return False, "Income must be a number."
    else:
        income = None

    net_worth = data.get("netWorth")
    if net_worth is not None and net_worth != "":
        try:
            net_worth = float(net_worth)
            if net_worth < 0:
                return False, "Net worth cannot be negative."
        except ValueError:
            return False, "Net worth must be a number."
    else:
        net_worth = None

    birth_rate = data.get("birthRate")
    if birth_rate is not None and birth_rate != "":
        try:
            birth_rate = float(birth_rate)
        except ValueError:
            return False, "Birth rate must be a number."
    else:
        birth_rate = None

    death_rate = data.get("deathRate")
    if death_rate is not None and death_rate != "":
        try:
            death_rate = float(death_rate)
        except ValueError:
            return False, "Death rate must be a number."
    else:
        death_rate = None

    # Validations for required fields
    if len(name) < 2:
        return False, "Name must be at least 2 characters."
    if not EMAIL_RE.match(email):
        return False, "Invalid email address."
    if not PHONE_RE.match(phone):
        return False, "Invalid phone number."
    if len(message) < 5:
        return False, "Message must be at least 5 characters."
    if len(nationality) < 2:
        return False, "Please provide a valid nationality."
    if employment_status not in VALID_EMPLOYMENT:
        return False, "Invalid employment status."
    if education_level not in VALID_EDUCATION:
        return False, "Invalid education level."

    # Optional dropdown validations
    if gender is not None and gender not in VALID_GENDERS:
        return False, "Invalid gender option."
    if sex is not None and sex not in VALID_SEX:
        return False, "Invalid sex option."
    if ethnicity is not None and ethnicity not in VALID_ETHNICITIES:
        return False, "Invalid ethnicity option."
    if disability is not None and disability not in VALID_DISABILITY:
        return False, "Invalid disability option."
    if marital_status is not None and marital_status not in VALID_MARITAL:
        return False, "Invalid marital status."
    if family_structure is not None and family_structure not in VALID_FAMILY:
        return False, "Invalid family structure."
    if housing_tenure is not None and housing_tenure not in VALID_HOUSING:
        return False, "Invalid housing tenure."
    if migration_status is not None and migration_status not in VALID_MIGRATION:
        return False, "Invalid migration status."

    return True, None

# ---------- routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True)

    is_valid, error = validate_payload(data)
    if not is_valid:
        return jsonify({"error": error}), 400

    # Build row with all fields
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "name": data["name"].strip(),
        "email": data["email"].strip(),
        "phone": data["phone"].strip(),
        "message": data["message"].strip(),
        "nationality": data["nationality"].strip(),
        "employment_status": data["employmentStatus"].strip(),
        "education_level": data["educationLevel"].strip(),
        # Optional – normalise empty to None
        "dob": (data.get("dob") or "").strip() or None,
        "gender": (data.get("gender") or "").strip() or None,
        "sex": (data.get("sex") or "").strip() or None,
        "ethnicity": (data.get("ethnicity") or "").strip() or None,
        "disability": (data.get("disability") or "").strip() or None,
        "marital_status": (data.get("maritalStatus") or "").strip() or None,
        "family_structure": (data.get("familyStructure") or "").strip() or None,
        "occupation": (data.get("occupation") or "").strip() or None,
        "language": (data.get("language") or "").strip() or None,
        "religion": (data.get("religion") or "").strip() or None,
        "geographic_location": (data.get("geographicLocation") or "").strip() or None,
        "housing_tenure": (data.get("housingTenure") or "").strip() or None,
        "migration_status": (data.get("migrationStatus") or "").strip() or None,
        # Numeric
        "household_size": data.get("householdSize") if data.get("householdSize") != "" else None,
        "income": data.get("income") if data.get("income") != "" else None,
        "net_worth": data.get("netWorth") if data.get("netWorth") != "" else None,
        "birth_rate": data.get("birthRate") if data.get("birthRate") != "" else None,
        "death_rate": data.get("deathRate") if data.get("deathRate") != "" else None,
    }

    # CSV backup
    try:
        append_to_csv(row)
    except OSError as e:
        return jsonify({"error": f"CSV write failed: {e}"}), 500

    # SQLite insert
    try:
        insert_into_db(row)
    except sqlite3.Error as e:
        return jsonify({"error": f"Database insert failed: {e}"}), 500

    return jsonify({"message": f"Thanks, {row['name']} — your submission was saved."}), 200

@app.route("/admin")
def admin_dashboard():
    try:
        db_submissions = get_db_submissions()
        csv_submissions = get_csv_submissions()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return render_template(
            "admin.html",
            db_submissions=db_submissions,
            csv_submissions=csv_submissions,
            now=now
        )
    except Exception as e:
        # Return error as plain text for debugging
        return f"Admin error: {str(e)}", 500

# ---------- startup ----------
if __name__ == "__main__":
    init_db()
    ensure_csv_header()
    print("✓ SQLite database and CSV ready.")
    # Bind to 0.0.0.0 and use PORT env var (for Render)
    port = int(os.environ.get("PORT", 5000))
    # For debugging, you can set debug=True temporarily
    app.run(host="0.0.0.0", port=port, debug=False)