import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

app = Flask(__name__)

# Arial fontunu sisteme tanıtıyoruz (arial.ttf deponuzda olmalı)
try:
    pdfmetrics.registerFont(TTFont('ArialCustom', 'arial.ttf'))
    FONT_NAME = 'ArialCustom'
except:
    FONT_NAME = 'Helvetica'

# --- UDF OKUMA MANTIĞI ---
def udf_cozucu(udf_verisi):
    try:
        # UDF içindeki <content> etiketleri arasındaki sıkıştırılmış veriyi bul
        baslangic = udf_verisi.find(b"<content>") + 9
        bitis = udf_verisi.find(b"</content>")
        
        # Sıkıştırılmış veriyi (zlib) aç
        sikistirilmis_data = udf_verisi[baslangic:bitis]
        xml_metni = zlib.decompress(sikistirilmis_data)
        
        # XML içinden saf metni ayıkla
        root = ET.fromstring(xml_metni)
        saf_metin = ""
        for content in root.iter('content'):
            if content.text:
                saf_metin += content.text + "\n"
        return saf_metin
    except Exception as e:
        return f"Hata: UDF yapısı çözülemedi. ({str(e)})"

# --- WEB ARAYÜZÜ VE ROTARLAR ---
@app.route('/')
def ana_sayfa():
    # Daha önce hazırladığımız o şık HTML (Güvenlik uyarılı ve KVKK'lı)
    return HTML_UI # (Burada yukarıdaki HTML_UI değişkeninin tanımlı olduğunu varsayıyoruz)

@app.route('/convert/pro', methods=['POST'])
def pdf_yap():
    if 'file' not in request.files: return "Dosya yok", 400
    file = request.files['file']
    
    # 1. ADIM: UDF'yi oku ve içindeki metni ayıkla (GERÇEK ALT YAPI BURASI)
    udf_metni = udf_cozucu(file.read())
    
    # 2. ADIM: Ayıklanan metni PDF'e dök
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    t = c.beginText(50, 800)
    t.setFont(FONT_NAME, 10)
    
    for satir in udf_metni.split('\n'):
        t.textLine(satir)
        
    c.drawText(t)
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="donusturuldu.pdf")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
