"""Regression test for the visual PDF compression pipeline."""

import io
import os
import tempfile

import fitz
from PIL import Image, ImageChops, ImageDraw, ImageStat

from modules.optimize import compress_pdf


def make_layered_scan(path):
    """Create a high-resolution, scan-like PDF with image and vector layers."""
    image = Image.effect_noise((3000, 2200), 90).convert("RGB")
    drawing = ImageDraw.Draw(image)
    drawing.rectangle((120, 120, 2880, 460), fill=(250, 250, 250))
    drawing.text((180, 220), "MrGrimPDF visual compression quality test", fill=(25, 35, 55))
    image_data = io.BytesIO()
    image.save(image_data, format="JPEG", quality=96, subsampling=0)

    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_image(page.rect, stream=image_data.getvalue())
    page.insert_text((42, 790), "Vector layer that must remain visually legible", fontsize=16, color=(0, 0, 0))
    document.save(path, deflate=False)
    document.close()


def page_mae(source_path, result_path):
    with fitz.open(source_path) as source, fitz.open(result_path) as result:
        source_pix = source[0].get_pixmap(dpi=100, colorspace=fitz.csRGB, alpha=False)
        result_pix = result[0].get_pixmap(dpi=100, colorspace=fitz.csRGB, alpha=False)
        source_image = Image.frombytes("RGB", (source_pix.width, source_pix.height), source_pix.samples)
        result_image = Image.frombytes("RGB", (result_pix.width, result_pix.height), result_pix.samples)
        return sum(ImageStat.Stat(ImageChops.difference(source_image, result_image)).mean) / 3


def test_extreme_visual_compression():
    with tempfile.TemporaryDirectory(prefix="mrgrimpdf_compression_") as workdir:
        original = os.path.join(workdir, "layered_scan.pdf")
        compressed = os.path.join(workdir, "compressed.pdf")
        make_layered_scan(original)

        stats = compress_pdf(original, compressed, level="extreme")
        assert stats["new_size"] < stats["original_size"] * 0.20
        assert stats["saved_percent"] > 80
        assert page_mae(original, compressed) < 12

        with fitz.open(compressed) as document:
            assert len(document) == 1
            assert document[0].get_pixmap(dpi=150).width > 0


if __name__ == "__main__":
    test_extreme_visual_compression()
    print("Visual compression quality test passed.")
