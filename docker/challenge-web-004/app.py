import subprocess
from flask import Flask, request, render_template_string

app = Flask(__name__)

template = '''
<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;">
<h1>Network Diagnostic Tool</h1>
<form method="POST">
    <label>IP to ping:</label>
    <input type="text" name="ip" value="127.0.0.1">
    <button type="submit">Ping</button>
</form>
<pre style="text-align:left; background:#0f3460; padding:20px; color:white;">{{ output }}</pre>
</body></html>
'''


@app.route('/', methods=['GET', 'POST'])
def index():
    output = ''
    if request.method == 'POST':
        ip = request.form.get('ip', '')
        try:
            # Intentional command injection vulnerability for CTF training
            result = subprocess.run(
                f'ping -c 1 {ip}',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=10,
            )
            output = result.stdout
        except subprocess.TimeoutExpired:
            output = 'Command timed out'
    return render_template_string(template, output=output)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
