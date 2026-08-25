import os
import fitz  # PyMuPDF
import io
import shutil
from PIL import Image

def compress_pdf(file_path, output_path, level='recommended'):
    """
    World-class multi-pass PDF compression engine (iLovePDF / Acrobat Pro grade).
    Intelligently re-encodes embedded image streams, downsamples excessive DPI with Lanczos,
    updates XObject dictionaries, and deflates structural streams with zero vector degradation.
    """
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)
    level = str(level).lower()

    if level == 'extreme':
        max_dim = 1300
        jpg_quality = 70
        subsample = 1
        dpi_target = 130
    elif level == 'low':
        max_dim = 2800
        jpg_quality = 90
        subsample = 0  # 4:4:4 full chroma
        dpi_target = 250
    else:  # recommended (iLovePDF default equivalent)
        max_dim = 1900
        jpg_quality = 82
        subsample = 0  # 4:4:4 full chroma - crystal clear edges and text
        dpi_target = 180

    original_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    if original_size == 0:
        if os.path.exists(file_path):
            shutil.copyfile(file_path, output_path)
        return {"output_path": output_path, "original_size": 0, "new_size": 0, "saved_percent": 0}

    temp_out = os.path.join(out_dir, f"temp_comp_{os.path.basename(output_path)}")
    doc = fitz.open(file_path)
    
    # 1. Native PyMuPDF image rewrite pass (handles standard high-DPI images)
    try:
        doc.rewrite_images(
            dpi_threshold=dpi_target + 30,
            dpi_target=dpi_target,
            quality=jpg_quality,
            lossy=True,
            lossless=True,
            color=True,
            gray=True
        )
    except Exception:
        pass

    # 2. Deep Image XObject Inspection & Re-encoding Pass
    processed_xrefs = set()
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

                raw_bytes = base_image.get("image")
                if not raw_bytes or len(raw_bytes) < 2048:
                    continue

                orig_len = len(raw_bytes)
                pil_img = Image.open(io.BytesIO(raw_bytes))
                orig_w, orig_h = pil_img.size

                # Calculate resize if dimensions exceed threshold
                needs_resize = (orig_w > max_dim or orig_h > max_dim)
                if needs_resize:
                    scale = min(max_dim / orig_w, max_dim / orig_h)
                    target_w = max(1, int(orig_w * scale))
                    target_h = max(1, int(orig_h * scale))
                    pil_img = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                else:
                    target_w, target_h = orig_w, orig_h

                has_alpha = pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info)
                out_io = io.BytesIO()

                if has_alpha:
                    pil_img.save(out_io, format="PNG", optimize=True)
                    new_bytes = out_io.getvalue()
                    if len(new_bytes) < orig_len:
                        doc.xref_set_key(xref, "Width", str(target_w))
                        doc.xref_set_key(xref, "Height", str(target_h))
                        doc.xref_set_key(xref, "Filter", "/FlateDecode")
                        doc.xref_set_key(xref, "DecodeParms", "null")
                        doc.update_stream(xref, new_bytes)
                else:
                    if pil_img.mode not in ("RGB", "L"):
                        pil_img = pil_img.convert("RGB")
                    
                    pil_img.save(
                        out_io,
                        format="JPEG",
                        quality=jpg_quality,
                        optimize=True,
                        progressive=True,
                        subsampling=subsample
                    )
                    new_bytes = out_io.getvalue()
                    if len(new_bytes) < orig_len:
                        doc.xref_set_key(xref, "Width", str(target_w))
                        doc.xref_set_key(xref, "Height", str(target_h))
                        doc.xref_set_key(xref, "Filter", "/DCTDecode")
                        doc.xref_set_key(xref, "ColorSpace", "/DeviceRGB" if pil_img.mode == "RGB" else "/DeviceGray")
                        doc.xref_set_key(xref, "BitsPerComponent", "8")
                        doc.xref_set_key(xref, "DecodeParms", "null")
                        doc.update_stream(xref, new_bytes)
            except Exception:
                continue

    # 3. Save with full garbage collection and stream deflation
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

    comp_size = os.path.getsize(temp_out) if os.path.exists(temp_out) else original_size

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
