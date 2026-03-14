import os
import zlib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string, Response
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

# -------------------------------
# SEO LANDING PAGES (50 SAYFA)
# -------------------------------

SEO_PAGES = [
"udf-to-pdf",
"udf-to-word",
"udf-to-txt",
"uyap-udf-converter",
"udf-dosyasi-acma",
"udf-dosyasi-pdf-yapma",
"udf-dosyasi-word-yapma",
"udf-viewer",
"udf-to-doc",
"udf-reader",
"udf-file-converter",
"udf-to-text",
"udf-belgesi-acma",
"udf-to-pdf-online",
"udf-dosyasi-donustur",
"uyap-belgesi-ac",
"uyap-udf-pdf",
"udf-to-pdf-free",
"udf-file-viewer",
"udf-to-docx",
"udf-belgesi-pdf",
"udf-belgesi-word",
"udf-reader-online",
"udf-parser",
"udf-converter-online",
"udf-file-reader",
"udf-to-printable",
"udf-document-viewer",
"udf-to-html",
"udf-to-markdown",
"udf-to-rtf",
"udf-to-open",
"udf-to-readable",
"udf-file-parser",
"udf-uyap-reader",
"udf-dava-belgesi-ac",
"udf-hukuk-belgesi",
"udf-belge-donusturucu",
"udf-court-file-viewer",
"udf-to-pdf-fast",
"udf-to-word-fast",
"udf-convert-free",
"udf-online-reader",
"udf-open-online",
"udf-belgesi-goruntule",
"udf-uyap-pdf",
"udf-uyap-word",
"udf-document-converter",
"udf-text-extractor",
"udf-belge-okuyucu"
]

# -------------------------------
# UDF PARSER
# -------------------------------

def udf_motoru(data):
    try:
        start_tag = b"<content>"
        end_tag = b"</content>"

        s = data.find(start_tag)
        e = data.find(end_tag)

        xml_ham = zlib.decompress(data[s+len(start_tag):e])

        root = ET.fromstring(xml_ham)

        lines = []
        for elem in root.iter():
            if elem.text:
                t = elem.text.strip()
                if t:
                    lines.append(t)

        return lines

    except:
        return ["UDF okunamadı"]

# -------------------------------
# ANA SAYFA
# -------------------------------

HTML = """
<html>
<head>

<title>UDF to PDF Converter | Ücretsiz UYAP Dönüştürücü</title>

<meta name="description" content="UDF dosyalarını ücretsiz olarak PDF, Word veya TXT formatına dönüştürün.">

</head>

<body style="font-family:Arial;text-align:center;margin-top:100px">

<h1>UDF DOSYA DÖNÜŞTÜRÜCÜ</h1>

<p>UDF dosyanızı yükleyin ve dönüştürün</p>

<form method="POST" enctype="multipart/form-data">

<input type="file" name="file" required>

<br><br>

<button name="mod" value="pdf">PDF</button>
<button name="mod" value="word">WORD</button>
<button name="mod" value="txt">TEXT</button>

</form>

<p style="margin-top:50px;font-size:12px">
Dosyalar sunucuda saklanmaz.
</p>

</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def index():

    if request.method == "GET":
        return render_template_string(HTML)

    f = request.files["file"]
    mod = request.form.get("mod")

    lines = udf_motoru(f.read())

    text = "\n".join(lines)

    if mod == "txt":

        return send_file(
            io.BytesIO(text.encode()),
            as_attachment=True,
            download_name="belge.txt",
            mimetype="text/plain"
        )

    if mod == "word":

        return send_file(
            io.BytesIO(text.encode()),
            as_attachment=True,
            download_name="belge.doc",
            mimetype="application/msword"
        )

    buf = io.BytesIO()

    c = canvas.Canvas(buf)

    y = 800

    for line in lines:

        c.drawString(50,y,line)

        y -= 15

        if y < 50:
            c.showPage()
            y = 800

    c.save()

    buf.seek(0)

    return send_file(
        buf,
        as_attachment=True,
        download_name="belge.pdf",
        mimetype="application/pdf"
    )

# -------------------------------
# SEO LANDING ROUTE
# -------------------------------

@app.route("/<slug>")
def seo_pages(slug):

    if slug not in SEO_PAGES:
        return "404",404

    return f"""
    <html>
    <head>

    <title>{slug.replace('-',' ').title()}</title>

    <meta name="description" content="{slug} online converter">

    </head>

    <body style="font-family:Arial;text-align:center;margin-top:120px">

    <h1>{slug.replace('-',' ').title()}</h1>

    <p>UDF dosyalarını ücretsiz dönüştürün.</p>

    <a href="/">UDF Converter</a>

    </body>
    </html>
    """

# -------------------------------
# ROBOTS.TXT
# -------------------------------

@app.route("/robots.txt")
def robots():

    return Response(
"""
User-agent: *
Allow: /

Sitemap: https://udf-to-pdf-production.up.railway.app/sitemap.xml
""",
mimetype="text/plain"
)

# -------------------------------
# SITEMAP.XML
# -------------------------------

@app.route("/sitemap.xml")
def sitemap():

    urls = ""

    base = "https://udf-to-pdf-production.up.railway.app"

    urls += f"<url><loc>{base}</loc></url>"

    for p in SEO_PAGES:

        urls += f"<url><loc>{base}/{p}</loc></url>"

    xml = f"""

<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

{urls}

</urlset>

"""

    return Response(xml,mimetype="text/xml")

# -------------------------------
# START
# -------------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT",8080))

    app.run(host="0.0.0.0",port=port)
