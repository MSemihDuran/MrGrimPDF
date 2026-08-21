import os
import sys
import fitz
from PIL import Image, ImageDraw

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from modules.organize import merge_pdfs, split_pdf, remove_pages, reorder_pages, rotate_pages, crop_pdf
from modules.convert import pdf_to_word, pdf_to_images, images_to_pdf, pdf_to_excel, pdf_to_pptx, pdf_to_pdfa
from modules.optimize import compress_pdf, repair_pdf, ocr_pdf
from modules.edit import add_watermark, add_page_numbers, apply_annotations
from modules.security import protect_pdf, unlock_pdf, sign_pdf, redact_pdf, compare_pdfs

TEST_DIR = os.path.join(os.path.dirname(__file__), 'test_sandbox')
os.makedirs(TEST_DIR, exist_ok=True)

def create_sample_pdf(filename, num_pages=3):
    path = os.path.join(TEST_DIR, filename)
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 80), f"MrGrimPDF Test Document - Page {i+1}", fontsize=18, color=(0.1, 0.2, 0.5))
        page.insert_text((50, 130), "Confidential info: SECRET_PASSWORD_123 and TCKN 12345678901", fontsize=12)
        page.insert_text((50, 180), "This is a sample PDF generated for automated verification of all tools.", fontsize=11)
        page.draw_rect(fitz.Rect(50, 220, 545, 300), color=(0.8, 0.8, 0.8), fill=(0.95, 0.95, 0.98))
        page.insert_text((70, 260), f"Item Name | Quantity | Price | Total", fontsize=12, color=(0.2, 0.2, 0.2))
    doc.save(path)
    doc.close()
    return path

def create_sample_image(filename):
    path = os.path.join(TEST_DIR, filename)
    img = Image.new('RGB', (400, 300), color=(147, 51, 234))
    d = ImageDraw.Draw(img)
    d.text((50, 130), "Test Image for PDF", fill=(255, 255, 255))
    img.save(path)
    return path

def create_sample_signature(filename):
    path = os.path.join(TEST_DIR, filename)
    img = Image.new('RGBA', (200, 80), color=(255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    d.line([(20, 40), (60, 20), (100, 60), (150, 30), (180, 50)], fill=(30, 27, 75, 255), width=4)
    img.save(path)
    return path

def run_all_tests():
    print("Starting MrGrimPDF Test Suite...\n" + "="*50)
    
    pdf1 = create_sample_pdf("doc1.pdf", num_pages=3)
    pdf2 = create_sample_pdf("doc2.pdf", num_pages=2)
    sample_img = create_sample_image("sample_pic.png")
    sample_sig = create_sample_signature("sample_sig.png")

    merged = os.path.join(TEST_DIR, "out_merged.pdf")
    merge_pdfs([pdf1, pdf2], merged)
    with fitz.open(merged) as d:
        assert len(d) == 5

    split_res = split_pdf(pdf1, TEST_DIR, mode='ranges', ranges_str='1-2, 3')
    assert os.path.exists(split_res)

    removed = os.path.join(TEST_DIR, "out_removed.pdf")
    remove_pages(pdf1, removed, [2])
    with fitz.open(removed) as d:
        assert len(d) == 2

    reordered = os.path.join(TEST_DIR, "out_reordered.pdf")
    reorder_pages(pdf1, reordered, [3, 1, 2])
    with fitz.open(reordered) as d:
        assert len(d) == 3

    rotated = os.path.join(TEST_DIR, "out_rotated.pdf")
    rotate_pages(pdf1, rotated, {"1": 90, "2": 180})
    with fitz.open(rotated) as d:
        assert d[0].rotation == 90
        assert d[1].rotation == 180

    cropped = os.path.join(TEST_DIR, "out_cropped.pdf")
    crop_pdf(pdf1, cropped, left_pct=10, top_pct=10, right_pct=10, bottom_pct=10)
    assert os.path.exists(cropped)

    compressed = os.path.join(TEST_DIR, "out_compressed.pdf")
    comp_stat = compress_pdf(pdf1, compressed, level='recommended')
    assert os.path.exists(compressed)

    img_res = pdf_to_images(pdf1, TEST_DIR, img_format='jpg')
    assert os.path.exists(img_res)

    img2pdf = os.path.join(TEST_DIR, "out_img2pdf.pdf")
    images_to_pdf([sample_img], img2pdf)
    with fitz.open(img2pdf) as d:
        assert len(d) == 1

    out_excel = os.path.join(TEST_DIR, "out_tables.xlsx")
    pdf_to_excel(pdf1, out_excel)
    assert os.path.exists(out_excel) and os.path.getsize(out_excel) > 0

    out_pptx = os.path.join(TEST_DIR, "out_presentation.pptx")
    pdf_to_pptx(pdf1, out_pptx)
    assert os.path.exists(out_pptx) and os.path.getsize(out_pptx) > 0

    out_word = os.path.join(TEST_DIR, "out_document.docx")
    pdf_to_word(pdf1, out_word)
    assert os.path.exists(out_word) and os.path.getsize(out_word) > 0

    out_pdfa = os.path.join(TEST_DIR, "out_pdfa.pdf")
    pdf_to_pdfa(pdf1, out_pdfa)
    assert os.path.exists(out_pdfa)

    watermarked = os.path.join(TEST_DIR, "out_watermark.pdf")
    add_watermark(pdf1, watermarked, text="TOP SECRET", position="center", rotation=45)
    assert os.path.exists(watermarked)

    numbered = os.path.join(TEST_DIR, "out_numbered.pdf")
    add_page_numbers(pdf1, numbered, format_str="Page {page} of {total}", position="bottom-center")
    assert os.path.exists(numbered)

    protected = os.path.join(TEST_DIR, "out_protected.pdf")
    protect_pdf(pdf1, protected, user_password="mySuperPassword123")
    with fitz.open(protected) as d:
        assert d.is_encrypted

    unlocked = os.path.join(TEST_DIR, "out_unlocked.pdf")
    unlock_pdf(protected, unlocked, password="mySuperPassword123")
    with fitz.open(unlocked) as d:
        assert not d.is_encrypted

    signed = os.path.join(TEST_DIR, "out_signed.pdf")
    sign_pdf(pdf1, signed, sample_sig, page_num=1)
    assert os.path.exists(signed)

    redacted = os.path.join(TEST_DIR, "out_redacted.pdf")
    redact_pdf(pdf1, redacted, search_terms=["SECRET_PASSWORD_123", "TCKN 12345678901"])
    with fitz.open(redacted) as d:
        page_text = d[0].get_text()
        assert "SECRET_PASSWORD_123" not in page_text

    comparison = os.path.join(TEST_DIR, "out_comparison.pdf")
    compare_pdfs(pdf1, pdf2, comparison)
    assert os.path.exists(comparison)

    repaired = os.path.join(TEST_DIR, "out_repaired.pdf")
    repair_pdf(pdf1, repaired)
    assert os.path.exists(repaired)

    print("ALL 21 TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_all_tests()
