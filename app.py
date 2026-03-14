import os
import zlib
import zipfile
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string, Response, redirect, make_response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import re
from datetime import datetime
import pytz

app = Flask(__name__)

# --- SEO SAYFALARI ---
SEO_PAGES = ["udf-to-pdf", "udf-to-word", "udf-to-txt", "uyap-udf-converter", "udf-dosyasi-acma", "udf-viewer"]

# --- HTTPS YÖNLENDİRMESİ ---
@app.before_request
def before_request():
    if request.headers.get('X-Forwarded-Proto') == 'http':
        return redirect(request.url.replace('http://', 'https://', 1), code=301)

# --- UDF PARSER ---
def guclu_parser(data):
    try:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for name in z.namelist():
                    if name.lower().endswith(".xml"):
                        with z.open(name) as f: return parse_xml_to_lines(f.read())
        except: pass
        sigs = [b'\x78\x9c', b'\x78\xda', b'\x78\x01']
        for sig in sigs:
            pos = data.find(sig)
            while pos != -1:
                try:
                    decompressed = zlib.decompress(data[pos:])
                    if b"<" in decompressed: return parse_xml_to_lines(decompressed)
                except: pass
                pos = data.find(sig, pos + 1)
        return ["HATA: İçerik ayrıştırılamadı."]
    except Exception as e: return [f"Hata: {str(e)}"]

def parse_xml_to_lines(xml_content):
    try:
        xml_str = xml_content.decode("utf-8", errors="ignore")
        xml_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', xml_str)
        xml_str = xml_str.replace('\xa0', ' ')
        root = ET.fromstring(xml_str)
        lines = [" ".join(elem.text.split()) for elem in root.iter() if elem.text and len(elem.text.strip()) > 1]
        return lines if lines else [re.sub(r'<[^>]+>', ' ', xml_str).strip()]
    except: return [re.sub(r'<[^>]+>', ' ', xml_content.decode("utf-8", errors="ignore")).strip()]

# --- UI TASARIMI ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <title>{{ seo_title or 'UDFTOPDF | Ücretsiz UYAP UDF Dönüştürücü' }}</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 480px; border: 1px solid #334155; box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
        .security-badge { background: rgba(6, 78, 59, 0.4); color: #6ee7b7; padding: 18px; border-radius: 12px; font-size: 13px; margin-bottom: 25px; border: 1px solid #059669; text-align: left; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; opacity: 0.3; pointer-events: none; }
        button.active { opacity: 1; pointer-events: auto; }
        .pdf { background: #0ea5e9; grid-column: span 2; font-size: 16px; }
        .word { background: #2b579a; } .txt { background: #64748b; }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; border: 1px dashed #475569; padding: 15px; border-radius: 10px; }
        .footer { margin-top: 30px; text-align: center; color: #64748b; font-size: 11px; line-height: 1.8; }
        .time-info { color: #38bdf8; font-weight: bold; margin-bottom: 10px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="box">
        <h1 style="color:#38bdf8; font-size: 32px; letter-spacing: 2px; margin-bottom: 10px;">UDFTOPDF</h1>
        <div class="time-info">🕒 {{ current_time }}</div>
        <div class="security-badge">🔒 <b>Sayın kullanıcımız;</b> Dosyalarınız sunucuda saklanmaz, anlık işlenir ve kalıcı olarak silinir.</div>
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
    <div class="footer">
        🛡️ 256-Bit SSL Sertifikası ile Korunmaktadır <br>
        © {{ current_year }} UDFTOPDF | İstanbul - Türkiye <br>
        Tüm Hakları Saklıdır.
    </div>
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
    tz = pytz.timezone('Europe/Istanbul')
    now = datetime.now(tz)
    time_str = now.strftime("%d.%m.%Y - %H:%M")
    year_str = now.year

    if request.method == "GET":
        resp = make_response(render_template_string(HTML_UI, current_time=time_str, current_year=year_str))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return resp
    
    f = request.files.get("file")
    mod = request.form.get("mod")
    lines = guclu_parser(f.read())
    text = "\n".join(lines)
    
    if mod == "txt": return send_file(io.BytesIO(text.encode("utf-8")), as_attachment=True, download_name="belge.txt", mimetype="text/plain")
    if mod == "word": return send_file(io.BytesIO(text.encode("utf-8")), as_attachment=True, download_name="belge.doc", mimetype="application/msword")
    
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    c.setFont("Helvetica", 11)
    for line in lines:
        if y < 50: c.showPage(); c.setFont("Helvetica", 11); y = 800
        c.drawString(50, y, line[:95]); y -= 18
    c.save(); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="belge.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
