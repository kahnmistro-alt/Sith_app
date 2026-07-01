"""
Flask backend – collects Contact Info, Email, ID Number + IP address.
Stores in Supabase table: contact_submissions
"""

import os
import sys
import csv
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ---------- environment checks ----------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set.")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ---------- constants ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "submissions.csv")
CSV_HEADERS = ["submitted_at", "ip_address", "user_agent", "full_name", "email", "phone", "id_number", "address"]

# ---------- CSV helpers ----------
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

# ---------- IP helper ----------
def get_client_ip():
    if "X-Forwarded-For" in request.headers:
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    if "X-Real-IP" in request.headers:
        return request.headers.get("X-Real-IP")
    return request.remote_addr

# ---------- routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data received"}), 400

    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip()
    id_number = (data.get("id_number") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    address = (data.get("address") or "").strip() or None

    # --- validation ---
    if len(full_name) < 2:
        return jsonify({"error": "Full name must be at least 2 characters"}), 400
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        return jsonify({"error": "Invalid email address"}), 400
    if len(id_number) < 3:
        return jsonify({"error": "ID number must be at least 3 characters"}), 400

    ip_address = get_client_ip()
    user_agent = request.headers.get("User-Agent", "unknown")

    row = {
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "ip_address": ip_address,
        "user_agent": user_agent,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "id_number": id_number,
        "address": address,
    }

    # 1. CSV backup
    try:
        append_to_csv(row)
    except OSError as e:
        print(f"⚠️ CSV write failed: {e}")

    # 2. Insert into Supabase (new table name)
    try:
        result = supabase.table("contact_submissions").insert(row).execute()
        if result.data:
            return jsonify({"message": f"Thank you, {full_name}! Your info was saved."}), 200
        else:
            return jsonify({"error": "Database insert returned no data"}), 500
    except Exception as e:
        return jsonify({"error": f"Database insert failed: {str(e)}"}), 500

@app.route("/admin")
def admin_dashboard():
    try:
        result = supabase.table("contact_submissions").select("*").order("submitted_at", desc=True).execute()
        db_submissions = result.data if result.data else []
    except Exception as e:
        db_submissions = []
        print(f"⚠️ Admin DB fetch error: {e}")

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
    try:
        supabase.table("contact_submissions").select("count", count="exact").limit(1).execute()
        return "✅ Supabase connection successful"
    except Exception as e:
        return f"❌ Supabase error: {e}"

if __name__ == "__main__":
    ensure_csv_header()
    print("✓ CSV backup ready.")
    try:
        supabase.table("contact_submissions").select("count", count="exact").limit(1).execute()
        print("✓ Connected to Supabase.")
    except Exception as e:
        print(f"⚠️ Supabase connection issue: {e}")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)