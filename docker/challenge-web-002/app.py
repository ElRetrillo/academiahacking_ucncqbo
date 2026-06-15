import os
from flask import Flask, request, make_response
app = Flask(__name__)

@app.route('/')
def index():
    return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome to SecureCorp</h1><p>Nothing to see here.</p></body></html>'

@app.route('/robots.txt')
def robots():
    return 'User-agent: *\nDisallow: /secret_flag_dir_991'

@app.route('/secret_flag_dir_991')
def flag():
    return 'EclipSec{r0b0ts_4r3_y0ur_fr13nd5}'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)