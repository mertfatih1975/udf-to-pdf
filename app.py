import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

app = Flask(__name__)

# --- ALTYAPI ---
try:
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

def udf_motoru(data):
    try:
        start_tag, end_tag = b"<content>", b"</content>"
        s, e = data.find(start_tag), data.find(end_tag)
        if s == -1 or e == -1: return ["Hata: Geçersiz UDF formatı."]
        xml_ham = zlib.decompress(data[s+len(start_tag):e])
        root = ET.fromstring(xml_ham)
        return [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
    except: return ["İşleme hatası oluştu."]

# --- GELİŞMİŞ ARAYÜZ (SEO + PROGRESS BAR + KVKK) ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF Pro | Hızlı PDF, Word ve TXT Dönüştürücü</title>
    <meta name="description" content="UYAP UDF dosyalarını saklamadan, güvenle PDF, Word ve TXT'ye dönüştürün. %100 KVKK uyumlu ve ücretsiz.">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 450px; border: 1px solid #334155; box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
        .badge { background: #064e3b; color: #6ee7b7; padding: 15px; border-radius: 12px; font-size: 13px; margin-bottom: 25px; border: 1px solid #059669; line-height: 1.5; }
        .progress-container { display: none; margin: 20px 0; background: #334155; border-radius: 10px; height: 10px; overflow: hidden; }
        .progress-bar { width: 0%; height: 100%; background: #38bdf8; transition: width 0.3s; }
        .btn-group { display: grid; grid-template-columns: 1fr; gap: 12px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; font-size: 14px; }
        .pdf { background: #0ea5e9; } .word { background: #2b579a; } .txt { background: #64748b; }
        button:hover { filter: brightness(1.2); transform: scale(1.02); }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; border: 1px dashed #475569; padding: 15px; border-radius: 10px; cursor: pointer; }
        .kvkk-link { margin-top: 25px; font-size: 11px; color: #94a3b8; cursor: pointer; text-decoration: underline; opacity: 0.7; }
    </style>
</head>
<body>
    <div class="box">
        <h1 style="color:#38bdf8; margin:0 0 10px 0;">UDF PRO <span style="color:white">DÖNÜŞTÜRÜCÜ</span></h1>
        
        <div class="badge">
            <b>🛡️ GİZLİLİK VE VERİ GÜVENLİĞİ:</b><br>
            Yüklediğiniz dosyalar sunucularımızda <u>asla saklanmaz</u>. Verileriniz sadece anlık olarak işlenir ve tarayıcınıza gönderildiği an bellekten silinir.
        </div>

        <form id="uploadForm" method="POST" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" accept=".udf" required>
            
            <div id="progressArea" class="progress-container">
                <div id="progressBar" class="progress-bar"></div>
            </div>
            <div id="statusText" style="font-size:12px; color:#38bdf8; margin-bottom:10px; display:none;">İşleniyor: %0</div>

            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" class="pdf">PRO PDF OLARAK DÖNÜŞTÜR</button>
                <button type="submit" name="mod" value="word" class="word">PRO WORD (DOC) OLARAK DÖNÜŞTÜR</button>
                <button type="submit" name="mod" value="txt" class="txt">HIZLI METİN (TEXT) OLARAK DÖNÜŞTÜR</button>
            </div>
        </form>

        <div class="kvkk-link" onclick="document.getElementById('kvkkModal').style.display='block'">KVKK Aydınlatma Metni</div>
        <p style="font-size:10px; color:#475569; margin-top:20px">© 2026 FATİH MERT | Ofis Gökçadır - BURSA</p>
    </div>

    <div id="kvkkModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:100;">
        <div style="background:#1e293b; width:80%; max-width:500px; margin:10% auto; padding:30px; border-radius:20px; border:1px solid #334155;">
            <h3>KVKK Aydınlatma Metni</h3>
            <p style="font-size:14px; line-height:1.6; color:#94a3b8;">
                Bu uygulama, 6698 sayılı KVKK kapsamında veri sorumlusu sıfatı taşımadan çalışır. Yüklenen .udf uzantılı dosyalar herhangi bir veri tabanına kaydedilmez, depolanmaz ve üçüncü taraflarla paylaşılmaz. İşlem tamamen RAM (bellek) üzerinde anlık olarak gerçekleştirilir.
            </p>
            <button onclick="document.getElementById('kvkkModal').style.display='none'" style="background:#0ea5e9; width:100%;">ANLADIM</button>
        </div>
    </div>

    <script>
        document.getElementById('uploadForm').onsubmit = function() {
            var progressBar = document.getElementById('progressBar');
            var progressArea = document.getElementById('progressArea');
            var statusText = document.getElementById('statusText');
            
            progressArea.style.display = 'block';
            statusText.style.display = 'block';
            
            var width = 0;
            var interval = setInterval(function() {
                if (width >= 95) {
                    clearInterval(interval);
                } else {
                    width += 5;
                    progressBar.style.width = width + '%';
                    statusText.innerHTML = 'İşleniyor: %' + width;
                }
            }, 100);
        };
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template_string(HTML_UI)
    
    f = request.files['file']
    mod = request.form.get('mod')
    lines = udf_motoru(f.read())
    text = "\\n".join(lines)

    # Dosya indirme başlığını "Soru Sormaya" zorlayacak şekilde ayarla
    response_headers = {
        'Content-Disposition': f'attachment; filename="donusturuldu_belge.{mod}"',
        'Cache-Control': 'no-cache, no-store, must-revalidate'
    }

    if mod == 'txt':
        return send_file(io.BytesIO(text.encode('utf-8')), as_attachment=True, download_name="belge.txt", mimetype='text/plain')
    
    elif mod == 'word':
        return send_file(io.BytesIO(text.encode('utf-8')), as_attachment=True, download_name="belge.doc", mimetype='application/msword')

    else: # PDF
        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        y = 800
        c.setFont(FONT_NAME, 10)
        for line in lines:
            if y < 50: c.showPage(); c.setFont(FONT_NAME, 10); y = 800
            c.drawString(50, y, line[:95])
            y -= 15
        c.save()
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name="belge.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
