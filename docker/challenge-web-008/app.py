import os
from pathlib import Path

from flask import Flask, render_template_string, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)

FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def ensure_flag_env() -> None:
    if FLAG_PATH.exists() and "FLAG" not in os.environ:
        os.environ["FLAG"] = FLAG_PATH.read_text(encoding="utf-8").strip()


ensure_flag_env()


@app.route("/")
def index():
    ensure_flag_env()
    name = request.args.get("name", "Guest")
    # Intentional SSTI vulnerability for CTF training
    body = (
        f'<p class="ctf-lead">Bienvenido, {name}.</p>'
        '<p class="ctf-muted">Intenta localizar la flag en variables de entorno o archivos.</p>'
    )
    template = render_page(
        title="Motor de Plantillas",
        heading="Portal de Bienvenida",
        subtitle="Renderizado dinamico de saludo personalizado.",
        badge="Template Engine",
        body_html=body,
    )
    return render_template_string(template)


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
