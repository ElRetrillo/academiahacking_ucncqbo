from flask import Flask, request, render_template_string
app = Flask(__name__)

@app.route('/')
def index():
    name = request.args.get('name', 'Guest')
    # VULNERABLE
    template = f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome {name}!</h1><p>Try to find the flag in the environment variables or files.</p></body></html>'
    return render_template_string(template)

if __name__ == '__main__':
    import os
    os.environ['FLAG'] = 'EclipSec{sst1_t3mpl4t3_1nj3ct10n}'
    app.run(host='127.0.0.1', port=8000)