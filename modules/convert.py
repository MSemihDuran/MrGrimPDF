import os
import fitz
from PIL import Image
import zipfile
import xlsxwriter
from pptx import Presentation
from pptx.util import Inches
from pdf2docx import Converter

def pdf_to_word(file_path, output_path):
    cv = Converter(file_path)
    cv.convert(output_path, start=0, end=None)
    cv.close()
    return output_path

def pdf_to_images(file_path, output_dir, img_format='jpg', dpi=150):
    doc = fitz.open(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    created_images = []
    
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat, alpha=False if img_format.lower() in ['jpg', 'jpeg'] else True)
        ext = 'jpg' if img_format.lower() in ['jpg', 'jpeg'] else 'png'
        img_file = os.path.join(output_dir, f"{base_name}_page_{i+1}.{ext}")
        pix.save(img_file)
        created_images.append(img_file)
        
    doc.close()
    
    if len(created_images) == 1:
        return created_images[0]
    else:
        zip_path = os.path.join(output_dir, f"{base_name}_images.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for img in created_images:
                zf.write(img, os.path.basename(img))
        return zip_path

def images_to_pdf(image_paths, output_path):
    pdf_doc = fitz.open()
    for img_path in image_paths:
        if os.path.exists(img_path):
            img = Image.open(img_path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            img_doc = fitz.open(img_path)
            rect = img_doc[0].rect
            pdf_bytes = img_doc.convert_to_pdf()
            img_pdf = fitz.open("pdf", pdf_bytes)
            pdf_doc.insert_pdf(img_pdf)
            img_doc.close()
            img_pdf.close()
            
    pdf_doc.save(output_path)
    pdf_doc.close()
    return output_path

def pdf_to_excel(file_path, output_path):
    doc = fitz.open(file_path)
    workbook = xlsxwriter.Workbook(output_path)
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#E2E8F0', 'border': 1})
    cell_fmt = workbook.add_format({'border': 1, 'text_wrap': True})

    for i, page in enumerate(doc):
        sheet_name = f"Page_{i+1}"
        worksheet = workbook.add_worksheet(sheet_name[:31])
        
        tables = page.find_tables()
        row_cursor = 0
        
        if tables.tables:
            for tab_idx, tab in enumerate(tables):
                worksheet.write(row_cursor, 0, f"Table {tab_idx+1}", header_fmt)
                row_cursor += 1
                for r_idx, row in enumerate(tab.extract()):
                    for c_idx, cell in enumerate(row):
                        worksheet.write(row_cursor + r_idx, c_idx, cell or "", cell_fmt)
                row_cursor += len(tab.extract()) + 2
        else:
            blocks = page.get_text("blocks")
            for b in blocks:
                text_content = b[4].strip()
                if text_content:
                    lines = text_content.split("\n")
                    for line in lines:
                        worksheet.write(row_cursor, 0, line, cell_fmt)
                        row_cursor += 1
                    row_cursor += 1
                    
    workbook.close()
    doc.close()
    return output_path

def pdf_to_pptx(file_path, output_path, dpi=120):
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)
    blank_slide_layout = prs.slide_layouts[6]
    
    doc = fitz.open(file_path)
    temp_dir = os.path.dirname(output_path)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_temp = os.path.join(temp_dir, f"_temp_slide_{i}.png")
        pix.save(img_temp)
        
        slide = prs.slides.add_slide(blank_slide_layout)
        slide.shapes.add_picture(img_temp, 0, 0, width=prs.slide_width, height=prs.slide_height)
        
        if os.path.exists(img_temp):
            os.remove(img_temp)
            
    doc.close()
    prs.save(output_path)
    return output_path

def pdf_to_pdfa(file_path, output_path):
    doc = fitz.open(file_path)
    meta = doc.metadata
    meta['producer'] = 'MrGrimPDF'
    meta['format'] = 'PDF/A-1b'
    doc.set_metadata(meta)
    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()
    return output_path
