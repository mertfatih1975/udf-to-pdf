import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

app = Flask(__name__)

# Font kaydı (arial.ttf deponuzda yüklü olmalı)
try:
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica' # Font yüklenemezse geri dönüş

HTML_UI = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>UDF Islemci v3.0</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 40px; border-radius: 15px; text-align: center; width: 400px; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
        .progress-container { width: 100%; background: #334155; border-radius: 10px; margin: 20px 0; display: none; }
        .progress-bar { width: 0%; height: 10px; background: #0ea5e9; border-radius: 10px; transition: width 0.3s; }
        button { border: none; padding: 12px; border-radius: 8px; cursor: pointer; font-weight: bold; margin: 5px; width: 45%; transition: 0.3s; }
        .pro { background: #0ea5e9; color: white; }
        .fast { background: #64748b; color: white; }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; }
    </style>
</head>
<body>
    <div class="box">
        <h2>UDF PRO <span style="font-size:12px; color:#0ea5e9">TURKCE</span></h2>
        <form id="uForm" method="post" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" accept=".udf" required>
            <div class="progress-container" id="pCont"><div class="progress-bar" id="pBar"></div></div>
            <div style="display:flex; justify-content: space-between;">
                <button type="submit" onclick="startProcess('/convert/fast')" class="fast">HIZLI (TXT)</button>
                <button type="submit" onclick="startProcess('/convert/pro')" class="pro">PRO (PDF)</button>
            </div>
        </form>
    </div>

    <script>
        function startProcess(path) {
            const file = document.getElementById('fileInput').files[0];
            if(!file) return;
            
            document.getElementById('uForm').action = path;
            document.getElementById('pCont').style.display = 'block';
            let width = 0;
            const interval = setInterval(() => {
                if (width >= 90) clearInterval(interval);
                width += 10;
                document.getElementById('pBar').style.width = width + '%';
            }, 200);
        }
    </script>
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
    except: return "Dosya okunamadi."

@app.route('/')
def home(): return HTML_UI

@app.route('/convert/fast', methods=['POST'])
def fast():
    f = request.files['file']
    t = get_text(f.read())
    buf = io.BytesIO(t.encode('utf-8'))
    return send_file(buf, as_attachment=True, download_name="belge.txt")

@app.route('/convert/pro', methods=['POST'])
def pro():
    f = request.files['file']
    t = get_text(f.read())
    buf = io.BytesIO()
    p = canvas.Canvas(buf)
    obj = p.beginText(50, 800)
    obj.setFont(FONT_NAME, 10)
    for line in t.split('\n'):
        obj.textLine(line)
    p.drawText(obj)
    p.showPage()
    p.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="profesyonel.pdf")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
