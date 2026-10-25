"""
Library Book Manager - DevOps Mid-Term Lab (CSC418)

Front-end : Jinja2 HTML templates + CSS   (templates/, static/)
Back-end  : Flask (served by Gunicorn inside the container)
Database  : MySQL 8 (separate container, data kept in a Docker named volume)

If DB_HOST is not set the app falls back to a local SQLite file. This lets the
image run on its own with a single `docker run` (Task 3) and lets the Selenium
test run without MySQL. In docker-compose DB_HOST is always set -> MySQL.
"""
import os
import socket
import sqlite3
import time
import urllib.request

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST")            # "db" = service name in docker-compose
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "libuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "librarydb")
SQLITE_PATH = os.getenv("SQLITE_PATH", "/data/library.db")
APP_VERSION = os.getenv("APP_VERSION", "1.0")
STUDENT = os.getenv("STUDENT", "Student Name - Reg No")


# ---------------------------------------------------------------- database --
def get_conn():
    """Return a DB connection (MySQL in compose, SQLite when run standalone)."""
    if DB_HOST:
        import pymysql
        return pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER,
                               password=DB_PASSWORD, database=DB_NAME,
                               autocommit=True, connect_timeout=5)
    os.makedirs(os.path.dirname(SQLITE_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.isolation_level = None  # autocommit
    return conn


PH = "%s" if DB_HOST else "?"   # SQL placeholder style differs per driver


def init_db(retries=20, delay=3):
    """Create the table. Retries because MySQL may still be starting up."""
    if DB_HOST:
        ddl = """CREATE TABLE IF NOT EXISTS books (
                   id INT AUTO_INCREMENT PRIMARY KEY,
                   title VARCHAR(200) NOT NULL,
                   author VARCHAR(120) NOT NULL,
                   added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    else:
        ddl = """CREATE TABLE IF NOT EXISTS books (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   title TEXT NOT NULL,
                   author TEXT NOT NULL,
                   added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    for attempt in range(1, retries + 1):
        try:
            conn = get_conn()
            conn.cursor().execute(ddl)
            conn.close()
            app.logger.info("Database ready (%s)", "MySQL" if DB_HOST else "SQLite")
            return
        except Exception as exc:  # noqa: BLE001
            app.logger.warning("DB not ready (attempt %s/%s): %s", attempt, retries, exc)
            time.sleep(delay)
    raise RuntimeError("Could not connect to the database")


def query(sql, params=(), fetch=False):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql.replace("?", PH), params)
        return cur.fetchall() if fetch else None
    finally:
        conn.close()


# ------------------------------------------------------- instance identity --
def ec2_instance_id():
    """Ask the EC2 metadata service (IMDSv2) which instance we are on.
    Shown on the page so you can SEE the load balancer switching instances."""
    try:
        tok_req = urllib.request.Request(
            "http://169.254.169.254/latest/api/token", method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"})
        token = urllib.request.urlopen(tok_req, timeout=0.5).read().decode()
        id_req = urllib.request.Request(
            "http://169.254.169.254/latest/meta-data/instance-id",
            headers={"X-aws-ec2-metadata-token": token})
        return urllib.request.urlopen(id_req, timeout=0.5).read().decode()
    except Exception:  # noqa: BLE001  (not on EC2, e.g. local test)
        return "local (not on EC2)"


INSTANCE_ID = os.getenv("INSTANCE_ID") or ec2_instance_id()


# ------------------------------------------------------------------ routes --
@app.route("/")
def index():
    rows = query("SELECT id, title, author FROM books ORDER BY id DESC", fetch=True)
    books = [{"id": r[0], "title": r[1], "author": r[2]} for r in rows]
    return render_template("index.html", books=books,
                           instance_id=INSTANCE_ID,
                           container=socket.gethostname(),
                           db_engine="MySQL" if DB_HOST else "SQLite",
                           version=APP_VERSION,
                           student=STUDENT)


@app.route("/add", methods=["POST"])
def add_book():
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    if title and author:
        query("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
    return redirect(url_for("index"))


@app.route("/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    query("DELETE FROM books WHERE id = ?", (book_id,))
    return redirect(url_for("index"))


@app.route("/api/books")
def api_books():
    rows = query("SELECT id, title, author FROM books ORDER BY id", fetch=True)
    return jsonify([{"id": r[0], "title": r[1], "author": r[2]} for r in rows])


@app.route("/health")
def health():
    """Health-check endpoint used by the AWS Target Group / Load Balancer."""
    try:
        query("SELECT 1", fetch=True)
        return jsonify(status="healthy", instance=INSTANCE_ID), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify(status="unhealthy", error=str(exc)), 503


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
