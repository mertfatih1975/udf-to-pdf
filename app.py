import os
import zlib
import zipfile
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string, make_response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import re

app = Flask(__name__)

# --- GÜÇLÜ UDF PARSER (v25.1) ---
def guclu_parser(data):
    try:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for name in z.namelist():
                    if name.endswith(".xml"):
                        with z.open(name) as f:
                            return parse_xml_to_lines(f.read())
        except: pass

        sigs = [b'\x78\x9c', b'\x78\xda', b'\x78\x01']
        for sig in sigs:
            pos = data.find(sig)
            while pos != -1:
                try:
                    decompressed = zlib.decompress(data[pos:])
                    if b"<" in decompressed:
                        return parse_xml_to_lines(decompressed)
                except: pass
                pos = data.find(sig, pos + 1)
        return ["UDF içeriği ayrıştırılamadı."]
    except Exception as e:
        return [f"Hata: {str(e)}"]

def parse_xml_to_lines(xml_content):
    try:
        xml_str = xml_content.decode("utf-8", errors="ignore")
        # Kontrol karakterlerini ve kutucukları temizle
        xml_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', xml_str)
        xml_str = xml_str.replace('\xa0', ' ')

        root = ET.fromstring(xml_str)
        lines = []
        for elem in root.iter():
            if elem.text:
                t = elem.text.strip()
                if len(t) > 0:
                    lines.append(" ".join(t.split()))
        return lines if lines else [re.sub(r'<[^>]+>', ' ', xml_str).strip()]
    except:
        return [re.sub(r'<[^>]+>', ' ', xml_content.decode("utf-8", errors="ignore")).strip()]

# --- ARAYÜZ ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>UDF Pro Elite v25.1</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 480px; border: 1px solid #334155; box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
        .security-badge { background: rgba(6, 78, 59, 0.4); color: #6ee7b7; padding: 18px; border-radius: 12px; font-size: 13px; margin-bottom: 25px; border: 1px solid #059669; text-align: left; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; opacity: 0.3; pointer-events: none; }
        button.active { opacity: 1; pointer-events: auto; }
        .pdf { background: #0ea5e9; grid-column: span 2; font-size: 16px; }
        .word { background: #2b579a; } .txt { background: #64748b; }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; border: 1px dashed #475569; padding: 15px; border-radius: 10px; }
        .version { position: fixed; bottom: 10px; right: 10px; font-size: 10px; color: #475569; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="color:#38bdf8; margin:0 0 15px 0;">UDF PRO <span style="color:white">ELITE</span></h2>
        <div class="security-badge">🔒 <b>Sayın kullanıcımız;</b> Dosyalarınız sunucuda saklanmaz, sadece anlık işlenir.</div>
        <form id="uForm" method="POST" action="/" enctype="multipart/form-data">
            <input type="file" name="file" id="fIn" accept=".udf" required>
            <label style="margin: 20px 0; font-size: 12px; display: block; cursor: pointer;">
                <input type="checkbox" id="kvkk" onchange="toggleBtns()"> KVKK Aydınlatma Metnini onaylıyorum.
            </label>
            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" id="btnPdf" class="pdf">PRO PDF OLARAK DÖNÜŞTÜR</button>
                <button type="submit" name="mod" value="word" id="btnWord" class="word">WORD (DOC)</button>
                <button type="submit" name="mod" value="txt" id="btnTxt" class="txt">TEXT (TXT)</button>
            </div>
        </form>
    </div>
    <div class="version">Sürüm: Elite v25.1 | Ofis Gökçadır</div>
    <script>
        function toggleBtns() {
            const isChecked = document.getElementById('kvkk').checked;
            ['btnPdf', 'btnWord', 'btnTxt'].forEach(id => {
                const b = document.getElementById(id);
                b.style.opacity = isChecked ? "1" : "0.3";
                b.style.pointerEvents = isChecked ? "auto" : "none";
            });
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "GET":
        response = make_response(render_template_string(HTML_UI))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    
    file = request.files.get("file")
    mod = request.form.get("mod")
    lines = guclu_parser(file.read())
    text = "\n".join(lines)

    if mod == "txt":
        return send_file(io.BytesIO(text.encode("utf-8")), as_attachment=True, download_name="belge.txt", mimetype="text/plain")
    if mod == "word":
        return send_file(io.BytesIO(text.encode("utf-8")), as_attachment=True, download_name="belge.doc", mimetype="application/msword")

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    c.setFont("Helvetica", 11)
    for line in lines:
        if y < 50: c.showPage(); c.setFont("Helvetica", 11); y = 800
        c.drawString(50, y, line[:95])
        y -= 18
    c.save(); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="belge.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
