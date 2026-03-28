# -*- coding: utf-8 -*-
import os
import zlib
import zipfile
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, Response, render_template_string
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY
from docx import Document
import io
import re

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

# --- GELİŞTİRİLMİŞ UDF PARSER ---
def guclu_parser(data):
    try:
        xml_content = None
        # 1. Zip kontrolü (UDF'ler genelde ziptir)
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for name in z.namelist():
                    if name.lower().endswith(".xml"):
                        xml_content = z.read(name)
                        break
        except: pass

        # 2. Zlib ham veri kontrolü
        if not xml_content:
            sigs = [b'\x78\x9c', b'\x78\xda', b'\x78\x01']
            for sig in sigs:
                pos = data.find(sig)
                if pos != -1:
                    try:
                        xml_content = zlib.decompress(data[pos:])
                        break
                    except: pass

        if not xml_content:
            xml_content = data # Düz metin varsayımı

        # XML Temizleme ve Metin Ayıklama
        xml_str = xml_content.decode("utf-8", errors="ignore")
        # Gizli karakterleri temizle
        xml_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', xml_str)
        
        # UYAP formatında metin genellikle <content> içindedir
        # Önce tag içindeki verileri çekelim, html etiketlerini temizleyelim
        clean_text = re.sub(r'<[^>]+>', '\n', xml_str)
        lines = [line.strip() for line in clean_text.split('\n') if len(line.strip()) > 1]
        
        return lines if lines else ["Dosya içeriği boş veya okunamadı."]
    except Exception as e:
        return [f"Hata oluştu: {str(e)}"]

# --- HTML UI ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF to PDF | Online UYAP Dönüştürücü</title>
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --accent: #38bdf8; --green: #10b981; --text: #f8fafc; --muted: #94a3b8; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); display: flex; flex-direction: column; align-items: center; padding: 20px; margin: 0; }
        .box { background: var(--card); padding: 30px; border-radius: 20px; text-align: center; width: 100%; max-width: 650px; border: 1px solid #334155; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .stats-badge { background: rgba(56, 189, 248, 0.1); color: var(--accent); padding: 10px 15px; border-radius: 12px; font-size: 14px; font-weight: bold; margin-bottom: 20px; display: inline-block; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 15px; }
        button { border: none; padding: 14px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.2s; }
        .pdf { background: #0ea5e9; } .word { background: #2563eb; } .green { background: var(--green); width: 100%; }
        #preview-box { display: none; background: #020617; border: 1px solid var(--accent); padding: 15px; border-radius: 10px; margin-top: 20px; text-align: left; max-height: 200px; overflow-y: auto; font-size: 13px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>UDF Dönüştürücü</h1>
        <div class="stats-badge">🚀 {{ current_sayac }} İşlem Tamamlandı</div>
        
        <form method="POST" action="/" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" required style="width:100%; margin-bottom:20px; color: var(--muted);">
            
            <button type="button" class="green" onclick="getPreview()">🔍 BELGE ÖNİZLE</button>

            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" class="pdf">PDF OLARAK İNDİR</button>
                <button type="submit" name="mod" value="word" class="word">WORD OLARAK İNDİR</button>
            </div>
            <div id="preview-box"></div>
        </form>
    </div>

    <script>
        async function getPreview() {
            const fIn = document.getElementById('fileInput');
            if (!fIn.files[0]) return alert("Dosya seçin!");
            const fd = new FormData(); fd.append('file', fIn.files[0]); fd.append('mod', 'preview');
            const pBox = document.getElementById('preview-box');
            pBox.style.display = "block"; pBox.innerText = "Okunuyor...";
            try {
                const r = await fetch('/', { method: 'POST', body: fd });
                pBox.innerText = await r.text();
            } catch (e) { pBox.innerText = "Hata!"; }
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template_string(HTML_UI, current_sayac=f"{get_sayac():,}".replace(',', '.'))
    
    file = request.files.get("file")
    mod = request.form.get("mod")
    if not file: return "Dosya seçilmedi."

    file_data = file.read()
    lines = guclu_parser(file_data)
    
    if mod == "preview":
        return "\n".join(lines)[:1500] + "..."

    increment_sayac()

    if mod == "word":
        doc = Document()
        for line in lines: doc.add_paragraph(line)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name="cevrilmis.docx")

    # PDF Oluşturma (Gelişmiş Metin Akışı)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Özel paragraf stili (Türkçe karakter ve hizalama desteği için)
    custom_style = ParagraphStyle(
        'CustomStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        alignment=TA_JUSTIFY,
        fontName='Helvetica' # Sunucuda Arial yüklü değilse en güvenlisi
    )
    
    story = []
    for line in lines:
        if line.strip():
            # XML/HTML kaçış karakterlerini temizle
            clean_line = line.replace("<", "&lt;").replace(">", "&gt;")
            p = Paragraph(clean_line, custom_style)
            story.append(p)
            story.append(Spacer(1, 6))
            
    doc.build(story)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="cevrilmis.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
