from flask import Flask, request, make_response
app = Flask(__name__)

@app.route('/')
def index():
    role = request.cookies.get('role', 'guest')
    if role == 'admin':
        return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome Admin!</h1><p>EclipSec{c00k13_m0nst3r_m4n1pul4t10n}</p></body></html>'
    else:
        resp = make_response('<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome Guest!</h1><p>You are not an admin.</p></body></html>')
        resp.set_cookie('role', 'guest')
        return resp

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8003)