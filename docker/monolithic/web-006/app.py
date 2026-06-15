import sqlite3
from flask import Flask, request, render_template_string
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
    c.execute("INSERT INTO users VALUES ('admin', 'super_secret_password_123!')")
    conn.commit()
    conn.close()

template = '''
<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;">
<h1>Admin Login</h1>
<form method="POST">
    <input type="text" name="user" placeholder="Username"><br><br>
    <input type="password" name="pass" placeholder="Password"><br><br>
    <button type="submit">Login</button>
</form>
<p style="color:red">{{ error }}</p>
</body></html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    error = ''
    if request.method == 'POST':
        u = request.form.get('user', '')
        p = request.form.get('pass', '')
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        # VULNERABLE
        query = f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
        try:
            c.execute(query)
            if c.fetchone():
                return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome Admin!</h1><p>EclipSec{sql1_byp4ss_l0g1n}</p></body></html>'
            else:
                error = 'Invalid credentials'
        except Exception as e:
            error = str(e)
    return render_template_string(template, error=error)

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=8006)