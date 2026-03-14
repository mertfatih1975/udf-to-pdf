import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

app = Flask(__name__)

# Font kaydı (arial.ttf deponuzda yüklü olmalı)
try:
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>UDF Pro v3.5 | Guvenli Donusturucu</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 40px; border-radius: 15px; text-align: center; width: 420px; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
        .security-note { background: #064e3b; color: #6ee7b7; padding: 10px; border-radius: 8px; font-size: 13px; margin-bottom: 20px; border: 1px solid #059669; }
        .progress-container { width: 100%; background: #334155; border-radius: 10px; margin: 20px 0; display: none; }
        .progress-bar { width: 0%; height: 10px; background: #0ea5e9; border-radius: 10px; transition: width 0.3s; }
        button { border: none; padding: 12px; border-radius: 8px; cursor: pointer; font-weight: bold; margin: 5px; width: 45%; transition: 0.3s; }
        .pro { background: #0ea5e9; color: white; }
        .fast { background: #64748b; color: white; }
        .kvkk-link { margin-top: 25px; font-size: 12px; color: #94a3b8; cursor: pointer; text-decoration: underline; }
        /* Modal Stili */
        #kvkkModal { display: none; position: fixed; z-index: 1; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); }
        .modal-content { background: #1e293b; margin: 10% auto; padding: 20px; border: 1px solid #334155; width: 60%; border-radius: 10px; font-size: 14px; line-height: 1.6; max-height: 70vh; overflow-y: auto; }
        .close { color: #aaa; float: right; font-size: 28px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="box">
        <h2>UDF PRO <span style="color:#0ea5e9">GÜVENLİ</span></h2>
        
        <div class="security-note">
            🛡️ <b>Gizlilik Bildirimi:</b> Dosyalarınız hiçbir şekilde kaydedilmez. İşlem doğrudan bellek üzerinde (RAM) yapılır ve sonuç iletildikten sonra silinir.
        </div>

        <form id="uForm" method="post" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" accept=".udf" required style="margin-bottom:20px; color:#94a3b8">
            <div class="progress-container" id="pCont"><div class="progress-bar" id="pBar"></div></div>
            <div style="display:flex; justify-content: space-between;">
                <button type="submit" onclick="startProcess('/convert/fast')" class="fast">HIZLI (TXT)</button>
                <button type="submit" onclick="startProcess('/convert/pro')" class="pro">PRO (PDF)</button>
            </div>
        </form>
        
        <div class="kvkk-link" onclick="openModal()">KVKK ve Veri Güvenliği Aydınlatma Metni</div>
        <p style="font-size:10px; color:#475569; margin-top:20px">FATİH MERT | BURSA 2026</p>
    </div>

    <div id="kvkkModal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h3 style="color:#0ea5e9">KVKK Aydınlatma Metni</h3>
            <p>1. Bu sistem, yüklenen UDF dosyalarını anlık olarak işlemek üzere tasarlanmıştır.<br>
            2. <b>Veri Saklanmaması:</b> Sunucularımızda hiçbir kullanıcı dosyası veya kişisel veri yedeklenmemekte, depolanmamakta veya üçüncü taraflarla paylaşılmamaktadır.<br>
            3. <b>İşlem Güvenliği:</b> Dönüştürme işlemi geçici RAM bellekte gerçekleşir. Tarayıcıya dosya gönderildiği an işlem sonlandırılır.<br>
            4. Bu hizmeti kullanarak, verilerinizin anlık işlenmesini kabul etmiş sayılırsınız.</p>
        </div>
    </div>

    <script>
        function startProcess(path) {
            const file = document.getElementById('fileInput').files[0];
            if(!file) return;
            document.getElementById('uForm').action = path;
            document.getElementById('pCont').style.display = 'block';
            let width = 0;
            const interval = setInterval(() => {
                if (width >= 90) clearInterval(interval);
                width += 10;
                document.getElementById('pBar').style.width = width + '%';
            }, 200);
        }
        function openModal() { document.getElementById('kvkkModal').style.display = "block"; }
        function closeModal() { document.getElementById('kvkkModal').style.display = "none"; }
    </script>
</body>
</html>
"""

def get_text(data):
    try:
        s = data.find(b"<content>") + 9
        e = data.find(b"</content>")
        xml = zlib.decompress(data[s:e])
        root = ET.fromstring(xml)
        return "".join([c.text for c in root.iter('content') if c.text])
    except: return "Hata: Dosya formatı uyumsuz."

@app.route('/')
def home(): return HTML_UI

@app.route('/convert/fast', methods=['POST'])
def fast():
    f = request.files['file']
    t = get_text(f.read())
    buf = io.BytesIO(text.encode('utf-8')) # Not: text degiskeni t olmali
    buf = io.BytesIO(t.encode('utf-8'))
    return send_file(buf, as_attachment=True, download_name="belge.txt")

@app.route('/convert/pro', methods=['POST'])
def pro():
    f = request.files['file']
    t = get_text(f.read())
    buf = io.BytesIO()
    p = canvas.Canvas(buf)
    obj = p.beginText(50, 800)
    obj.setFont(FONT_NAME, 10)
    for line in t.split('\n'):
        obj.textLine(line)
    p.drawText(obj)
    p.showPage()
    p.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="profesyonel.pdf")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
