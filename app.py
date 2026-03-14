import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

def udf_motoru(content):
    try:
        s = content.find(b"<content>") + 9
        e = content.find(b"</content>")
        if s < 9 or e == -1: return ["Hata: UDF içeriği bulunamadı."]
        xml = zlib.decompress(content[s:e])
        root = ET.fromstring(xml)
        return [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
    except:
        return ["Dönüştürme hatası oluştu."]

HTML_KODU = """
<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>UDF Pro v6.0</title></head>
<body style="font-family:sans-serif; background:#0f172a; color:white; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
    <div style="background:#1e293b; padding:40px; border-radius:20px; text-align:center; width:350px; border:1px solid #334155;">
        <h2>UDF PRO GÜVENLİ</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept=".udf" required style="margin-bottom:20px; color:#94a3b8; width:100%;">
            <button type="submit" style="width:100%; padding:15px; background:#0ea5e9; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">PDF OLARAK İNDİR</button>
        </form>
        <p style="font-size:10px; color:#475569; margin-top:20px">FATİH MERT | BURSA 2026</p>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template_string(HTML_KODU)
    
    if 'file' not in request.files: return "Dosya yok", 400
    file = request.files['file']
    lines = udf_motoru(file.read())
    
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800
    for line in lines:
        if y < 50: c.showPage(); y = 800
        c.drawString(50, y, line[:95])
        y -= 15
    c.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="belge.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
