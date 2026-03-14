import os
import zlib
import zipfile
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string, Response, jsonify
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import re
from datetime import datetime

app = Flask(__name__)

# -------------------
# ANALYTICS
# -------------------

analytics = {
    "visits":0,
    "conversions":0
}

# -------------------
# SEO SLUGS
# -------------------

SEO_PAGES = [f"udf-converter-{i}" for i in range(1,101)]

# -------------------
# UDF PARSER
# -------------------

def guclu_parser(data):

    try:

        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:

                if "content.xml" in z.namelist():

                    with z.open("content.xml") as f:
                        return parse_xml_to_lines(f.read())

        except:
            pass

        sigs=[b'\x78\x9c',b'\x78\xda',b'\x78\x01']

        for sig in sigs:

            pos=data.find(sig)

            while pos!=-1:

                for wbits in [zlib.MAX_WBITS,-zlib.MAX_WBITS]:

                    try:

                        decompressed=zlib.decompress(data[pos:],wbits)

                        if b'<' in decompressed:
                            return parse_xml_to_lines(decompressed)

                    except:
                        pass

                pos=data.find(sig,pos+1)

        return ["Belge formatı tanınamadı"]

    except Exception as ex:

        return [str(ex)]

def parse_xml_to_lines(xml_content):

    try:

        xml_str=xml_content.decode("utf-8",errors="ignore")

        lines=re.findall(r'>([^<]{2,})<',xml_str)

        lines=[l.strip() for l in lines if l.strip()]

        if not lines:

            root=ET.fromstring(xml_str)

            lines=[e.text.strip() for e in root.iter() if e.text and e.text.strip()]

        return lines

    except:

        clean=re.sub(r'<[^>]+>',' ',xml_content.decode("utf-8",errors="ignore"))

        return [clean]

# -------------------
# UI
# -------------------

HTML="""
<!DOCTYPE html>
<html>
<head>

<title>UDF Converter PRO</title>

<meta name="description" content="UYAP UDF dosyalarını PDF Word veya TXT yapın">

<style>

body{
font-family:Arial;
background:#0f172a;
color:white;
display:flex;
justify-content:center;
align-items:center;
height:100vh
}

.box{
background:#1e293b;
padding:40px;
border-radius:15px;
width:500px;
text-align:center
}

.drop{
border:2px dashed #38bdf8;
padding:30px;
margin-bottom:20px;
cursor:pointer
}

button{
padding:12px;
margin:5px;
border:none;
border-radius:6px;
background:#38bdf8;
color:white;
cursor:pointer
}

.preview{
background:#020617;
padding:15px;
height:200px;
overflow:auto;
margin-top:20px;
font-size:12px
}

</style>

</head>

<body>

<div class="box">

<h2>UDF Converter PRO</h2>

<div class="drop" id="drop">

Dosyayı buraya sürükle

</div>

<form method="POST" enctype="multipart/form-data" id="form">

<input type="file" name="file" id="fileInput">

<br><br>

<button name="mod" value="preview">Preview</button>
<button name="mod" value="pdf">PDF</button>
<button name="mod" value="word">Word</button>
<button name="mod" value="txt">Text</button>

</form>

<div class="preview" id="preview"></div>

</div>

<script>

const drop=document.getElementById("drop")
const input=document.getElementById("fileInput")

drop.ondragover=e=>{
e.preventDefault()
}

drop.ondrop=e=>{
e.preventDefault()
input.files=e.dataTransfer.files
}

</script>

</body>
</html>
"""

# -------------------
# MAIN
# -------------------

@app.route("/",methods=["GET","POST"])
def index():

    analytics["visits"]+=1

    if request.method=="GET":

        return render_template_string(HTML)

    file=request.files["file"]

    mod=request.form.get("mod")

    lines=guclu_parser(file.read())

    text="\n".join(lines)

    if mod=="preview":

        return "<br>".join(lines[:200])

    if mod=="txt":

        analytics["conversions"]+=1

        return send_file(

        io.BytesIO(text.encode()),

        as_attachment=True,

        download_name="belge.txt",

        mimetype="text/plain")

    if mod=="word":

        analytics["conversions"]+=1

        return send_file(

        io.BytesIO(text.encode()),

        as_attachment=True,

        download_name="belge.doc",

        mimetype="application/msword")

    if mod=="pdf":

        analytics["conversions"]+=1

        buf=io.BytesIO()

        c=canvas.Canvas(buf,pagesize=A4)

        y=800

        for line in lines:

            c.drawString(50,y,line)

            y-=15

            if y<50:

                c.showPage()

                y=800

        c.save()

        buf.seek(0)

        return send_file(

        buf,

        as_attachment=True,

        download_name="belge.pdf",

        mimetype="application/pdf")

# -------------------
# ANALYTICS PANEL
# -------------------

@app.route("/analytics")

def stats():

    return jsonify(analytics)

# -------------------
# SEO PAGE
# -------------------

@app.route("/<slug>")

def seo(slug):

    if slug not in SEO_PAGES:

        return "404",404

    return f"""

    <html>

    <head>

    <title>{slug}</title>

    </head>

    <body>

    <h1>{slug}</h1>

    <a href="/">UDF Converter</a>

    </body>

    </html>

    """

# -------------------
# ROBOTS
# -------------------

@app.route("/robots.txt")

def robots():

    return Response("""

User-agent: *

Allow: /

Sitemap: /sitemap.xml

""",mimetype="text/plain")

# -------------------
# SITEMAP
# -------------------

@app.route("/sitemap.xml")

def sitemap():

    base="https://udf-to-pdf-production.up.railway.app"

    urls=""

    urls+=f"<url><loc>{base}</loc></url>"

    for p in SEO_PAGES:

        urls+=f"<url><loc>{base}/{p}</loc></url>"

    xml=f"""

<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

{urls}

</urlset>

"""

    return Response(xml,mimetype="text/xml")

# -------------------
# SERVER
# -------------------

if __name__=="__main__":

    port=int(os.environ.get("PORT",8080))

    app.run(host="0.0.0.0",port=port)
