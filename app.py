import os
import zlib
import zipfile
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import re

app = Flask(__name__)

# -------------------------------
# GÜÇLÜ UDF PARSER
# -------------------------------

def guclu_parser(data):

    try:

        # ZIP kontrolü
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for name in z.namelist():
                    if name.endswith(".xml"):
                        with z.open(name) as f:
                            return parse_xml_to_lines(f.read())
        except:
            pass

        # ZLIB tarama
        sigs = [b'\x78\x9c', b'\x78\xda', b'\x78\x01']

        for sig in sigs:

            pos = data.find(sig)

            while pos != -1:

                try:
                    decompressed = zlib.decompress(data[pos:])
                    if b"<" in decompressed:
                        return parse_xml_to_lines(decompressed)
                except:
                    pass

                pos = data.find(sig, pos + 1)

        return ["UDF içeriği bulunamadı"]

    except Exception as e:

        return [f"Hata: {str(e)}"]


def parse_xml_to_lines(xml_content):

    try:

        xml_str = xml_content.decode("utf-8", errors="ignore")

        root = ET.fromstring(xml_str)

        lines = []

        for elem in root.iter():

            if elem.text:

                t = elem.text.strip()

                if len(t) > 1:
                    lines.append(t)

        if not lines:

            clean = re.sub(r'<[^>]+>', ' ', xml_str)
            return [clean]

        return lines

    except:

        clean = re.sub(r'<[^>]+>', ' ', xml_content.decode("utf-8", errors="ignore"))

        return [clean]


# -------------------------------
# SENİN ARAYÜZÜN (DEĞİŞMEDİ)
# -------------------------------

HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>UDF Pro Elite v23.0 | Ofis Gökçadır</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 480px; border: 1px solid #334155; box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
        .security-badge { background: rgba(6, 78, 59, 0.4); color: #6ee7b7; padding: 18px; border-radius: 12px; font-size: 13px; margin-bottom: 25px; border: 1px solid #059669; text-align: left; line-height: 1.6; }
        .progress-container { display: none; margin: 20px 0; background: #334155; border-radius: 10px; height: 12px; overflow: hidden; }
        .progress-bar { width: 0%; height: 100%; background: linear-gradient(90deg, #38bdf8, #818cf8); transition: width 0.2s; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; opacity: 0.3; pointer-events: none; }
        button.active { opacity: 1; pointer-events: auto; }
        .pdf { background: #0ea5e9; grid-column: span 2; font-size: 16px; }
        .word { background: #2b579a; } .txt { background: #64748b; }
        button:hover { filter: brightness(1.2); transform: translateY(-2px); }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; border: 1px dashed #475569; padding: 15px; border-radius: 10px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="color:#38bdf8; margin:0 0 15px 0;">UDF PRO <span style="color:white">v23.0 ELITE</span></h2>
        <div class="security-badge">
            🔒 <b>Sayın kullanıcımız;</b> yüklediğiniz dosyalar hiçbir şekilde sunucularımızda depolanmaz. Anlık işlenir ve kalıcı olarak silinir.
        </div>
        <form id="uForm" method="POST" action="/" enctype="multipart/form-data">
            <input type="file" name="file" id="fIn" accept=".udf" required>
            <label style="margin: 20px 0; font-size: 12px; display: flex; align-items: center; justify-content: center; gap: 10px; cursor: pointer;">
                <input type="checkbox" id="kvkk" onchange="toggleBtns()"> KVKK Aydınlatma Metnini okudum ve onaylıyorum.
            </label>
            <div id="pCont" class="progress-container"><div id="pBar" class="progress-bar"></div></div>
            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" id="btnPdf" class="pdf" onclick="run()">PRO PDF OLARAK DÖNÜŞTÜR</button>
                <button type="submit" name="mod" value="word" id="btnWord" class="word" onclick="run()">PRO WORD (DOC)</button>
                <button type="submit" name="mod" value="txt" id="btnTxt" class="txt" onclick="run()">HIZLI TEXT (TXT)</button>
            </div>
        </form>
        <p style="font-size:10px; color:#475569; margin-top:30px">© 2026 FATİH MERT | BURSA</p>
    </div>
    <script>
        function toggleBtns() {
            const isChecked = document.getElementById('kvkk').checked;
            const btns = ['btnPdf', 'btnWord', 'btnTxt'];
            btns.forEach(id => { 
                const b = document.getElementById(id);
                b.style.opacity = isChecked ? "1" : "0.3"; 
                b.style.pointerEvents = isChecked ? "auto" : "none"; 
            });
        }
        function run() {
            document.getElementById('pCont').style.display = 'block';
            let w = 0; let b = document.getElementById('pBar');
            let i = setInterval(() => { w += (100 - w) * 0.12; b.style.width = w + '%'; if(w > 98) clearInterval(i); }, 100);
        }
    </script>
</body>
</html>
"""

# -------------------------------
# ANA ROUTE
# -------------------------------

@app.route("/", methods=["GET","POST"])
def index():

    if request.method == "GET":
        return render_template_string(HTML_UI)

    file = request.files.get("file")

    if not file:
        return "Dosya yüklenmedi"

    mod = request.form.get("mod")

    lines = guclu_parser(file.read())

    text = "\n".join(lines)

    if mod == "txt":

        return send_file(
            io.BytesIO(text.encode("utf-8")),
            as_attachment=True,
            download_name="belge.txt",
            mimetype="text/plain"
        )

    if mod == "word":

        return send_file(
            io.BytesIO(text.encode("utf-8")),
            as_attachment=True,
            download_name="belge.doc",
            mimetype="application/msword"
        )

    # PDF
    buf = io.BytesIO()

    c = canvas.Canvas(buf, pagesize=A4)

    y = 800

    for line in lines:

        c.drawString(50, y, line[:90])

        y -= 15

        if y < 50:

            c.showPage()

            y = 800

    c.save()

    buf.seek(0)

    return send_file(
        buf,
        as_attachment=True,
        download_name="belge.pdf",
        mimetype="application/pdf"
    )


# -------------------------------
# SERVER
# -------------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT",8080))

    app.run(host="0.0.0.0", port=port)
