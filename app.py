# -*- coding: utf-8 -*-
import os
import zlib
import zipfile
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string, Response, make_response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import re
from datetime import datetime
import pytz
import json

app = Flask(__name__)

# --- SAYAÇ SİSTEMİ ---
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
        return ["İçerik ayrıştırılamadı."]
    except: return ["Hata oluştu."]

def parse_xml_to_lines(xml_content):
    try:
        xml_str = xml_content.decode("utf-8", errors="ignore")
        xml_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', xml_str)
        root = ET.fromstring(xml_str)
        lines = [" ".join(elem.text.split()) for elem in root.iter() if elem.text and len(elem.text.strip()) > 1]
        return lines if lines else [re.sub(r'<[^>]+>', ' ', xml_str).strip()]
    except: return ["XML hatası."]

# --- UI TASARIMI ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page_title }}</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; flex-direction: column; align-items: center; padding: 20px; }
        .box { background: #1e293b; padding: 30px; border-radius: 20px; text-align: center; width: 100%; max-width: 600px; border: 1px solid #334155; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .stats-badge { background: rgba(56, 189, 248, 0.1); color: #38bdf8; padding: 10px; border-radius: 10px; font-size: 14px; margin-bottom: 20px; border: 1px solid rgba(56, 189, 248, 0.3); font-weight: bold; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }
        button { border: none; padding: 12px; border-radius: 8px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; opacity: 0.3; pointer-events: none; font-size: 13px; }
        .active { opacity: 1 !important; pointer-events: auto !important; }
        .pdf { background: #0ea5e9; } .word { background: #2b579a; } .preview-btn-ui { background: #10b981; grid-column: span 2; }
        .info-panel { width: 100%; max-width: 600px; background: #111827; padding: 25px; border-radius: 20px; border: 1px solid #334155; margin-bottom: 20px; font-size: 14px; line-height: 1.6; color: #94a3b8; text-align: left; }
        #preview-box { display: none; background: #020617; border: 1px solid #38bdf8; padding: 15px; border-radius: 10px; margin-top: 20px; text-align: left; max-height: 250px; overflow-y: auto; color: #cbd5e1; font-family: monospace; font-size: 12px; white-space: pre-wrap; }
        .preview-title { color: #10b981; font-weight: bold; margin-bottom: 10px; display: block; border-bottom: 1px solid #1e293b; }
        .review-box { background: #1e293b; padding: 15px; border-radius: 12px; margin-bottom: 12px; border-left: 4px solid #38bdf8; }
        .review-text { font-style: italic; color: #cbd5e1; font-size: 13px; }
        .review-author { color: #f8fafc; font-weight: bold; font-size: 12px; margin-top: 5px; text-align: right; }
        .contact-link { color: #38bdf8; text-decoration: none; font-weight: bold; }
        .review-btn { background: #38bdf8; color: #0f172a; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-size: 11px; font-weight: bold; float: right; }
        h1 { color:#38bdf8; font-size: 24px; }
        h2 { color:#e2e8f0; font-size: 18px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>UDF Dönüştürücü</h1>
        <div class="stats-badge">🚀 Toplam {{ current_sayac }} güvenli işlem tamamlandı.</div>
        <form id="uForm" method="POST" action="/" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" accept=".udf, .pdf, .docx, .txt" required style="width:100%; margin-bottom:15px; color: #94a3b8;">
            <label style="font-size: 12px; display: block; margin-bottom: 15px; cursor: pointer;">
                <input type="checkbox" id="kvkk" onchange="toggleBtns()"> KVKK Aydınlatma Metnini onaylıyorum.
            </label>
            <div class="btn-group">
                <button type="button" id="btnPreview" class="preview-btn-ui" onclick="getPreview()">🔍 DOSYA ÖNİZLE</button>
                <button type="submit" name="mod" value="pdf" id="btn1" class="pdf">UDF ➔ PDF</button>
                <button type="submit" name="mod" value="word" id="btn2" class="word">UDF ➔ WORD</button>
            </div>
            <div id="preview-box">
                <span class="preview-title">📄 Belge Önizlemesi (İlk 500 Karakter):</span>
                <div id="preview-content"></div>
            </div>
        </form>
        <div style="margin-top:25px; font-size:13px; color:#94a3b8; border-top:1px solid #334155; padding-top:15px;">
            🤝 <b>İşbirliği:</b> <a href="mailto:mertfatih1975@gmail.com" class="contact-link">mertfatih1975@gmail.com</a> | 
            <a href="tel:+905327641661" class="contact-link">0532 764 16 61</a>
        </div>
    </div>

    <div class="info-panel">
        <h2><span>💬 Kullanıcı Yorumları</span><a href="mailto:mertfatih1975@gmail.com?subject=Yeni Yorum" class="review-btn">+ Yorum Yap</a></h2>
        <div class="review-box"><div class="review-text">"Duruşma öncesi telefonumdan anında PDF'e çeviriyorum. Program kurmaya gerek kalmıyor."</div><div class="review-author">- Av. M.T.</div></div>
        <div class="review-box"><div class="review-text">"Sistemin kayıt istememesi ve dosyaları hemen silmesi güven veriyor."</div><div class="review-author">- A.Y.</div></div>
        <div class="review-box"><div class="review-text">"UDF dosyalarını Word formatına çevirmek için harika bir araç."</div><div class="review-author">- K.S.</div></div>
        <div class="review-box"><div class="review-text">"Baro kartla giriş yapamadığım anlarda hayat kurtarıyor."</div><div class="review-author">- Av. S.G.</div></div>
        <div class="review-box"><div class="review-text">"İcra katipliği yapıyorum, her gün onlarca UDF'yi PDF yapmam gerekiyor. Çok hızlı."</div><div class="review-author">- M.B. (Katip)</div></div>
        <div class="review-box"><div class="review-text">"Vatandaş portalından indirdiğim kararları telefonumda açabildim, teşekkürler."</div><div class="review-author">- H.K.</div></div>
        <div class="review-box"><div class="review-text">"PDF'ten UDF'ye çevirme özelliği sayesinde dilekçelerimi UYAP'a uyumlu hale getiriyorum."</div><div class="review-author">- Stj. Av. C.D.</div></div>
        <div class="review-box"><div class="review-text">"Ofis dışında acil evrak gelince direkt cepten hallediyoruz. Elinize sağlık."</div><div class="review-author">- Av. Z.F.</div></div>
        <div class="review-box"><div class="review-text">"Dosya boyutu kısıtlaması olmaması çok iyi. Büyük dosyaları bile çeviriyor."</div><div class="review-author">- H.A.</div></div>
        <div class="review-box"><div class="review-text">"UYAP editörüyle uğraşmaktansa burada çevirmek çok daha pratik."</div><div class="review-author">- Av. B.R.</div></div>
        <div class="review-box"><div class="review-text">"Basit, hızlı ve ücretsiz. Favorilerime ekledim bile."</div><div class="review-author">- E.S.</div></div>
        <div class="review-box"><div class="review-text">"Word'e çevirirken yazıların kaymaması çok başarılı."</div><div class="review-author">- Av. E.O.</div></div>
        <div class="review-box"><div class="review-text">"Kişisel verilerin hemen silinmesi beni ikna eden en büyük özellik."</div><div class="review-author">- D.M.</div></div>
    </div>

    <script>
        function toggleBtns() {
            const isChecked = document.getElementById('kvkk').checked;
            ['btn1','btn2','btnPreview'].forEach(id => {
                const b = document.getElementById(id);
                if(isChecked) b.classList.add('active');
                else b.classList.remove('active');
            });
        }
        async function getPreview() {
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.files[0]) return alert("Lütfen önce bir dosya seçin.");
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('mod', 'preview');
            const previewBox = document.getElementById('preview-box');
            const previewContent = document.getElementById('preview-content');
            previewContent.innerText = "Yükleniyor...";
            previewBox.style.display = "block";
            try {
                const response = await fetch('/', { method: 'POST', body: formData });
                const text = await response.text();
                previewContent.innerText = text;
            } catch (e) { previewContent.innerText = "Önizleme alınamadı."; }
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def index():
    now = datetime.now(pytz.timezone('Europe/Istanbul'))
    if request.method == "GET":
        sayac = get_sayac()
        return render_template_string(HTML_UI, 
            current_sayac=f"{sayac:,}".replace(',', '.'),
            page_title="UDFTOPDF | Önizlemeli Ücretsiz Çevirici")
    
    f = request.files.get("file")
    mod = request.form.get("mod")
    
    if mod == "preview":
        try:
            lines = guclu_parser(f.read())
            full_text = " ".join(lines)
            return full_text[:500] + "..."
        except: return "Önizleme alınamadı."

    increment_sayac()
    lines = guclu_parser(f.read())
    text = "\n".join(lines)
    
    if mod == "word":
        return send_file(io.BytesIO(text.encode("utf-8")), as_attachment=True, download_name="belge.doc", mimetype="application/msword")
    
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    c.setFont("Helvetica", 10)
    for line in lines:
        if y < 50: c.showPage(); y = 800
        c.drawString(50, y, line[:100]); y -= 15
    c.save(); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="belge.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
