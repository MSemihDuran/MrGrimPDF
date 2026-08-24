import os
import fitz
from PIL import Image

def create_pdf_from_content(title, content, output_path, orientation='portrait', page_size='a4', images=None):
    doc = fitz.open()
    
    # Paper Dimensions (pts)
    if page_size.lower() == 'letter':
        page_w, page_h = (612, 792)
    else:  # A4
        page_w, page_h = (595, 842)
        
    if orientation.lower() == 'landscape':
        page_w, page_h = page_h, page_w

    has_text = bool(content and content.strip())
    has_title = bool(title and title.strip() and title.strip() != 'Untitled Document')
    
    # CASE A: ONLY IMAGES (or Images Primary Mode)
    if images and isinstance(images, list) and not has_text and not has_title:
        for img_path in images:
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    img_w, img_h = img.size
                    
                    # Create page matching image aspect ratio or standard page
                    page = doc.new_page(width=page_w, height=page_h)
                    
                    margin = 25
                    target_rect = fitz.Rect(margin, margin, page_w - margin, page_h - margin)
                    page.insert_image(target_rect, filename=img_path, keep_proportion=True)
                except Exception as e:
                    print(f"Error embedding image {img_path}: {e}")
                    
    # CASE B: TEXT + IMAGES OR DOCUMENT MODE
    else:
        margin = 45
        y = margin
        page = doc.new_page(width=page_w, height=page_h)
        
        # 1. Add Document Title
        if has_title:
            page.insert_text(
                fitz.Point(margin, y + 24),
                title,
                fontsize=20,
                fontname="helv",
                color=(0.06, 0.09, 0.16) # #0f172a
            )
            y += 40
            
            # Decorative line under title
            page.draw_line(
                fitz.Point(margin, y),
                fitz.Point(page_w - margin, y),
                color=(0.31, 0.27, 0.9), # Indigo
                width=1.5
            )
            y += 25

        # 2. Add Text Content
        if has_text:
            lines = content.split('\n')
            line_height = 16
            font_size = 11
            
            for line in lines:
                if y > page_h - margin - 40:
                    page = doc.new_page(width=page_w, height=page_h)
                    y = margin
                    
                page.insert_text(
                    fitz.Point(margin, y + font_size),
                    line,
                    fontsize=font_size,
                    fontname="helv",
                    color=(0.2, 0.25, 0.33)
                )
                y += line_height
            y += 20

        # 3. Add Embedded Images in exact order
        if images and isinstance(images, list):
            for img_path in images:
                if os.path.exists(img_path):
                    # Start new page for large images if space is tight
                    if y > page_h - 260:
                        page = doc.new_page(width=page_w, height=page_h)
                        y = margin
                        
                    img_rect = fitz.Rect(margin, y, page_w - margin, min(y + 320, page_h - margin))
                    page.insert_image(img_rect, filename=img_path, keep_proportion=True)
                    y += 340

    # Ensure document has at least one page
    if len(doc) == 0:
        doc.new_page(width=page_w, height=page_h)

    doc.save(output_path)
    doc.close()
    return output_path
