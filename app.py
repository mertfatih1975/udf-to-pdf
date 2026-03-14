import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string, Response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io

app = Flask(__name__)

# --- SEO YOLLARI ---
SEO_PAGES = ["udf-to-pdf", "udf-to-word", "udf-to-txt", "uyap-udf-donusturucu", "udf-dosya-ac"]

# --- SENİN VERDİĞİN GÜÇLÜ PARSER (ESNEK YAPI) ---
def guclu_parser(data):
    try:
        # 1. Strateji: Standart Tag Arama
        s, e = data.find(b"<content>"), data.find(b"</content>")
        if s != -1 and e != -1:
            raw_xml = zlib.decompress(data[s+9:e])
        else:
            # 2. Strateji: Tag yoksa zlib başlangıcını (78 9C) yakala
            zlib_start = data.find(b'\x78\x9c')
            if zlib_start != -1:
                raw_xml = zlib.decompress(data[zlib_start:])
            else: return ["Hata: UDF verisi ayrıştırılamadı."]

        root = ET.fromstring(raw_xml)
        return [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
    except Exception as ex:
        return [f"Parser Hatası: {str(ex)}"]

# --- GÖRSEL VE FONKSİYONEL ARAYÜZ ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF Pro v15.0 | Bursa Ofis Gökçadır</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 480px; border: 1px solid #334155; box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
        .badge { background: #064e3b; color: #6ee7b7; padding: 12px; border-radius: 10px; font-size: 13px; margin-bottom: 20px; border: 1px solid #059669; }
        .preview-box { display: none; background: #0f172a; border: 1px solid #334155; padding: 15px; border-radius: 10px; margin: 15px 0; text-align: left; font-size: 12px; color: #94a3b8; max-height: 100px; overflow: hidden; }
        .progress-container { display: none; margin: 20px 0; background: #334155; border-radius: 10px; height: 12px; overflow: hidden; position: relative; }
        .progress-bar { width: 0%; height: 100%; background: linear-gradient(90deg, #38bdf8, #818cf8); transition: width 0.2s; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; font-size: 14px; }
        .pdf { background: #0ea5e9; grid-column: span 2; font-size: 16px; }
        .word { background: #2b579a; } .txt { background: #64748b; }
        button:hover { filter: brightness(1.2); transform: translateY(-2px); }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; cursor: pointer; border: 1px dashed #475569; padding: 15px; border-radius: 10px; }
        .kvkk-note { margin-top: 25px; font-size: 11px; color: #64748b; text-decoration: underline; cursor: pointer; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="color:#38bdf8; margin:0 0 10px 0;">UDF PRO <span style="color:white">MASTER</span></h2>
        <div class="badge">🛡️ <b>GÜVENLİK:</b> Dosyalar saklanmaz, sadece RAM'de işlenir.</div>
        
        <form id="uForm" method="POST" action="/" enctype="multipart/form-data">
            <input type="file" name="file" id="fIn" accept=".udf" required onchange="handleFile()">
            
            <div id="pView" class="preview-box">
                <b>📄 Belge Önizleme:</b><br>
                <span id="pText">Dosya hazır...</span>
            </div>

            <div id="pCont" class="progress-container"><div id="pBar" class="progress-bar"></div></div>
            <p id="pPerc" style="display:none; color:#38bdf8; font-size:12px; margin-bottom:10px;">%0 Hazırlanıyor...</p>

            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" class="pdf" onclick="run()">PRO PDF OLARAK DÖNÜŞTÜR</button>
                <button type="submit" name="mod" value="word" class="word" onclick="run()">PRO WORD (DOC)</button>
                <button type="submit" name="mod" value="txt" class="txt" onclick="run()">HIZLI TEXT (TXT)</button>
            </div>
        </form>

        <div class="kvkk-note" onclick="alert('KVKK AYDINLATMA: Verileriniz sunucuda yedeklenmez. İşlem bittiği an bellekten (RAM) kalıcı olarak silinir.')">KVKK ve Veri Güvenliği Aydınlatma Metni</div>
        <p style="font-size:10px; color:#475569; margin-top:25px">© 2026 FATİH MERT | BURSA | Ofis Gökçadır</p>
    </div>

    <script>
        function handleFile() {
            const f = document.getElementById('fIn').files[0];
            if (f) {
                document.getElementById('pView').style.display = 'block';
                document.getElementById('pText').innerText = "Belge: " + f.name + " (" + (f.size/1024).toFixed(1) + " KB)";
            }
        }

        function run() {
            if(document.getElementById('fIn').files.length == 0) return;
            document.getElementById('pCont').style.display = 'block';
            document.getElementById('pPerc').style.display = 'block';
            let w = 0;
            let int = setInterval(() => {
                w += (100 - w) * 0.15;
                document.getElementById('pBar').style.width = w + '%';
                document.getElementById('pPerc').innerText = '%' + Math.floor(w) + ' İşleniyor...';
                if(w > 98) clearInterval(int);
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
    lines = guclu_parser(f.read())
    text = "\n".join(lines)

    if mod == "txt":
        return send_file(io.BytesIO(text.encode('utf-8')), as_attachment=True, download_name="belge.txt", mimetype='text/plain')
    elif mod == "word":
        return send_file(io.BytesIO(text.encode('utf-8')), as_attachment=True, download_name="belge.doc", mimetype='application/msword')
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
        return send_file(buf, as_attachment=True, download_name="belge.pdf", mimetype='application/pdf')

@app.route("/sitemap.xml")
def sitemap():
    base = "https://udf-to-pdf-production.up.railway.app"
    xml = f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{base}/</loc></url>'
    for p in SEO_PAGES: xml += f"<url><loc>{base}/{p}</loc></url>"
    return Response(xml + "</urlset>", mimetype="text/xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
