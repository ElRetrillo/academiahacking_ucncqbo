import html
import os
import subprocess

from flask import Flask, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)


@app.route("/")
def index():
    cmd = request.args.get("cmd")
    if cmd:
        try:
            # Intentional command injection vulnerability for CTF training
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=10,
            )
            out = html.escape(result.stdout)
        except subprocess.TimeoutExpired:
            out = "Command timed out"
        body = f'<pre class="ctf-output">{out}</pre>'
        return render_page(
            title="Consola de Depuracion",
            heading="Consola Administrativa",
            subtitle="Salida de ejecucion remota.",
            badge="Debug Console",
            body_html=body,
            wide=True,
        )

    body = '<p class="ctf-muted">Uso esperado: ?cmd=whoami</p>'
    return render_page(
        title="Consola de Depuracion",
        heading="Consola Administrativa",
        subtitle="Interfaz de diagnostico por parametro GET.",
        badge="Debug Console",
        body_html=body,
    )


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
