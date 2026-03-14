import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
import io

app = Flask(__name__)

# --- ALTYAPI: FONT ---
try:
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

def udf_motoru(data):
    try:
        # UDF dosyasının kalbindeki sıkıştırılmış bloğu bul
        start_tag = b"<content>"
        end_tag = b"</content>"
        s = data.find(start_tag)
        e = data.find(end_tag)
        
        if s == -1 or e == -1:
            return ["HATA: Dosya standart UYAP UDF formatında değil veya kilitli."]

        # Zlib katmanını soy ve XML'i aç
        xml_raw = zlib.decompress(data[s+9:e])
        root = ET.fromstring(xml_raw)
        
        # Metinleri çek
        lines = []
        for elem in root.iter():
            if elem.text and elem.text.strip():
                lines.append(elem.text.strip())
        
        return lines if lines else ["HATA: Dosya boş veya okunabilir metin içermiyor."]
    except Exception as ex:
        return [f"TEKNİK HATA: {str(ex)}"]

# --- FULL ARAYÜZ (BAR + KVKK + FORMATLAR) ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF Pro v11.0 | Ofis Gökçadır Güvenli Dönüştürücü</title>
    <meta name="description" content="UYAP UDF dosyalarınızı saklamadan PDF, Word ve TXT'ye dönüştürün.">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 450px; border: 1px solid #334155; box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
        .badge { background: #064e3b; color: #6ee7b7; padding: 15px; border-radius: 12px; font-size: 13px; margin-bottom: 25px; border: 1px solid #059669; }
        .progress-box { display: none; margin: 20px 0; }
        .bar-bg { width: 100%; background: #334155; border-radius: 10px; height: 12px; overflow: hidden; }
        .bar-fill { width: 0%; height: 100%; background: #0ea5e9; transition: width 0.1s; }
        .btn-group { display: flex; flex-direction: column; gap: 12px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; font-size: 14px; transition: 0.3s; }
        .pdf { background: #0ea5e9; } .word { background: #2b579a; } .txt { background: #64748b; }
        button:hover { filter: brightness(1.2); transform: scale(1.01); }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; cursor: pointer; border: 1px dashed #475569; padding: 10px; border-radius: 10px; }
        .kvkk-info { margin-top: 25px; font-size: 11px; color: #94a3b8; cursor: pointer; text-decoration: underline; }
    </style>
</head>
<body>
    <div class="box">
        <h1 style="color:#38bdf8; margin:0 0 10px 0;">UDF PRO <span style="color:white">v11.0</span></h1>
        <div class="badge">🛡️ <b>GİZLİLİK:</b> Dosyalarınız saklanmaz, sadece RAM'de işlenir ve anında silinir.</div>
        
        <form id="uForm" method="POST" enctype="multipart/form-data">
            <input type="file" name="file" id="fIn" accept=".udf" required>
            
            <div id="pBox" class="progress-box">
                <div class="bar-bg"><div id="bFill" class="bar-fill"></div></div>
                <p id="pStat" style="font-size:12px; margin-top:8px; color:#38bdf8;">İşleniyor: %0</p>
            </div>

            <div class="btn-group">
                <button type="submit" name="m" value="pdf" class="pdf" onclick="go()">PRO PDF OLARAK DÖNÜŞTÜR</button>
                <button type="submit" name="m" value="word" class="word" onclick="go()">PRO WORD (DOC) OLARAK DÖNÜŞTÜR</button>
                <button type="submit" name="m" value="txt" class="txt" onclick="go()">HIZLI TEXT OLARAK DÖNÜŞTÜR</button>
            </div>
        </form>

        <div class="kvkk-info" onclick="alert('KVKK Metni: Verileriniz hiçbir şekilde kaydedilmez veya paylaşılmaz. İşlem bitince bellekten silinir.')">KVKK ve Güvenlik Metni</div>
        <p style="font-size:10px; color:#475569; margin-top:30px">© 2026 FATİH MERT | BURSA</p>
    </div>

    <script>
        function go() {
            if (document.getElementById('fIn').files.length === 0) return;
            document.getElementById('pBox').style.display = 'block';
            let f = document.getElementById('bFill');
            let s = document.getElementById('pStat');
            let val = 0;
            let int = setInterval(() => {
                val += (98 - val) * 0.1;
                f.style.width = val + '%';
                s.innerText = 'Dönüştürülüyor: %' + Math.floor(val);
                if (val > 97) clearInterval(int);
            }, 100);
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template_string(HTML_UI)
    
    file = request.files.get('file')
    mod = request.form.get('m')
    lines = udf_motoru(file.read())
    
    # Hata kontrolü
    if any("HATA" in str(line) for line in lines):
        # Eğer hata varsa PDF olarak hata mesajını indir
        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(50, 800, lines[0])
        c.save()
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name="hata_raporu.pdf")

    text = "\\n".join(lines)

    if mod == 'txt':
        return send_file(io.BytesIO(text.encode('utf-8')), as_attachment=True, download_name="belge.txt", mimetype='text/plain')
    elif mod == 'word':
        return send_file(io.BytesIO(text.encode('utf-8')), as_attachment=True, download_name="belge.doc", mimetype='application/msword')
    else: # PDF
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
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
