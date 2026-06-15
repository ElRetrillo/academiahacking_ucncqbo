from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def index():
    ua = request.headers.get('User-Agent', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if 'SecureBrowser1.0' not in ua:
        return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Access Denied</h1><p>Only SecureBrowser1.0 is allowed.</p></body></html>'
    
    if ip != '127.0.0.1':
        return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Access Denied</h1><p>Only local connections (127.0.0.1) are allowed.</p></body></html>'
        
    return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Access Granted!</h1><p>EclipSec{h34d3rs_c4n_b3_sp00f3d}</p></body></html>'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)