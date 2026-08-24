import os
import fitz  # PyMuPDF
import io
import shutil
from PIL import Image

def compress_pdf(file_path, output_path, level='recommended'):
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)
    level = str(level).lower()
    
    # Distinct, carefully tuned compression profiles
    if level == 'extreme':
        max_dim = 1000
        jpg_quality = 52
        png_to_jpg_if_opaque = True
        dpi_target = 110
    elif level == 'low':
        max_dim = 2400
        jpg_quality = 88
        png_to_jpg_if_opaque = False
        dpi_target = 220
    else:  # recommended
        max_dim = 1600
        jpg_quality = 74
        png_to_jpg_if_opaque = True
        dpi_target = 150

    original_size = os.path.getsize(file_path)
    if original_size == 0:
        shutil.copyfile(file_path, output_path)
        return {"output_path": output_path, "original_size": 0, "new_size": 0, "saved_percent": 0}

    # Step 1: Smart Embedded Image Optimization (Preserves 100% Vector Text & Layout)
    doc = fitz.open(file_path)
    processed_xrefs = set()
    images_compressed = 0
    
    for page in doc:
        img_list = page.get_images(full=True)
        for img_info in img_list:
            xref = img_info[0]
            if xref in processed_xrefs:
                continue
            processed_xrefs.add(xref)
            
            try:
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue
                
                raw_bytes = base_image["image"]
                orig_bytes_len = len(raw_bytes)
                if orig_bytes_len < 1024:  # Don't touch tiny icons/bullets
                    continue
                    
                img_ext = base_image.get("ext", "").lower()
                pil_img = Image.open(io.BytesIO(raw_bytes))
                
                orig_w, orig_h = pil_img.size
                needs_resize = (orig_w > max_dim or orig_h > max_dim)
                
                if needs_resize:
                    scale = min(max_dim / orig_w, max_dim / orig_h)
                    new_w = max(1, int(orig_w * scale))
                    new_h = max(1, int(orig_h * scale))
                    pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                out_io = io.BytesIO()
                
                # Check for transparency
                has_alpha = pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info)
                
                if not has_alpha and (img_ext in ['jpg', 'jpeg'] or png_to_jpg_if_opaque or pil_img.mode == 'RGB'):
                    if pil_img.mode != "RGB":
                        pil_img = pil_img.convert("RGB")
                    pil_img.save(out_io, format="JPEG", quality=jpg_quality, optimize=True, progressive=True)
                else:
                    if has_alpha:
                        pil_img.save(out_io, format="PNG", optimize=True)
                    else:
                        if pil_img.mode != "RGB":
                            pil_img = pil_img.convert("RGB")
                        pil_img.save(out_io, format="JPEG", quality=jpg_quality, optimize=True)
                
                comp_bytes = out_io.getvalue()
                if len(comp_bytes) < orig_bytes_len:
                    doc.update_stream(xref, comp_bytes)
                    images_compressed += 1
            except Exception:
                continue

    # Step 2: Save with structural garbage cleanup and stream deflation
    temp_out = os.path.join(out_dir, f"temp_comp_{os.path.basename(output_path)}")
    doc.save(
        temp_out,
        garbage=4,
        deflate=True,
        deflate_images=True,
        deflate_fonts=True,
        clean=True,
        linear=False
    )
    doc.close()
    
    comp_size = os.path.getsize(temp_out)
    
    # Step 3: If document had no standard XObject images (e.g. heavy raster scan pages where images are drawn on content streams),
    # evaluate visual raster optimization for extreme / recommended modes:
    if comp_size >= original_size * 0.92 and level in ('extreme', 'recommended'):
        try:
            render_doc = fitz.open(file_path)
            rendered_out = os.path.join(out_dir, f"temp_render_{os.path.basename(output_path)}")
            new_pdf = fitz.open()
            
            scale = dpi_target / 72.0
            matrix = fitz.Matrix(scale, scale)
            
            for p in render_doc:
                pix = p.get_pixmap(matrix=matrix, alpha=False)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img_io = io.BytesIO()
                img.save(img_io, format="JPEG", quality=jpg_quality, optimize=True, progressive=True)
                
                rect = p.rect
                page_new = new_pdf.new_page(width=rect.width, height=rect.height)
                page_new.insert_image(page_new.rect, stream=img_io.getvalue())
            
            new_pdf.save(rendered_out, garbage=4, deflate=True, clean=True)
            new_pdf.close()
            render_doc.close()
            
            rendered_size = os.path.getsize(rendered_out)
            if rendered_size < comp_size:
                if os.path.exists(temp_out):
                    os.remove(temp_out)
                temp_out = rendered_out
                comp_size = rendered_size
            else:
                if os.path.exists(rendered_out):
                    os.remove(rendered_out)
        except Exception:
            pass

    # Save final result
    if comp_size < original_size:
        if os.path.exists(output_path):
            os.remove(output_path)
        os.replace(temp_out, output_path)
    else:
        if os.path.exists(temp_out):
            os.remove(temp_out)
        shutil.copyfile(file_path, output_path)

    final_size = os.path.getsize(output_path)
    saved_pct = max(0, round(((original_size - final_size) / original_size) * 100, 1)) if original_size > 0 else 0

    return {
        "output_path": output_path,
        "original_size": original_size,
        "new_size": final_size,
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
