import html
import os

from flask import Flask, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)


@app.route("/")
def index():
    file_path = request.args.get("file", "home.txt")
    try:
        # Intentional local file inclusion vulnerability for CTF training
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            content = html.escape(fh.read())
    except Exception:
        content = "File not found"

    body = (
        '<nav aria-label="Archivos" class="ctf-nav">'
        '<a class="ctf-link" href="?file=home.txt">Inicio (home.txt)</a>'
        "</nav>"
        f'<pre class="ctf-output">{content}</pre>'
    )
    return render_page(
        title="Visor de Archivos",
        heading="Visor Corporativo",
        subtitle="Lectura de documentos del servidor.",
        badge="Archivo Local",
        body_html=body,
        wide=True,
    )


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
