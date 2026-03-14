import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

HTML_UI = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>UDF Islemci</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 40px; border-radius: 15px; text-align: center; width: 350px; }
        button { border: none; padding: 12px; border-radius: 8px; cursor: pointer; font-weight: bold; margin: 5px; width: 100%; }
        .pro { background: #0ea5e9; color: white; }
        .fast { background: #64748b; color: white; }
    </style>
</head>
<body>
    <div class="box">
        <h2>UDF Islemci</h2>
        <form id="uForm" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".udf" required style="margin-bottom:20px">
            <button type="submit" formaction="/convert/fast" class="fast">HIZLI (TXT)</button>
            <button type="submit" formaction="/convert/pro" class="pro">PRO (PDF)</button>
        </form>
        <p style="font-size:10px; color:#475569; margin-top:20px">Fatih Mert | Bursa</p>
    </div>
</body>
</html>
"""

def get_text(data):
    try:
        s = data.find(b"<content>") + 9
        e = data.find(b"</content>")
        xml = zlib.decompress(data[s:e])
        root = ET.fromstring(xml)
        return "".join([c.text for c in root.iter('content') if c.text])
    except:
        return "Hata: Dosya okunamadi."

@app.route('/')
def home():
    return HTML_UI

@app.route('/convert/fast', methods=['POST'])
def fast():
    f = request.files['file']
    t = get_text(f.read())
    buf = io.BytesIO(t.encode('utf-8'))
    return send_file(buf, as_attachment=True, download_name="ozet.txt")

@app.route('/convert/pro', methods=['POST'])
def pro():
    f = request.files['file']
    t = get_text(f.read())
    buf = io.BytesIO()
    p = canvas.Canvas(buf)
    obj = p.beginText(50, 800)
    obj.setFont("Helvetica", 10)
    for line in t.split('\\n'):
        obj.textLine(line)
    p.drawText(obj)
    p.showPage()
    p.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="belge.pdf")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
