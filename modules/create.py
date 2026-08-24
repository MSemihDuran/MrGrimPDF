import os
import fitz
from PIL import Image

def create_pdf_from_content(title, content, output_path, orientation='portrait', page_size='a4', images=None):
    doc = fitz.open()
    
    # Paper Dimensions (pts)
    if page_size.lower() == 'letter':
        width, height = (612, 792)
    else:  # A4
        width, height = (595, 842)
        
    if orientation.lower() == 'landscape':
        width, height = height, width
        
    page = doc.new_page(width=width, height=height)
    
    margin = 50
    y = margin
    
    # 1. Add Document Title
    if title:
        page.insert_text(
            fitz.Point(margin, y + 24),
            title,
            fontsize=22,
            fontname="helv",
            color=(0.06, 0.09, 0.16) # #0f172a
        )
        y += 45
        
        # Add decorative line under title
        page.draw_line(
            fitz.Point(margin, y),
            fitz.Point(width - margin, y),
            color=(0.31, 0.27, 0.9), # Indigo
            width=1.5
        )
        y += 25

    # 2. Add Text Content
    if content:
        lines = content.split('\n')
        line_height = 16
        font_size = 11
        
        for line in lines:
            if y > height - margin - 40:
                page = doc.new_page(width=width, height=height)
                y = margin
                
            page.insert_text(
                fitz.Point(margin, y + font_size),
                line,
                fontsize=font_size,
                fontname="helv",
                color=(0.2, 0.25, 0.33)
            )
            y += line_height
            
    # 3. Add Embedded Images if any
    if images and isinstance(images, list):
        for img_path in images:
            if os.path.exists(img_path):
                if y > height - 250:
                    page = doc.new_page(width=width, height=height)
                    y = margin
                    
                img_rect = fitz.Rect(margin, y, width - margin, min(y + 250, height - margin))
                page.insert_image(img_rect, filename=img_path, keep_proportion=True)
                y += 260

    # 4. Footer Branding
    for p in doc:
        p.insert_text(
            fitz.Point(margin, height - 20),
            "Created with MrGrimPDF - 100% Free & Unlimited PDF Suite (mrgrimpdf.vercel.app)",
            fontsize=8,
            fontname="helv",
            color=(0.6, 0.65, 0.75)
        )

    doc.save(output_path)
    doc.close()
    return output_path
