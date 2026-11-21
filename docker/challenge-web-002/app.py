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
    body = '<p class="ctf-muted">Bienvenido al portal publico de SecureCorp. Sin novedades operativas.</p>'
    return render_page(
        title="SecureCorp",
        heading="SecureCorp",
        subtitle="Sitio corporativo publico",
        badge="Web Corporativa",
        body_html=body,
    )


@app.route("/robots.txt")
def robots():
    return Response("User-agent: *\nDisallow: /secret_flag_dir_991\n", mimetype="text/plain; charset=utf-8")


@app.route("/secret_flag_dir_991")
def flag():
    return Response(read_flag(), mimetype="text/plain; charset=utf-8")


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
