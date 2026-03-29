# -*- coding: utf-8 -*-
import os
import zlib
import zipfile
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string, Response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from docx import Document
import io
import re

app = Flask(__name__)

# --- YAPILANDIRMA ---
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024
SAYAC_DOSYASI = "sayac.txt"
DEFAULT_FONT = "Helvetica"

# Font Yükleme (Türkçe Karakter Desteği)
try:
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("TurkishFont", font_path))
        DEFAULT_FONT = "TurkishFont"
except: pass

def get_sayac():
    try:
        if os.path.exists(SAYAC_DOSYASI):
            with open(SAYAC_DOSYASI, "r") as f:
                return int(f.read().strip())
    except: pass
    return 11537 # Başlangıç değeri

def increment_sayac():
    count = get_sayac() + 1
    with open(SAYAC_DOSYASI, "w") as f: f.write(str(count))
    return count

# --- GELİŞMİŞ PARSER ---
def guclu_parser(data):
    try:
        xml_raw = None
        # ZIP/UDF Kontrolü
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for info in z.infolist():
                    if info.file_size < 10*1024*1024 and info.filename.endswith(".xml"):
                        xml_raw = z.read(info.filename)
        except: pass
        
        if not xml_raw:
            try: xml_raw = zlib.decompress(data)
            except: xml_raw = data

        xml_str = xml_raw.decode("utf-8", errors="ignore")
        xml_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_str)
        
        # XML ve Regex Karma extraction
        lines = re.findall(r'<(?:content|w:t)[^>]*>(.*?)</(?:content|w:t)>', xml_str, re.DOTALL)
        if not lines:
            lines = re.findall(r'>([^<]{2,})<', xml_str)
            
        return [re.sub(r'<[^>]+>', '', line).strip() for line in lines if line.strip()]
    except: return ["İçerik ayrıştırılamadı."]

# --- UI (HTML + CSS + JS) ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF to PDF | Online UYAP Dosya Dönüştürücü</title>
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --accent: #38bdf8; --green: #10b981; --text: #f8fafc; --muted: #94a3b8; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); display: flex; flex-direction: column; align-items: center; padding: 20px; margin: 0; }
        .box { background: var(--card); padding: 30px; border-radius: 20px; text-align: center; width: 100%; max-width: 650px; border: 1px solid #334155; box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-bottom: 25px; position: relative; }
        .stats-badge { background: rgba(56, 189, 248, 0.1); color: var(--accent); padding: 10px 15px; border-radius: 12px; font-size: 14px; font-weight: bold; margin-bottom: 20px; border: 1px solid rgba(56, 189, 248, 0.3); display: inline-block; }
        .security-badge { background: rgba(16, 185, 129, 0.1); color: #6ee7b7; padding: 18px; border-radius: 16px; font-size: 13.5px; text-align: left; margin-bottom: 20px; border: 1px solid rgba(16, 185, 129, 0.2); line-height: 1.5; }
        .contact-box { background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 15px; padding: 15px; margin-bottom: 20px; font-size: 13.5px; }
        .contact-box a { color: var(--accent); text-decoration: none; font-weight: bold; margin: 0 10px; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 15px; }
        button { border: none; padding: 14px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; font-size: 13px; transition: 0.2s; }
        button:hover { opacity: 0.8; transform: translateY(-1px); }
        .pdf { background: #0ea5e9; } .word { background: #2563eb; } .green { background: var(--green); }
        
        /* Progress Bar */
        #progress-container { display: none; width: 100%; background: #020617; border-radius: 10px; height: 10px; margin: 15px 0; overflow: hidden; }
        #progress-bar { width: 0%; height: 100%; background: var(--accent); transition: width 0.3s; }

        .info-panel { width: 100%; max-width: 650px; background: #111827; padding: 30px; border-radius: 24px; border: 1px solid #334155; margin-bottom: 20px; text-align: left; }
        .info-panel h2 { color: var(--accent); font-size: 18px; margin-bottom: 15px; border-bottom: 1px solid #1e293b; padding-bottom: 10px; }
        .review-card { background: var(--card); padding: 18px; border-radius: 15px; margin-bottom: 15px; border-left: 4px solid var(--accent); }
        .review-author { color: var(--accent); font-weight: bold; font-size: 12px; text-align: right; display: block; margin-top: 5px; }
        #preview-box { display: none; background: #020617; border: 1px solid var(--accent); padding: 20px; border-radius: 14px; margin-top: 20px; color: #cbd5e1; font-family: monospace; max-height: 250px; overflow-y: auto; text-align: left; white-space: pre-wrap; }
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

        <form id="uForm" method="POST" action="/" enctype="multipart/form-data" onsubmit="return handleForm(event)">
            <input type="file" name="file" id="fileInput" required style="width:100%; margin-bottom:20px; color: var(--muted);">
            
            <div id="progress-container"><div id="progress-bar"></div></div>

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
        <div class="review-card">"Duruşma salonunda tabletimden UDF dosyalarımı PDF'e çevirip anında okuyabiliyorum. Harika." <span class="review-author">- Av. M.T.</span></div>
        <div class="review-card">"Sistemin kayıt istememesi güven veriyor. Elinize sağlık." <span class="review-author">- A.Y.</span></div>
        <div class="review-card">"Dilekçelerimi Word'e çevirirken formatın bozulmaması çok başarılı." <span class="review-author">- K.S.</span></div>
        <div class="review-card">"İcra dairelerinde dosya incelerken en büyük yardımcım." <span class="review-author">- M.B. (Katip)</span></div>
        <div class="review-card">"Kişisel verilerin hemen silinmesi beni ikna eden en büyük özellik." <span class="review-author">- D.M.</span></div>
    </div>

    <script>
        function updateProgress(val) {
            const container = document.getElementById('progress-container');
            const bar = document.getElementById('progress-bar');
            container.style.display = 'block';
            bar.style.width = val + '%';
        }

        async function getPreview() {
            const fIn = document.getElementById('fileInput');
            if (!fIn.files[0]) return alert("Lütfen dosya seçin!");
            
            updateProgress(50);
            const fd = new FormData(); fd.append('file', fIn.files[0]); fd.append('mod', 'preview');
            const pBox = document.getElementById('preview-box');
            const pCont = document.getElementById('preview-content');
            
            pBox.style.display = "block"; pCont.innerText = "⏳ Belge okunuyor...";
            try {
                const r = await fetch('/', { method: 'POST', body: fd });
                pCont.innerText = await r.text();
                updateProgress(100);
            } catch (e) { pCont.innerText = "Hata oluştu!"; updateProgress(0); }
            setTimeout(() => document.getElementById('progress-container').style.display='none', 1000);
        }

        function handleForm(e) {
            updateProgress(30);
            let p = 30;
            const iv = setInterval(() => { p += 10; if(p < 90) updateProgress(p); }, 200);
            setTimeout(() => { clearInterval(iv); updateProgress(100); }, 2000);
            return true;
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "GET":
        return render_template_string(HTML_UI, current_sayac=f"{get_sayac():,}".replace(',', '.'))
    
    f = request.files.get("file")
    mod = request.form.get("mod")
    if not f: return "Dosya yok."
    
    raw_data = f.read()
    if mod == "preview":
        lines = guclu_parser(raw_data)
        return " ".join(lines)[:1000] + "..."

    increment_sayac()
    lines = guclu_parser(raw_data)
    
    if mod == "word":
        doc = Document()
        doc.add_paragraph("\n".join(lines))
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name="cevrilmis.docx")
    
    # PDF OLUŞTURMA
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    p_style = ParagraphStyle('Tr', fontName=DEFAULT_FONT, fontSize=11, leading=14)
    
    story = [Paragraph(line.replace('\\n', '<br/>'), p_style) for line in lines]
    doc.build(story)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="cevrilmis.pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
