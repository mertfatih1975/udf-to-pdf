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

# --- ALTYAPI: FONT DESTEĞİ ---
try:
    # arial.ttf ana dizinde olmalı, yoksa hata vermez Helvetica ile devam eder
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

def udf_motoru(content):
    try:
        # UDF dosyasının kalbine iniyoruz
        s = content.find(b"<content>") + 9
        e = content.find(b"</content>")
        if s < 9 or e == -1: return ["Hata: UDF içeriği bulunamadı."]
        
        xml_data = zlib.decompress(content[s:e])
        root = ET.fromstring(xml_data)
        
        # XML düğümlerini hiyerarşik olarak temizle ve listele
        return [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
    except Exception as ex:
        return [f"Dönüştürme Hatası: {str(ex)}"]

HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF Pro v4.5 | Güvenli Dönüştürücü</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 420px; border: 1px solid #334155; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
        .secure-badge { background: #064e3b; color: #6ee7b7; padding: 12px; border-radius: 10px; font-size: 13px; margin-bottom: 25px; border: 1px solid #059669; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; width: 45%; transition: 0.3s; color: white; }
        .pro { background: #0ea5e9; }
        .fast { background: #64748b; }
        button:hover { filter: brightness(1.2); }
        input[type="file"] { margin-bottom: 25px; color: #94a3b8; width: 100%; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="margin-top:0">UDF PRO <span style="color:#0ea5e9">GÜVENLİ</span></h2>
        <div class="secure-badge">🛡️ UYAP Altyapısı Aktif. Veriler RAM'de işlenir.</div>
        <form method="POST" enctype="multipart/form-data" action="">
            <input type="file" name="file" accept=".udf" required>
            <div style="display:flex; justify-content:space-between">
                <button type="submit" formaction="/convert/fast" class="fast">HIZLI (TXT)</button>
                <button type="submit" formaction="/convert/pro" class="pro">PRO (PDF)</button>
            </div>
        </form>
        <p style="font-size:10px; color:#475569; margin-top:25px">FATİH MERT | BURSA 2026</p>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    return HTML_UI

@app.route('/convert/fast', methods=['POST'])
def fast():
    if 'file' not in request.files: return "Dosya seçilmedi", 400
    f = request.files['file']
    lines = udf_motoru(f.read())
    text = "\n".join(lines)
    buf = io.BytesIO(text.encode('utf-8'))
    return send_file(buf, as_attachment=True, download_name="belge.txt", mimetype='text/plain')

@app.route('/convert/pro', methods=['POST'])
def pro():
    if 'file' not in request.files: return "Dosya seçilmedi", 400
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
        # Metni otomatik sığdırma (Simple wrap)
        text_line = line if len(line) < 95 else line[:92] + "..."
        c.drawString(50, y, text_line)
        y -= 15
        
    c.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="profesyonel.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    # Railway ve Gunicorn için dinamik port
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
