import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

app = Flask(__name__)

# --- FONT ALTYAPISI ---
try:
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

# --- UDF ÇÖZÜCÜ MOTOR ---
def udf_cozucu(data):
    try:
        s = data.find(b"<content>") + 9
        e = data.find(b"</content>")
        if s < 9 or e == -1: return ["Hata: UDF içerik yapısı uyumsuz."]
        xml = zlib.decompress(data[s:e])
        root = ET.fromstring(xml)
        return [c.text.strip() for c in root.iter() if c.text and c.text.strip()]
    except:
        return ["Hata: Dosya işlenemedi."]

# --- SEO VE GÜVENLİK ODAKLI HTML ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>En Hızlı UDF Dönüştürücü | PDF, Word, TXT | Ücretsiz & Güvenli</title>
    <meta name="description" content="UYAP UDF dosyalarını anında PDF, Word ve TXT formatına dönüştürün. Dosyalarınız saklanmaz, %100 güvenli ve KVKK uyumludur.">
    <meta name="keywords" content="udf dönüştür, udf pdf yapma, udf word çevir, uyap dosya açma, güvenli udf dönüştürücü">
    
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 450px; border: 1px solid #334155; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }
        .secure-badge { background: #064e3b; color: #6ee7b7; padding: 12px; border-radius: 10px; font-size: 13px; margin-bottom: 20px; border: 1px solid #059669; }
        .btn-group { display: grid; grid-template-columns: 1fr; gap: 10px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; font-size: 14px; }
        .pro { background: #0ea5e9; } .pro:hover { background: #0284c7; }
        .word { background: #2b579a; } .word:hover { background: #1e3a63; }
        .fast { background: #64748b; } .fast:hover { background: #475569; }
        input[type="file"] { margin-bottom: 25px; color: #94a3b8; width: 100%; border: 1px dashed #334155; padding: 10px; border-radius: 10px; }
        .kvkk { margin-top: 25px; font-size: 11px; color: #475569; cursor: pointer; text-decoration: underline; }
    </style>
</head>
<body>
    <div class="box">
        <h1 style="font-size:24px; color:#38bdf8; margin-bottom:5px;">UDF PRO <span style="color:white">Dönüştürücü</span></h1>
        <p style="color:#94a3b8; font-size:14px; margin-bottom:20px;">Bursa Ofis Gökçadır Güvencesiyle</p>
        
        <div class="secure-badge">
            🛡️ <b>GİZLİLİK GARANTİSİ:</b> Dosyalarınız asla sunucuda saklanmaz. İşlem bittiği an bellekten (RAM) kalıcı olarak silinir.
        </div>

        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept=".udf" required>
            <div class="btn-group">
                <button type="submit" name="mode" value="pdf" class="pro">PRO PDF OLARAK İNDİR</button>
                <button type="submit" name="mode" value="word" class="word">WORD (DOCX) OLARAK İNDİR</button>
                <button type="submit" name="mode" value="txt" class="fast">HIZLI METİN (TXT) OLARAK İNDİR</button>
            </div>
        </form>

        <div class="kvkk" onclick="alert('KVKK AYDINLATMA METNİ:\\n1. Verileriniz işlenirken kaydedilmez.\\n2. Üçüncü taraflarla paylaşılmaz.\\n3. Sadece dönüştürme amacıyla anlık RAM kullanımı yapılır.')">
            KVKK ve Veri Güvenliği Metni
        </div>
        <p style="font-size:10px; color:#334155; margin-top:20px">© 2026 FATİH MERT | BURSA</p>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template_string(HTML_UI)
    
    if 'file' not in request.files: return "Dosya seçilmedi", 400
    file = request.files['file']
    mode = request.form.get('mode')
    lines = udf_cozucu(file.read())
    
    if mode == 'txt':
        text = "\\n".join(lines)
        buf = io.BytesIO(text.encode('utf-8'))
        return send_file(buf, as_attachment=True, download_name="belge.txt", mimetype='text/plain')
    
    elif mode == 'word':
        # Word dosyası aslında düz metin içeren bir yapıya büründürülebilir (basit sürüm)
        text = "\\n".join(lines)
        buf = io.BytesIO(text.encode('utf-8'))
        return send_file(buf, as_attachment=True, download_name="belge.doc", mimetype='application/msword')

    else: # PDF Modu
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
