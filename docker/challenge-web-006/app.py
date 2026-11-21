import html
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, render_template_string, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)

BASE_DIR = Path(__file__).resolve().parent
FLAG_PATH = BASE_DIR / ".flag"


def get_db_path() -> Path:
    return Path(os.environ.get("CTF_DB_PATH", str(BASE_DIR / "users.db")))


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


def init_db() -> Path:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
        count = c.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'").fetchone()[0]
        if count == 0:
            c.execute("INSERT INTO users VALUES ('admin', 'super_secret_password_123!')")
        conn.commit()
    return db_path


BODY_TEMPLATE = (
    '<form method="POST" action="" class="ctf-form">'
    '<div class="ctf-field">'
    '<label class="ctf-label" for="login-user">Usuario</label>'
    '<input class="ctf-input" id="login-user" type="text" name="user" placeholder="Username">'
    "</div>"
    '<div class="ctf-field">'
    '<label class="ctf-label" for="login-pass">Contrasena</label>'
    '<input class="ctf-input" id="login-pass" type="password" name="pass" placeholder="Password">'
    "</div>"
    '<button type="submit" class="ctf-btn ctf-btn--primary">Iniciar Sesion</button>'
    "</form>"
    "{% if error %}"
    '<p class="ctf-alert ctf-alert--error">{{ error }}</p>'
    "{% endif %}"
)
PAGE_TEMPLATE = render_page(
    title="Admin Login",
    heading="Acceso Administrativo",
    subtitle="Autenticacion interna de operadores.",
    badge="SQLite Auth",
    body_html=BODY_TEMPLATE,
)


@app.route("/", methods=["GET", "POST"])
def index():
    db_path = init_db()
    error = ""
    if request.method == "POST":
        u = request.form.get("user", "")
        p = request.form.get("pass", "")
        with closing(sqlite3.connect(db_path)) as conn:
            c = conn.cursor()
            # Intentional SQL injection vulnerability for CTF training
            query = f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
            try:
                c.execute(query)
                if c.fetchone():
                    success_body = f'<p class="ctf-alert ctf-alert--success">Acceso concedido: {html.escape(read_flag())}</p>'
                    return render_page(
                        title="Bienvenido Admin",
                        heading="Bienvenido Administrador",
                        subtitle="Sesion iniciada correctamente.",
                        badge="SQLite Auth",
                        body_html=success_body,
                    )
                error = "Invalid credentials"
            except Exception as exc:
                error = str(exc)
    return render_template_string(PAGE_TEMPLATE, error=error)


if __name__ == "__main__":
    init_db()
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
