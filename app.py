"""
Flask backend – collects CV text + IP address and stores in Supabase.
- Uses Supabase API (service role key) for permanent storage.
- Falls back to CSV if database fails.
- Captures real IP even behind proxies (Render/Heroku).
"""

import os
import sys
import csv
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
CSV_HEADERS = ["submitted_at", "ip_address", "user_agent", "cv_text"]

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

# ---------- IP extraction helper ----------
def get_client_ip():
    """Extract the real client IP from request headers."""
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

    cv_text = (data.get("cv_text") or "").strip()

    if not cv_text:
        return jsonify({"error": "CV content cannot be empty"}), 400

    # Get IP and user-agent automatically
    ip_address = get_client_ip()
    user_agent = request.headers.get("User-Agent", "unknown")

    row = {
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "ip_address": ip_address,
        "user_agent": user_agent,
        "cv_text": cv_text,
    }

    # 1. CSV backup (always)
    try:
        append_to_csv(row)
    except OSError as e:
        print(f"⚠️ CSV write failed: {e}")

    # 2. Insert into Supabase (table name: cv_submissions)
    try:
        result = supabase.table("cv_submissions").insert(row).execute()
        if result.data:
            return jsonify({"message": f"CV submitted from IP {ip_address}."}), 200
        else:
            return jsonify({"error": "Database insert returned no data"}), 500
    except Exception as e:
        return jsonify({"error": f"Database insert failed: {str(e)}"}), 500

@app.route("/admin")
def admin_dashboard():
    # Fetch from Supabase (new table)
    try:
        result = supabase.table("cv_submissions").select("*").order("submitted_at", desc=True).execute()
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
    """Quick connectivity test for Supabase."""
    try:
        supabase.table("cv_submissions").select("count", count="exact").limit(1).execute()
        return "✅ Supabase API connection successful"
    except Exception as e:
        return f"❌ Supabase error: {e}"

# ---------- startup ----------
if __name__ == "__main__":
    ensure_csv_header()
    print("✓ CSV backup file ready.")

    try:
        supabase.table("cv_submissions").select("count", count="exact").limit(1).execute()
        print("✓ Connected to Supabase successfully.")
    except Exception as e:
        print(f"⚠️ Could not connect to Supabase on startup: {e}")
        print("   The app will still run, but DB operations may fail.")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)