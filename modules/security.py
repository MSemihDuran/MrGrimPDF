import os
import fitz
from PIL import Image, ImageChops

def protect_pdf(file_path, output_path, user_password, owner_password=None, allow_print=True, allow_copy=True):
    doc = fitz.open(file_path)
    if not owner_password:
        owner_password = user_password + "_owner"
        
    perm = fitz.PDF_PERM_ACCESSIBILITY
    if allow_print:
        perm |= fitz.PDF_PERM_PRINT
    if allow_copy:
        perm |= fitz.PDF_PERM_COPY
        
    doc.save(
        output_path,
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw=user_password,
        owner_pw=owner_password,
        permissions=perm
    )
    doc.close()
    return output_path

def unlock_pdf(file_path, output_path, password=""):
    doc = fitz.open(file_path)
    if doc.is_encrypted:
        success = doc.authenticate(password)
        if not success:
            doc.close()
            raise ValueError("Invalid password for protected PDF.")
            
    doc.save(output_path, encryption=fitz.PDF_ENCRYPT_NONE, garbage=4, deflate=True)
    doc.close()
    return output_path

def sign_pdf(file_path, output_path, signature_img_path, page_num=1, x=None, y=None, width=160, height=70):
    doc = fitz.open(file_path)
    p_idx = max(0, min(len(doc) - 1, int(page_num) - 1))
    page = doc[p_idx]
    rect = page.rect
    
    if x is None:
        x = rect.width - width - 40
    if y is None:
        y = rect.height - height - 40
        
    sig_rect = fitz.Rect(x, y, x + width, y + height)
    page.insert_image(sig_rect, filename=signature_img_path, overlay=True)
    
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return output_path

def redact_pdf(file_path, output_path, search_terms=None, custom_rects=None):
    doc = fitz.open(file_path)
    
    if search_terms:
        for term in search_terms:
            if not term.strip():
                continue
            for page in doc:
                text_instances = page.search_for(term.strip())
                for inst in text_instances:
                    page.add_redact_annot(inst, fill=(0, 0, 0))
                page.apply_redactions()
                
    if custom_rects:
        for item in custom_rects:
            p_idx = int(item.get('page', 1)) - 1
            if 0 <= p_idx < len(doc):
                page = doc[p_idx]
                r = fitz.Rect(item['x'], item['y'], item['x'] + item['w'], item['y'] + item['h'])
                page.add_redact_annot(r, fill=(0, 0, 0))
                page.apply_redactions()
                
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return output_path

def compare_pdfs(file1_path, file2_path, output_path):
    doc1 = fitz.open(file1_path)
    doc2 = fitz.open(file2_path)
    
    max_pages = max(len(doc1), len(doc2))
    report_doc = fitz.open()
    
    for i in range(max_pages):
        pix1 = doc1[i].get_pixmap(dpi=120) if i < len(doc1) else None
        pix2 = doc2[i].get_pixmap(dpi=120) if i < len(doc2) else None
        
        w1 = pix1.width if pix1 else 600
        h1 = pix1.height if pix1 else 800
        w2 = pix2.width if pix2 else 600
        h2 = pix2.height if pix2 else 800
        
        total_w = w1 + w2 + 60
        max_h = max(h1, h2) + 80
        
        page = report_doc.new_page(width=total_w, height=max_h)
        
        header_rect = fitz.Rect(0, 0, total_w, 40)
        shape = page.new_shape()
        shape.draw_rect(header_rect)
        shape.finish(color=None, fill=(0.1, 0.12, 0.18))
        shape.commit()
        
        page.insert_text(fitz.Point(30, 26), f"MrGrimPDF Comparison - Page {i+1}", fontsize=14, color=(1, 1, 1))
        page.insert_text(fitz.Point(total_w / 2 + 30, 26), "Document B (Modified / New)", fontsize=12, color=(0.8, 0.9, 1))
        
        if pix1:
            page.insert_image(fitz.Rect(20, 50, 20 + w1, 50 + h1), pixmap=pix1)
        if pix2:
            page.insert_image(fitz.Rect(w1 + 40, 50, w1 + 40 + w2, 50 + h2), pixmap=pix2)
            
    doc1.close()
    doc2.close()
    
    report_doc.save(output_path, garbage=4, deflate=True)
    report_doc.close()
    return output_path
