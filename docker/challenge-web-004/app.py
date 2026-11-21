import os
import subprocess

from flask import Flask, render_template_string, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)

BODY_TEMPLATE = (
    '<form method="POST" action="" class="ctf-form">'
    '<div class="ctf-field">'
    '<label class="ctf-label" for="ping-ip">Direccion IP o host</label>'
    '<input class="ctf-input" id="ping-ip" type="text" name="ip" value="127.0.0.1" required>'
    "</div>"
    '<button type="submit" class="ctf-btn ctf-btn--primary">Ejecutar Ping</button>'
    "</form>"
    '<pre class="ctf-output">{{ output }}</pre>'
)
PAGE_TEMPLATE = render_page(
    title="Diagnostico de Red",
    heading="Herramienta de Diagnostico",
    subtitle="Comprueba la conectividad ICMP hacia un nodo destino.",
    badge="Diagnostico",
    body_html=BODY_TEMPLATE,
    wide=True,
)


@app.route("/", methods=["GET", "POST"])
def index():
    output = ""
    if request.method == "POST":
        ip = request.form.get("ip", "")
        try:
            # Intentional command injection vulnerability for CTF training
            result = subprocess.run(
                f"ping -c 1 {ip}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=10,
            )
            output = result.stdout
        except subprocess.TimeoutExpired:
            output = "Command timed out"
    return render_template_string(PAGE_TEMPLATE, output=output)


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
