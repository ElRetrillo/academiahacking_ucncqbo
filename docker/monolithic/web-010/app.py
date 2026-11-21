import html
import os
from pathlib import Path

from flask import Flask, request
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
    ua = request.headers.get("User-Agent", "")
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.remote_addr or "")

    if "SecureBrowser1.0" not in ua:
        body = '<p class="ctf-alert ctf-alert--error">Acceso denegado: solo se permite SecureBrowser1.0.</p>'
        return render_page(
            title="Acceso Denegado",
            heading="Control de Acceso",
            subtitle="Validacion estricta de cabeceras HTTP.",
            badge="Gateway",
            body_html=body,
        )

    if client_ip != "127.0.0.1":
        body = '<p class="ctf-alert ctf-alert--error">Acceso denegado: solo conexiones locales (127.0.0.1).</p>'
        return render_page(
            title="Acceso Denegado",
            heading="Control de Acceso",
            subtitle="Validacion estricta de cabeceras HTTP.",
            badge="Gateway",
            body_html=body,
        )

    body = f'<p class="ctf-alert ctf-alert--success">Acceso concedido: {html.escape(read_flag())}</p>'
    return render_page(
        title="Acceso Concedido",
        heading="Panel Interno Verificado",
        subtitle="Validacion superada correctamente.",
        badge="Gateway",
        body_html=body,
    )


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
