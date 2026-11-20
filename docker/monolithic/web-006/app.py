import sqlite3
from contextlib import closing
from pathlib import Path
from flask import Flask, request, render_template_string

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "users.db"
FLAG_PATH = BASE_DIR / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
        count = c.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'").fetchone()[0]
        if count == 0:
            c.execute("INSERT INTO users VALUES ('admin', 'super_secret_password_123!')")
        conn.commit()


template = '''
<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;">
<h1>Admin Login</h1>
<form method="POST">
    <input type="text" name="user" placeholder="Username"><br><br>
    <input type="password" name="pass" placeholder="Password"><br><br>
    <button type="submit">Login</button>
</form>
<p style="color:red">{{ error }}</p>
</body></html>
'''


@app.route('/', methods=['GET', 'POST'])
def index():
    error = ''
    if request.method == 'POST':
        u = request.form.get('user', '')
        p = request.form.get('pass', '')
        with closing(sqlite3.connect(DB_PATH)) as conn:
            c = conn.cursor()
            # Intentional SQL injection vulnerability for CTF training
            query = f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
            try:
                c.execute(query)
                if c.fetchone():
                    return render_template_string(
                        '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome Admin!</h1><p>{{ flag }}</p></body></html>',
                        flag=read_flag(),
                    )
                error = 'Invalid credentials'
            except Exception as e:
                error = str(e)
    return render_template_string(template, error=error)


if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=8006)
