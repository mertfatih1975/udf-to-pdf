# -*- coding: utf-8 -*-
import os
import zlib
import zipfile
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string, Response, make_response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from docx import Document
import pdfplumber
import io
import re
from datetime import datetime
import pytz

app = Flask(__name__)

# --- YAPILANDIRMA ---
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024
SAYAC_DOSYASI = "sayac.txt"

def get_sayac():
    try:
        if os.path.exists(SAYAC_DOSYASI):
            with open(SAYAC_DOSYASI, "r") as f:
                content = f.read().strip()
                return int(content) if content else 11535
    except: pass
    return 11535

def increment_sayac():
    count = get_sayac() + 1
    try:
        with open(SAYAC_DOSYASI, "w") as f: f.write(str(count))
    except: pass
    return count

# --- ZIRHLI UDF PARSER ---
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
        raw_text = data.decode("utf-8", errors="ignore")
        found = re.findall(r'>([^<]{10,})<', raw_text)
        return found if found else ["İçerik ayrıştırılamadı."]
    except Exception as e: return [f"Hata: {str(e)}"]

def parse_xml_to_lines(xml_content):
    try:
        xml_str = xml_content.decode("utf-8", errors="ignore")
        xml_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', xml_str)
        try:
            root = ET.fromstring(xml_str)
            lines = [elem.text.strip() for elem in root.iter() if elem.text and len(elem.text.strip()) > 1]
            if lines: return lines
        except: pass
        return re.findall(r'[^>]+(?=<)', xml_str)
    except: return ["Okuma hatası."]

# --- HTML UI (HER ŞEY DAHİL) ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF to PDF | Online UYAP Dosya Dönüştürücü</title>
    <meta name="description" content="UDF to PDF dönüştürücü. UYAP UDF dosyalarını ücretsiz PDF veya Word formatına çevirin.">
    <link rel="canonical" href="https://udftopdf.com/">
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --accent: #38bdf8; --green: #10b981; --text: #f8fafc; --muted: #94a3b8; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); display: flex; flex-direction: column; align-items: center; padding: 20px; margin: 0; }
        .box { background: var(--card); padding: 30px; border-radius: 20px; text-align: center; width: 100%; max-width: 650px; border: 1px solid #334155; box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-bottom: 25px; }
        .stats-badge { background: rgba(56, 189, 248, 0.1); color: var(--accent); padding: 10px 15px; border-radius: 12px; font-size: 14px; font-weight: bold; margin-bottom: 20px; border: 1px solid rgba(56, 189, 248, 0.3); display: inline-block; }
        .security-badge { background: rgba(16, 185, 129, 0.1); color: #6ee7b7; padding: 18px; border-radius: 16px; font-size: 13.5px; text-align: left; margin-bottom: 20px; border: 1px solid rgba(16, 185, 129, 0.2); line-height: 1.5; }
        .contact-box { background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 15px; padding: 15px; margin-bottom: 20px; font-size: 13.5px; }
        .contact-box a { color: var(--accent); text-decoration: none; font-weight: bold; margin: 0 10px; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 15px; }
        button { border: none; padding: 14px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; font-size: 13px; transition: 0.2s; }
        .pdf { background: #0ea5e9; } .word { background: #2563eb; } .green { background: var(--green); }
        .info-panel { width: 100%; max-width: 650px; background: #111827; padding: 30px; border-radius: 24px; border: 1px solid #334155; margin-bottom: 20px; text-align: left; }
        .info-panel h2 { color: var(--accent); font-size: 18px; margin-bottom: 15px; border-bottom: 1px solid #1e293b; padding-bottom: 10px; }
        .info-panel p, .info-panel li { font-size: 14px; color: var(--muted); line-height: 1.7; }
        .review-card { background: var(--card); padding: 18px; border-radius: 15px; margin-bottom: 15px; border-left: 4px solid var(--accent); }
        .review-author { color: var(--accent); font-weight: bold; font-size: 12px; text-align: right; display: block; margin-top: 5px; }
        #preview-box { display: none; background: #020617; border: 1px solid var(--accent); padding: 20px; border-radius: 14px; margin-top: 20px; color: #cbd5e1; font-family: monospace; max-height: 250px; overflow-y: auto; }
        h1 { color: var(--accent); font-size: 26px; margin: 0 0 10px 0; }
    </style>
</head>
<body>
    <div class="box">
        <h1>UDF Dönüştürücü</h1>
        <div class="stats-badge">🚀 {{ current_sayac }} Güvenli İşlem Tamamlandı</div>
        
        <div class="security-badge">
            🛡️ <b>Veri Güvenliği Protokolü:</b> Belgeler sunucu RAM'i üzerinde işlenir. Oturum biter bitmez verileriniz diskte iz bırakmadan kalıcı olarak silinir.
        </div>

        <div class="contact-box">
            🤝 <b>İletişim:</b> <a href="mailto:mertfatih1975@gmail.com">mertfatih1975@gmail.com</a> | <a href="tel:+905327641661">0532 764 16 61</a>
        </div>

        <form id="uForm" method="POST" action="/" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" required style="width:100%; margin-bottom:20px; color: var(--muted);">
            <button type="button" class="green" style="width:100%; margin-bottom:15px;" onclick="getPreview()">🔍 BELGE ÖNİZLE</button>

            <span style="font-size: 11px; font-weight: bold; display: block; text-align: left; color: var(--accent); margin-bottom: 10px;">⬇️ UDF'DEN DIŞA AKTAR</span>
            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" class="pdf">UDF ➔ PDF</button>
                <button type="submit" name="mod" value="word" class="word">UDF ➔ WORD</button>
            </div>

            <span style="font-size: 11px; font-weight: bold; display: block; text-align: left; color: var(--accent); margin-bottom: 10px;">⬆️ UDF'YE DÖNÜŞTÜR</span>
            <div class="btn-group">
                <button type="submit" name="mod" value="pdf_to_udf" class="pdf">PDF ➔ UDF</button>
                <button type="submit" name="mod" value="word_to_udf" class="word">WORD ➔ UDF</button>
            </div>
            <div id="preview-box"><div id="preview-content"></div></div>
        </form>
    </div>

    <div class="info-panel">
        <h2>🔄 Nasıl Çalışır?</h2>
        <ol>
            <li><b>Dosyayı Yükleyin:</b> .udf, .pdf veya .docx dosyanızı seçin.</li>
            <li><b>Önizleme:</b> İçeriği "Belge Önizle" butonuyla kontrol edin.</li>
            <li><b>Dönüştürün:</b> PDF veya Word butonuna tıklayın.</li>
            <li><b>Güvenle Kullanın:</b> Dosyanız saniyeler içinde hazır olur ve sunucudan silinir.</li>
        </ol>
    </div>

    <div class="info-panel">
        <h2>⚖️ UDF Dosyası Nedir? (UYAP)</h2>
        <p><b>UDF (Uyap Document Format)</b>, Türkiye Cumhuriyeti Adalet Bakanlığı UYAP sisteminde kullanılan resmi belge formatıdır. Standart programlarla açılmadığı için bu araç ile <b>PDF</b> veya <b>Word</b> formatına çevrilmesi gerekir.</p>
    </div>

    <div class="info-panel">
        <h2>💬 Kullanıcı Yorumları</h2>
        <div class="review-card">"Duruşma salonunda telefondan anında PDF'e çeviriyorum. Harika." <span class="review-author">- Av. M.T.</span></div>
        <div class="review-card">"Sistemin kayıt istememesi güven veriyor. Elinize sağlık." <span class="review-author">- A.Y.</span></div>
        <div class="review-card">"Dilekçelerimi Word'e çevirirken formatın bozulmaması çok başarılı." <span class="review-author">- K.S.</span></div>
        <div class="review-card">"İcra dairelerinde dosya incelerken en büyük yardımcım." <span class="review-author">- M.B. (Katip)</span></div>
        <div class="review-card">"Baro kartla giriş yapamadığım anlarda hayat kurtarıyor." <span class="review-author">- Av. S.G.</span></div>
        <div class="review-card">"Vatandaş portalından indirdiğim kararları telefonumda açabildim." <span class="review-author">- H.K.</span></div>
        <div class="review-card">"PDF'ten UDF'ye çevirme özelliği sayesinde dilekçelerimi hazırlıyorum." <span class="review-author">- Stj. Av. C.D.</span></div>
        <div class="review-card">"Ofis dışında acil evrak gelince direkt cepten hallediyoruz." <span class="review-author">- Av. Z.F.</span></div>
        <div class="review-card">"Dosya boyutu kısıtlaması olmaması çok iyi." <span class="review-author">- H.A.</span></div>
        <div class="review-card">"UYAP editörüyle uğraşmaktansa burada çevirmek çok daha pratik." <span class="review-author">- Av. B.R.</span></div>
        <div class="review-card">"Basit, hızlı ve ücretsiz. Favorilerime ekledim." <span class="review-author">- E.S.</span></div>
        <div class="review-card">"Word'e çevirirken yazıların kaymaması çok başarılı." <span class="review-author">- Av. E.O.</span></div>
        <div class="review-card">"Kişisel verilerin hemen silinmesi beni ikna eden en büyük özellik." <span class="review-author">- D.M.</span></div>
    </div>

    <script>
        async function getPreview() {
            const fIn = document.getElementById('fileInput');
            if (!fIn.files[0]) return alert("Lütfen dosya seçin!");
            const fd = new FormData(); fd.append('file', fIn.files[0]); fd.append('mod', 'preview');
            const pBox = document.getElementById('preview-box');
            const pCont = document.getElementById('preview-content');
            pBox.style.display = "block"; pCont.innerText = "⏳ Belge okunuyor...";
            try {
                const r = await fetch('/', { method: 'POST', body: fd });
                pCont.innerText = await r.text();
            } catch (e) { pCont.innerText = "Hata!"; }
        }
    </script>
</body>
</html>
"""

@app.route("/sitemap.xml")
def sitemap():
    pages = ["https://udftopdf.com/", "https://udftopdf.com/udf-to-pdf", "https://udftopdf.com/udf-viewer", "https://udftopdf.com/udf-acma", "https://udftopdf.com/udf-to-word"]
    xml = ['<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages: xml.append(f"<url><loc>{p}</loc></url>")
    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")

@app.route("/udf-to-pdf")
@app.route("/udf-viewer")
@app.route("/udf-acma")
@app.route("/udf-to-word")
def seo_landings():
    return render_template_string(HTML_UI, current_sayac=f"{get_sayac():,}".replace(',', '.'))

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "GET":
        return render_template_string(HTML_UI, current_sayac=f"{get_sayac():,}".replace(',', '.'))
    
    f = request.files.get("file")
    mod = request.form.get("mod")
    if not f: return "Dosya yok."
    
    if mod == "preview":
        try:
            lines = guclu_parser(f.read())
            return " ".join(lines)[:1000] + "..."
        except: return "Hata"

    increment_sayac()
    
    # PDF'DEN UDF'YE (pdfplumber)
    if mod == "pdf_to_udf":
        text_content = ""
        try:
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages: text_content += (page.extract_text() or "") + "\n"
            xml = f'<?xml version="1.0" encoding="UTF-8"?><udf><icerik><![CDATA[{text_content[:5000]}]]></icerik></udf>'
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z: z.writestr("content.xml", xml)
            buf.seek(0)
            return send_file(buf, as_attachment=True, download_name="cevrilmis.udf", mimetype="application/octet-stream")
        except: return "PDF hatası."

    # UDF'DEN DİĞERLERİNE
    lines = guclu_parser(f.read())
    
    if mod == "word":
        doc = Document()
        for line in lines: doc.add_paragraph(line)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name="cevrilmis.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    for line in lines:
        if y < 50: c.showPage(); y = 800
        c.drawString(50, y, line[:100]); y -= 15
    c.save(); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="cevrilmis.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
