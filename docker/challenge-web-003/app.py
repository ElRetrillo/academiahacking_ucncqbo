import html
import os
from pathlib import Path

from flask import Flask, make_response, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)

FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route("/")
def index():
    role = request.cookies.get("role", "guest")
    if role == "admin":
        body = f'<p class="ctf-alert ctf-alert--success">Acceso administrativo verificado: {html.escape(read_flag())}</p>'
        return render_page(
            title="Panel Admin",
            heading="Bienvenido Administrador",
            subtitle="Sesion privilegiada activa",
            badge="Control de Rol",
            body_html=body,
        )

    body = '<p class="ctf-alert ctf-alert--info">Sesion actual: invitado. Se requiere rol de administrador.</p>'
    resp = make_response(
        render_page(
            title="Panel Invitado",
            heading="Bienvenido Invitado",
            subtitle="No cuentas con privilegios de administrador",
            badge="Control de Rol",
            body_html=body,
        )
    )
    resp.set_cookie("role", "guest")
    return resp


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
