import os
from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def index():
    cmd = request.args.get('cmd')
    if cmd:
        # VULNERABLE
        out = os.popen(cmd).read()
        return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><pre style="text-align:left; background:#0f3460; padding:20px; color:white;">{out}</pre></body></html>'
    return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Admin Debug Console</h1><p>Usage: ?cmd=whoami</p></body></html>'

if __name__ == '__main__':
    with open('/flag.txt', 'w') as f: f.write('EclipSec{c0mm4nd_3x3cut10n_v1a_g3t}')
    app.run(host='127.0.0.1', port=8000)