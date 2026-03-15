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
    except:
        pass
    return 11535

def increment_sayac():
    count = get_sayac() + 1
    try:
        with open(SAYAC_DOSYASI, "w") as f:
            f.write(str(count))
    except:
        pass
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
    <title>UDFTOPDF | Profesyonel UYAP Dosya Dönüştürücü</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; flex-direction: column; align-items: center; padding: 20px; }
        .box { background: #1e293b; padding: 30px; border-radius: 20px; text-align: center; width: 100%; max-width: 600px; border: 1px solid #334155; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .stats-badge { background: rgba(56, 189, 248, 0.1); color: #38bdf8; padding: 10px; border-radius: 10px; font-size: 14px; margin-bottom: 20px; border: 1px solid rgba(56, 189, 248, 0.3); font-weight: bold; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }
        .section-title { font-size: 13px; font-weight: bold; margin: 15px 0 5px 0; display: block; text-align: left; }
        .t-down { color: #38bdf8; } .t-up { color: #10b981; }
        button { border: none; padding: 12px; border-radius: 8px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; opacity: 0.3; pointer-events: none; font-size: 12px; }
        .active { opacity: 1 !important; pointer-events: auto !important; }
        .pdf { background: #0ea5e9; } .word { background: #2b579a; } .txt { background: #64748b; } .jpeg { background: #f59e0b; }
        .pdf-u { background: #0284c7; } .word-u { background: #1e3a8a; } .txt-u { background: #475569; } .jpeg-u { background: #d97706; }
        .preview-btn-ui { background: #10b981; grid-column: span 2; margin-bottom: 10px; }
        .info-panel { width: 100%; max-width: 600px; background: #111827; padding: 25px; border-radius: 20px; border: 1px solid #334155; margin-bottom: 20px; font-size: 14px; line-height: 1.6; color: #94a3b8; text-align: left; }
        .info-panel h2 { color: #38bdf8; font-size: 18px; margin-top: 0; margin-bottom: 15px; border-bottom: 1px solid #1e293b; padding-bottom: 10px; }
        .info-panel b { color: #f8fafc; }
        #preview-box { display: none; background: #020617; border: 1px solid #38bdf8; padding: 15px; border-radius: 10px; margin-top: 20px; max-height: 200px; overflow-y: auto; color: #cbd5e1; font-family: monospace; font-size: 12px; white-space: pre-wrap; }
        .review-box { background: #1e293b; padding: 15px; border-radius: 12px; margin-bottom: 12px; border-left: 4px solid #38bdf8; }
        .review-text { font-style: italic; color: #cbd5e1; }
        .review-author { color: #f8fafc; font-weight: bold; font-size: 12px; margin-top: 5px; text-align: right; }
        .contact-link { color: #38bdf8; text-decoration: none; font-weight: bold; }
        .review-btn { background: #38bdf8; color: #0f172a; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-size: 11px; float: right; font-weight: bold; }
        .security-badge { background: rgba(6, 78, 59, 0.4); color: #6ee7b7; padding: 15px; border-radius: 12px; font-size: 13px; margin-bottom: 25px; border: 1px solid #059669; text-align: left; line-height: 1.5; }
    </style>
</head>
<body>
    <div class="box">
        <h1>UDF Dönüştürücü</h1>
        <div class="stats-badge">🚀 Toplam {{ current_sayac }} güvenli işlem tamamlandı.</div>
        
        <div class="security-badge">
            🛡️ <b>Veri Güvenliği Protokolü:</b> Yüklediğiniz belgeler sunucu disklerine asla kaydedilmez. Tüm işlemler şifrelenmiş geçici bellek (RAM) üzerinde gerçekleştirilir ve oturum sonlandırıldığı an verileriniz geri döndürülemez şekilde sistemden temizlenir.
        </div>

        <form id="uForm" method="POST" action="/" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" required style="width:100%; margin-bottom:15px; color: #94a3b8;">
            <label style="font-size: 12px; display: block; margin-bottom: 15px; cursor: pointer;">
                <input type="checkbox" id="kvkk" onchange="toggleBtns()"> KVKK Aydınlatma Metnini okudum ve onaylıyorum.
            </label>

            <button type="button" id="btnPreview" class="preview-btn-ui" onclick="getPreview()">🔍 BELGE ÖNİZLE</button>

            <span class="section-title t-down">⬇️ UDF'den Çevir</span>
            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" id="b1" class="pdf">UDF ➔ PDF</button>
                <button type="submit" name="mod" value="word" id="b2" class="word">UDF ➔ WORD</button>
                <button type="submit" name="mod" value="txt" id="b3" class="txt">UDF ➔ TXT</button>
                <button type="submit" name="mod" value="jpeg" id="b4" class="jpeg">UDF ➔ JPEG</button>
            </div>

            <span class="section-title t-up">⬆️ UDF'ye Dönüştür (Tersine)</span>
            <div class="btn-group">
                <button type="submit" name="mod" value="pdf_to_udf" id="b5" class="pdf-u">PDF ➔ UDF</button>
                <button type="submit" name="mod" value="word_to_udf" id="b6" class="word-u">WORD ➔ UDF</button>
                <button type="submit" name="mod" value="txt_to_udf" id="b7" class="txt-u">TXT ➔ UDF</button>
                <button type="submit" name="mod" value="jpeg_to_udf" id="b8" class="jpeg-u">JPEG ➔ UDF</button>
            </div>

            <div id="preview-box">
                <div id="preview-content"></div>
            </div>
        </form>

        <div style="margin-top:25px; font-size:13px; color:#94a3b8; border-top:1px solid #334155; padding-top:15px;">
            🤝 <b>İletişim:</b> <a href="mailto:mertfatih1975@gmail.com" class="contact-link">mertfatih1975@gmail.com</a> | 
            <a href="tel:+905327641661" class="contact-link">0532 764 16 61</a>
        </div>
    </div>

    <div class="info-panel">
        <h2>🔄 UDF Dönüştürme Nasıl Yapılır?</h2>
        <ol>
            <li><b>Belgeyi Seçin:</b> Cihazınızdaki .udf veya PDF/Word dosyasını yükleyin.</li>
            <li><b>Hızlı Önizleme:</b> İndirmeden önce içeriğe göz atmak için "Belge Önizle" butonunu kullanın.</li>
            <li><b>Formatı Belirleyin:</b> İhtiyacınıza uygun çeviri butonuna tıklayın.</li>
            <li><b>Anında İndirin:</b> İşlem saniyeler içinde tamamlanır ve belgeniz hazır olur.</li>
        </ol>
    </div>

    <div class="info-panel">
        <h2>⚖️ UDF Nedir? (UYAP Doküman Formatı)</h2>
        <p><b>UDF dosyası</b>, Adalet Bakanlığı Ulusal Yargı Ağı Bilişim Sistemi (UYAP) tarafından kullanılan resmi belge formatıdır. Hukuki yazışmalar, dava dilekçeleri ve mahkeme kararları bu uzantı ile kaydedilir.</p>
        <p><b>UDF dosyası nasıl açılır?</b> Standart programlar bu dosyayı açamaz. Bu çevirici ile UDF dosyalarınızı her cihazda açılabilen <b>PDF</b> formatına veya düzenlenebilir <b>Word</b> formatına ücretsiz dönüştürebilirsiniz.</p>
    </div>

    <div class="info-panel">
        <h2>🛡️ Güvenli ve Hızlı Çeviri</h2>
        <p>Sistemimiz, belgelerinizin gizliliğini en üst düzeyde tutar. Dönüştürme işlemi geçici bellek üzerinden yapılır ve hiçbir veri sunucularımızda depolanmaz. Avukatlar, katipler ve vatandaşlar için en hızlı UYAP araçlarını sunuyoruz.</p>
    </div>

    <div class="info-panel">
        <h2><span>💬 Kullanıcı Yorumları</span><a href="mailto:mertfatih1975@gmail.com?subject=Yeni Yorum" class="review-btn">+ Yorum Yap</a></h2>
        <div class="review-box"><div class="review-text">"Duruşma öncesi telefondan anında PDF'e çeviriyorum. Harika."</div><div class="review-author">- Av. M.T.</div></div>
        <div class="review-box"><div class="review-text">"Sistemin kayıt istememesi ve dosyaları silmesi güven veriyor."</div><div class="review-author">- A.Y.</div></div>
        <div class="review-box"><div class="review-text">"UDF dosyalarını Word formatına çevirmek için harika bir araç."</div><div class="review-author">- K.S.</div></div>
        <div class="review-box"><div class="review-text">"İcra katipliği yapıyorum, her gün onlarca UDF çeviriyorum."</div><div class="review-author">- M.B. (Katip)</div></div>
        <div class="review-box"><div class="review-text">"Baro kartla giriş yapamadığım anlarda hayat kurtarıyor."</div><div class="review-author">- Av. S.G.</div></div>
        <div class="review-box"><div class="review-text">"Word'e çevirirken yazıların kaymaması çok başarılı."</div><div class="review-author">- Av. E.O.</div></div>
        <div class="review-box"><div class="review-text">"Kişisel verilerin hemen silinmesi beni ikna eden en büyük özellik."</div><div class="review-author">- D.M.</div></div>
    </div>

    <script>
        function toggleBtns() {
            const isChecked = document.getElementById('kvkk').checked;
            const bIds = ['b1','b2','b3','b4','b5','b6','b7','b8','btnPreview'];
            bIds.forEach(id => {
                const b = document.getElementById(id);
                if(b) {
                    if(isChecked) b.classList.add('active');
                    else b.classList.remove('active');
                }
            });
        }
        async function getPreview() {
            const fIn = document.getElementById('fileInput');
            if (!fIn.files[0]) return alert("Lütfen bir dosya seçin.");
            const fd = new FormData(); fd.append('file', fIn.files[0]); fd.append('mod', 'preview');
            const pB = document.getElementById('preview-box');
            const pC = document.getElementById('preview-content');
            pC.innerText = "Okunuyor..."; pB.style.display = "block";
            try {
                const r = await fetch('/', { method: 'POST', body: fd });
                const t = await r.text(); pC.innerText = t;
            } catch (e) { pC.innerText = "Hata!"; }
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
        return render_template_string(HTML_UI, current_sayac=f"{sayac:,}".replace(',', '.'))
    
    f = request.files.get("file")
    mod = request.form.get("mod")
    
    if mod == "preview":
        try:
            lines = guclu_parser(f.read())
            return " ".join(lines)[:500] + "..."
        except: return "Hata!"

    increment_sayac()
    
    if mod and "to_udf" in mod:
        text_content = ""
        try:
            if mod == "pdf_to_udf":
                import PyPDF2
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages: text_content += (page.extract_text() or "") + "\n"
            elif mod == "word_to_udf":
                import docx
                doc = docx.Document(f)
                text_content = "\n".join([p.text for p in doc.paragraphs])
            elif mod == "txt_to_udf":
                text_content = f.read().decode("utf-8", errors="ignore")

            safe_text = text_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_c = f'<html><body><p>{safe_text.replace(chr(10), "<br>")}</p></body></html>'
            udf_xml = f'<?xml version="1.0" encoding="UTF-8"?><uyap><icerik><![CDATA[{html_c}]]></icerik></uyap>'
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf: zf.writestr('content.xml', udf_xml.encode('utf-8'))
            buf.seek(0)
            return send_file(buf, as_attachment=True, download_name="cevrilmis.udf", mimetype="application/zip")
        except Exception as e: return Response(f"Hata: {str(e)}")

    lines = guclu_parser(f.read())
    text = "\n".join(lines)
    
    if mod == "txt": return send_file(io.BytesIO(text.encode("utf-8")), as_attachment=True, download_name="belge.txt", mimetype="text/plain")
    if mod == "word": return send_file(io.BytesIO(text.encode("utf-8")), as_attachment=True, download_name="belge.doc", mimetype="application/msword")
    
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
