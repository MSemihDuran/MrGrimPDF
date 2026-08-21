import os
import uuid
import json
import time
import shutil
import fitz
from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename

from modules.organize import merge_pdfs, split_pdf, remove_pages, reorder_pages, rotate_pages, crop_pdf
from modules.convert import pdf_to_word, pdf_to_images, images_to_pdf, pdf_to_excel, pdf_to_pptx, pdf_to_pdfa
from modules.optimize import compress_pdf, repair_pdf, ocr_pdf
from modules.edit import add_watermark, add_page_numbers, apply_annotations
from modules.security import protect_pdf, unlock_pdf, sign_pdf, redact_pdf, compare_pdfs

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mrgrimpdf-super-secret-key-2026'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def cleanup_old_files(max_age_seconds=3600):
    now = time.time()
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        try:
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
            "protect", "unlock", "sign", "redact", "compare"
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

@app.route('/api/process/<action>', methods=['POST'])
def process_action(action):
    data = request.form.to_dict() if request.form else (request.get_json() or {})
    files = request.files
    out_id = str(uuid.uuid4())[:8]

    try:
        if action == 'merge':
            file_ids = json.loads(data.get('file_ids', '[]'))
            file_paths = [os.path.join(UPLOAD_FOLDER, secure_filename(fid)) for fid in file_ids]
            out_filename = f"MrGrimPDF_Merged_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            merge_pdfs(file_paths, out_path)

        elif action == 'split':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            mode = data.get('mode', 'all')
            ranges = data.get('ranges', '')
            extract_pages = json.loads(data.get('extract_pages', '[]'))
            out_path = split_pdf(file_path, OUTPUT_FOLDER, mode=mode, ranges_str=ranges, extract_pages=extract_pages)
            out_filename = os.path.basename(out_path)

        elif action == 'remove-pages':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            pages = json.loads(data.get('pages', '[]'))
            out_filename = f"MrGrimPDF_Removed_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            remove_pages(file_path, out_path, pages)

        elif action == 'organize':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            order = json.loads(data.get('order', '[]'))
            out_filename = f"MrGrimPDF_Organized_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            reorder_pages(file_path, out_path, order)

        elif action == 'rotate':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            rot_map = json.loads(data.get('rotations', '{}'))
            global_angle = int(data.get('global_angle', 0))
            out_filename = f"MrGrimPDF_Rotated_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            rotate_pages(file_path, out_path, rot_map, global_angle)

        elif action == 'crop':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            left = float(data.get('left', 0))
            top = float(data.get('top', 0))
            right = float(data.get('right', 0))
            bottom = float(data.get('bottom', 0))
            out_filename = f"MrGrimPDF_Cropped_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            crop_pdf(file_path, out_path, left, top, right, bottom)

        elif action == 'pdf-to-word':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            out_filename = f"MrGrimPDF_Converted_{out_id}.docx"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            pdf_to_word(file_path, out_path)

        elif action == 'pdf-to-images':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            fmt = data.get('format', 'jpg')
            dpi = int(data.get('dpi', 150))
            out_path = pdf_to_images(file_path, OUTPUT_FOLDER, img_format=fmt, dpi=dpi)
            out_filename = os.path.basename(out_path)

        elif action == 'images-to-pdf':
            file_ids = json.loads(data.get('file_ids', '[]'))
            file_paths = [os.path.join(UPLOAD_FOLDER, secure_filename(fid)) for fid in file_ids]
            out_filename = f"MrGrimPDF_Images_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            images_to_pdf(file_paths, out_path)

        elif action == 'pdf-to-excel':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            out_filename = f"MrGrimPDF_Tables_{out_id}.xlsx"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            pdf_to_excel(file_path, out_path)

        elif action == 'pdf-to-pptx':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            out_filename = f"MrGrimPDF_Slides_{out_id}.pptx"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            pdf_to_pptx(file_path, out_path)

        elif action == 'pdf-to-pdfa':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            out_filename = f"MrGrimPDF_Archival_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            pdf_to_pdfa(file_path, out_path)

        elif action == 'compress':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
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
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            out_filename = f"MrGrimPDF_Repaired_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            repair_pdf(file_path, out_path)

        elif action == 'ocr':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            lang = data.get('lang', 'tur+eng')
            out_filename = f"MrGrimPDF_OCR_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            ocr_pdf(file_path, out_path, lang=lang)

        elif action == 'watermark':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
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
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
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
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            annots = json.loads(data.get('annotations', '[]'))
            out_filename = f"MrGrimPDF_Edited_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            apply_annotations(file_path, out_path, annots)

        elif action == 'protect':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            pw = data.get('password', '')
            if not pw:
                return jsonify({"error": "Password cannot be empty"}), 400
            allow_print = data.get('allow_print', 'true').lower() == 'true'
            allow_copy = data.get('allow_copy', 'true').lower() == 'true'
            out_filename = f"MrGrimPDF_Protected_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            protect_pdf(file_path, out_path, user_password=pw, allow_print=allow_print, allow_copy=allow_copy)

        elif action == 'unlock':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            pw = data.get('password', '')
            out_filename = f"MrGrimPDF_Unlocked_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            unlock_pdf(file_path, out_path, password=pw)

        elif action == 'sign':
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
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
            file_id = data.get('file_id')
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file_id))
            search_terms = json.loads(data.get('terms', '[]'))
            rects = json.loads(data.get('rectangles', '[]'))
            out_filename = f"MrGrimPDF_Redacted_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            redact_pdf(file_path, out_path, search_terms=search_terms, custom_rects=rects)

        elif action == 'compare':
            fid1 = data.get('file_id_1')
            fid2 = data.get('file_id_2')
            fpath1 = os.path.join(UPLOAD_FOLDER, secure_filename(fid1))
            fpath2 = os.path.join(UPLOAD_FOLDER, secure_filename(fid2))
            out_filename = f"MrGrimPDF_Comparison_{out_id}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            compare_pdfs(fpath1, fpath2, out_path)

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
