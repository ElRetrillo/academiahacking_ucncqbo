import sqlite3
import os
from flask import Flask, request, render_template

app = Flask(__name__)

DB_PATH = "/tmp/challenge.db"
FLAG = "EclipSec{l0g1n_byp4ss_sqli_success_9f81a7}"


def init_db():
    """Initialize the SQLite database with challenge users.

    The flag is stored as the admin password — the player only sees it
    after successfully bypassing the login via SQL Injection.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)")
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", FLAG, "admin"))
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("guest", "guest123", "user"))
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("user1", "password123", "user"))
        conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # DELIBERATELY VULNERABLE — SQL Injection target
        query = f"SELECT username, password, role FROM users WHERE username='{username}' AND password='{password}'"
        try:
            c.execute(query)
            row = c.fetchone()
            if row:
                user, pwd, role = row
                if role == "admin":
                    return render_template("login.html", flag=pwd, user=user)
                return render_template("login.html", message=f"Welcome, {user}. You are logged in as {role}.", user=user)
            else:
                error = "Invalid credentials."
        except Exception as e:
            error = f"Database error: {e}"
        finally:
            conn.close()
    return render_template("login.html", error=error)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
