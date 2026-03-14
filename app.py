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

# --- GÜVENLİK: HTTP -> HTTPS YÖNLENDİRMESİ ---
@app.before_request
def redirect_to_https():
    if request.headers.get('X-Forwarded-Proto', 'http') == 'http':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

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
    <meta name="description" content="UDF dosyalarını ücretsiz PDF ve Word formatına dönüştürün. UYAP Doküman Formatı çevirici.">
    <title>UDFTOPDF | UYAP Dosya Dönüştürücü</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; flex-direction: column; align-items: center; min-height: 100vh; margin: 0; padding: 30px 20px; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 600px; border: 1px solid #334155; box-shadow: 0 25px 50px rgba(0,0,0,0.5); margin-bottom: 30px; }
        .stats-badge { background: rgba(56, 189, 248, 0.1); color: #38bdf8; padding: 12px; border-radius: 10px; font-size: 15px; font-weight: bold; margin-bottom: 25px; border: 1px solid rgba(56, 189, 248, 0.3); }
        .trust-points { text-align: left; margin-bottom: 25px; font-size: 14px; color: #94a3b8; display: grid; gap: 10px; }
        .trust-points span { display: flex; align-items: center; gap: 8px; }
        .trust-points b { color: #f8fafc; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; opacity: 0.3; pointer-events: none; }
        button.active { opacity: 1; pointer-events: auto; }
        .pdf { background: #0ea5e9; grid-column: span 2; font-size: 16px; }
        .word { background: #2b579a; } .txt { background: #64748b; }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; border: 1px dashed #475569; padding: 15px; border-radius: 10px; cursor: pointer; box-sizing: border-box; }
        
        /* GÜVENLİK BADGE */
        .security-badge { background: rgba(6, 78, 59, 0.4); color: #6ee7b7; padding: 15px; border-radius: 12px; font-size: 13px; margin-bottom: 25px; border: 1px solid #059669; text-align: left; line-height: 1.5; }
        
        /* BİLGİ PANELLERİ (SEO METİNLERİ) */
        .info-panel { width: 600px; background: #111827; padding: 35px; border-radius: 20px; border: 1px solid #334155; margin-bottom: 20px; font-size: 15px; line-height: 1.7; color: #94a3b8; box-sizing: border-box; text-align: left; }
        .info-panel h2 { color: #38bdf8; font-size: 20px; margin-top: 0; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #1e293b; padding-bottom: 10px; }
        .info-panel h3 { color: #e2e8f0; font-size: 18px; margin-top: 25px; margin-bottom: 10px; }
        .info-panel b { color: #f8fafc; }
        .info-panel ul, .info-panel ol { padding-left: 20px; margin-bottom: 20px; }
        .info-panel li { margin-bottom: 8px; }
        .info-panel p { margin-bottom: 15px; }
        
        .footer { margin-top: 20px; text-align: center; color: #64748b; font-size: 12px; line-height: 1.8; }
        .contact-area { margin-top: 25px; padding: 15px; border-top: 1px solid #334155; color: #94a3b8; font-size: 14px; }
        .contact-area b { color: #38bdf8; }
        h1 { color:#38bdf8; font-size: 24px; line-height: 1.4; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>Uyap Uzantılı Dosyalarınızı<br>Güvenle Dönüştürebilirsiniz</h1>
        
        <div class="stats-badge">🚀 Toplam 11.535 dönüştürme başarıyla tamamlandı.</div>

        <div class="trust-points">
            <span>✅ <b>Güvenli:</b> Dosyalarınız işlem sonrası otomatik olarak silinir.</span>
            <span>✅ <b>Ücretsiz:</b> Hiçbir ücret veya kayıt gerektirmez.</span>
            <span>✅ <b>Hızlı:</b> Saniyeler içinde dönüştürme işlemi tamamlanır.</span>
        </div>

        <div class="security-badge">
            🔒 <b>Sevgili Kullanıcımız;</b> Sunucularımızda hiçbir dosyanız depolanmaz. Verileriniz yalnızca dönüştürme esnasında anlık olarak işlenir ve işlem biter bitmez kalıcı olarak silinir.
        </div>

        <form id="uForm" method="POST" action="/" enctype="multipart/form-data">
            <input type="file" name="file" id="fIn" accept=".udf" required>
            <label style="margin: 20px 0; font-size: 13px; display: block; cursor: pointer; text-align: center;">
                <input type="checkbox" id="kvkk" onchange="toggleBtns()"> KVKK Aydınlatma Metnini okudum ve onaylıyorum.
            </label>
            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" id="btnPdf" class="pdf">PDF OLARAK DÖNÜŞTÜR</button>
                <button type="submit" name="mod" value="word" id="btnWord" class="word">WORD YAP</button>
                <button type="submit" name="mod" value="txt" id="btnTxt" class="txt">TXT YAP</button>
            </div>
        </form>
        
        <div class="contact-area">
            🤝 <b>Reklam ve İşbirliği:</b><br>
            mertfatih1975@gmail.com | 0532 764 16 61
        </div>
    </div>

    <div class="info-panel">
        <h2>📋 Desteklenen Formatlar</h2>
        <ul>
            <li><b>Giriş:</b> .udf (UYAP Doküman Formatı)</li>
            <li><b>Çıkış:</b> PDF (Editable veya Visual), Word (.doc), Metin (.txt)</li>
        </ul>
        
        <h2>🔄 Nasıl Çalışır?</h2>
        <ol>
            <li><b>Dosyayı yükleyin:</b> Dönüştürmek istediğiniz dosyayı seçin.</li>
            <li><b>Format seçin (PDF/Word):</b> İhtiyacınıza uygun çıktı formatını belirleyin.</li>
            <li><b>Modu belirleyin:</b> Gerekli çeviri modunu ayarlayın.</li>
            <li><b>Dönüştür ve indirin:</b> İşlemi başlatın ve saniyeler içinde belgenizi alın.</li>
        </ol>

        <h2>⚖️ UDF Nedir? UYAP Doküman Formatı</h2>
        <p>
            <b>UDF dosyası (UYAP Doküman Formatı)</b>, Türkiye'de mahkemeler ve avukatlar tarafından UYAP (Ulusal Yargı Ağı Bilişim Sistemi) üzerinden oluşturulan belge formatıdır. Dava dilekçeleri, mahkeme kararları ve resmi hukuki yazışmalar <b>.udf uzantılı</b> dosyalar olarak kaydedilmektedir.
        </p>
        <p>
            <b>UDF dosyası nasıl açılır?</b> sorusu avukatlar ve vatandaşlar tarafından sıkça sorulmaktadır. Standart belgelerden farklı olduğundan Adobe Reader veya Microsoft Word ile doğrudan açılamaz. Bu <b>UDF çevirici</b> araç, UDF dosyalarınızı PDF formatına dönüştürerek erişilebilir hale getirir.
        </p>

        <h3>📄 UDF PDF Dönüştürme – Nasıl Yapılır?</h3>
        <p>UDF'den PDF'ye dönüştürme işlemi bu araç ile oldukça kolaydır:</p>
        <ul>
            <li>UYAP üzerinden indirdiğiniz <b>.udf dosyasını</b> yükleme alanına sürükleyin.</li>
            <li><b>PDF formatını</b> seçin.</li>
            <li>Düzenlenebilir metin veya görsel mod tercihini yapın.</li>
            <li>Dönüştür butonuna tıklayın ve PDF'yi indirin.</li>
        </ul>
        <p>
            <b>UDF dönüştürücü</b> aracımız, avukatlar, hakimler, savcılar ve adli işlerle ilgilenen her kullanıcı için tasarlanmıştır. <b>UYAP UDF belge dönüştürme</b> işlemi ücretsiz ve kayıtsız kullanılabilir.
        </p>
    </div>

    <div class="footer">
        🛡️ SSL Güvenli Bağlantı | İstanbul - Türkiye | 🕒 {{ current_time }}<br>
        © {{ current_year }} UDFTOPDF - Tüm Hakları Saklıdır.
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
    
    if request.method == "GET":
        resp = make_response(render_template_string(HTML_UI, current_time=now.strftime("%H:%M"), current_year=now.year))
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
