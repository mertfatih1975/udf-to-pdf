import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF Islemci v2.0</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #0f172a; color: #f8fafc; }
        .container { background: #1e293b; padding: 40px; border-radius: 20px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); text-align: center; width: 450px; border: 1px solid #334155; }
        h2 { margin-bottom: 10px; font-weight: 600; color: #38bdf8; }
        p { color: #94a3b8; font-size: 14px; margin-bottom: 30px; }
        input[type="file"] { margin-bottom: 25px; width: 100%; font-size: 14px; color: #94a3b8; }
        .button-group { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; transition: 0.3s; font-size: 14px; }
        .btn-fast { background: #64748b; color: white; }
        .btn-fast:hover { background: #475569; }
        .btn-pro { background: #0ea5e9; color: white; }
        .btn-pro:hover { background: #0284c7; box-shadow: 0 0 15px rgba(14, 165, 233, 0.4); }
        .footer { margin-top: 30px; font-size: 11px; color: #475569; border-top: 1px solid #334155; padding-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>UDF Islemci</h2>
        <p>Lutfen donusturmek istediginiz UDF dosyasini secin</p>
        <form id="udfForm" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".udf" required>
            <div class="button-group">
                <button type="submit" onclick="setEndpoint('/convert/fast')" class="btn-fast">HIZLI (TXT)</button>
                <button type="submit" onclick="setEndpoint('/convert/pro')" class="btn-pro">PRO (PDF)</button>
            </div>
        </form>
        <div class="footer">FATIH MERT | Ofis Gokcadir Is Merkezi</div>
    </div>
    <script>
        function setEndpoint(path) {
            document.getElementById('udfForm').action = path;
        }
    </script>
</body>
</html>
"""

def extract_udf_text(udf_content):
    try:
        start_tag, end_tag = b"<content>", b"</content>"
        start_idx = udf_content.find(start_tag) + len(start_tag)
        end_idx = udf_content.find(end_tag)
        xml_data = zlib.decompress(udf_content[start_idx:end_idx])
        root = ET.fromstring(xml_data)
        return "".join([c.text for c in root.iter('content') if c.text])
    except:
        return "Dosya okunurken hata olustu."

@app.route('/')
def index():
    return HTML_INTERFACE

@app.route('/convert/fast', methods=['POST'])
def fast_convert():
    file = request.files['file']
    text = extract_udf_text(file.read())
    buffer = io.BytesIO(text.encode('utf-8'))
    return send_file(buffer, as_attachment=True, download_name="ozet.txt", mimetype='text/plain')

@app.route('/convert/pro', methods=['POST'])
def pro_convert():
    file = request.files['file']
    text = extract_udf_text(file.read())
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    t = p.beginText(50, 800)
    t.setFont("Helvetica", 10)
    for line in text.split('\n'):
        t.textLine(line)
    p.drawText(t)
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="profesyonel.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
