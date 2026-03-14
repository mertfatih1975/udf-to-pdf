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
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

def udf_motoru(content):
    try:
        s = content.find(b"<content>") + 9
        e = content.find(b"</content>")
        if s < 9 or e == -1: return ["Hata: UDF icerigi bulunamadi."]
        xml = zlib.decompress(content[s:e])
        root = ET.fromstring(xml)
        return [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
    except:
        return ["Donusturme sirasinda teknik bir hata olustu."]

HTML_KODU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>UDF Pro v6.0 | Kesin Cozum</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 400px; border: 1px solid #334155; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; width: 45%; color: white; margin-top: 10px; }
        .pro { background: #0ea5e9; }
        .fast { background: #64748b; }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; }
    </style>
</head>
<body>
    <div class="box">
        <h2>UDF PRO GUVENLI</h2>
        <p style="font-size:12px; color:#6ee7b7">🛡️ Altyapi: RAM-Only Processing</p>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept=".udf" required>
            <div style="display:flex; justify-content: space-between;">
                <button type="submit" name="islem" value="txt" class="fast">HIZLI (TXT)</button>
                <button type="submit" name="islem" value="pdf" class="pro">PRO (PDF)</button>
            </div>
        </form>
        <p style="font-size:10px; color:#475569; margin-top:20px">FATIH MERT | 2026</p>
    </div>
</body>
</html>
"""

# BUTUN KAPIYI HERKESE ACTIK
@app.route('/', methods=['GET', 'POST', 'PUT'])
def home():
    if request.method == 'GET':
        return render_template_string(HTML_KODU)
    
    if 'file' not in request.files:
        return "Dosya secilmedi", 400
    
    file = request.files['file']
    mod = request.form.get('islem')
    lines = udf_motoru(file.read())
    
    if mod == 'txt':
        text = "\\n".join(lines)
        buf = io.BytesIO(text.encode('utf-8'))
        return send_file(buf, as_attachment=True, download_name="belge.txt", mimetype='text/plain')
    else:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        y = 800
        c.setFont(FONT_NAME, 10)
        for line in lines:
            if y < 50:
                c.showPage()
                c.setFont(FONT_NAME, 10)
                y = 800
            c.drawString(50, y, line[:95])
            y -= 15
        c.save()
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name="belge.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
