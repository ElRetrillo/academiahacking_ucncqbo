from pathlib import Path
from flask import Flask, request

app = Flask(__name__)
FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route('/')
def index():
    ua = request.headers.get('User-Agent', '')
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    client_ip = forwarded_for.split(',')[0].strip() if forwarded_for else (request.remote_addr or '')

    if 'SecureBrowser1.0' not in ua:
        return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Access Denied</h1><p>Only SecureBrowser1.0 is allowed.</p></body></html>'

    if client_ip != '127.0.0.1':
        return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Access Denied</h1><p>Only local connections (127.0.0.1) are allowed.</p></body></html>'

    return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Access Granted!</h1><p>{read_flag()}</p></body></html>'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
