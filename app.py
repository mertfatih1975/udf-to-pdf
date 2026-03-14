import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

app = Flask(__name__)

# --- ALTYAPI: FONT VE MOTOR ---
try:
    # arial.ttf dosyasının deponuzun ana dizininde olması gerekir
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

def extract_text(data):
    try:
        # UDF'nin içindeki sıkıştırılmış veriyi (zlib) açma altyapısı
        s = data.find(b"<content>") + 9
        e = data.find(b"</content>")
        if s < 9 or e == -1: return "UDF yapısı bozuk veya içerik bulunamadı."
        xml = zlib.decompress(data[s:e])
        root = ET.fromstring(xml)
        return "".join([c.text for c in root.iter('content') if c.text])
    except Exception as ex:
        return f"Dönüştürme hatası: {str(ex)}"

# --- WEB ARAYÜZÜ (Görselli ve KVKK'lı) ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>UDF Pro v3.5 | Ofis Gökçadır</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 40px; border-radius: 15px; text-align: center; width: 420px; box-shadow: 0 20px 40px rgba(0,0,0,0.4); border: 1px solid #334155; }
        .security-note { background: #064e3b; color: #6ee7b7; padding: 12px; border-radius: 8px; font-size: 13px; margin-bottom: 20px; border: 1px solid #059669; }
        .progress-container { width: 100%; background: #334155; border-radius: 10px; margin: 20px 0; display: none; }
        .progress-bar { width: 0%; height: 10px; background: #0ea5e9; border-radius: 10px; transition: width 0.3s; }
        button { border: none; padding: 14px; border-radius: 8px; cursor: pointer; font-weight: bold; margin: 5px; width: 46%; transition: 0.3s; }
        .pro { background: #0ea5e9; color: white; }
        .fast { background: #64748b; color: white; }
        .kvkk-link { margin-top: 25px; font-size: 12px; color: #94a3b8; cursor: pointer; text-decoration: underline; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="margin-top:0">UDF PRO <span style="color:#0ea5e9">GÜVENLİ</span></h2>
        <div class="security-note">
            🛡️ <b>Gizlilik Bildirimi:</b> Dosyalarınız saklanmaz, sadece bellek (RAM) üzerinde işlenir ve anında silinir.
        </div>
        <form id="uForm" method="post" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" accept=".udf" required style="margin-bottom:20px; color:#94a3b8">
            <div class="progress-container" id="pCont"><div class="progress-bar" id="pBar"></div></div>
            <div style="display:flex; justify-content: space-between;">
                <button type="submit" formaction="/convert/fast" class="fast">HIZLI (TXT)</button>
                <button type="submit" formaction="/convert/pro" class="pro">PRO (PDF)</button>
            </div>
        </form>
        <div class="kvkk-link">KVKK ve Veri Güvenliği</div>
        <p style="font-size:10px; color:#475569; margin-top:20px">FATİH MERT | BURSA 2026</p>
    </div>
    <script>
        document.getElementById('uForm').onsubmit = function() {
            document.getElementById('pCont').style.display = 'block';
            let width = 0;
            const interval = setInterval(() => {
                if (width >= 90) clearInterval(interval);
                width += 10;
                document.getElementById('pBar').style.width = width + '%';
            }, 150);
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return HTML_UI

@app.route('/convert/fast', methods=['POST'])
def fast():
    f = request.files['file']
    text = extract_text(f.read())
    buf = io.BytesIO(text.encode('utf-8'))
    return send_file(buf, as_attachment=True, download_name="ozet.txt")

@app.route('/convert/pro', methods=['POST'])
def pro():
    f = request.files['file']
    text = extract_text(f.read())
    buf = io.BytesIO()
    p = canvas.Canvas(buf)
    t = p.beginText(50, 800)
    t.setFont(FONT_NAME, 10)
    for line in text.split('\n'):
        t.textLine(line)
    p.drawText(t)
    p.showPage()
    p.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="belge.pdf")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
