import os
import zlib
import zipfile
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string, Response, redirect, make_response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import re
from datetime import datetime
import pytz
import json

app = Flask(__name__)

# --- GÜVENLİK: HTTP -> HTTPS YÖNLENDİRMESİ ---
@app.before_request
def redirect_to_https():
    if request.headers.get('X-Forwarded-Proto', 'http') == 'http':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

# --- UDF PARSER ---
def guclu_parser(data):
    try:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for name in z.namelist():
                    if name.lower().endswith(".xml"):
                        with z.open(name) as f: return parse_xml_to_lines(f.read())
        except: pass
        sigs = [b'\x78\x9c', b'\x78\xda', b'\x78\x01']
        for sig in sigs:
            pos = data.find(sig)
            while pos != -1:
                try:
                    decompressed = zlib.decompress(data[pos:])
                    if b"<" in decompressed: return parse_xml_to_lines(decompressed)
                except: pass
                pos = data.find(sig, pos + 1)
        return ["HATA: İçerik ayrıştırılamadı."]
    except Exception as e: return [f"Hata: {str(e)}"]

def parse_xml_to_lines(xml_content):
    try:
        xml_str = xml_content.decode("utf-8", errors="ignore")
        xml_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', xml_str)
        xml_str = xml_str.replace('\xa0', ' ')
        root = ET.fromstring(xml_str)
        lines = [" ".join(elem.text.split()) for elem in root.iter() if elem.text and len(elem.text.strip()) > 1]
        return lines if lines else [re.sub(r'<[^>]+>', ' ', xml_str).strip()]
    except: return [re.sub(r'<[^>]+>', ' ', xml_content.decode("utf-8", errors="ignore")).strip()]

# --- MOBİL UYGULAMA (PWA) ---
@app.route("/manifest.json")
def manifest():
    data = {
        "name": "UDFTOPDF Dönüştürücü",
        "short_name": "UDFTOPDF",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#0f172a",
        "description": "UYAP UDF dosyalarınızı kolayca dönüştürün.",
        "icons": [{"src": "/icon.svg", "sizes": "512x512", "type": "image/svg+xml", "purpose": "any maskable"}]
    }
    return Response(json.dumps(data), mimetype="application/json")

@app.route("/sw.js")
def service_worker():
    js = "self.addEventListener('install', (e) => { self.skipWaiting(); }); self.addEventListener('fetch', (e) => { e.respondWith(fetch(e.request)); });"
    return Response(js, mimetype="application/javascript")

@app.route("/icon.svg")
def app_icon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" rx="100" fill="#1e293b"/><text x="50%" y="45%" dominant-baseline="middle" text-anchor="middle" font-size="100" font-weight="bold" font-family="Arial, sans-serif" fill="#38bdf8">UDF</text><text x="50%" y="65%" dominant-baseline="middle" text-anchor="middle" font-size="60" font-weight="bold" font-family="Arial, sans-serif" fill="#f8fafc">TO PDF</text></svg>"""
    return Response(svg, mimetype="image/svg+xml")

# --- UI TASARIMI ---
HTML_UI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta name="description" content="UDF dosyalarını ücretsiz PDF, Word ve JPEG formatına dönüştürün. UYAP Doküman Formatı çevirici.">
    <title>UDFTOPDF | UYAP Dosya Dönüştürücü</title>
    
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#0f172a">
    <link rel="apple-touch-icon" href="/icon.svg">
    <meta name="apple-mobile-web-app-capable" content="yes">
    
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; display: flex; flex-direction: column; align-items: center; min-height: 100vh; margin: 0; padding: 20px 15px; }
        .box { background: #1e293b; padding: 30px; border-radius: 20px; text-align: center; width: 100%; max-width: 600px; border: 1px solid #334155; box-shadow: 0 15px 30px rgba(0,0,0,0.5); margin-bottom: 25px; box-sizing: border-box; }
        
        .mobile-install-badge { display: none; background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 12px; border-radius: 10px; font-size: 13px; font-weight: bold; margin-bottom: 20px; border: 1px solid rgba(16, 185, 129, 0.3); }
        @media (max-width: 600px) { .mobile-install-badge { display: block; } }

        .stats-badge { background: rgba(56, 189, 248, 0.1); color: #38bdf8; padding: 12px; border-radius: 10px; font-size: 15px; font-weight: bold; margin-bottom: 25px; border: 1px solid rgba(56, 189, 248, 0.3); }
        .trust-points { text-align: left; margin-bottom: 25px; font-size: 14px; color: #94a3b8; display: grid; gap: 10px; }
        .trust-points span { display: flex; align-items: center; gap: 8px; }
        .trust-points b { color: #f8fafc; }
        .security-badge { background: rgba(6, 78, 59, 0.4); color: #6ee7b7; padding: 15px; border-radius: 12px; font-size: 13px; margin-bottom: 25px; border: 1px solid #059669; text-align: left; line-height: 1.5; }
        
        .btn-group { display: flex; flex-direction: column; gap: 10px; }
        button { border: none; padding: 15px; border-radius: 10px; cursor: pointer; font-weight: bold; color: white; transition: 0.3s; opacity: 0.3; pointer-events: none; width: 100%; }
        button.active { opacity: 1; pointer-events: auto; }
        .pdf { background: #0ea5e9; font-size: 16px; }
        .word { background: #2b579a; } .txt { background: #64748b; }
        input[type="file"] { margin-bottom: 20px; color: #94a3b8; width: 100%; border: 1px dashed #475569; padding: 15px; border-radius: 10px; cursor: pointer; box-sizing: border-box; }
        
        .info-panel { width: 100%; max-width: 600px; background: #111827; padding: 25px; border-radius: 20px; border: 1px solid #334155; margin-bottom: 20px; font-size: 14px; line-height: 1.6; color: #94a3b8; box-sizing: border-box; text-align: left; }
        .info-panel h2 { color: #38bdf8; font-size: 18px; margin-top: 0; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #1e293b; padding-bottom: 10px; }
        .info-panel h3 { color: #e2e8f0; font-size: 16px; margin-top: 20px; margin-bottom: 10px; }
        .info-panel b { color: #f8fafc; }
        .info-panel ul, .info-panel ol { padding-left: 20px; margin-bottom: 20px; }
        .info-panel li { margin-bottom: 8px; }
        
        /* KULLANICI YORUMLARI CSS */
        .review-box { background: #1e293b; padding: 15px 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #38bdf8; }
        .review-text { font-style: italic; color: #cbd5e1; margin-bottom: 8px; font-size: 14px; }
        .review-author { color: #f8fafc; font-weight: bold; font-size: 13px; text-align: right; }
        .stars { color: #fbbf24; font-size: 14px; margin-bottom: 5px; }

        .footer { margin-top: 10px; text-align: center; color: #64748b; font-size: 11px; line-height: 1.8; }
        .contact-area { margin-top: 20px; padding: 15px; border-top: 1px solid #334155; color: #94a3b8; font-size: 13px; }
        .contact-area b { color: #38bdf8; }
        h1 { color:#38bdf8; font-size: 20px; line-height: 1.4; margin-bottom: 15px; }

        @media
