import os
import re
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s()]{7,20}$")
VALID_GENDERS = {"female", "male", "non_binary", "other", "prefer_not_to_say", None}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data"}), 400

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    dob = (data.get("dob") or "").strip() or None
    gender = (data.get("gender") or "").strip() or None
    nationality = (data.get("nationality") or "").strip() or None
    message = (data.get("message") or "").strip() or None

    if len(name) < 2:
        return jsonify({"error": "Name too short"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email"}), 400
    if phone and not PHONE_RE.match(phone):
        return jsonify({"error": "Invalid phone"}), 400
    if gender and gender not in VALID_GENDERS:
        return jsonify({"error": "Invalid gender"}), 400

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

    try:
        result = supabase.table("profiles").insert(row).execute()
        if result.data:
            return jsonify({"message": f"Thanks, {name} – profile saved."}), 200
        else:
            return jsonify({"error": "Insert failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin")
def admin_dashboard():
    try:
        result = supabase.table("profiles").select("*").order("submitted_at", desc=True).execute()
        submissions = result.data if result.data else []
    except Exception:
        submissions = []
    return render_template(
        "admin.html",
        db_submissions=submissions,
        csv_submissions=[],
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.route("/testdb")
def test_db():
    try:
        supabase.table("profiles").select("count", count="exact").limit(1).execute()
        return "✅ Supabase API connection successful"
    except Exception as e:
        return f"❌ Supabase error: {e}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)