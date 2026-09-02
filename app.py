import os
import uuid
import json
import time
import shutil
import fitz
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from modules.organize import merge_pdfs, split_pdf, remove_pages, reorder_pages, rotate_pages, crop_pdf
from modules.convert import pdf_to_word, pdf_to_images, images_to_pdf, pdf_to_excel, pdf_to_pptx, pdf_to_pdfa
from modules.optimize import compress_pdf, repair_pdf, ocr_pdf
from modules.edit import add_watermark, add_page_numbers, apply_annotations
from modules.security import protect_pdf, unlock_pdf, sign_pdf, redact_pdf, compare_pdfs
from modules.create import create_pdf_from_content
from modules.card_sheet import generate_card_sheet

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mrgrimpdf-super-secret-key-2026'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Vercel Serverless environment: /var/task is read-only, only /tmp is writable
is_serverless = bool(os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME') or not os.access(BASE_DIR, os.W_OK))

if is_serverless:
    TEMP_DIR = tempfile.gettempdir()
    UPLOAD_FOLDER = os.path.join(TEMP_DIR, 'mrgrimpdf_uploads')
    OUTPUT_FOLDER = os.path.join(TEMP_DIR, 'mrgrimpdf_outputs')
else:
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')

try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
except Exception:
    pass

@app.errorhandler(RequestEntityTooLarge)
def file_too_large(_error):
    return jsonify({"error": "Dosya boyutu 500 MB sınırını aşıyor."}), 413

def json_value(data, key, default, expected_type):
    """Parse a JSON form field and return a safe, user-facing validation error."""
    raw_value = data.get(key)
    if raw_value in (None, ''):
        return default
    if isinstance(raw_value, expected_type):
        return raw_value
    try:
        value = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid {key} value.") from exc
    if not isinstance(value, expected_type):
        raise ValueError(f"Invalid {key} value.")
    return value

def cleanup_old_files(max_age_seconds=3600):
    now = time.time()
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        try:
            if not os.path.exists(folder):
                continue
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path) and not filename.startswith('.'):
                    if now - os.path.getmtime(file_path) > max_age_seconds:
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
        except Exception:
            pass

@app.route('/')
def index():
    cleanup_old_files()
    return render_template('index.html')

@app.route('/robots.txt')
def robots():
    return send_file(os.path.join(BASE_DIR, 'static', 'robots.txt'), mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    return send_file(os.path.join(BASE_DIR, 'static', 'sitemap.xml'), mimetype='application/xml')

@app.route('/manifest.json')
def manifest():
    return send_file(os.path.join(BASE_DIR, 'static', 'manifest.json'), mimetype='application/json')

@app.route('/google7673d195cb0b2acf.html')
def google_verify():
    return send_file(os.path.join(BASE_DIR, 'static', 'google7673d195cb0b2acf.html'), mimetype='text/html')

@app.route('/favicon.ico')
def favicon():
    return send_file(os.path.join(BASE_DIR, 'static', 'img', 'favicon.png'), mimetype='image/png')

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "app": "MrGrimPDF",
        "version": "1.0.0",
        "features": [
            "merge", "split", "remove-pages", "organize", "rotate", "crop",
            "pdf-to-word", "pdf-to-images", "images-to-pdf", "pdf-to-excel", "pdf-to-pptx", "pdf-to-pdfa",
            "compress", "repair", "ocr",
            "watermark", "page-numbers", "edit",
            "protect", "unlock", "sign", "redact", "compare",
            "game-cards-a3"
        ]
    })

@app.route('/api/upload', methods=['POST'])
def upload_files():
    cleanup_old_files()
    if 'files' not in request.files and 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_files = request.files.getlist('files') or [request.files['file']]
    results = []

    for file in uploaded_files:
        if file and file.filename:
            file_id = str(uuid.uuid4())
            orig_name = secure_filename(file.filename) or "document.pdf"
            ext = os.path.splitext(orig_name)[1].lower()
            save_name = f"{file_id}_{orig_name}"
            save_path = os.path.join(UPLOAD_FOLDER, save_name)
            file.save(save_path)

            file_info = {
                "file_id": save_name,
                "original_name": orig_name,
                "size": os.path.getsize(save_path),
                "extension": ext,
                "pages": 0,
                "is_pdf": ext == '.pdf'
            }

            if ext == '.pdf':
                try:
                    doc = fitz.open(save_path)
                    file_info["pages"] = len(doc)
                    file_info["is_encrypted"] = doc.is_encrypted
                    doc.close()
                except Exception:
                    file_info["pages"] = 0

            results.append(file_info)

    return jsonify({"success": True, "files": results})

@app.route('/api/render-preview/<file_id>/<int:page_num>')
def render_preview(file_id, page_num):
    safe_name = secure_filename(file_id)
    file_path = os.path.join(UPLOAD_FOLDER, safe_name)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        doc = fitz.open(file_path)
        idx = max(0, min(len(doc) - 1, page_num - 1))
        page = doc[idx]
        pix = page.get_pixmap(dpi=100)
        img_bytes = pix.tobytes("png")
        doc.close()
        return img_bytes, 200, {'Content-Type': 'image/png'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_primary_file(request, data, out_id, key='file'):
    if key in request.files and request.files[key].filename:
        f = request.files[key]
        safe_name = f"proc_{out_id}_{secure_filename(f.filename)}"
        p = os.path.join(UPLOAD_FOLDER, safe_name)
        f.save(p)
        return p
    if 'files' in request.files:
        flist = request.files.getlist('files')
        if flist and flist[0].filename:
            f = flist[0]
            safe_name = f"proc_{out_id}_{secure_filename(f.filename)}"
            p = os.path.join(UPLOAD_FOLDER, safe_name)
            f.save(p)
            return p
    fid = data.get(key) or data.get('file_id')
    if fid:
        p = os.path.join(UPLOAD_FOLDER, secure_filename(fid))
        if os.path.exists(p):
            return p
    return None

def get_multi_files(request, data, out_id, key='files'):
    paths = []
    if key in request.files:
        for idx, f in enumerate(request.files.getlist(key)):
            if f and f.filename:
                safe_name = f"multi_{out_id}_{idx}_{secure_filename(f.filename)}"
                p = os.path.join(UPLOAD_FOLDER, safe_name)
                f.save(p)
                paths.append(p)
    if not paths and data.get('file_ids'):
        try:
            fids = json.loads(data.get('file_ids', '[]'))
            for fid in fids:
                p = os.path.join(UPLOAD_FOLDER, secure_filename(fid))
                if os.path.exists(p):
                    paths.append(p)
        except Exception:
            pass
    return paths

@app.route('/api/process/<action>', methods=['POST'])
def process_action(action):
    data = request.form.to_dict() if request.form else (request.get_json() or {})
    files = request.files
    out_id = str(uuid.uuid4())[:8]

    try:
        if action == 'merge':
            file_paths = get_multi_files(request, data, out_id)
            if not file_paths:
                return jsonify({"error": "Lütfen birleştirilecek PDF dosyalarını seçin."}), 400
            out_filename = f"MrGrimPDF_Merged_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            merge_pdfs(file_paths, out_path)

        elif action == 'split':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            mode = data.get('mode', 'all')
            ranges = data.get('ranges', '')
            extract_pages = json_value(data, 'extract_pages', [], list)
            out_path = split_pdf(file_path, OUTPUT_FOLDER, mode=mode, ranges_str=ranges, extract_pages=extract_pages)
            out_filename = os.path.basename(out_path)

        elif action == 'remove-pages':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            pages = json_value(data, 'pages', [], list)
            out_filename = f"MrGrimPDF_Removed_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            remove_pages(file_path, out_path, pages)

        elif action == 'organize':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            order = json_value(data, 'order', [], list)
            out_filename = f"MrGrimPDF_Organized_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            reorder_pages(file_path, out_path, order)

        elif action == 'rotate':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            rot_map = json_value(data, 'rotations', {}, dict)
            global_angle = int(data.get('global_angle', 0))
            removed_pages = json_value(data, 'remove_pages', [], list)
            out_filename = f"MrGrimPDF_Rotated_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            rotate_pages(file_path, out_path, rot_map, global_angle, removed_pages)

        elif action == 'crop':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            left = float(data.get('left', 0))
            top = float(data.get('top', 0))
            right = float(data.get('right', 0))
            bottom = float(data.get('bottom', 0))
            out_filename = f"MrGrimPDF_Cropped_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            crop_pdf(file_path, out_path, left, top, right, bottom)

        elif action == 'pdf-to-word':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            out_filename = f"MrGrimPDF_Converted_{out_id}.docx"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            pdf_to_word(file_path, out_path)

        elif action == 'pdf-to-images':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            fmt = data.get('format', 'jpg').lower()
            dpi = max(72, min(int(data.get('dpi', 150)), 600))
            out_path = pdf_to_images(file_path, OUTPUT_FOLDER, img_format=fmt, dpi=dpi)
            out_filename = os.path.basename(out_path)

        elif action == 'images-to-pdf':
            file_paths = get_multi_files(request, data, out_id)
            if not file_paths:
                return jsonify({"error": "Lütfen eklenecek resimleri seçin."}), 400
            out_filename = f"MrGrimPDF_Images_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            images_to_pdf(file_paths, out_path)

        elif action == 'pdf-to-excel':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            out_filename = f"MrGrimPDF_Tables_{out_id}.xlsx"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            pdf_to_excel(file_path, out_path)

        elif action == 'pdf-to-pptx':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            out_filename = f"MrGrimPDF_Slides_{out_id}.pptx"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            pdf_to_pptx(file_path, out_path)

        elif action == 'pdf-to-pdfa':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            out_filename = f"MrGrimPDF_Archival_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            pdf_to_pdfa(file_path, out_path)

        elif action == 'compress':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            level = data.get('level', 'recommended')
            out_filename = f"MrGrimPDF_Compressed_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            comp_res = compress_pdf(file_path, out_path, level=level)
            return jsonify({
                "success": True,
                "download_url": f"/download/{out_filename}",
                "filename": out_filename,
                "stats": {
                    "original_size": comp_res["original_size"],
                    "new_size": comp_res["new_size"],
                    "saved_percent": comp_res["saved_percent"]
                }
            })

        elif action == 'repair':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            out_filename = f"MrGrimPDF_Repaired_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            repair_pdf(file_path, out_path)

        elif action == 'ocr':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            lang = data.get('lang', 'tur+eng')
            out_filename = f"MrGrimPDF_OCR_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            ocr_pdf(file_path, out_path, lang=lang)

        elif action == 'watermark':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            wm_type = data.get('wm_type', 'text')
            wm_text = data.get('text', 'CONFIDENTIAL')
            opacity = float(data.get('opacity', 0.35))
            rotation = int(data.get('rotation', 45))
            position = data.get('position', 'center')
            font_size = int(data.get('font_size', 48))
            color = data.get('color', '#E11D48')
            
            img_file_path = None
            if 'image' in files:
                img = files['image']
                img_name = f"wm_{out_id}_{secure_filename(img.filename)}"
                img_file_path = os.path.join(UPLOAD_FOLDER, img_name)
                img.save(img_file_path)

            out_filename = f"MrGrimPDF_Watermarked_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            add_watermark(file_path, out_path, wm_type=wm_type, text=wm_text,
                          image_path=img_file_path, opacity=opacity, rotation=rotation,
                          position=position, font_size=font_size, color=color)

        elif action == 'page-numbers':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            fmt = data.get('format', '{page} / {total}')
            pos = data.get('position', 'bottom-center')
            fsize = int(data.get('font_size', 11))
            start_num = int(data.get('start_number', 1))
            color = data.get('color', '#4B5563')
            out_filename = f"MrGrimPDF_Numbered_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            add_page_numbers(file_path, out_path, format_str=fmt, position=pos,
                             font_size=fsize, start_num=start_num, color=color)

        elif action == 'edit':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            annots = json_value(data, 'annotations', [], list)
            overlay_path = None
            if 'annotation_image' in files and files['annotation_image'].filename:
                overlay = files['annotation_image']
                overlay_path = os.path.join(UPLOAD_FOLDER, f"annot_{out_id}_{secure_filename(overlay.filename)}")
                overlay.save(overlay_path)
            out_filename = f"MrGrimPDF_Edited_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            apply_annotations(file_path, out_path, annots, overlay_path, int(data.get('page', 1)))

        elif action == 'protect':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            pw = data.get('password', '')
            if not pw:
                return jsonify({"error": "Lütfen bir şifre girin"}), 400
            allow_print = data.get('allow_print', 'true').lower() == 'true'
            allow_copy = data.get('allow_copy', 'true').lower() == 'true'
            out_filename = f"MrGrimPDF_Protected_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            protect_pdf(file_path, out_path, user_password=pw, allow_print=allow_print, allow_copy=allow_copy)

        elif action == 'unlock':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            pw = data.get('password', '')
            out_filename = f"MrGrimPDF_Unlocked_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            unlock_pdf(file_path, out_path, password=pw)

        elif action == 'sign':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            sig_file_path = None
            if 'signature' in files:
                sig = files['signature']
                sig_name = f"sig_{out_id}_{secure_filename(sig.filename or 'sig.png')}"
                sig_file_path = os.path.join(UPLOAD_FOLDER, sig_name)
                sig.save(sig_file_path)
            elif data.get('signature_data'):
                import base64
                sig_data = data.get('signature_data').split(',')[-1]
                sig_name = f"sig_{out_id}.png"
                sig_file_path = os.path.join(UPLOAD_FOLDER, sig_name)
                with open(sig_file_path, 'wb') as f:
                    f.write(base64.b64decode(sig_data))

            page_num = int(data.get('page', 1))
            x = float(data.get('x')) if data.get('x') is not None else None
            y = float(data.get('y')) if data.get('y') is not None else None
            out_filename = f"MrGrimPDF_Signed_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            sign_pdf(file_path, out_path, sig_file_path, page_num=page_num, x=x, y=y)

        elif action == 'redact':
            file_path = get_primary_file(request, data, out_id)
            if not file_path:
                return jsonify({"error": "Lütfen bir PDF dosyası seçin."}), 400
            search_terms = json_value(data, 'terms', [], list)
            rects = json_value(data, 'rectangles', [], list)
            out_filename = f"MrGrimPDF_Redacted_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            redact_pdf(file_path, out_path, search_terms=search_terms, custom_rects=rects)

        elif action == 'compare':
            fpath1 = get_primary_file(request, data, out_id, 'file_1') or get_primary_file(request, data, out_id, 'file_id_1')
            fpath2 = get_primary_file(request, data, out_id, 'file_2') or get_primary_file(request, data, out_id, 'file_id_2')
            if not fpath1 or not fpath2:
                return jsonify({"error": "Lütfen karşılaştırılacak iki PDF dosyasını seçin."}), 400
            out_filename = f"MrGrimPDF_Comparison_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            compare_pdfs(fpath1, fpath2, out_path)

        elif action == 'create-pdf':
            doc_title = data.get('title', '')
            doc_content = data.get('content', '')
            orientation = data.get('orientation', 'portrait')
            page_size = data.get('page_size', 'a4')
            
            # 1. Direct multipart image uploads (100% serverless safe - single request)
            uploaded_images = request.files.getlist('images') or request.files.getlist('files')
            image_paths = []
            if uploaded_images:
                for idx, img_file in enumerate(uploaded_images):
                    if img_file and img_file.filename:
                        safe_orig = secure_filename(img_file.filename) or f"img_{idx}.png"
                        tmp_name = f"create_{out_id}_{idx}_{safe_orig}"
                        tmp_path = os.path.join(UPLOAD_FOLDER, tmp_name)
                        img_file.save(tmp_path)
                        image_paths.append(tmp_path)
                        
            # 2. Fallback to image_ids if sent as JSON string
            if not image_paths and data.get('image_ids'):
                try:
                    image_ids = json.loads(data.get('image_ids', '[]'))
                    for fid in image_ids:
                        if fid:
                            p = os.path.join(UPLOAD_FOLDER, secure_filename(fid))
                            if os.path.exists(p):
                                image_paths.append(p)
                except Exception:
                    pass
            
            # Format filename with current date & time or custom name
            import datetime
            now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            custom_name = data.get('custom_name', '').strip()
            if custom_name:
                safe_base = secure_filename(custom_name).replace('.pdf', '')
                out_filename = f"{safe_base}.pdf" if safe_base else f"MrGrimPDF_{now_str}.pdf"
            else:
                out_filename = f"MrGrimPDF_{now_str}.pdf"
                
            custom_w = data.get('custom_w')
            custom_h = data.get('custom_h')
            custom_unit = data.get('custom_unit', 'mm')
            margin_type = data.get('margin_type', 'standard')
            custom_margin = data.get('custom_margin')
            margin_unit = data.get('margin_unit', 'mm')
            
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            create_pdf_from_content(doc_title, doc_content, out_path, orientation=orientation, 
                                    page_size=page_size, custom_w=custom_w, custom_h=custom_h, custom_unit=custom_unit,
                                    margin_type=margin_type, custom_margin=custom_margin, margin_unit=margin_unit,
                                    images=image_paths)

        elif action == 'game-cards-a3':
            # 1. Direct multipart image uploads
            uploaded_images = request.files.getlist('images') or request.files.getlist('files')
            image_paths = []
            if uploaded_images:
                for idx, img_file in enumerate(uploaded_images):
                    if img_file and img_file.filename:
                        safe_orig = secure_filename(img_file.filename) or f"card_{idx}.png"
                        tmp_name = f"card_{out_id}_{idx}_{safe_orig}"
                        tmp_path = os.path.join(UPLOAD_FOLDER, tmp_name)
                        img_file.save(tmp_path)
                        image_paths.append(tmp_path)

            # 2. Fallback to image_ids / file_ids
            if not image_paths:
                fids_raw = data.get('image_ids') or data.get('file_ids')
                if fids_raw:
                    try:
                        fids = json.loads(fids_raw) if isinstance(fids_raw, str) else fids_raw
                        for fid in fids:
                            if fid:
                                p = os.path.join(UPLOAD_FOLDER, secure_filename(fid))
                                if os.path.exists(p):
                                    image_paths.append(p)
                    except Exception:
                        pass

            if not image_paths:
                return jsonify({"error": "Lütfen en az bir oyun kartı görseli yükleyin."}), 400

            fill_mode = data.get('fill_mode', 'uploaded_only')
            rotation = data.get('rotation', 'ccw90')
            empty_color = data.get('empty_color', 'black')
            crop_marks = data.get('crop_marks', 'none')
            export_format = data.get('export_format', 'png').lower()
            grid_order = data.get('grid_order', 'col_first')
            try:
                gap_mm = float(data.get('gap_mm', 2.5))
            except (ValueError, TypeError):
                gap_mm = 2.5

            import datetime
            now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            custom_name = data.get('custom_name', '').strip()
            ext = 'pdf' if export_format == 'pdf' else ('jpg' if export_format in ['jpg', 'jpeg'] else 'png')

            if custom_name:
                safe_base = secure_filename(custom_name).replace(f'.{ext}', '')
                out_filename = f"{safe_base}.{ext}" if safe_base else f"MrGrimPDF_CardSheet_{now_str}.{ext}"
            else:
                out_filename = f"MrGrimPDF_CardSheet_A3_400DPI_{now_str}.{ext}"

            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            generate_card_sheet(
                image_paths=image_paths,
                output_path=out_path,
                dpi=400,
                gap_mm=gap_mm,
                fill_mode=fill_mode,
                rotation=rotation,
                empty_color=empty_color,
                crop_marks=crop_marks,
                export_format=export_format,
                grid_order=grid_order
            )

        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400

        return jsonify({
            "success": True,
            "download_url": f"/download/{out_filename}",
            "filename": out_filename,
            "size": os.path.getsize(out_path)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    safe_name = secure_filename(filename)
    file_path = os.path.join(OUTPUT_FOLDER, safe_name)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=safe_name)
    return jsonify({"error": "File not found or expired"}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
