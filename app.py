import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

app = Flask(__name__)

# Altyapi: Arial fontu (arial.ttf deponuzda olmali)
try:
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

# --- UDF COZUCU MOTOR ---
def extract_text(data):
    try:
        s = data.find(b"<content>") + 9
        e = data.find(b"</content>")
        xml = zlib.decompress(data[s:e])
        root = ET.fromstring(xml)
        return "".join([c.text for c in root.iter('content') if c.text])
    except:
        return "Dosya okunamadi."

@app.route('/')
def home():
    # Buraya daha once hazirladigimiz HTML_UI gelecek
    return HTML_UI 

@app.route('/convert/pro', methods=['POST']) # Hata buradaydi, POST eklendi
def pro_convert():
    if 'file' not in request.files: return "Dosya yok", 400
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

@app.route('/convert/fast', methods=['POST'])
def fast_convert():
    f = request.files['file']
    text = extract_text(f.read())
    buf = io.BytesIO(text.encode('utf-8'))
    return send_file(buf, as_attachment=True, download_name="belge.txt")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
