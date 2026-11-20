import html
import subprocess
from flask import Flask, request

app = Flask(__name__)


@app.route('/')
def index():
    cmd = request.args.get('cmd')
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
            out = 'Command timed out'
        return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><pre style="text-align:left; background:#0f3460; padding:20px; color:white;">{out}</pre></body></html>'
    return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Admin Debug Console</h1><p>Usage: ?cmd=whoami</p></body></html>'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
