# MrGrimPDF - iLovePDF Özellik Analizi & Proje Yol Haritası

Bu doküman, **iLovePDF** platformunun tüm fonksiyonlarını, ücretsiz ve premium paketleri arasındaki farkları ve `E:\RemakeProject\MrGrimPDF` projesi kapsamında geliştireceğimiz açık kaynaklı, sınırsız ve yerel (self-hosted) alternatifin teknik altyapı analizini içerir.

---

## 1. iLovePDF Araç Seti ve Fonksiyon Listesi

iLovePDF platformu, sunduğu tüm araçları 5 ana kategori altında toplar:

### 📑 1. Organize & Sayfa Yönetimi (Organize)
* **Merge PDF (PDF Birleştir):** Birden fazla PDF belgesini istenen sırada tek bir PDF dosyasında birleştirir.
* **Split PDF (PDF Böl / Sayfa Ayıkla):** Belirli sayfa aralıklarını ayırır veya her sayfayı bağımsız bir PDF olarak dışa aktarır.
* **Remove Pages (Sayfa Sil):** PDF içinden seçilen gereksiz sayfaları kalıcı olarak siler.
* **Organize / Reorder PDF (Sayfa Sıralama):** Sayfa küçük resimlerini (thumbnails) sürükle-bırak yöntemiyle yeniden sıralar, sayfa ekler veya çıkarır.
* **Rotate PDF (Döndür):** Sayfaları 90°, 180° veya 270° açıyla saat yönünde/tersine döndürür.
* **Crop PDF (Kırp):** Sayfa kenar boşluklarını kırpar ve görünür sayfa alanını ayarlar.

### 🔄 2. Dönüştürme Araçları (Convert)
* **PDF'e Dönüştürme (To PDF):**
  * `JPG / PNG -> PDF`
  * `Word (DOCX) -> PDF`
  * `PowerPoint (PPTX) -> PDF`
  * `Excel (XLSX) -> PDF`
  * `HTML -> PDF` (Web sayfası URL'si veya saf HTML kodu)
* **PDF'ten Dönüştürme (From PDF):**
  * `PDF -> JPG / PNG` (Tüm sayfaları veya gömülü resimleri yüksek çözünürlükte çıkarma)
  * `PDF -> Word (DOCX)` (Düzenlenebilir belge)
  * `PDF -> Excel (XLSX)` (Tablo verilerini çıkarma)
  * `PDF -> PowerPoint (PPTX)` (Sunum slaytları oluşturma)
  * `PDF -> PDF/A` (Uzun vadeli arşivleme ve ISO standardına uyarlama)

### ⚡ 3. Optimizasyon & Onarma (Optimize & Repair)
* **Compress PDF (Sıkıştırma):** Kalite kaybını optimize ederek dosya boyutunu düşürür (Aşırı, Önerilen ve Düşük sıkıştırma seviyeleri).
* **Repair PDF (Onarma):** Bozulmuş, hasarlı veya okunamayan PDF belgelerindeki veri yapısını onarır.
* **OCR PDF (Optik Karakter Tanıma):** Taranmış (resim tabanlı) belgeleri metin tabanlı, aranabilir ve seçilebilir PDF formatına dönüştürür.

### ✍️ 4. İçerik Düzenleme & İşaretleme (Edit & Annotate)
* **Edit PDF (PDF Düzenleyici):** PDF üzerine yeni metin, resim, şekil (dikdörtgen, elips, ok), serbest çizim ve vurgu ekleme.
* **Page Numbers (Sayfa Numaralandırma):** İstenen formatta (1/N, Sayfa X), fontta, boyutta ve konumda (alt, üst, kenar) sayfa numarası basma.
* **Watermark (Filigran):** PDF sayfalarının arkasına veya önüne özel metin ya da logo/resim filigranı yerleştirme.
* **PDF Forms (Form Doldurma):** İnteraktif PDF form alanlarını doldurma ve dışa aktarma.

### 🔒 5. Güvenlik & Doğrulama (Security)
* **Protect PDF (Şifreleme):** 128-bit / 256-bit AES şifreleme ile açılış şifresi ve izin kısıtlamaları (yazdırma, kopyalama engeli) koyma.
* **Unlock PDF (Kilit Kaldırma):** Parolası bilinen veya korumalı PDF'lerin güvenlik kısıtlamalarını kaldırma.
* **Sign PDF (Elektronik & Dijital İmza):** Belgeye el yazısı imza, şirket kaşesi ve dijital sertifikalı yasal imza ekleme.
* **Redact PDF (Sansürleme / Karartma):** Hassas kişisel/finansal bilgileri (TCKN, IBAN vb.) geri getirilemez biçimde siyah bantla silme.
* **Compare PDF (Karşılaştırma):** İki farklı PDF revizyonunu yan yana karşılaştırıp eklenen/silinen farkları renklendirerek gösterme.

---

## 2. Ücretsiz (Free) vs. Premium (Paid) Karşılaştırması

iLovePDF, ücretsiz kullanıcıları kısıtlayarak aylık ~**\$5 - \$9** bandında bir Premium abonelik modeline yönlendirir:

| Kriter / Özellik | 🆓 Ücretsiz (Kayıtsız / Ücretsiz Hesap) | 💎 Premium Abonelik |
| :--- | :--- | :--- |
| **Erişim Platformu** | Sadece Web Tarayıcısı | Web + Masaüstü Uygulaması (Win/Mac) + Mobil |
| **Çevrimdışı (Offline) Çalışma** | ❌ Yok (Dosyalar uzak sunucuya yüklenir) |  Var (Masaüstü uygulaması ile yerel işlem) |
| **Dosya Boyut Limiti** | ~15 MB – 100 MB arası (Araca göre kısıtlı) | 4 GB'a kadar devasa dosya işleme |
| **Toplu İşlem (Batch Processing)** | 1 – 3 dosya (Çok sınırlı) | Sınırsız / 100+ dosya aynı anda |
| **Günlük Kota / İşlem Sayısı** | Günlük işlem kotaları ve bekleme süreleri | Sınırsız işlem |
| **OCR Desteği** | ❌ Kapalı veya tek sayfalık demo |  Çok dilli, sınırsız tam sayfa OCR |
| **Reklamlar** |  Arayüzde reklam gösterimi var | ❌ Tamamen reklamsız |
| **İşlem Kuyruk Hızı** | Standart sunucu kuyruğu (yavaş) | Özel dedike yüksek hızlı sunucular |
| **PDF -> Office Dönüşüm Kalitesi** | Temel motor (Karmaşık tablolarda kayma) | OCR destekli, yüksek hassasiyetli motor |
| **Dijital İmza Güvencesi** | Basit görsel imza yerleştirme | Audit Trail (Denetim İzi), zaman damgası, yasal e-imza |
| **Müşteri Desteği** | Topluluk / Yavaş | 7/24 Öncelikli Müşteri Desteği |

---

## 3. MrGrimPDF Proje Vizyonu ve Avantajları

Kendi yerel klonumuzu (**MrGrimPDF**) geliştirdiğimizde iLovePDF'in tüm kısıtlamalarını aşmış olacağız:

1. **Tam Veri Gizliliği (Privacy-First):** Belgeler asla yabancı bir sunucuya yüklenmez, tüm işlemler kullanıcının kendi yerel makinesinde gerçekleşir (KVKK / GDPR %100 uyumlu).
2. **Sıfır Maliyet & Sonsuz Limit:** Abonelik ücreti yok; dosya boyutu sınırı, sayfa sınırı veya günlük işlem limiti olmadan 4 GB+ dosyalar dahi işlenebilir.
3. **Sınırsız OCR & Toplu İşlem:** Açık kaynaklı OCR motorlarıyla yüzlerce sayfalık taranmış dokümanlar tek tıkla işlenebilir.
4. **Çoklu Arayüz Desteği:** Hem modern ve hızlı bir Web UI (localhost üzerinden), hem de isteğe bağlı Masaüstü (Desktop) uygulaması olarak çalıştırılabilir.

---

## 4. Kullanılacak Açık Kaynak Motorlar ve Teknoloji Önerisi

MrGrimPDF'i oluştururken kullanabileceğimiz güçlü açık kaynak kütüphaneler:

* **PDF Manipülasyonu & Render:** `PyMuPDF (fitz)`, `pypdf`, `pdfplumber`, `pdf.js`
* **Optik Karakter Tanıma (OCR):** `Tesseract OCR` / `pytesseract` / `ocrmypdf`
* **Ofis Format Dönüşümleri (DOCX/XLSX/PPTX):** `LibreOffice (Headless CLI)`, `pdf2docx`, `docx2pdf`
* **Optimizasyon & Sıkıştırma:** `Ghostscript`, `qpdf`, `pikepdf`
* **Güvenlik & Şifreleme:** `pikepdf` (QPDF C++ motoru altyapısıyla 256-bit AES)
* **Backend:** `FastAPI` (Python - Asenkron, hızlı, OpenAPI dokümantasyonu hazır)
* **Frontend:** `TailwindCSS` + `Modern Vanilla JS` veya `React/Vue` (iLovePDF benzeri temiz, modern sürükle-bırak arayüzü)
