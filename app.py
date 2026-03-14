import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
import io

app = Flask(__name__)

# --- ALTYAPI: FONT VE UDF MOTORU ---
try:
    # arial.ttf dosyasının deponun ana dizininde olması gerekir
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

def udf_motoru(content):
    try:
        s = content.find(b"<content>") + 9
        e = content.find(b"</content>")
        if s < 9 or e == -1: return ["Hata: UDF yapisi bozuk."]
        xml = zlib.decompress(content[s:e])
        root = ET.fromstring(xml)
        return [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
    except Exception as ex:
        return [f"Altyapi Hatasi: {str(ex)}"]

# --- ARAYÜZ ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>UDF Pro v4.0 | Bursa</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 400px; border: 1px solid #334155; }
        .badge { background: #064e3b; color: #6ee7b7; padding: 10px; border-radius: 8px; font-size: 12px; margin-bottom: 20px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; width: 45%; transition: 0.3s; }
        .pro { background: #0ea5e9; color: white; }
        .fast { background: #64748b; color: white; }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; }
    </style>
</head>
<body>
    <div class="box">
        <h2>UDF PRO GÜVENLİ</h2>
        <div class="badge">🛡️ Altyapi Aktif: Dosyalar RAM'de islenir.</div>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".udf" required>
            <div style="display:flex; justify-content: space-between;">
                <button type="submit" formaction="/convert/fast" class="fast">HIZLI (TXT)</button>
                <button type="submit" formaction="/convert/pro" class="pro">PRO (PDF)</button>
            </div>
        </form>
        <p style="font-size:10px; color:#475569; margin-top:20px">FATİH MERT | BURSA 2026</p>
    </div>
</body>
</html>
"""

# BURASI KRİTİK: Hem GET (Giriş) hem POST (Yükleme) izni verdik
@app.route('/', methods=['GET', 'POST'])
def index():
    return HTML_UI

@app.route('/convert/fast', methods=['POST'])
def fast():
    f = request.files['file']
    text = "\\n".join(udf_motoru(f.read()))
    buf = io.BytesIO(text.encode('utf-8'))
    return send_file(buf, as_attachment=True, download_name="belge.txt")

@app.route('/convert/pro', methods=['POST'])
def pro():
    f = request.files['file']
    lines = udf_motoru(f.read())
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    c.setFont(FONT_NAME, 10)
    for line in lines:
        if y < 50:
            c.showPage()
            c.setFont(FONT_NAME, 10)
            y = 800
        c.drawString(50, y, line[:100])
        y -= 15
    c.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="belge.pdf")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
