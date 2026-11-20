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
    profiles = {
        "1": "Alice - Normal User",
        "2": "Bob - Normal User",
        "0": f"Admin - {read_flag()}",
    }
    uid = request.args.get('id', '1')
    profile = profiles.get(uid, "User not found")
    return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>User Profile</h1><p>{profile}</p><a href="?id=1" style="color:white;">View Alice</a> | <a href="?id=2" style="color:white;">View Bob</a></body></html>'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
