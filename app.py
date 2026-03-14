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
    <title>UDFTOPDF | UYAP Dosya Dönüştürücü</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; flex-direction: column; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 600px; border: 1px solid #334155; box-shadow: 0 25px 50px rgba(0,0,0,0.5); margin-bottom: 20px; }
        .stats-badge { background: rgba(56, 189, 248, 0.1); color: #38bdf8; padding: 10px; border-radius: 10px; font-size: 14px; font-weight: bold; margin-bottom: 20px; border: 1px solid rgba(56, 189, 248, 0.3); }
        .trust-points { text-align: left; margin-bottom: 25px; font-size: 13px; color: #94a3b8; display: grid; gap: 8px; }
        .trust-points span { display: flex; align-items: center; gap: 8px; }
        .trust-points b { color: #f8fafc; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; opacity: 0.3; pointer-events: none; }
        button.active { opacity: 1; pointer-events: auto; }
        .pdf { background: #0ea5e9; grid-column: span 2; font-size: 16px; }
        .word { background: #2b579a; } .txt { background: #64748b; }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; border: 1px dashed #475569; padding: 15px; border-radius: 10px; cursor: pointer; }
        
        /* BİLGİ PANELLERİ */
        .info-panel { width: 600px; background: #111827; padding: 30px; border-radius: 20px; border: 1px solid #334155; margin-bottom: 20px; font-size: 14px; line-height: 1.6; color: #94a3b8; }
        .info-panel h2 { color: #38bdf8; font-size: 18px; margin-top: 0; display: flex; align-items: center; gap: 10px; }
        .info-panel b { color: #f8fafc; }
        .info-panel ul { padding-left: 20px; }
        
        .footer { margin-top: 10px; text-align: center; color: #64748b; font-size: 11px; line-height: 1.8; }
        .contact-area { margin-top: 20px; padding: 15px; border-top: 1px solid #334155; color: #94a3b8; font-size: 13px; }
        .contact-area b { color: #38bdf8; }
        h1 { color:#38bdf8; font-size: 22px; line-height: 1.4; margin-bottom: 10px; }
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

        <form id="uForm" method="POST" action="/" enctype="multipart/form-data">
            <input type="file" name="file" id="fIn" accept=".udf" required>
            <label style="margin: 20px 0; font-size: 12px; display: block; cursor: pointer;">
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
            <li><b>Çıkış:</b> PDF (Editable veya Visual), Word, TXT</li>
        </ul>
        
        <h2>🔄 Nasıl Çalışır?</h2>
        <ol>
            <li><b>Dosyayı yükleyin:</b> UYAP'tan indirdiğiniz .udf dosyasını seçin.</li>
            <li><b>Format seçin:</b> PDF, Word veya TXT seçeneklerinden birini belirleyin.</li>
            <li><b>Dönüştür ve İndirin:</b> İşlem saniyeler içinde tamamlanır ve dosyanız hazır olur.</li>
        </ol>
    </div>

    <div class="info-panel">
        <h2>⚖️ UDF Nedir? UYAP Doküman Formatı</h2>
        <p>
            <b>UDF dosyası (UYAP Doküman Formatı)</b>, Türkiye'de mahkemeler ve avukatlar tarafından UYAP üzerinden oluşturulan resmi belge formatıdır. 
            Dava dilekçeleri ve mahkeme kararları gibi tüm hukuki yazışmalar bu formatla kaydedilir.
        </p>
        <p>
            <b>UDF dosyası nasıl açılır?</b> Standart bir dosya olmadığından Word veya Adobe Reader ile doğrudan açılamaz. 
            Bu <b>UDF çevirici</b> araç, dosyalarınızı herkesin açabileceği PDF formatına saniyeler içinde dönüştürür.
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
