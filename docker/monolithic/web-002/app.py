from pathlib import Path
from flask import Flask

app = Flask(__name__)
FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route('/')
def index():
    return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome to SecureCorp</h1><p>Nothing to see here.</p></body></html>'


@app.route('/robots.txt')
def robots():
    return 'User-agent: *\nDisallow: /secret_flag_dir_991'


@app.route('/secret_flag_dir_991')
def flag():
    return read_flag()


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8002)
