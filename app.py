import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

app = Flask(__name__)

# --- GERÇEK ALTYAPI: UDF ÇÖZÜCÜ MOTOR ---
def extract_udf_text(udf_content):
    try:
        # UDF dosyasının içindeki sıkıştırılmış XML verisini bul
        start_tag, end_tag = b"<content>", b"</content>"
        start_idx = udf_content.find(start_tag) + len(start_tag)
        end_idx = udf_content.find(end_tag)
        
        if start_idx < 9 or end_idx == -1:
            return "UDF içeriği bulunamadı veya dosya bozuk."
        
        # Zlib ile sıkıştırmayı aç
        xml_data = zlib.decompress(udf_content[start_idx:end_idx])
        root = ET.fromstring(xml_data)
        
        # XML içindeki saf metni birleştir
        return "".join([c.text for c in root.iter('content') if c.text])
    except Exception as e:
        return f"Dönüştürme hatası: {str(e)}"

# --- WEB ARAYÜZÜ ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>UDF Pro v3.5 | Ofis Gökçadır</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 450px; box-shadow: 0 20px 40px rgba(0,0,0,0.5); border: 1px solid #334155; }
        .security-note { background: #064e3b; color: #6ee7b7; padding: 12px; border-radius: 8px; font-size: 13px; margin-bottom: 20px; border: 1px solid #059669; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; margin: 5px; width: 45%; transition: 0.3s; }
        .pro { background: #0ea5e9; color: white; }
        .fast { background: #64748b; color: white; }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; }
    </style>
</head>
<body>
    <div class="box">
        <img src="https://i.ibb.co/9pDgT2B/trust.png" alt="Güvenli" style="width:60px; margin-bottom:15px;">
        <h2>UDF PRO <span style="color:#0ea5e9">GÜVENLİ</span></h2>
        <div class="security-note">🛡️ Verileriniz RAM'de işlenir ve anında silinir.</div>
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

@app.route('/')
def index(): return HTML_UI

@app.route('/convert/fast', methods=['POST'])
def fast():
    f = request.files['file']
    text = extract_udf_text(f.read())
    buf = io.BytesIO(text.encode('utf-8'))
    return send_file(buf, as_attachment=True, download_name="belge.txt")

@app.route('/convert/pro', methods=['POST'])
def pro():
    f = request.files['file']
    text = extract_udf_text(f.read())
    buf = io.BytesIO()
    p = canvas.Canvas(buf)
    t = p.beginText(50, 800)
    t.setFont("Helvetica", 10) # arial.ttf yüklüyse Arial yazabilirsin
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
