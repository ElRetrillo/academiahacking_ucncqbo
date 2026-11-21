import os
from pathlib import Path

from flask import Flask, Response
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
    body = '<p class="ctf-muted">Sistema endurecido sin copias de respaldo expuestas en produccion.</p>'
    return render_page(
        title="Sistema Seguro",
        heading="Sistema de Autenticacion",
        subtitle="Despliegue limpio en produccion.",
        badge="Source Audit",
        body_html=body,
    )


@app.route("/index.bak")
def bak():
    content = (
        "# Backup file\n"
        "def login():\n"
        f'    password = "{read_flag()}"\n'
    )
    return Response(content, mimetype="text/plain; charset=utf-8")


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
