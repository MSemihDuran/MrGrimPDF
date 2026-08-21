<div align="center">

  <img src="static/img/logo.png" alt="MrGrimPDF Logo" width="130" style="border-radius: 24px; box-shadow: 0 10px 30px rgba(79, 70, 229, 0.35);"/>

  # 💀 MrGrimPDF
  ### *The 100% Free, Unlimited & Privacy-First All-in-One PDF Suite*

  [![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg?style=for-the-badge)](LICENSE)
  [![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Flask](https://img.shields.io/badge/Framework-Flask%203.0-000000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
  [![PyMuPDF Engine](https://img.shields.io/badge/Engine-PyMuPDF%20%2F%20fitz-red.svg?style=for-the-badge)](https://pymupdf.readthedocs.io/)
  [![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](Dockerfile)
  [![Free & Unlimited](https://img.shields.io/badge/Usage-100%25%20Free%20%26%20No%20Limits-emerald.svg?style=for-the-badge)](#why-mrgrimpdf)

  <p align="center">
    <b>A modern, open-source alternative to iLovePDF & Smallpdf.</b><br>
    No subscriptions. No fake 15 MB file size caps. No cloud data harvesting. Run it 100% locally on your machine or deploy for free on cloud hosting.
  </p>

  <p align="center">
    <a href="#-quick-start-local">Quick Start</a> •
    <a href="#-features--tools">Features</a> •
    <a href="#-deploy-to-free-cloud-hosting">1-Click Deploy</a> •
    <a href="#-tech-stack">Tech Stack</a> •
    <a href="#-license">License</a>
  </p>

</div>

---

## 🌟 Why MrGrimPDF?

Commercial PDF web services charge **$5–$9/month**, limit free users to 1–3 files per task, cap file sizes at 15–50 MB, and upload your sensitive documents to remote third-party servers.

**MrGrimPDF gives you complete freedom:**

* 🔒 **100% Privacy & KVKK/GDPR Friendly:** Documents never leave your private machine or your isolated container.
* 🚀 **Zero Limits:** Process 500 MB+ documents, hundreds of pages, and batch files with no paywalls or daily quotas.
* 🎨 **Stunning Glassmorphism UI:** Dreamy iridescent pastel gradients, frosted glass cards, PDF.js live previews, drag-and-drop page sorting (`SortableJS`), and HTML5 digital signature pad.
* ⚡ **High-Performance Python Engine:** Built on PyMuPDF (C++ MuPDF bindings), pdf2docx, Pillow, and Tesseract OCR.
* 🌐 **Self-Hosted & Cloud-Ready:** Run with `python app.py` or deploy to Render, Railway, Hugging Face Spaces with 1 click.

---

## 🛠️ Features & Tools (20+ Tools)

| Category | Tools & Capabilities |
| :--- | :--- |
| **📑 Organize & Pages** | • **Merge PDF:** Combine multiple PDF documents in any order.<br>• **Split PDF:** Extract pages, split all pages into ZIP, or use custom ranges (e.g. `1-3, 5-7`).<br>• **Organize / Reorder:** Visual drag-and-drop page thumbnail sorter.<br>• **Remove Pages:** Delete selected unwanted pages.<br>• **Rotate PDF:** Rotate single pages or whole files by 90°, 180°, 270°.<br>• **Crop PDF:** Trim page margins by exact percentages. |
| **🔄 Convert Formats** | • **PDF to Word:** Convert PDF into editable `.docx` with preserved layout (`pdf2docx`).<br>• **PDF to Excel:** Extract tables and data structures directly to `.xlsx`.<br>• **PDF to PowerPoint:** Convert PDF pages into `.pptx` presentation slides.<br>• **PDF to Images:** Export pages as high-res JPG/PNG bundles in ZIP.<br>• **Images to PDF:** Merge JPG, PNG, and WebP images into a clean PDF.<br>• **PDF to PDF/A:** ISO-compliant archival normalization. |
| **⚡ Optimize & Repair** | • **Compress PDF:** Extreme (~70%), Recommended (~50%), and Low (lossless) compression.<br>• **Repair PDF:** Reconstruct corrupted xref tables and repair unreadable PDF streams.<br>• **OCR PDF:** Multi-language (Turkish, English, French, German, Spanish) searchable text layer generator. |
| **✍️ Edit & Watermark** | • **Add Watermark:** Text or Image watermark with 3x3 position matrix, rotation, and opacity.<br>• **Page Numbers:** Insert dynamic numbering (`Page {page} of {total}`, `{page}`) with position & font controls.<br>• **Edit & Annotate:** Overlay drawings, text boxes, and shapes on pages.<br>• **Sign PDF:** Interactive HTML5 drawing signature pad or transparent image stamp. |
| **🔒 Security & Audit** | • **Protect PDF:** AES-256 military-grade encryption with user/owner passwords and print/copy permissions.<br>• **Unlock PDF:** Decrypt and remove password restrictions instantly.<br>• **Redact PDF:** Permanently blackout and purge sensitive passwords, SSN/TCKN, or confidential keywords.<br>• **Compare PDFs:** Side-by-side visual difference comparison report generator. |

---

## 🚀 Quick Start (Local)

### Prerequisites
* Python 3.10 or higher
* Git

### Installation & Run

```bash
# 1. Clone the repository
git clone https://github.com/MSemihDuran/MrGrimPDF.git
cd MrGrimPDF

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the application
python app.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## ☁️ Deploy to Free Cloud Hosting

MrGrimPDF is 100% cloud-ready with pre-configured `render.yaml`, `Dockerfile`, `Procfile`, and `requirements.txt`.

### Option 1: Render.com (Recommended - Free Tier)
1. Fork or push this repository to your GitHub account (`MSemihDuran/MrGrimPDF`).
2. Go to [Render.com](https://render.com) and click **New +** -> **Web Service**.
3. Connect your repository. Render will automatically detect `render.yaml`:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. Click **Create Web Service**. Your app will be live at `https://mrgrimpdf.onrender.com` in 2 minutes!

### Option 2: Hugging Face Spaces (Free Docker Hosting)
1. Create a new Space on [Hugging Face Spaces](https://huggingface.co/spaces).
2. Choose **Docker** as the Space SDK.
3. Push or upload this repo. The included `Dockerfile` will automatically build and run.

### Option 3: Railway.app / Koyeb / Fly.io
Simply link your GitHub repository. The `Procfile` and `Dockerfile` are auto-detected.

---

## 🐳 Docker Deployment

```bash
# Build the Docker image
docker build -t mrgrimpdf .

# Run container on port 5000
docker run -d -p 5000:5000 --name mrgrimpdf mrgrimpdf
```

---

## 🧪 Automated Testing

Verify all 21 PDF processing engines locally:

```bash
python test_suite.py
```

Expected output:
```text
🧪 Starting MrGrimPDF Automated Test Suite...
==================================================
✅ Test fixtures created successfully.
✅ 1. Merge PDF: PASSED (3 + 2 = 5 pages)
✅ 2. Split PDF (Ranges & ZIP): PASSED
✅ 3. Remove Pages: PASSED (3 -> 2 pages)
✅ 4. Reorder Pages: PASSED
✅ 5. Rotate Pages: PASSED
✅ 6. Crop PDF: PASSED
✅ 7. Compress PDF: PASSED
✅ 8. PDF to Images (ZIP/JPG): PASSED
✅ 9. Images to PDF: PASSED
✅ 10. PDF to Excel (.xlsx): PASSED
✅ 11. PDF to PowerPoint (.pptx): PASSED
✅ 12. PDF to Word (.docx): PASSED
✅ 13. PDF to PDF/A Archival: PASSED
✅ 14. Watermark Injection: PASSED
✅ 15. Page Numbering: PASSED
✅ 16. Protect PDF (AES-256): PASSED
✅ 17. Unlock PDF (Decryption): PASSED
✅ 18. Sign PDF (Digital Signature Stamp): PASSED
✅ 19. Redact PDF (Data Censorship & Purge): PASSED
✅ 20. Compare PDFs: PASSED
✅ 21. Repair PDF Structure: PASSED
==================================================
🎉 ALL 21 TEST SUITE CASES PASSED WITH 100% SUCCESS!
```

---

## 🏗️ Architecture & Tech Stack

```
MrGrimPDF/
├── app.py                  # Flask REST API & Web Application
├── modules/
│   ├── organize.py         # Merge, Split, Remove, Reorder, Rotate, Crop
│   ├── convert.py          # PDF to Word/Images/Excel/PPTX/PDFA & Img2PDF
│   ├── optimize.py         # Compress, Repair, Multi-lingual OCR
│   ├── edit.py             # Watermark, Page Numbers, Canvas Annotations
│   └── security.py         # Protect (AES-256), Unlock, Sign, Redact, Compare
├── templates/
│   └── index.html          # Glassmorphic UI with PDF.js Studio & SortableJS
├── static/
│   ├── css/style.css       # Custom Glassmorphism, Aurora Blobs, Responsive
│   ├── js/app.js           # Client-side state, Drag-Drop, Canvas Engine
│   ├── img/                # Brand Logo & Favicon
│   ├── robots.txt          # Search Engine indexing
│   └── sitemap.xml         # XML Sitemap
├── test_suite.py           # 21-case Automated Test Suite
├── Dockerfile              # Containerization for Hugging Face / Cloud
├── Procfile                # Heroku / Railway / Render web process
├── render.yaml             # 1-Click Render Deploy blueprint
├── requirements.txt        # Python dependencies
└── LICENSE                 # MIT License
```

* **Backend:** Python 3, Flask, PyMuPDF (fitz), pdf2docx, python-docx, python-pptx, xlsxwriter, Pillow, pytesseract, gunicorn
* **Frontend:** Glassmorphic HTML5/CSS3, Vanilla JavaScript, PDF.js, SortableJS, FontAwesome 6, Space Grotesk & Plus Jakarta Sans fonts

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to check the [issues page](https://github.com/MSemihDuran/MrGrimPDF/issues).

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/MSemihDuran">MSemihDuran</a></sub>
</div>
