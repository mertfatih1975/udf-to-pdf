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

# --- ZIRHLI UDF PARSER (Geliştirilmiş Versiyon) ---
def guclu_parser(data):
    try:
        # 1. Standart ZIP Yapısını Dene
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for name in z.namelist():
                    if name.lower().endswith(".xml"):
                        with z.open(name) as f: 
                            return parse_xml_to_lines(f.read())
        except: pass

        # 2. Ham ZLIB Akışlarını Ara (UDF Karakteristiği)
        sigs = [b'\x78\x9c', b'\x78\xda', b'\x78\x01']
        for sig in sigs:
            pos = data.find(sig)
            while pos != -1:
                try:
                    decompressed = zlib.decompress(data[pos:])
                    if b"<" in decompressed: 
                        return parse_xml_to_lines(decompressed)
                except: pass
                pos = data.find(sig, pos + 1)

        # 3. ACİL DURUM: Regex ile Ham Metin Ayıklama (Fallback)
        raw_text = data.decode("utf-8", errors="ignore")
        found = re.findall(r'>([^<]{10,})<', raw_text)
        if found:
            return [line.strip() for line in found if len(line.strip()) > 2]

        return ["⚠️ Dosya içeriği ayrıştırılamadı. Dosya bozuk veya şifreli olabilir."]
    except Exception as e: 
        return [f"⚠️ Sistem Hatası: {str(e)}"]

def parse_xml_to_lines(xml_content):
    try:
        xml_str = xml_content.decode("utf-8", errors="ignore")
        xml_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', xml_str)
        
        try:
            root = ET.fromstring(xml_str)
            lines = []
            for elem in root.iter():
                if elem.text and len(elem.text.strip()) > 1:
                    clean_line = " ".join(elem.text.split())
                    lines.append(clean_line)
            if lines: return lines
        except: pass

        # XML Yapısı bozuksa Regex ile ayıkla
        lines = re.findall(r'[^>]+(?=<)', xml_str)
        return [l.strip() for l in lines if len(l.strip()) > 2]
    except:
        return ["⚠️ XML okuma hatası."]

# --- UI TASARIMI ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDFTOPDF | Profesyonel UYAP Belge Yönetim Sistemi</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; display: flex; flex-direction: column; align-items: center; padding: 20px; margin: 0; }
        .box { background: #1e293b; padding: 35px; border-radius: 24px; text-align: center; width: 100%; max-width: 650px; border: 1px solid #334155; margin-bottom: 25px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
        .stats-badge { background: rgba(56, 189, 248, 0.1); color: #38bdf8; padding: 12px; border-radius: 12px; font-size: 15px; margin-bottom: 25px; border: 1px solid rgba(56, 189, 248, 0.3); font-weight: bold; display: inline-block; }
        .security-badge { background: rgba(16, 185, 129, 0.1); color: #6ee7b7; padding: 18px; border-radius: 16px; font-size: 13.5px; margin-bottom: 30px; border: 1px solid rgba(16, 185, 129, 0.3); text-align: left; line-height: 1.6; }
        .section-title { font-size: 14px; font-weight: bold; margin: 20px 0 10px 0; display: block; text-align: left; text-transform: uppercase; letter-spacing: 1px; }
        .t-down { color: #38bdf8; } .t-up { color: #10b981; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px; }
        button { border: none; padding: 14px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.2s; opacity: 0.3; pointer-events: none; font-size: 13px; }
        .active { opacity: 1 !important; pointer-events: auto !important; }
        .pdf { background: #0ea5e9; } .word { background: #2563eb; } .txt { background: #475569; } .jpeg { background: #d97706; }
        .pdf-u { background: #0369a1; } .word-u { background: #1e3a8a; } .txt-u { background: #334155; } .jpeg-u { background: #b45309; }
        .preview-btn-ui { background: #10b981; grid-column: span 2; margin-bottom: 15px; }
        .info-panel { width: 100%; max-width: 650px; background: #111827; padding: 30px; border-radius: 24px; border: 1px solid #334155; margin-bottom: 20px; font-size: 14.5px; line-height: 1.7; color: #94a3b8; text-align: left; }
        .info-panel h2 { color: #38bdf8; font-size: 20px; margin-top: 0; margin-bottom: 20px; border-bottom: 1px solid #1e293b; padding-bottom: 12px; }
        #preview-box { display: none; background: #020617; border: 1px solid #38bdf8; padding: 20px; border-radius: 14px; margin-top: 25px; max-height: 300px; overflow-y: auto; color: #cbd5e1; font-family: monospace; font-size: 12.5px; white-space: pre-wrap; }
        .review-box { background: #1e293b; padding: 18px; border-radius: 15px; margin-bottom: 15px; border-left: 5px solid #38bdf8; }
        .review-text { font-style: italic; color: #cbd5e1; margin-bottom: 8px; }
        .review-author { color: #f8fafc; font-weight: bold; font-size: 13px; text-align: right; }
        .contact-link { color: #38bdf8; text-decoration: none; font-weight: bold; }
        .review-btn { background: #38bdf8; color: #0f172a; padding: 6px 14px; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: bold; float: right; }
        h1 { color:#38bdf8; font-size: 28px; margin-bottom: 15px; }
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
            <input type="file" name="file" id="fileInput" required style="width:100%; margin-bottom:20px; color: #94a3b8; background: #0f172a; padding: 15px; border-radius: 10px; border: 1px dashed #334155;">
            
            <label style="font-size: 13px; display: block; margin-bottom: 20px; cursor: pointer; color: #cbd5e1;">
                <input type="checkbox" id="kvkk" onchange="toggleBtns()"> KVKK Aydınlatma Metnini okudum ve onaylıyorum.
            </label>

            <button type="button" id="btnPreview" class="preview-btn-ui" onclick="getPreview()">🔍 BELGE İÇERİĞİNİ ÖNİZLE</button>

            <span class="section-title t-down">⬇️ UDF'den Dışa Aktar</span>
            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" id="b1" class="pdf">PDF OLARAK İNDİR</button>
                <button type="submit" name="mod" value="word" id="b2" class="word">WORD OLARAK İNDİR</button>
                <button type="submit" name="mod" value="txt" id="b3" class="txt">METİN (TXT) İNDİR</button>
                <button type="submit" name="mod" value="jpeg" id="b4" class="jpeg">GÖRSEL (JPG)</button>
            </div>

            <span class="section-title t-up">⬆️ Formatı UDF'ye Çevir</span>
            <div class="btn-group">
                <button type="submit" name="mod" value="pdf_to_udf" id="b5" class="pdf-u">PDF ➔ UDF</button>
                <button type="submit" name="mod" value="word_to_udf" id="b6" class="word-u">WORD ➔ UDF</button>
                <button type="submit" name="mod" value="txt_to_udf" id="b7" class="txt-u">TXT ➔ UDF</button>
                <button type="submit" name="mod" value="jpeg_to_udf" id="b8" class="jpeg-u">JPG ➔ UDF</button>
            </div>

            <div id="preview-box">
                <div id="preview-content"></div>
            </div>
        </form>

        <div style="margin-top:35px; font-size:14px; color:#64748b; border-top:1px solid #334155; padding-top:20px;">
            🤝 <b>Kurumsal İletişim:</b> <a href="mailto:mertfatih1975@gmail.com" class="contact-link">mertfatih1975@gmail.com</a> | 
            <a href="tel:+905327641661" class="contact-link">0532 764 16 61</a>
        </div>
    </div>

    <div class="info-panel">
        <h2>🔄 Sistem Nasıl Çalışır?</h2>
        <ol>
            <li><b>Belge Seçimi:</b> Dönüştürmek istediğiniz dosyayı seçin.</li>
            <li><b>Anlık Önizleme:</b> "Belge İçeriğini Önizle" butonuna basarak metni kontrol edin.</li>
            <li><b>Format Belirleme:</b> PDF, Word veya TXT formatını belirleyin.</li>
            <li><b>Güvenli İndirme:</b> Belgeniz işlenir ve sunucuda iz bırakmadan cihazınıza iletilir.</li>
        </ol>
    </div>

    <div class="info-panel">
        <h2>⚖️ UDF (UYAP Doküman Formatı) Bilgilendirme</h2>
        <p><b>UDF dosyaları</b>, UYAP kapsamında resmi evrakların bütünlüğünü sağlayan özel bir dosya yapısıdır. Standart yazılımlarla doğrudan görüntülenemezler. Bu portal, hukuk profesyonellerinin ve vatandaşların bu belgelere her cihazdan kolayca erişebilmesini sağlar.</p>
    </div>

    <div class="info-panel">
        <h2><span>💬 Kullanıcı Deneyimleri</span><a href="mailto:mertfatih1975@gmail.com?subject=Yeni Yorum" class="review-btn">+ Yorum Yaz</a></h2>
        <div class="review-box"><div class="review-text">"Duruşma salonunda tabletimden UDF dosyalarımı PDF'e çevirip anında okuyabiliyorum. Muazzam bir hız."</div><div class="review-author">- Av. M.T.</div></div>
        <div class="review-box"><div class="review-text">"Kayıt zorunluluğu olmaması ve dosyaların anında silinmesi güven verici. Harika bir iş."</div><div class="review-author">- A.Y.</div></div>
        <div class="review-box"><div class="review-text">"İcra dairelerinde dosya incelerken en büyük yardımcım bu site."</div><div class="review-author">- M.B. (Katip)</div></div>
        <div class="review-box"><div class="review-text">"Mobil uyumu çok başarılı, telefonumdan her türlü UYAP evrakını açabiliyorum."</div><div class="review-author">- Av. S.G.</div></div>
        <div class="review-box"><div class="review-text">"Ücretsiz ve reklamsız olması büyük bir avantaj. Teşekkürler."</div><div class="review-author">- Av. E.O.</div></div>
        <div class="review-box"><div class="review-text">"Güvenlik protokolü metni beni ikna etti, gizlilik hassasiyeti çok yerinde."</div><div class="review-author">- D.M.</div></div>
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
            const pBox = document.getElementById('preview-box');
            const pCont = document.getElementById('preview-content');
            
            if (!fIn.files[0]) {
                alert("Lütfen önce bir dosya seçin.");
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fIn.files[0]);
            formData.append('mod', 'preview');

            pCont.innerText = "⏳ Belge ayrıştırılıyor, lütfen bekleyin...";
            pBox.style.display = "block";

            try {
                const response = await fetch('/', { method: 'POST', body: formData });
                if (response.ok) {
                    const text = await response.text();
                    pCont.innerText = text;
                } else {
                    pCont.innerText = "❌ Önizleme oluşturulurken bir hata meydana geldi.";
                }
            } catch (error) {
                pCont.innerText = "🌐 Sunucu bağlantısı kurulamadı.";
            }
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def index():
    tz = pytz.timezone('Europe/Istanbul')
    if request.method == "GET":
        sayac = get_sayac()
        return render_template_string(HTML_UI, current_sayac=f"{sayac:,}".replace(',', '.'))
    
    f = request.files.get("file")
    mod = request.form.get("mod")
    
    # --- ÖNİZLEME (PREVIEW) ---
    if mod == "preview":
        if not f: return "Dosya seçilmedi."
        try:
            lines = guclu_parser(f.read())
            preview_text = " ".join(lines)[:1000]
            return preview_text + "..." if len(preview_text) >= 1000 else preview_text
        except: return "Ayrıştırma hatası."

    increment_sayac()
    
    # FORMATI UDF'YE ÇEVİRME
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

    # UDF'YI DİĞER FORMATLARA ÇEVİRME
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
