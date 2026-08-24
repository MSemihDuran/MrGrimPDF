import os
import fitz
from PIL import Image

def parse_dimension_to_points(value, unit='mm'):
    """Convert mm, cm, inch, or pt to PDF points (72 points = 1 inch = 25.4 mm)."""
    try:
        val = float(value)
    except (ValueError, TypeError):
        return 0.0
        
    unit = str(unit).lower().strip()
    if unit in ['mm', 'millimeter', 'millimeters']:
        return val * (72.0 / 25.4)
    elif unit in ['cm', 'centimeter', 'centimeters']:
        return val * (72.0 / 2.54)
    elif unit in ['in', 'inch', 'inches']:
        return val * 72.0
    elif unit in ['pt', 'point', 'points', 'px']:
        return val
    return val * (72.0 / 25.4)

STANDARD_SIZES = {
    'a0': (2384, 3370),
    'a1': (1684, 2384),
    'a2': (1191, 1684),
    'a3': (842, 1191),
    'a4': (595, 842),
    'a5': (420, 595),
    'a6': (298, 420),
    'b4': (709, 1001),
    'b5': (499, 709),
    'letter': (612, 792),
    'legal': (612, 1008),
    'tabloid': (792, 1224),
    'ledger': (1224, 792),
    'executive': (522, 756),
    'postcard': (283, 419)
}

def create_pdf_from_content(title, content, output_path, orientation='portrait', page_size='a4', 
                            custom_w=None, custom_h=None, custom_unit='mm',
                            margin_type='standard', custom_margin=None, margin_unit='mm',
                            images=None):
    doc = fitz.open()
    
    # 1. Determine Page Dimensions
    page_key = str(page_size).lower().strip()
    if page_key == 'custom' and custom_w and custom_h:
        page_w = parse_dimension_to_points(custom_w, custom_unit)
        page_h = parse_dimension_to_points(custom_h, custom_unit)
        if page_w <= 0: page_w = 595.0
        if page_h <= 0: page_h = 842.0
    elif page_key in STANDARD_SIZES:
        page_w, page_h = [float(x) for x in STANDARD_SIZES[page_key]]
    elif page_key == 'fit':
        page_w, page_h = (595.0, 842.0)
    else:
        page_w, page_h = (595.0, 842.0) # default A4
        
    if orientation.lower() == 'landscape':
        page_w, page_h = max(page_w, page_h), min(page_w, page_h)
    else:
        page_w, page_h = min(page_w, page_h), max(page_w, page_h)

    # 2. Determine Margins (Points)
    if margin_type == 'none':
        margin = 0.0
    elif margin_type == 'small':
        margin = 15.0 # ~5mm
    elif margin_type == 'large':
        margin = 54.0 # ~19mm
    elif margin_type == 'custom' and custom_margin is not None:
        margin = parse_dimension_to_points(custom_margin, margin_unit)
    else: # standard
        margin = 32.0 # ~11mm

    has_text = bool(content and content.strip())
    has_title = bool(title and title.strip() and title.strip() not in ['Untitled Document', 'Başlıksız Belge'])
    valid_images = [img for img in (images or []) if os.path.exists(img)]
    
    # CASE A: IMAGES PRESENT (Gallery / Images to PDF Mode)
    if valid_images and not has_text:
        for img_path in valid_images:
            try:
                img = Image.open(img_path)
                img_w, img_h = img.size
                
                if page_key == 'fit':
                    cur_w = float(img_w)
                    cur_h = float(img_h)
                    page = doc.new_page(width=cur_w, height=cur_h)
                    rect = fitz.Rect(0, 0, cur_w, cur_h)
                    page.insert_image(rect, filename=img_path)
                else:
                    page = doc.new_page(width=page_w, height=page_h)
                    if margin <= 0:
                        target_rect = fitz.Rect(0, 0, page_w, page_h)
                    else:
                        target_rect = fitz.Rect(margin, margin, page_w - margin, page_h - margin)
                    page.insert_image(target_rect, filename=img_path, keep_proportion=True)
            except Exception as e:
                print(f"Error embedding image {img_path}: {e}")
                
    # CASE B: TEXT + OPTIONAL IMAGES DOCUMENT MODE
    elif has_text or has_title or not valid_images:
        doc_margin = max(margin, 25.0)
        y = doc_margin
        page = doc.new_page(width=page_w, height=page_h)
        
        # Add Title
        if has_title:
            page.insert_text(
                fitz.Point(doc_margin, y + 22),
                title,
                fontsize=18,
                fontname="helv",
                color=(0.06, 0.09, 0.16)
            )
            y += 36
            page.draw_line(
                fitz.Point(doc_margin, y),
                fitz.Point(page_w - doc_margin, y),
                color=(0.31, 0.27, 0.9),
                width=1.2
            )
            y += 20

        # Add Text
        if has_text:
            lines = content.split('\n')
            line_height = 16
            font_size = 11
            
            for line in lines:
                if y > page_h - doc_margin - 30:
                    page = doc.new_page(width=page_w, height=page_h)
                    y = doc_margin
                    
                page.insert_text(
                    fitz.Point(doc_margin, y + font_size),
                    line,
                    fontsize=font_size,
                    fontname="helv",
                    color=(0.2, 0.25, 0.33)
                )
                y += line_height
            y += 20

        # Add Embedded Images
        if valid_images:
            for img_path in valid_images:
                if y > page_h - 260:
                    page = doc.new_page(width=page_w, height=page_h)
                    y = doc_margin
                    
                img_rect = fitz.Rect(doc_margin, y, page_w - doc_margin, min(y + 320, page_h - doc_margin))
                page.insert_image(img_rect, filename=img_path, keep_proportion=True)
                y += 340

    if len(doc) == 0:
        doc.new_page(width=page_w, height=page_h)

    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)
    
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception:
            pass

    doc.save(output_path, deflate=True)
    doc.close()
    return output_path
