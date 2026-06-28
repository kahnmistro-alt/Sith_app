# Contact Form → CSV → Yugabyte Cloud Pipeline

A simple web app: a form collects name/email/phone/message, the Flask backend
validates it, appends it to a local CSV backup, and inserts it into your
Yugabyte Cloud (PostgreSQL-compatible) database.

## Files

```
sith-project/
├── app.py                 # Flask backend
├── requirements.txt       # Python dependencies
├── .env.example           # Template for your real .env (copy this)
├── .gitignore             # Keeps secrets/.env out of git
├── root.crt               # Yugabyte Cloud SSL root certificate
├── templates/
│   └── index.html         # The form
└── static/
    ├── css/style.css      # Styling
    └── js/script.js       # Client-side validation + fetch POST
```

`submissions.csv` is created automatically next to `app.py` the first time
someone submits the form — it's your local backup/export trail.

## Setup

1. **Install Python 3.10+** if you don't have it.

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # on Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your environment variables:**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in `YB_PASSWORD` with your real Yugabyte Cloud
   database password. The other values (host, port, database, user) are
   already filled in based on your `incredible-toad` cluster — double check
   they match what's on your cluster's **Connect** tab in the Yugabyte Cloud
   console.

5. **Confirm `root.crt` is in the project root.** It already is — this is
   the SSL certificate Yugabyte Cloud requires for `sslmode=verify-full`.

6. **Run the app:**
   ```bash
   python app.py
   ```
   On first run, it will try to connect to Yugabyte Cloud and create the
   `form_submissions` table if it doesn't exist yet. If the connection
   fails (wrong password, IP not allow-listed, etc.) the app will still
   start — submissions will save to CSV but the warning will tell you the
   DB insert failed.

7. **Open the form:**
   Visit `http://127.0.0.1:5000` in your browser.

## Before it will actually reach your database

Two things outside this code that you need to check in the Yugabyte Cloud
console:

- **IP Allow List:** Yugabyte Cloud only accepts connections from IP
  addresses you've explicitly allowed. Make sure the machine running this
  app (your laptop's public IP, or `0.0.0.0/0` for testing — not
  recommended for production) is on the allow list under your cluster's
  network settings.
- **Database user & password:** Confirm the username in `.env` matches a
  real database user on your cluster, and that you have the correct
  password. If you're not sure, you can reset/create a DB user from the
  Yugabyte Cloud console.

## How a submission flows through the system

1. Browser sends a `POST /submit` with JSON `{name, email, phone, message}`.
2. Flask validates the fields server-side (never trusts the client-side
   checks alone).
3. The row is appended to `submissions.csv` (timestamped, UTC).
4. The row is inserted into the `form_submissions` table in Yugabyte Cloud.
5. Flask returns a JSON success or error message, which the frontend
   displays without a page reload.

## Security notes

- `root.crt` is a public CA certificate — safe to keep in the repo.
- `.env` (with your real password) is in `.gitignore` — **never commit it**.
- Never share your `.env` contents, account ID, or device IP in chat
  messages, tickets, or public repos.

## Stretch goals (not yet built, but the codebase supports adding them)

- Recruiter/admin authentication (e.g. Flask-Login + a users table).
- A `/export` route that streams all rows as a downloadable CSV.
- An analytics dashboard (e.g. a `/dashboard` route with Chart.js,
  querying aggregate stats from `form_submissions`).
- A scheduled job to back up `submissions.csv` to cloud storage.
