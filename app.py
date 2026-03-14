import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

app = Flask(__name__)

# --- ALTYAPI: TÜRKÇE KARAKTER DESTEĞİ ---
try:
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

def udf_motoru(data):
    try:
        # UDF'nin içindeki zlib bloğunu milimetrik bulma
        start_tag, end_tag = b"<content>", b"</content>"
        s, e = data.find(start_tag), data.find(end_tag)
        if s == -1 or e == -1: return ["Hata: UDF yapısı çözülemedi."]
        
        # Zlib katmanını soy
        xml_ham = zlib.decompress(data[s+9:e])
        root = ET.fromstring(xml_ham)
        
        # Tüm metin parçalarını hiyerarşik topla
        lines = [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
        return lines if lines else ["Hata: Dosya içeriği boş."]
    except Exception as ex:
        return [f"İşleme Hatası: {str(ex)}"]

HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>UDF Pro v10.0 | Ofis Gökçadır</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 450px; border: 1px solid #334155; box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
        .badge { background: #064e3b; color: #6ee7b7; padding: 15px; border-radius: 12px; font-size: 13px; margin-bottom: 25px; border: 1px solid #059669; }
        .progress-box { display: none; margin: 20px 0; }
        .progress-bar { width: 100%; background: #334155; border-radius: 10px; height: 12px; position: relative; }
        .progress-fill { width: 0%; height: 100%; background: #0ea5e9; border-radius: 10px; transition: width 0.2s; }
        .btn-group { display: grid; grid-template-columns: 1fr; gap: 12px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; font-size: 14px; }
        .pdf { background: #0ea5e9; } .word { background: #2b579a; } .txt { background: #64748b; }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; cursor: pointer; }
    </style>
</head>
<body>
    <div class="box">
        <h1 style="color:#38bdf8; margin:0 0 10px 0;">UDF PRO <span style="color:white">v10.0</span></h1>
        <div class="badge">🛡️ <b>KVKK VE GÜVENLİK:</b> Verileriniz kaydedilmez, sadece işlenir.</div>
        
        <form id="mainForm" method="POST" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" accept=".udf" required>
            
            <div id="progressContainer" class="progress-box">
                <div class="progress-bar"><div id="progressFill" class="progress-fill"></div></div>
                <p id="status" style="font-size:12px; margin-top:8px; color:#38bdf8;">Hazırlanıyor...</p>
            </div>

            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" class="pdf" onclick="startProcess()">PRO PDF OLARAK DÖNÜŞTÜR</button>
                <button type="submit" name="mod" value="word" class="word" onclick="startProcess()">PRO WORD (DOC) OLARAK DÖNÜŞTÜR</button>
                <button type="submit" name="mod" value="txt" class="txt" onclick="startProcess()">HIZLI TEXT OLARAK DÖNÜŞTÜR</button>
            </div>
        </form>
        <p style="font-size:10px; color:#475569; margin-top:30px">© 2026 FATİH MERT | BURSA</p>
    </div>

    <script>
        function startProcess() {
            if (document.getElementById('fileInput').files.length === 0) return;
            document.getElementById('progressContainer').style.display = 'block';
            let fill = document.getElementById('progressFill');
            let status = document.getElementById('status');
            let w = 0;
            let interval = setInterval(() => {
                w += (100 - w) * 0.1; // Logaritmik artış (asla 100'e takılmaz)
                fill.style.width = w + '%';
                status.innerText = 'Dönüştürülüyor: %' + Math.floor(w);
                if (w > 99) clearInterval(interval);
            }, 150);
            
            // Dosya indikten sonra barı sıfırla (Kullanıcı yeni dosya atabilsin)
            setTimeout(() => { 
                status.innerText = 'Dosya İndiriliyor...';
            }, 2000);
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def handle():
    if request.method == 'GET':
        return render_template_string(HTML_UI)
    
    f = request.files.get('file')
    mod = request.form.get('mod')
    
    # DOSYA OKUMA VE HATA AYIKLAMA
    raw_data = f.read()
    lines = udf_motoru(raw_data)
    
    # "UDF içeriği bulunamadı" hatası alıyorsan, listeyi kontrol et
    if not lines or "Hata" in lines[0]:
        text = "Hata: Sectiginiz UDF dosyasi uyumlu degil veya bos."
    else:
        text = "\\n".join(lines)

    # FORMAT SEÇİMİ (KESİN AYRIM)
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
