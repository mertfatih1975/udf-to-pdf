import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

# En temel UDF okuma altyapısı
def udf_oku(data):
    try:
        s = data.find(b"<content>") + 9
        e = data.find(b"</content>")
        xml = zlib.decompress(data[s:e])
        root = ET.fromstring(xml)
        return [c.text.strip() for c in root.iter() if c.text and c.text.strip()]
    except: return ["Dosya okunamadi."]

HTML = """
<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>UDF Islemci</title></head>
<body style="font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding-top:100px;">
    <h2>UDF PRO GUVENLI</h2>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" accept=".udf" required><br><br>
        <button type="submit" name="t" value="pdf" style="padding:10px 20px; background:#0ea5e9; color:white; border:none; border-radius:5px; cursor:pointer;">PDF'E CEVIR</button>
    </form>
    <p style="font-size:10px; color:#475569; margin-top:50px">FATIH MERT | BURSA 2026</p>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template_string(HTML)
    
    file = request.files['file']
    lines = udf_oku(file.read())
    
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800
    for line in lines:
        c.drawString(50, y, line[:90])
        y -= 15
        if y < 50: c.showPage(); y = 800
    c.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="belge.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
