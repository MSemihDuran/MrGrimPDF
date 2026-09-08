import os
import sys
import unittest
from PIL import Image
import fitz

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from modules.card_sheet_50x70 import (
    calculate_grid_positions_50x70,
    generate_card_sheet_50x70,
    prepare_card_image,
    prepare_card_back,
    DPI_DEFAULT,
    COLS,
    ROWS,
    TOTAL_SLOTS,
    DEFAULT_CARD_BACK_PATH
)
from app import app

TEST_DIR = os.path.join(os.path.dirname(__file__), 'test_sandbox_50x70')
os.makedirs(TEST_DIR, exist_ok=True)


def create_dummy_card(filename, color=(220, 50, 50)):
    path = os.path.join(TEST_DIR, filename)
    img = Image.new('RGB', (300, 440), color=color)
    img.save(path)
    return path


class TestCardSheet50x70(unittest.TestCase):

    def setUp(self):
        self.card1 = create_dummy_card("card1.png", (220, 50, 50))
        self.card2 = create_dummy_card("card2.png", (50, 120, 220))
        self.card3 = create_dummy_card("card3.png", (50, 200, 100))

    def test_grid_math(self):
        layout = calculate_grid_positions_50x70(dpi=400)
        self.assertEqual(layout["canvas_w"], 7874)
        self.assertEqual(layout["canvas_h"], 11024)
        self.assertEqual(layout["cell_w"], 1087)
        self.assertEqual(layout["cell_h"], 1512)
        self.assertEqual(layout["card_w"], 884)
        self.assertEqual(layout["card_h"], 1318)
        self.assertEqual(layout["bleed_x"], 101)
        self.assertEqual(layout["bleed_y"], 95)
        self.assertEqual(len(layout["slots"]), 49)

        # Check first slot alignment
        first = layout["slots"][0]
        self.assertEqual(first["card_x"], first["cell_x"] + layout["bleed_x"])
        self.assertEqual(first["card_y"], first["cell_y"] + layout["bleed_y"])

    def test_card_back_file_exists(self):
        self.assertTrue(os.path.isfile(DEFAULT_CARD_BACK_PATH), f"Card back image not found at {DEFAULT_CARD_BACK_PATH}")
        card_back = prepare_card_back(DEFAULT_CARD_BACK_PATH, 1087, 1512)
        self.assertEqual(card_back.size, (1087, 1512))

    def test_generate_png(self):
        out_png = os.path.join(TEST_DIR, "test_sheet_50x70.png")
        generate_card_sheet_50x70(
            image_paths=[self.card1, self.card2, self.card3],
            output_path=out_png,
            dpi=400,
            fill_mode="repeat",
            crop_marks="corners",
            export_format="png"
        )
        self.assertTrue(os.path.exists(out_png))
        with Image.open(out_png) as img:
            self.assertEqual(img.size, (7874, 11024))
            # Verify 400 DPI in image metadata
            dpi = img.info.get("dpi")
            self.assertIsNotNone(dpi)
            self.assertEqual(round(dpi[0]), 400)
            self.assertEqual(round(dpi[1]), 400)

    def test_generate_pdf(self):
        out_pdf = os.path.join(TEST_DIR, "test_sheet_50x70.pdf")
        generate_card_sheet_50x70(
            image_paths=[self.card1, self.card2],
            output_path=out_pdf,
            dpi=400,
            fill_mode="uploaded_only",
            crop_marks="border",
            export_format="pdf"
        )
        self.assertTrue(os.path.exists(out_pdf))
        doc = fitz.open(out_pdf)
        self.assertEqual(len(doc), 1)
        page = doc[0]
        # 500mm = 1417.32 pt, 700mm = 1984.25 pt
        self.assertAlmostEqual(page.rect.width, 1417.32, delta=1.0)
        self.assertAlmostEqual(page.rect.height, 1984.25, delta=1.0)
        doc.close()

    def test_flask_api_route(self):
        client = app.test_client()

        # Check health endpoint includes game-cards-50x70
        health = client.get('/api/health')
        self.assertEqual(health.status_code, 200)
        data = health.get_json()
        self.assertIn('game-cards-50x70', data.get('features', []))

        # Check process endpoint
        with open(self.card1, 'rb') as f1, open(self.card2, 'rb') as f2:
            resp = client.post(
                '/api/process/game-cards-50x70',
                data={
                    'files': [(f1, 'card1.png'), (f2, 'card2.png')],
                    'fillMode': 'repeat',
                    'cropMarks': 'corners',
                    'exportFormat': 'png'
                },
                content_type='multipart/form-data'
            )
            self.assertEqual(resp.status_code, 200)
            json_resp = resp.get_json()
            self.assertTrue(json_resp.get('success'))
            self.assertIn('download_url', json_resp)
            self.assertTrue(json_resp.get('filename', '').endswith('.png'))


if __name__ == '__main__':
    unittest.main()
