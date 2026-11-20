from pathlib import Path
from flask import Flask, request, make_response

app = Flask(__name__)
FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route('/')
def index():
    role = request.cookies.get('role', 'guest')
    if role == 'admin':
        return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome Admin!</h1><p>{read_flag()}</p></body></html>'
    resp = make_response('<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome Guest!</h1><p>You are not an admin.</p></body></html>')
    resp.set_cookie('role', 'guest')
    return resp


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
