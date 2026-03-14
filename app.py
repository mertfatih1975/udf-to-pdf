import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string, Response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io

app = Flask(__name__)

# --- SEO YOLLARI ---
SEO_PAGES = ["udf-to-pdf", "udf-to-word", "udf-to-txt", "uyap-udf-donusturucu"]

# --- GÜÇLÜ PARSER (ESNEK YAPI) ---
def guclu_parser(data):
    try:
        s, e = data.find(b"<content>"), data.find(b"</content>")
        if s != -1 and e != -1:
            raw_xml = zlib.decompress(data[s+9:e])
        else:
            zlib_start = data.find(b'\x78\x9c')
            if zlib_start != -1:
                raw_xml = zlib.decompress(data[zlib_start:])
            else: return ["Hata: UDF verisi ayrıştırılamadı."]
        root = ET.fromstring(raw_xml)
        return [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
    except Exception as ex:
        return [f"Parser Hatası: {str(ex)}"]

# --- PROFESYONEL ARAYÜZ ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF Pro Elite | Güvenli UYAP Dönüştürme Sistemi</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 480px; border: 1px solid #334155; box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
        .security-badge { background: rgba(6, 78, 59, 0.4); color: #6ee7b7; padding: 18px; border-radius: 12px; font-size: 13.5px; margin-bottom: 25px; border: 1px solid #059669; line-height: 1.6; text-align: left; }
        .progress-container { display: none; margin: 20px 0; background: #334155; border-radius: 10px; height: 12px; overflow: hidden; }
        .progress-bar { width: 0%; height: 100%; background: linear-gradient(90deg, #38bdf8, #818cf8); transition: width 0.2s; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: 600; color: white; transition: 0.3s; font-size: 14px; }
        .pdf { background: #0ea5e9; grid-column: span 2; font-size: 16px; }
        .word { background: #2b579a; } .txt { background: #64748b; }
        button:hover { filter: brightness(1.2); transform: translateY(-2px); }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; cursor: pointer; border: 1px dashed #475569; padding: 15px; border-radius: 10px; }
        .kvkk-link { margin-top: 30px; font-size: 12px; color: #94a3b8; text-decoration: underline; cursor: pointer; opacity: 0.8; }
        .kvkk-link:hover { color: #38bdf8; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="color:#38bdf8; margin:0 0 15px 0; letter-spacing: 1px;">UDF PRO <span style="color:white">ELITE</span></h2>
        
        <div class="security-badge">
            🔒 <b>Kurumsal Güvenlik Protokolü:</b><br>
            Sistemimiz "Sıfır Kayıt" prensibiyle çalışmaktadır. Yüklenen belgeler uçtan uca şifreli olarak işlenir, sunucu üzerinde depolanmaz ve işlem tamamlandığında bellekten (RAM) kalıcı olarak silinir.
        </div>
        
        <form id="uForm" method="POST" action="/" enctype="multipart/form-data">
            <input type="file" name="file" id="fIn" accept=".udf" required>
            
            <div id="pCont" class="progress-container"><div id="pBar" class="progress-bar"></div></div>
            <p id="pPerc" style="display:none; color:#38bdf8; font-size:12px; margin-bottom:15px; font-weight:bold;">%0 İşleniyor...</p>

            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" class="pdf" onclick="run()">PRO PDF OLARAK DÖNÜŞTÜR</button>
                <button type="submit" name="mod" value="word" class="word" onclick="run()">PRO WORD (DOC)</button>
                <button type="submit" name="mod" value="txt" class="txt" onclick="run()">HIZLI TEXT (TXT)</button>
            </div>
        </form>

        <div class="kvkk-link" onclick="document.getElementById('kvkkModal').style.display='block'">KVKK Aydınlatma Metni ve Gizlilik Bildirimi</div>
        <p style="font-size:10px; color:#475569; margin-top:25px">© 2026 FATİH MERT | BURSA | Ofis Gökçadır</p>
    </div>

    <div id="kvkkModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:1000; overflow-y: auto;">
        <div style="background:#1e293b; width:90%; max-width:600px; margin:50px auto; padding:35px; border-radius:20px; border:1px solid #334155; text-align: left;">
            <h3 style="color:#38bdf8; margin-top:0;">KVKK Aydınlatma Metni</h3>
            <p style="font-size:13px; line-height:1.7; color:#cbd5e1;">
                6698 sayılı Kişisel Verilerin Korunması Kanunu ("KVKK") uyarınca, bu platform üzerinden gerçekleştirilen işlemler "anlık veri işleme" statüsündedir. <br><br>
                <b>1. Veri İşleme Amacı:</b> Sadece kullanıcı tarafından yüklenen .udf formatındaki belgelerin PDF, Word veya TXT formatına dönüştürülmesi.<br>
                <b>2. Depolama:</b> İşlenen veriler hiçbir veri tabanına veya fiziksel sürücüye kaydedilmez. İşlem tamamlandığında oturum sonlandırılır.<br>
                <b>3. Veri Aktarımı:</b> Verileriniz üçüncü şahıs veya kurumlarla paylaşılmaz.<br>
                <b>4. Kullanıcı Onayı:</b> Belge yükleyerek bu gizlilik protokolünü kabul etmiş sayılırsınız.
            </p>
            <button onclick="document.getElementById('kvkkModal').style.display='none'" style="background:#0ea5e9; width:100%; margin-top:20px; padding:12px;">KAPAT</button>
        </div>
    </div>

    <script>
        function run() {
            if(document.getElementById('fIn').files.length == 0) return;
            document.getElementById('pCont').style.display = 'block';
            document.getElementById('pPerc').style.display = 'block';
            let w = 0;
            let int = setInterval(() => {
                w += (100 - w) * 0.12;
                document.getElementById('pBar').style.width = w + '%';
                document.getElementById('pPerc').innerText = '%' + Math.floor(w) + ' İşleniyor...';
                if(w > 98) clearInterval(int);
            }, 100);
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "GET":
        return render_template_string(HTML_UI)
    
    f = request.files.get("file")
    mod = request.form.get("mod")
    lines = guclu_parser(f.read())
    text = "\n".join(lines)

    if mod == "txt":
        return send_file(io.BytesIO(text.encode('utf-8')), as_attachment=True, download_name="belge.txt", mimetype='text/plain')
    elif mod == "word":
        return send_file(io.BytesIO(text.encode('utf-8')), as_attachment=True, download_name="belge.doc", mimetype='application/msword')
    else: # PDF
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        y = 800
        for line in lines:
            if y < 50: c.showPage(); y = 800
            c.drawString(50, y, line[:95])
            y -= 15
        c.save()
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name="belge.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
