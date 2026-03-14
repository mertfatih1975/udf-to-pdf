import os
from flask import Flask, request, send_file

app = Flask(__name__)

# HTML içeriğini doğrudan buraya gömüyoruz
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>UDF - PDF Dönüştürücü</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-color: #f0f2f5; }
        .container { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; width: 350px; }
        h2 { color: #1a73e8; margin-bottom: 20px; }
        input[type="file"] { margin-bottom: 20px; width: 100%; }
        button { background-color: #1a73e8; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; transition: background 0.3s; }
        button:hover { background-color: #1557b0; }
        .footer { margin-top: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h2>UDF → PDF</h2>
        <form action="/convert" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".udf" required>
            <button type="submit">Dönüştür ve İndir</button>
        </form>
        <div class="footer">Fatih Mert - UDF İşlemci</div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    # Dosya okumak yerine doğrudan yukarıdaki değişkeni döndürüyoruz
    return HTML_INTERFACE

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return "Dosya seçilmedi", 400
    file = request.files['file']
    if file.filename == '':
        return "Dosya adı boş", 400
    
    # Şimdilik sistemi test etmek için gönderdiğin dosyayı 'donusturuldu.pdf' olarak geri verir
    return send_file(file, as_attachment=True, download_name="donusturuldu.pdf")

if __name__ == "__main__":
    # Railway'in atadığı portu dinamik olarak alır
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
