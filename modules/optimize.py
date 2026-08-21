import os
import fitz
import io
from PIL import Image

def compress_pdf(file_path, output_path, level='recommended'):
    doc = fitz.open(file_path)
    
    if level == 'extreme':
        img_quality = 50
        max_dim = 1000
    elif level == 'low':
        img_quality = 85
        max_dim = 2400
    else:
        img_quality = 70
        max_dim = 1600

    for page in doc:
        img_list = page.get_images(full=True)
        for img_info in img_list:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue
                image_bytes = base_image["image"]
                img_ext = base_image["ext"]
                
                pil_img = Image.open(io.BytesIO(image_bytes))
                
                orig_w, orig_h = pil_img.size
                if orig_w > max_dim or orig_h > max_dim:
                    scale = min(max_dim / orig_w, max_dim / orig_h)
                    new_w = int(orig_w * scale)
                    new_h = int(orig_h * scale)
                    pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                if pil_img.mode in ("RGBA", "P") and img_ext.lower() in ['jpg', 'jpeg']:
                    pil_img = pil_img.convert("RGB")
                    
                out_io = io.BytesIO()
                if pil_img.mode in ("RGB", "L"):
                    pil_img.save(out_io, format="JPEG", quality=img_quality, optimize=True)
                else:
                    pil_img.save(out_io, format="PNG", optimize=True)
                    
                compressed_bytes = out_io.getvalue()
                
                if len(compressed_bytes) < len(image_bytes):
                    doc.update_stream(xref, compressed_bytes)
            except Exception:
                continue

    doc.save(
        output_path,
        garbage=4,
        deflate=True,
        clean=True
    )
    doc.close()
    
    orig_size = os.path.getsize(file_path)
    new_size = os.path.getsize(output_path)
    saved_pct = round(((orig_size - new_size) / orig_size) * 100, 1) if orig_size > 0 else 0
    
    return {
        "output_path": output_path,
        "original_size": orig_size,
        "new_size": new_size,
        "saved_percent": saved_pct
    }

def repair_pdf(file_path, output_path):
    doc = fitz.open(file_path)
    doc.save(output_path, garbage=4, clean=True, deflate=True)
    doc.close()
    return output_path

def ocr_pdf(file_path, output_path, lang='tur+eng'):
    doc = fitz.open(file_path)
    ocr_doc = fitz.open()

    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        
        try:
            page_ocr_pdf = fitz.open("pdf", page.get_pdf_ocr(language=lang, dpi=200))
            ocr_doc.insert_pdf(page_ocr_pdf)
            page_ocr_pdf.close()
        except Exception:
            img_doc = fitz.open("png", img_bytes)
            pdf_bytes = img_doc.convert_to_pdf()
            temp_pdf = fitz.open("pdf", pdf_bytes)
            ocr_doc.insert_pdf(temp_pdf)
            img_doc.close()
            temp_pdf.close()

    ocr_doc.save(output_path, garbage=4, deflate=True)
    ocr_doc.close()
    doc.close()
    return output_path
