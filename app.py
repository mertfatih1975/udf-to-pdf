import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string, Response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io

app = Flask(__name__)

# --- DERİN ARAMA PARSER (v20.0) ---
def guclu_parser(data):
    try:
        # Denenecek tüm olası zlib/sıkıştırma imzaları
        sigs = [b'\x78\x9c', b'\x78\xda', b'\x78\x01', b'\x78\x5e', b'\x1f\x8b']
        
        # 1. Adım: XML etiketlerini temizle ve ham veriyi tara
        content_start = data.find(b"<content>")
        content_end = data.find(b"</content>")
        
        search_data = data
        if content_start != -1 and content_end != -1:
            search_data = data[content_start+9:content_end]

        # 2. Adım: Tüm imzaları dosya boyunca tara
        for sig in sigs:
            pos = search_data.find(sig)
            while pos != -1:
                try:
                    # Bulunan noktadan itibaren açmayı dene
                    decompressed = zlib.decompress(search_data[pos:])
                    return parse_xml_to_lines(decompressed)
                except:
                    # Başarısızsa bir sonraki aynı imzayı ara
                    pos = search_data.find(sig, pos + 1)
        
        return ["HATA: Dosya içeriği şifreli (DYS Korumalı) veya tanınmayan bir formatta."]
    except Exception as ex:
        return [f"TEKNİK HATA: {str(ex)}"]

def parse_xml_to_lines(xml_content):
    try:
        # Bazı XML'ler hatalı karakter içerebilir, temizleyerek işle
        xml_str = xml_content.decode('utf-8', errors='ignore')
        root = ET.fromstring(xml_str)
        lines = []
        for elem in root.iter():
            if elem.text and elem.text.strip():
                lines.append(elem.text.strip())
        return lines if lines else ["Belge içeriği boş."]
    except:
        # Eğer XML parse edilemezse, ham metni regex benzeri çekmeye çalış
        import re
        lines = re.findall(r'>([^<]+)<', xml_content.decode('utf-8', errors='ignore'))
        return [l.strip() for l in lines if l.strip()]

# --- KURUMSAL ARAYÜZ (GÜVENLİK ODAKLI) ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <title>UDF Pro Elite v20.0 | Ofis Gökçadır</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .box { background: #1e293b; padding: 40px; border-radius: 20px; text-align: center; width: 480px; border: 1px solid #334155; box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
        .security-badge { background: rgba(6, 78, 59, 0.4); color: #6ee7b7; padding: 18px; border-radius: 12px; font-size: 13px; margin-bottom: 25px; border: 1px solid #059669; text-align: left; line-height: 1.6; }
        .progress-container { display: none; margin: 20px 0; background: #334155; border-radius: 10px; height: 12px; overflow: hidden; }
        .progress-bar { width: 0%; height: 100%; background: linear-gradient(90deg, #38bdf8, #818cf8); transition: width 0.2s; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; opacity: 0.3; pointer-events: none; }
        button.active { opacity: 1; pointer-events: auto; }
        .pdf { background: #0ea5e9; grid-column: span 2; font-size: 16px; }
        .word { background: #2b579a; } .txt { background: #64748b; }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; border: 1px dashed #475569; padding: 15px; border-radius: 10px; }
        .kvkk-check { margin: 20px 0; font-size: 12.5px; color: #cbd5e1; display: flex; align-items: flex-start; justify-content: center; gap: 10px; cursor: pointer; text-align: left; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="color:#38bdf8; margin:0 0 15px 0;">UDF PRO <span style="color:white">ELITE v20.0</span></h2>
        <div class="security-badge">
            🔒 <b>Güvenlik Bildirimi:</b> Sayın kullanıcımız; yüklemiş olduğunuz dosyalar hiçbir şekilde sunucularımızda depolanmaz. Anlık işlenir ve kalıcı olarak silinir.
        </div>
        <form id="uForm" method="POST" action="/" enctype="multipart/form-data">
            <input type="file" name="file" id="fIn" accept=".udf" required>
            <label class="kvkk-check">
                <input type="checkbox" id="kvkkBox" onchange="toggleBtns()">
                <span><a href="#" style="color:#38bdf8;" onclick="alert('Verileriniz sadece anlık işlenir.')">KVKK Aydınlatma Metnini</a> okudum ve onaylıyorum.</span>
            </label>
            <div id="pCont" class="progress-container"><div id="pBar" class="progress-bar"></div></div>
            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" id="btnPdf" class="pdf" onclick="run()">PRO PDF OLARAK DÖNÜŞTÜR</button>
                <button type="submit" name="mod" value="word" id="btnWord" class="word" onclick="run()">PRO WORD (DOC)</button>
                <button type="submit" name="mod" value="txt" id="btnTxt" class="txt" onclick="run()">HIZLI TEXT (TXT)</button>
            </div>
        </form>
    </div>
    <script>
        function toggleBtns() {
            const isChecked = document.getElementById('kvkkBox').checked;
            const active = isChecked ? 'active' : '';
            const btns = ['btnPdf', 'btnWord', 'btnTxt'];
            btns.forEach(id => {
                const b = document.getElementById(id);
                if(isChecked) b.classList.add('active'); else b.classList.remove('active');
            });
        }
        function run() {
            document.getElementById('pCont').style.display = 'block';
            let w = 0; let b = document.getElementById('pBar');
            let i = setInterval(() => {
                w += (100 - w) * 0.12; b.style.width = w + '%';
                if(w > 98) clearInterval(i);
            }, 100);
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "GET":
        resp = Response(render_template_string(HTML_UI))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return resp
    
    f = request.files.get("file")
    mod = request.form.get("mod")
    lines = guclu_parser(f.read())

    if "HATA" in lines[0] or "TEKNİK" in lines[0]:
        return f"<body style='background:#0f172a; color:white; text-align:center; padding-top:100px;'><h2>⚠️ {lines[0]}</h2><a href='/' style='color:#38bdf8;'>Geri Dön</a></body>", 400

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
        c.save(); buf.seek(0)
        return send_file(buf, as_attachment=True, download_name="belge.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
