from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

def create_pdf(text):
    buffer = io.BytesIO()
    width, height = A4
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Kurumsal başlık
    p.setFont("Helvetica-Bold", 16)
    p.setFillColor(colors.HexColor("#0ea5e9"))
    p.drawString(50, height - 50, "UDF Dosya Özeti")
    
    # Alt başlık veya logo yeri
    p.setFont("Helvetica", 12)
    p.setFillColor(colors.black)
    p.drawString(50, height - 70, "Ofis Gökçadır İş Merkezi")
    
    # Metin alanı
    t = p.beginText(50, height - 100)
    t.setFont("Helvetica", 10)
    t.setFillColor(colors.black)
    line_height = 14
    for line in text.split('\n'):
        if t.getY() < 50:
            p.drawText(t)
            p.showPage()
            # Başlık tekrar
            p.setFont("Helvetica-Bold", 16)
            p.setFillColor(colors.HexColor("#0ea5e9"))
            p.drawString(50, height - 50, "UDF Dosya Özeti")
            t = p.beginText(50, height - 100)
            t.setFont("Helvetica", 10)
            t.setFillColor(colors.black)
        t.textLine(line)
    p.drawText(t)
    
    # Footer
    p.setFont("Helvetica-Oblique", 9)
    p.setFillColor(colors.HexColor("#64748b"))
    p.drawString(50, 30, "FATİH MERT | Ofis Gökçadır İş Merkezi")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer
