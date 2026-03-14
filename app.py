import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
import io

app = Flask(__name__)

# --- ALTYAPI: FONT ---
try:
    # arial.ttf dosyasının deponun ana dizininde olması gerekir
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

def udf_motoru(content):
    try:
        s = content.find(b"<content>") + 9
        e = content.find(b"<content>".replace(b"<", b"</")) # </content> bulma
        e = content.find(b"</content>")
        if s < 9 or e == -1: return ["Hata: UDF içeriği bulunamadı."]
        xml = zlib.decompress(content[s:e])
        root = ET.fromstring(xml)
        return [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
    except Exception as ex:
        return [f"Dönüştürme Hatası: {str(ex)}"]

HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>UDF Pro v6.0 | Ofis Gökçadır</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 400px; border: 1px solid #334155; box-shadow: 0 20px 50px rgba(0,0,0,0.3); }
        .secure-badge { background: #064e3b; color: #6ee7b7; padding: 12px; border-radius: 8px; font-size: 12px; margin-bottom: 25px; border: 1px solid #059669; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; width: 100%; transition: 0.3s; background: #0ea5e9; color: white; font-size: 16px; }
        button:hover { background: #0284c7; }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="margin-top:0">UDF PRO <span style="color:#0ea5e9">GÜVENLİ</span></h2>
        <div class="secure-badge">🛡️ Altyapı Aktif: Veriler RAM'de işlenir.</div>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept=".udf" required>
            <button type="submit">PDF OLARAK DÖNÜŞTÜR</button>
        </form>
        <p style="font-size:10px; color:#475569; margin-top:20px">FATİH MERT | BURSA 2026</p>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def handle_everything():
    # Sayfaya girişte (GET) formu göster
    if request.method == 'GET':
        return render_template_string(HTML_UI)
    
    # Butona basıldığında (POST) dönüştür
    if 'file' not in request.files: 
        return "Dosya seçilmedi!", 400
        
    file = request.files['file']
    lines = udf_motoru(file.read())
    
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 50
    c.setFont(FONT_NAME, 10)
    
    for line in lines:
        if y < 50:
            c.showPage()
            c.setFont(FONT_NAME, 10)
            y = height - 50
        # Satır kısıtlaması (Taşmayı önlemek için)
        c.drawString(50, y, line[:95])
        y -= 15
        
    c.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="belge.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    # Railway'in istediği dinamik port ayarı
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
