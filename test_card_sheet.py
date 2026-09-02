import os
import io
import unittest
from PIL import Image, ImageDraw
import fitz

import modules.card_sheet as cs
from app import app

class TestCardSheet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(os.path.dirname(__file__), 'test_cards_temp')
        os.makedirs(cls.test_dir, exist_ok=True)
        
        # Create 3 test card images (portrait: 590x860)
        cls.card_paths = []
        colors = [(220, 50, 50), (50, 180, 50), (50, 80, 220)]
        for i, col in enumerate(colors):
            p = os.path.join(cls.test_dir, f'card_{i+1}.png')
            img = Image.new('RGB', (590, 860), col)
            d = ImageDraw.Draw(img)
            d.text((120, 150), f'CARD {i+1}', fill=(255, 255, 255))
            img.save(p)
            cls.card_paths.append(p)

    @classmethod
    def tearDownClass(cls):
        import shutil
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_grid_layout_math(self):
        layout = cs.calculate_grid_positions(dpi=400, gap_mm=2.5)
        self.assertEqual(layout['canvas_w'], 4677)
        self.assertEqual(layout['canvas_h'], 6614)
        self.assertEqual(layout['card_w'], 1354)
        self.assertEqual(layout['card_h'], 929)
        self.assertEqual(len(layout['slots']), 18)

        # Check that cards fit within margins
        margin_x = layout['margin_x']
        margin_y = layout['margin_y']
        self.assertGreater(margin_x, 0)
        self.assertGreater(margin_y, 0)

        # Verify last slot is within canvas
        last_slot = layout['slots'][-1]
        self.assertLessEqual(last_slot['x'] + last_slot['w'], layout['canvas_w'])
        self.assertLessEqual(last_slot['y'] + last_slot['h'], layout['canvas_h'])

    def test_generate_png_uploaded_only(self):
        out_png = os.path.join(self.test_dir, 'output_uploaded_only.png')
        cs.generate_card_sheet(
            image_paths=self.card_paths,
            output_path=out_png,
            dpi=400,
            fill_mode='uploaded_only',
            rotation='ccw90',
            empty_color='black',
            crop_marks='corners',
            export_format='png'
        )
        self.assertTrue(os.path.exists(out_png))
        with Image.open(out_png) as img:
            self.assertEqual(img.size, (4677, 6614))
            dpi = img.info.get('dpi')
            self.assertIsNotNone(dpi)
            self.assertAlmostEqual(dpi[0], 400.0, places=0)
            self.assertAlmostEqual(dpi[1], 400.0, places=0)

    def test_generate_png_repeat(self):
        out_png = os.path.join(self.test_dir, 'output_repeat.png')
        cs.generate_card_sheet(
            image_paths=self.card_paths,
            output_path=out_png,
            dpi=400,
            fill_mode='repeat',
            rotation='ccw90',
            empty_color='black',
            crop_marks='border',
            export_format='png'
        )
        self.assertTrue(os.path.exists(out_png))
        with Image.open(out_png) as img:
            self.assertEqual(img.size, (4677, 6614))

    def test_generate_pdf(self):
        out_pdf = os.path.join(self.test_dir, 'output_card_sheet.pdf')
        cs.generate_card_sheet(
            image_paths=self.card_paths,
            output_path=out_pdf,
            dpi=400,
            fill_mode='uploaded_only',
            export_format='pdf'
        )
        self.assertTrue(os.path.exists(out_pdf))
        doc = fitz.open(out_pdf)
        self.assertEqual(len(doc), 1)
        page = doc[0]
        # A3 is 841.89 x 1190.55 pt
        self.assertAlmostEqual(page.rect.width, 841.89, places=1)
        self.assertAlmostEqual(page.rect.height, 1190.55, places=1)
        doc.close()

    def test_flask_endpoint(self):
        client = app.test_client()
        
        # Test health check
        health_res = client.get('/api/health')
        self.assertEqual(health_res.status_code, 200)
        self.assertIn('game-cards-a3', health_res.get_json()['features'])

        # Prepare multipart upload with 2 cards
        data = {
            'fill_mode': 'uploaded_only',
            'rotation': 'ccw90',
            'empty_color': 'black',
            'crop_marks': 'corners',
            'export_format': 'png',
            'custom_name': 'Test_Deck_A3'
        }
        
        files = []
        for i in range(2):
            with open(self.card_paths[i], 'rb') as f:
                files.append((io.BytesIO(f.read()), f'card_{i+1}.png'))

        data['images'] = files

        resp = client.post('/api/process/game-cards-a3', data=data, content_type='multipart/form-data')
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertTrue(json_data['success'])
        self.assertTrue(json_data['filename'].startswith('Test_Deck_A3'))
        self.assertTrue(json_data['filename'].endswith('.png'))

        # Test download
        dl_resp = client.get(json_data['download_url'])
        self.assertEqual(dl_resp.status_code, 200)
        self.assertGreater(len(dl_resp.data), 1000)

        # Verify downloaded image DPI
        with Image.open(io.BytesIO(dl_resp.data)) as dl_img:
            self.assertEqual(dl_img.size, (4677, 6614))
            self.assertAlmostEqual(dl_img.info.get('dpi')[0], 400.0, places=0)

if __name__ == '__main__':
    unittest.main()
