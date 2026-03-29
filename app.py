# -*- coding: utf-8 -*-
import os, zlib, zipfile, io, re, smtplib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)

# --- AYARLAR ---
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
SAYAC_DOSYASI = "sayac.txt"
DEFAULT_FONT = "Helvetica"
MY_MAIL = "mertfatih1975@gmail.com"
MAIL_APP_PASS = "xxxx xxxx xxxx xxxx" # Gmail Uygulama Şifreniz

# --- TÜRKÇE FONT DESTEĞİ ---
try:
    font_paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:\\Windows\\Fonts\\arial.ttf"]
    for path in font_paths:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont("TurkishFont", path))
            DEFAULT_FONT = "TurkishFont"
            break
except: pass

# --- SAYAÇ ---
def get_sayac():
    if not os.path.exists(SAYAC_DOSYASI): return 11537
    with open(SAYAC_DOSYASI, "r") as f: 
        val = f.read().strip()
        return int(val) if val else 11537

def increment_sayac():
    c = get_sayac() + 1
    with open(SAYAC_DOSYASI, "w") as f: f.write(str(c))
    return c

# --- GELİŞMİŞ UDF PARSER (REVIZELI) ---
def advanced_udf_parser(data):
    xml_content = None
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for n in z.namelist():
                if n.lower().endswith(".xml"):
                    xml_content = z.read(n)
                    break
    except: pass

    if not xml_content:
        try:
            xml_content = zlib.decompress(data)
        except:
            for sig in (b'\x78\x9c', b'\x78\xda', b'\x78\x01'):
                pos = data.find(sig)
                if pos != -1:
                    try:
                        xml_content = zlib.decompress(data[pos:])
                        break
                    except: pass
    
    if not xml_content: xml_content = data

    try:
        xml_str = xml_content.decode("utf-8", errors="ignore")
        xml_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_str)
        lines = []

        # 1- UYAP Content Tarama
        content_matches = re.findall(r'<content[^>]*>(.*?)</content>', xml_str, re.DOTALL)
        for m in content_matches:
            clean = re.sub(r'<[^>]+>', '', m).strip()
            if clean: lines.append(clean)

        # 2- Word XML (w:t) Tarama - ASIL ÇÖZÜM
        word_matches = re.findall(r'<w:t[^>]*>(.*?)</w:t>', xml_str, re.DOTALL)
        if word_matches:
            for w in word_matches:
                clean = re.sub(r'<[^>]+>', '', w).strip()
                if clean: lines.append(clean)

        # 3- Fallback (Garantör)
        if not lines:
            fallback = re.findall(r'>([^<]{4,})<', xml_str)
            lines = [f.strip() for f in fallback if len(f.strip()) > 3]

        return lines if lines else ["Belge içeriği bulunamadı."]
    except Exception as e:
        return [f"Ayrıştırma hatası: {str(e)}"]

# --- MAİL GÖNDERİMİ ---
def send_mail(name, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = MY_MAIL
        msg['To'] = MY_MAIL
        msg['Subject'] = f"UDF Yeni Yorum: {name}"
        msg.attach(MIMEText(f"Gönderen: {name}\n\nMesaj:\n{message}", 'plain'))
        server = smtplib.SMTP("smtp.gmail.com", 587); server.starttls()
        server.login(MY_MAIL, MAIL_APP_PASS)
        server.send_message(msg); server.quit()
        return True
    except: return False

# --- UI ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF to PDF | Online UYAP Dönüştürücü</title>
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --accent: #38bdf8; --text: #f8fafc; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); display: flex; flex-direction: column; align-items: center; padding: 20px; }
        .box { background: var(--card); padding: 30px; border-radius: 20px; width: 100%; max-width: 600px; text-align: center; border: 1px solid #334155; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .stats { background: rgba(56, 189, 248, 0.1); color: var(--accent); padding: 10px; border-radius: 12px; font-weight: bold; margin-bottom: 20px; display: inline-block; }
        #pb { display: none; width: 100%; background: #020617; height: 10px; border-radius: 5px; margin: 15px 0; overflow: hidden; }
        #pb-bar { width: 0%; height: 100%; background: var(--accent); transition: width 0.3s; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 15px; }
        button { border: none; padding: 14px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.2s; }
        .pdf { background: #0ea5e9; } .word { background: #2563eb; } .pre { background: #10b981; width: 100%; }
        .review-card { background: var(--card); padding: 15px; border-radius: 15px; margin-top: 15px; border-left: 4px solid var(--accent); text-align: left; }
        input, textarea { width: 100%; padding: 12px; margin-top: 10px; background: #020617; border: 1px solid #334155; color: white; border-radius: 8px; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="box">
        <h1>UDF Dönüştürücü</h1>
        <div class="stats">🚀 {{ count }} Güvenli İşlem Tamamlandı</div>
        <form id="uForm" method="POST" enctype="multipart/form-data" onsubmit="start()">
            <input type="file" name="file" id="fIn" required style="margin-bottom:20px;">
            <div id="pb"><div id="pb-bar"></div></div>
            <button type="button" class="pre" onclick="getPre()">🔍 BELGE ÖNİZLE</button>
            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" class="pdf">UDF ➔ PDF</button>
                <button type="submit" name="mod" value="word" class="word">UDF ➔ WORD</button>
            </div>
            <div id="pBox" style="display:none; background:#020617; padding:15px; margin-top:15px; text-align:left; font-size:13px; max-height:150px; overflow:auto; border:1px dashed var(--accent);"></div>
        </form>
    </div>

    <div style="width:100%; max-width:600px; margin-top:30px;">
        <h3>💬 Kullanıcı Yorumları</h3>
        <div class="review-card">"Ekranda 'belge içeriği bulunamadı' hatası alıyordum, bu yeni parser ile hepsi çözüldü!" <br><b>- Av. Mert F.</b></div>
        
        <div style="margin-top:20px; background: var(--card); padding:20px; border-radius:15px;">
            <h4>✍️ Yorum Paneli</h4>
            <input type="text" id="yAd" placeholder="Adınız">
            <textarea id="yMsg" placeholder="Görüşleriniz..." rows="2"></textarea>
            <button onclick="sendY()" class="pre" style="margin-top:10px;">Yorumu Gönder (mertfatih1975@gmail.com)</button>
            <p id="ySt" style="font-size:12px; margin-top:5px;"></p>
        </div>
    </div>

    <script>
        function start() { document.getElementById('pb').style.display='block'; let w=0; setInterval(()=>{if(w<90){w+=10;document.getElementById('pb-bar').style.width=w+'%'}},200); }
        async function getPre() {
            const f = document.getElementById('fIn'); if(!f.files[0]) return alert("Dosya seç!");
            const fd = new FormData(); fd.append('file', f.files[0]); fd.append('mod', 'preview');
            const b = document.getElementById('pBox'); b.style.display='block'; b.innerText='Okunuyor...';
            const r = await fetch('/', {method:'POST', body:fd}); b.innerText = await r.text();
        }
        async function sendY() {
            const st = document.getElementById('ySt'); st.innerText = "Gönderiliyor...";
            const fd = new FormData(); fd.append('isim', document.getElementById('yAd').value); fd.append('mesaj', document.getElementById('yMsg').value);
            const r = await fetch('/yorum-yap', {method:'POST', body:fd});
            if(r.ok) st.innerText = "✅ Teşekkürler, yorumunuz iletildi.";
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template_string(HTML_UI, count=f"{get_sayac():,}".replace(',', '.'))
    
    f = request.files.get("file")
    mod = request.form.get("mod")
    if not f: return "Dosya yok."
    
    data = f.read()
    parsed_lines = advanced_udf_parser(data)
    print(f"DEBUG: Extracted lines count: {len(parsed_lines)}") # Terminal takibi için

    if mod == "preview":
        return " ".join(parsed_lines)[:1000] + "..."

    increment_sayac()

    if mod == "word":
        doc = Document(); doc.add_paragraph("\n".join(parsed_lines))
        buf = io.BytesIO(); doc.save(buf); buf.seek(0)
        return send_file(buf, as_attachment=True, download_name="uyap_cikti.docx")

    # PDF MODU (İyileştirilmiş Metin Dizilimi)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    p_style = ParagraphStyle('Tr', fontName=DEFAULT_FONT, fontSize=11, leading=15)
    
    elements = []
    for line in parsed_lines:
        if line.strip():
            # w:t içindeki metinleri Paragraph nesnesine ekle
            elements.append(Paragraph(line.replace('\n', '<br/>'), p_style))
            elements.append(Spacer(1, 8)) # Satır arası ferahlık

    if not elements:
        elements.append(Paragraph("<b>HATA:</b> Belge içeriği ayrıştırılamadı.", p_style))

    doc.build(elements)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="uyap_cikti.pdf")

@app.route("/yorum-yap", methods=["POST"])
def handle_yorum():
    if send_mail(request.form.get("isim"), request.form.get("mesaj")):
        return "OK"
    return "Error", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
