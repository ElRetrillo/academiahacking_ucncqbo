import os
from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def index():
    file = request.args.get('file', 'home.txt')
    try:
        # VULNERABLE
        content = open(file).read()
    except:
        content = 'File not found'
    return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>LFI Challenge</h1><p><a href="?file=home.txt" style="color:white;">Home</a></p><pre style="text-align:left; background:#0f3460; padding:20px; color:white;">{content}</pre></body></html>'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8005)