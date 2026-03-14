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

# --- PROFESYONEL ALTYAPI: FONT VE PARAGRAF MOTORU ---
try:
    # Onemli: arial.ttf dosyasini GitHub'a yuklemis olmalisin
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

def udf_isleyici(udf_content):
    try:
        # UDF icindeki zlib sıkıştırılmış bloğu bul
        s = udf_content.find(b"<content>") + 9
        e = udf_content.find(b"</content>")
        if s < 9 or e == -1: return ["Hata: UDF icerigi bulunamadi."]
        
        xml_data = zlib.decompress(udf_content[s:e])
        root = ET.fromstring(xml_data)
        
        # Altyapi farki: Metni hiyerarsik ve temiz bir sekilde topla
        lines = []
        for elem in root.iter():
            if elem.text and elem.text.strip():
                clean_line = elem.text.replace('\r', '').strip()
                lines.append(clean_line)
        return lines
    except Exception as ex:
        return [f"Altyapi Hatasi: {str(ex)}"]

# --- MODERN ARAYUZ ---
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>UDF Pro v4.0 | Ofis Gokcadir</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 420px; border: 1px solid #334155; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
        .secure-badge { background: #064e3b; color: #6ee7b7; padding: 12px; border-radius: 10px; font-size: 13px; margin-bottom: 25px; border: 1px solid #059669; }
        .btn-group { display: flex; justify-content: space-between; gap: 10px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; flex: 1; transition: 0.3s; }
        .btn-pro { background: #0ea5e9; color: white; }
        .btn-fast { background: #64748b; color: white; }
        input[type="file"] { margin-bottom: 25px; color: #94a3b8; width: 100%; }
    </style>
</head>
<body>
    <div class="box">
        <img src="https://i.ibb.co/9pDgT2B/trust.png" alt="Guvenli" style="width:60px; margin-bottom:15px;">
        <h2>UDF PRO <span style="color:#0ea5e9">PREMIUM</span></h2>
        <div class="secure-badge">🛡️ UYAP Veri Isleme Altyapisi Aktif. Dosyalariniz RAM'de islenir.</div>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".udf" required>
            <div class="btn-group">
                <button type="submit" formaction="/convert/fast" class="btn-fast">HIZLI (TXT)</button>
                <button type="submit" formaction="/convert/pro" class="btn-pro">PRO (PDF)</button>
            </div>
        </form>
        <p style="font-size:10px; color:#475569; margin-top:25px">FATIH MERT | BURSA 2026</p>
    </div>
</body>
</html>
"""

@app.route('/')
def index(): return HTML_INTERFACE

@app.route('/convert/fast', methods=['POST'])
def fast():
    f = request.files['file']
    lines = udf_isleyici(f.read())
    text = "\\n".join(lines)
    buf = io.BytesIO(text.encode('utf-8'))
    return send_file(buf, as_attachment=True, download_name="belge.txt")

@app.route('/convert/pro', methods=['POST'])
def pro():
    f = request.files['file']
    lines = udf_isleyici(f.read())
    
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    
    # PDF Yazma Altyapisi: Sayfa kenarlarini ayarla
    y = height - 50
    c.setFont(FONT_NAME, 10)
    
    for line in lines:
        if y < 50: # Sayfa biterse yeni sayfaya gec
            c.showPage()
            c.setFont(FONT_NAME, 10)
            y = height - 50
        
        # Uzun satirlari PDF icinde tutma (Basit Wrap)
        c.drawString(50, y, line[:100]) 
        y -= 15
        
    c.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="profesyonel.pdf")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
