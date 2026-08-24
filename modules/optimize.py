import os
import fitz
import io
from PIL import Image

def compress_pdf(file_path, output_path, level='recommended'):
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)
    
    doc = fitz.open(file_path)
    
    if level == 'extreme':
        img_quality = 45
        max_dim = 900
    elif level == 'low':
        img_quality = 85
        max_dim = 2200
    else:
        img_quality = 65
        max_dim = 1400

    processed_xrefs = set()
    for page in doc:
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            if xref in processed_xrefs:
                continue
            processed_xrefs.add(xref)
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
                
                if pil_img.mode in ("RGBA", "P"):
                    pil_img = pil_img.convert("RGB")
                    
                out_io = io.BytesIO()
                if pil_img.mode in ("RGB", "L"):
                    pil_img.save(out_io, format="JPEG", quality=img_quality, optimize=True)
                else:
                    pil_img.save(out_io, format="PNG", optimize=True)
                    
                compressed_bytes = out_io.getvalue()
                
                if len(compressed_bytes) < len(image_bytes):
                    # update_stream only changes bytes, not the image object's
                    # filter metadata; replace_image updates both and prevents
                    # broken/corrupted PDFs after compression.
                    page.replace_image(xref, stream=compressed_bytes)
            except Exception:
                continue

    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception:
            pass

    doc.save(
        output_path,
        garbage=4,
        deflate=True,
        clean=True
    )
    doc.close()
    
    orig_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    new_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    saved_pct = max(0, round(((orig_size - new_size) / orig_size) * 100, 1)) if orig_size > 0 else 0
    
    return {
        "output_path": output_path,
        "original_size": orig_size,
        "new_size": new_size,
        "saved_percent": saved_pct
    }

def repair_pdf(file_path, output_path):
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(file_path)
    doc.save(output_path, garbage=4, clean=True, deflate=True)
    doc.close()
    return output_path

def ocr_pdf(file_path, output_path, lang='tur+eng'):
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(file_path)
    ocr_doc = fitz.open()

    for i, page in enumerate(doc):
        try:
            page_ocr_pdf = fitz.open("pdf", page.get_pdf_ocr(language=lang, dpi=150))
            ocr_doc.insert_pdf(page_ocr_pdf)
            page_ocr_pdf.close()
        except Exception as exc:
            ocr_doc.close()
            doc.close()
            raise RuntimeError(
                "OCR could not run. Install Tesseract and the selected language data "
                f"on the server. Details: {exc}"
            ) from exc

    ocr_doc.save(output_path, garbage=4, deflate=True)
    ocr_doc.close()
    doc.close()
    return output_path
