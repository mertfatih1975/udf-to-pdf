# -*- coding: utf-8 -*-
import os, zlib, zipfile, io, re, smtplib
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)

# --- YAPILANDIRMA ---
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024
SAYAC_DOSYASI = "sayac.txt"
DEFAULT_FONT = "Helvetica"
MY_MAIL = "mertfatih1975@gmail.com"
# Gmail "Uygulama Şifresi" buraya gelecek:
MAIL_APP_PASS = "xxxx xxxx xxxx xxxx" 

# --- TÜRKÇE FONT DESTEĞİ ---
try:
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:\\Windows\\Fonts\\arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont("TurkishFont", path))
            DEFAULT_FONT = "TurkishFont"
            break
except: pass

# --- SAYAÇ SİSTEMİ ---
def get_sayac():
    if not os.path.exists(SAYAC_DOSYASI):
        with open(SAYAC_DOSYASI, "w") as f: f.write("11537")
        return 11537
    try:
        with open(SAYAC_DOSYASI, "r") as f:
            val = f.read().strip()
            return int(val) if val else 11537
    except: return 11537

def increment_sayac():
    count = get_sayac() + 1
    with open(SAYAC_DOSYASI, "w") as f: f.write(str(count))
    return count

# --- GÜÇLÜ UDF PARSER ---
def guclu_parser(data):
    xml_raw = None
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for n in z.namelist():
                if n.endswith(".xml"): xml_raw = z.read(n); break
    except: pass
    if not xml_raw:
        try: xml_raw = zlib.decompress(data)
        except: xml_raw = data
    try:
        xml_str = xml_raw.decode("utf-8", errors="ignore")
        xml_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_str)
        lines = re.findall(r'<(?:content|w:t)[^>]*>(.*?)</(?:content|w:t)>', xml_str, re.DOTALL)
        if not lines: lines = re.findall(r'>([^<]{5,})<', xml_str)
        return [re.sub(r'<[^>]+>', '', l).strip() for l in lines if l.strip()]
    except: return ["İçerik okunamadı."]

# --- MAİL GÖNDERME SİSTEMİ ---
def send_feedback_mail(isim, mesaj, puan):
    try:
        msg = MIMEMultipart()
        msg['From'] = MY_MAIL
        msg['To'] = MY_MAIL
        msg['Subject'] = f"UDF Dönüştürücü Yeni Yorum: {isim}"
        body = f"Gönderen: {isim}\nPuan: {puan}/5\n\nMesaj:\n{mesaj}"
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(MY_MAIL, MAIL_APP_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

# --- UI TASARIMI ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDF to PDF | Online UYAP Dosya Dönüştürücü</title>
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --accent: #38bdf8; --green: #10b981; --text: #f8fafc; --muted: #94a3b8; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); display: flex; flex-direction: column; align-items: center; padding: 20px; margin: 0; }
        .box { background: var(--card); padding: 30px; border-radius: 20px; text-align: center; width: 100%; max-width: 600px; border: 1px solid #334155; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .stats-badge { background: rgba(56, 189, 248, 0.1); color: var(--accent); padding: 10px 15px; border-radius: 12px; font-weight: bold; margin-bottom: 20px; border: 1px solid rgba(56, 189, 248, 0.3); display: inline-block; }
        #pb-bg { display: none; width: 100%; background: #020617; height: 10px; border-radius: 5px; margin: 15px 0; overflow: hidden; }
        #pb-fill { width: 0%; height: 100%; background: var(--accent); transition: width 0.3s; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 15px; }
        button { border: none; padding: 14px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.2s; }
        .pdf { background: #0ea5e9; } .word { background: #2563eb; } .pre { background: var(--green); width: 100%; }
        .info-panel { width: 100%; max-width: 600px; margin-top: 25px; text-align: left; }
        .review-card { background: var(--card); padding: 15px; border-radius: 15px; margin-bottom: 12px; border-left: 4px solid var(--accent); font-size: 14px; }
        .author { color: var(--accent); font-weight: bold; font-size: 12px; display: block; margin-top: 5px; text-align: right; }
        #preview-box { display: none; background: #020617; padding: 15px; border-radius: 10px; margin-top: 15px; font-size: 13px; text-align: left; max-height: 200px; overflow-y: auto; color: var(--muted); border: 1px dashed var(--accent); }
        input[type="text"], textarea, select { width: 100%; padding: 12px; margin-bottom: 10px; border-radius: 8px; border: 1px solid #334155; background: #020617; color: white; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="box">
        <h1>UDF Dönüştürücü</h1>
        <div class="stats-badge">🚀 {{ count }} Güvenli İşlem Tamamlandı</div>
        <form id="uForm" method="POST" enctype="multipart/form-data" onsubmit="startLoad()">
            <input type="file" name="file" id="fInput" required style="margin-bottom:20px; color: var(--muted);">
            <div id="pb-bg"><div id="pb-fill"></div></div>
            <button type="button" class="pre" onclick="getPre()">🔍 BELGE ÖNİZLE</button>
            <div class="btn-group">
                <button type="submit" name="mod" value="pdf" class="pdf">UDF ➔ PDF</button>
                <button type="submit" name="mod" value="word" class="word">UDF ➔ WORD</button>
            </div>
            <div id="preview-box"></div>
        </form>
    </div>

    <div class="info-panel">
        <h2 style="color: var(--accent); font-size: 18px;">💬 Kullanıcı Yorumları</h2>
        <div class="review-card">"UYAP Editörle uğraşmadan cepten hızlıca PDF yapabiliyorum. Harika." <span class="author">- Av. Selçuk G.</span></div>
        <div class="review-card">"Dilekçelerimi Word'e çevirirken format hiç bozulmuyor." <span class="author">- Katip Murat B.</span></div>
        
        <div style="background: rgba(15, 23, 42, 0.5); padding: 20px; border-radius: 15px; border: 1px solid #334155; margin-top: 20px;">
            <h3 style="font-size: 15px; margin-top: 0;">✍️ Siz de Yorum Yapın</h3>
            <form id="yForm" onsubmit="sendYorum(event)">
                <input type="text" id="yAd" placeholder="Adınız / Ünvanınız" required>
                <select id="yPuan"><option value="5">⭐⭐⭐⭐⭐</option><option value="4">⭐⭐⭐⭐</option></select>
