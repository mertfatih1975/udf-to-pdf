import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

app = Flask(__name__)

# --- ALTYAPI: TURKCE FONT DESTEGI ---
# Onemli: arial.ttf dosyasini GitHub deponun ana dizinine yuklemeyi unutma!
try:
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF Islemci v3.5</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #0f172a; color: #f8fafc; }
        .container { background: #1e293b; padding: 40px; border-radius: 20px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); text-align: center; width: 450px; border: 1px solid #334155; }
        h2 { margin-bottom: 10px; color: #38bdf8; }
        .security-box { background: #064e3b; color: #6ee7b7; padding: 12px; border-radius: 8px; font-size: 13px; margin-bottom: 20px; border: 1px solid #059669; }
        input[type="file"] { margin-bottom: 25px; width: 100%; color: #94a3b8; }
        .button-group { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; transition: 0.3s; }
        .btn-fast { background: #64748b; color: white; }
        .btn-pro { background: #0ea5e9; color: white; }
        .footer { margin-top: 30px; font-size: 11px; color: #475569; }
    </style>
</head>
<body>
    <div class="container">
        <img src="https://i.ibb.co/9pDgT2B/trust.png" alt="Guvenli" style="width:60px; margin-bottom:10px;">
        <h2>UDF PRO GUVENLI</h2>
        <div class="security-box">
            🛡️ <b>Gizlilik:</b> Dosyalar saklanmaz, RAM uzerinde islenip aninda silinir.
        </div>
        <form id="udfForm" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".udf" required>
            <div class="button-group">
                <button type="submit" formaction="/convert/fast" class="btn-fast">HIZLI (TXT)</button>
                <button type="submit" formaction="/convert/pro" class="btn-pro">PRO (PDF)</button>
            </div>
        </form>
        <div class="footer">FATIH MERT | Bursa Ofis Gokcadir</div>
    </div>
</body>
</html>
"""

def extract_udf_text(udf_content):
    try:
        start_tag, end_tag = b"<content>", b"</content>"
        start_idx = udf_content.find(start_tag) + len(start_tag)
        end_idx = udf_content.find(end_tag)
        if start_idx < 9 or end_idx == -1: return "UDF icerigi bulunamadi."
        xml_data = zlib.decompress(udf_content[start_idx:end_idx])
        root = ET.fromstring(xml_data)
        return "".join([c.text for c in root.iter('content') if c.text])
    except Exception as e:
        return f"Hata: {str(e)}"

@app.route('/')
def index():
    return HTML_INTERFACE

@app.route('/convert/fast', methods=['POST'])
def fast_convert():
    if 'file' not in request.files: return "Dosya yok", 400
    file = request.files['file']
    text = extract_udf_text(file.read())
    buffer = io.BytesIO(text.encode('utf-8'))
    return send_file(buffer, as_attachment=True, download_name="belge.txt", mimetype='text/plain')

@app.route('/convert/pro', methods=['POST'])
def pro_convert():
    if 'file' not in request.files: return "Dosya yok", 400
    file = request.files['file']
    text = extract_udf_text(file.read())
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    t = p.beginText(50, 800)
    t.setFont(FONT_NAME, 10)
    # Metni satirlara bol ve PDF'e isle
    for line in text.split('\n'):
        t.textLine(line)
    p.drawText(t)
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="profesyonel.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    # Railway icin port ayari onemli
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
