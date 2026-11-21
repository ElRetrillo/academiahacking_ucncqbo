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
    profiles = {
        "1": "Alice - Normal User",
        "2": "Bob - Normal User",
        "0": f"Admin - {read_flag()}",
    }
    uid = request.args.get("id", "1")
    profile = profiles.get(uid, "User not found")
    alert_class = "ctf-alert ctf-alert--success" if uid == "0" else "ctf-alert ctf-alert--info"
    body = (
        f'<p class="{alert_class}">{html.escape(profile)}</p>'
        '<nav aria-label="Perfiles" class="ctf-nav">'
        '<a class="ctf-link" href="?id=1">Ver Alice</a>'
        '<a class="ctf-link" href="?id=2">Ver Bob</a>'
        "</nav>"
    )
    return render_page(
        title="Perfiles de Usuario",
        heading="Directorio de Perfiles",
        subtitle="Consulta de fichas de usuario registradas.",
        badge="Directorio",
        body_html=body,
    )


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
