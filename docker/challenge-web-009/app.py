from flask import Flask, request
app = Flask(__name__)

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
    return '''
# Backup file
def login():
    password = "EclipSec{b4ckup_f1l3s_4r3_l34ks}"
    # TODO: Implement database auth
'''

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)