import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string, Response, jsonify
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import base64

app = Flask(__name__)

# --- SEO PAGES ---
SEO_PAGES = ["udf-to-pdf", "udf-to-word", "udf-to-txt", "uyap-udf-converter", "udf-dosyasi-acma", "udf-preview", "udf-viewer-online"]

# --- GÜÇLÜ UDF PARSER (HER VERSİYONA UYUMLU) ---
def guclu_udf_parser(data):
    try:
        # Önce standart content tagı ara
        start_tag, end_tag = b"<content>", b"</content>"
        s, e = data.find(start_tag), data.find(end_tag)
        
        if s != -1 and e != -1:
            raw_xml = zlib.decompress(data[s+9:e])
        else:
            # Tag yoksa dosyanın içindeki zlib bloğunu otomatik ayıkla
            # UDF dosyaları genelde PK veya belirli header ile başlar, metin zlib ile sıkıştırılmıştır
            try:
                # Ham veri içindeki zlib başlangıcını (78 9C veya 78 DA) bulmaya çalış
                raw_xml = zlib.decompress(data[data.find(b'\x78\x9c'):])
            except:
                return ["Hata: UDF yapısı çözülemedi."]

        root = ET.fromstring(raw_xml)
        lines = [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
        return lines if lines else ["Belge metni boş."]
    except Exception as ex:
        return [f"Parser Hatası: {str(ex)}"]

# --- GÖRSEL ARAYÜZ ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF Pro v14.0 | Ultra Parser & Preview</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 500px; border: 1px solid #334155; box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
        .badge { background: #064e3b; color: #6ee7b7; padding: 12px; border-radius: 10px; font-size: 13px; margin-bottom: 20px; border: 1px solid #059669; }
        .preview-area { display: none; background: #0f172a; border: 1px solid #334155; padding: 15px; border-radius: 10px; margin: 20px 0; max-height: 150px; overflow-y: auto; text-align: left; font-size: 12px; color: #94a3b8; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        button { border: none; padding: 12px; border-radius: 8px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; }
        .pdf { background: #0ea5e9; grid-column: span 2; padding: 18px; font-size: 16px; }
        .word { background: #2b579a; } .txt { background: #64748b; }
        .bar-container { display: none; margin: 15px 0; background: #334155; border-radius: 5px; height: 8px; overflow: hidden; }
        .bar { width: 0%; height: 100%; background: #38bdf8; transition: width 0.3s; }
        input[type="file"] { margin-bottom: 15px; color: #94a3b8; width: 100%; border: 1px dashed #475569; padding: 10px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="color:#38bdf8; margin:0 0 10px 0;">UDF PRO <span style="color:white">ULTRA</span></h2>
        <div class="badge">🛡️ <b>GÜÇLÜ PARSER:</b> Her türlü UDF versiyonunu açar.</div>
        
        <form id="uForm" method="POST" action="/" enctype="multipart/form-data">
            <input type="file" name="file" id="fIn" accept=".udf" required onchange="showPreview()">
            
            <div id="pView" class="preview-area"><b>Önizleme:</b><br><span id="pText"></span></div>
            
            <div id="pBox" class="bar-container"><div id="pBar" class="bar"></div></div>

            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" class="pdf" onclick="go()">PRO PDF OLARAK İNDİR</button>
                <button type="submit" name="mod" value="word" class="word" onclick="go()">WORD (DOC)</button>
                <button type="submit" name="mod" value="txt" class="txt" onclick="go()">TEXT (TXT)</button>
            </div>
        </form>
        <p style="font-size:10px; color:#475569; margin-top:20px">© 2026 FATİH MERT | BURSA | KVKK UYUMLU</p>
    </div>

    <script>
        function showPreview() {
            const file = document.getElementById('fIn').files[0];
            if (!file) return;
            // Önizleme için ilk birkaç satırı okuyan logic buraya eklenebilir veya kullanıcıya görsel bildirim verilir
            document.getElementById('pView').style.display = 'block';
            document.getElementById('pText').innerText = file.name + " işlenmeye hazır...";
        }

        function go() {
            document.getElementById('pBox').style.display = 'block';
            let w = 0; let b = document.getElementById('pBar');
            let i = setInterval(() => {
                w += (99 - w) * 0.1; b.style.width = w + '%';
                if(w > 98) clearInterval(i);
            }, 100);
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "GET":
        return render_template_string(HTML_UI)
    
    f = request.files.get("file")
    mod = request.form.get("mod")
    lines = guclu_udf_parser(f.read())
    text = "\n".join(lines)

    if mod == "txt":
        return send_file(io.BytesIO(text.encode('utf-8')), as_attachment=True, download_name="belge.txt")
    elif mod == "word":
        return send_file(io.BytesIO(text.encode('utf-8')), as_attachment=True, download_name="belge.doc")
    else: # PDF
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        y = 800
        for line in lines:
            if y < 50: c.showPage(); y = 800
            c.drawString(50, y, line[:95])
            y -= 15
        c.save()
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name="belge.pdf")

@app.route("/robots.txt")
def robots():
    return Response("User-agent: *\nAllow: /\nSitemap: https://udf-to-pdf-production.up.railway.app/sitemap.xml", mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap():
    base = "https://udf-to-pdf-production.up.railway.app"
    urls = f"<url><loc>{base}/</loc></url>"
    for p in SEO_PAGES: urls += f"<url><loc>{base}/{p}</loc></url>"
    return Response(f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', mimetype="text/xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
