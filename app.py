from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
