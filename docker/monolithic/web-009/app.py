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
    return '''
    <html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;">
    <h1>Secure Login System</h1>
    <p>Everything is secure here. Definitely no backup files left on the server.</p>
    </body></html>
    '''


@app.route('/index.bak')
def bak():
    return f'''
# Backup file
def login():
    password = "{read_flag()}"
'''


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8009)
