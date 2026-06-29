"""
Flask backend – minimal profile collection with Supabase persistence.
- Uses Supabase API (service role key) for permanent storage.
- Falls back to CSV if database fails (optional).
- Checks environment variables on startup.
"""

import os
import sys
import csv
import re
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env (for local development)
load_dotenv()

app = Flask(__name__)

# ---------- environment variable checks ----------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment.")
    print("   On Render: set them under Environment Variables.")
    print("   Locally: add them to a .env file.")
    sys.exit(1)

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ---------- constants ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "submissions.csv")
CSV_HEADERS = ["timestamp", "name", "email", "phone", "dob", "gender", "nationality", "message"]

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s()]{7,20}$")
VALID_GENDERS = {"female", "male", "non_binary", "other", "prefer_not_to_say", None}

# ---------- CSV backup helpers ----------
def ensure_csv_header():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(CSV_HEADERS)

def append_to_csv(row):
    ensure_csv_header()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([row.get(h, "") or "" for h in CSV_HEADERS])

def get_csv_submissions():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [{h: row.get(h, "") for h in CSV_HEADERS} for row in reader]

# ---------- routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data received"}), 400

    # Extract and validate
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    dob = (data.get("dob") or "").strip() or None
    gender = (data.get("gender") or "").strip() or None
    nationality = (data.get("nationality") or "").strip() or None
    message = (data.get("message") or "").strip() or None

    if len(name) < 2:
        return jsonify({"error": "Name must be at least 2 characters"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email address"}), 400
    if phone and not PHONE_RE.match(phone):
        return jsonify({"error": "Invalid phone number"}), 400
    if gender and gender not in VALID_GENDERS:
        return jsonify({"error": "Invalid gender option"}), 400

    row = {
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "name": name,
        "email": email,
        "phone": phone,
        "dob": dob,
        "gender": gender,
        "nationality": nationality,
        "message": message,
    }

    # 1. Write CSV backup (always)
    try:
        append_to_csv(row)
    except OSError as e:
        # Log but don't fail – we still try the database.
        print(f"⚠️ CSV write failed: {e}")

    # 2. Insert into Supabase
    try:
        result = supabase.table("profiles").insert(row).execute()
        if result.data:
            return jsonify({"message": f"Thanks, {name} – profile saved."}), 200
        else:
            return jsonify({"error": "Database insert returned no data"}), 500
    except Exception as e:
        return jsonify({"error": f"Database insert failed: {str(e)}"}), 500

@app.route("/admin")
def admin_dashboard():
    # Fetch from Supabase
    try:
        result = supabase.table("profiles").select("*").order("submitted_at", desc=True).execute()
        db_submissions = result.data if result.data else []
    except Exception as e:
        db_submissions = []
        print(f"⚠️ Admin DB fetch error: {e}")

    # Optionally read CSV as fallback / comparison
    csv_submissions = get_csv_submissions()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template(
        "admin.html",
        db_submissions=db_submissions,
        csv_submissions=csv_submissions,
        now=now
    )

@app.route("/testdb")
def test_db():
    """Quick connectivity test for Supabase."""
    try:
        supabase.table("profiles").select("count", count="exact").limit(1).execute()
        return "✅ Supabase API connection successful"
    except Exception as e:
        return f"❌ Supabase error: {e}"

# ---------- startup ----------
if __name__ == "__main__":
    # Ensure CSV header exists
    ensure_csv_header()
    print("✓ CSV backup file ready.")

    # Optional: verify Supabase connection at startup
    try:
        supabase.table("profiles").select("count", count="exact").limit(1).execute()
        print("✓ Connected to Supabase successfully.")
    except Exception as e:
        print(f"⚠️ Could not connect to Supabase on startup: {e}")
        print("   The app will still run, but DB operations may fail.")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)