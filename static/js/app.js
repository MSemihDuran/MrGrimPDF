if (window.pdfjsLib) {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}

const state = {
    currentTool: null,
    uploadedFiles: [],
    activePages: [],
    sessionHistory: [],
    watermarkPos: 'center',
    pageNumberPos: 'bottom-center',
    compressLevel: 'recommended',
    canvasMode: 'pen',
    canvasColor: '#E11D48',
    isDrawing: false,
    redactTerms: []
};

const TOOLS = {
    'create-pdf': { title: 'Create PDF', subtitle: 'Create blank documents, format notes, write rich text, or embed images into a new PDF', icon: 'fa-file-circle-plus', accept: '.pdf,.png,.jpg,.jpeg,.webp,.txt', multiple: true },
    'merge': { title: 'Merge PDFs', subtitle: 'Combine multiple PDF files into one in your chosen order', icon: 'fa-object-group', accept: '.pdf', multiple: true },
    'split': { title: 'Split PDF', subtitle: 'Extract specific pages or split document into multiple files', icon: 'fa-scissors', accept: '.pdf', multiple: false },
    'compress': { title: 'Compress PDF', subtitle: 'Reduce file size while keeping maximum visual quality', icon: 'fa-down-left-and-up-right-to-center', accept: '.pdf', multiple: false },
    'edit': { title: 'Edit & Annotate PDF', subtitle: 'Add freehand drawing, shapes, and text to your document', icon: 'fa-pen-to-square', accept: '.pdf', multiple: false },
    'unlock': { title: 'Unlock PDF', subtitle: 'Remove passwords and permissions from encrypted PDF', icon: 'fa-lock-open', accept: '.pdf', multiple: false },
    'rotate': { title: 'Rotate PDF', subtitle: 'Rotate single pages or all pages permanently', icon: 'fa-rotate-right', accept: '.pdf', multiple: false },
    'protect': { title: 'Protect PDF', subtitle: 'Encrypt your document with military-grade AES-256 password', icon: 'fa-shield-halved', accept: '.pdf', multiple: false },
    'pdf-to-word': { title: 'PDF to Word', subtitle: 'Convert PDF to editable DOCX format with layout preserved', icon: 'fa-file-word', accept: '.pdf', multiple: false },
    'pdf-to-images': { title: 'PDF to JPG/PNG', subtitle: 'Export each page as high-resolution image', icon: 'fa-file-image', accept: '.pdf', multiple: false },
    'images-to-pdf': { title: 'Images to PDF', subtitle: 'Combine multiple JPG, PNG, WebP images into a single PDF', icon: 'fa-images', accept: 'image/*', multiple: true },
    'watermark': { title: 'Add Watermark', subtitle: 'Stamp text or company logo with transparency and rotation', icon: 'fa-stamp', accept: '.pdf', multiple: false },
    'page-numbers': { title: 'Add Page Numbers', subtitle: 'Insert customized numbering into header or footer', icon: 'fa-list-ol', accept: '.pdf', multiple: false },
    'sign': { title: 'Sign PDF', subtitle: 'Draw, upload, or create your digital electronic signature', icon: 'fa-signature', accept: '.pdf', multiple: false },
    'redact': { title: 'Redact PDF', subtitle: 'Permanently blackout confidential information and keywords', icon: 'fa-eraser', accept: '.pdf', multiple: false },
    'ocr': { title: 'OCR PDF', subtitle: 'Extract and generate searchable text layer from scanned documents', icon: 'fa-font', accept: '.pdf', multiple: false },
    'repair': { title: 'Repair PDF', subtitle: 'Recover damaged or unreadable PDF document structure', icon: 'fa-screwdriver-wrench', accept: '.pdf', multiple: false },
    'organize': { title: 'Organize Pages', subtitle: 'Reorder, delete, or duplicate pages visually', icon: 'fa-arrow-down-up-across-line', accept: '.pdf', multiple: false },
    'pdf-to-excel': { title: 'PDF to Excel', subtitle: 'Extract tables and data into an Excel spreadsheet (.xlsx)', icon: 'fa-file-excel', accept: '.pdf', multiple: false },
    'pdf-to-pptx': { title: 'PDF to PowerPoint', subtitle: 'Convert PDF pages into PowerPoint (.pptx) slides', icon: 'fa-file-powerpoint', accept: '.pdf', multiple: false },
    'compare': { title: 'Compare PDFs', subtitle: 'Highlight visual differences between two revisions', icon: 'fa-code-compare', accept: '.pdf', multiple: true },
    'crop': { title: 'Crop PDF', subtitle: 'Crop page margins by percentages', icon: 'fa-crop-simple', accept: '.pdf', multiple: false }
};

document.addEventListener('DOMContentLoaded', () => {
    initDragAndDrop();
    initCanvas();
    loadSessionHistory();
});

function initDragAndDrop() {
    const heroCard = document.getElementById('dropZoneHero');
    const heroInput = document.getElementById('heroFileInput');
    const studioInput = document.getElementById('studioFileInput');

    ['dragenter', 'dragover'].forEach(eventName => {
        heroCard.addEventListener(eventName, (e) => {
            e.preventDefault();
            heroCard.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        heroCard.addEventListener(eventName, (e) => {
            e.preventDefault();
            heroCard.classList.remove('drag-over');
        });
    });

    heroCard.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files, state.currentTool || 'merge');
        }
    });

    heroInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files, state.currentTool || 'merge');
        }
    });

    studioInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files, state.currentTool);
        }
    });
}

function triggerHeroUpload() {
    document.getElementById('heroFileInput').click();
}

function filterTools(category) {
    document.querySelectorAll('.filter-pill').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    const cards = document.querySelectorAll('.glass-tool-card');
    cards.forEach(card => {
        if (category === 'all' || card.getAttribute('data-category') === category) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

function scrollToSection(id) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
}

function resetToHome() {
    closeStudio();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function openTool(toolKey) {
    const tool = TOOLS[toolKey];
    if (!tool) return;

    state.currentTool = toolKey;
    document.getElementById('studioToolTitle').textContent = tool.title;
    document.getElementById('studioToolSubtitle').textContent = tool.subtitle;
    document.getElementById('studioToolIcon').innerHTML = `<i class="fa-solid ${tool.icon}"></i>`;
    document.getElementById('processBtnText').textContent = toolKey === 'create-pdf' ? 'Create PDF & Download' : `${tool.title} Now`;

    const fileInput = document.getElementById('studioFileInput');
    fileInput.accept = tool.accept;
    fileInput.multiple = tool.multiple;

    resetStudioWorkspace();

    if (toolKey === 'create-pdf') {
        document.getElementById('stageDropHint').style.display = 'none';
        const createStage = document.getElementById('stageCreatePdfContainer');
        if (createStage) createStage.style.display = 'flex';
        state.createImages = [];
        switchCreateTab('images');
        renderCreateImagesGrid();
        const tIn = document.getElementById('createDocTitleInput');
        const cIn = document.getElementById('createDocContentInput');
        if (tIn) tIn.value = '';
        if (cIn) cIn.value = '';
    }

    renderDynamicToolOptions(toolKey);

    document.getElementById('studioModal').classList.add('active');
}

function closeStudio() {
    document.getElementById('studioModal').classList.remove('active');
    state.currentTool = null;
    state.uploadedFiles = [];
    state.rawFiles = [];
    state.activePages = [];
}

function resetStudioWorkspace() {
    state.rawFiles = [];
    state.uploadedFiles = [];
    document.getElementById('stageDropHint').style.display = 'block';
    document.getElementById('stagePreviewContainer').style.display = 'none';
    document.getElementById('stageCanvasContainer').style.display = 'none';
    const createStage = document.getElementById('stageCreatePdfContainer');
    if (createStage) createStage.style.display = 'none';
    document.getElementById('studioResultState').style.display = 'none';
    document.getElementById('dynamicToolOptions').style.display = 'block';
    document.getElementById('btnProcessAction').style.display = 'block';
    document.getElementById('processProgressBar').style.display = 'none';
    document.getElementById('thumbnailsGrid').innerHTML = '';
}

function resetStudioForNewTask() {
    resetStudioWorkspace();
    renderDynamicToolOptions(state.currentTool);
}

async function handleFileUpload(fileList, targetTool) {
    if (!targetTool) targetTool = 'merge';
    if (!state.currentTool) openTool(targetTool);

    state.rawFiles = Array.from(fileList);

    const formData = new FormData();
    for (let i = 0; i < fileList.length; i++) {
        formData.append('files', fileList[i]);
    }

    document.getElementById('stageDropHint').innerHTML = `
        <i class="fa-solid fa-spinner fa-spin text-4xl mb-3 text-indigo-500"></i>
        <h3>Uploading & Processing Files...</h3>
        <p>Please wait a moment</p>
    `;

    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.success && data.files.length > 0) {
            state.uploadedFiles = data.files;
            document.getElementById('stageDropHint').style.display = 'none';

            if (state.currentTool === 'sign' || state.currentTool === 'edit') {
                document.getElementById('stageCanvasContainer').style.display = 'flex';
            } else {
                document.getElementById('stagePreviewContainer').style.display = 'flex';
                renderThumbnails();
            }
        } else {
            alert(data.error || 'Failed to upload file');
            resetStudioWorkspace();
        }
    } catch (err) {
        alert('Upload failed: ' + err.message);
        resetStudioWorkspace();
    }
}

function renderThumbnails() {
    const grid = document.getElementById('thumbnailsGrid');
    grid.innerHTML = '';
    state.activePages = [];

    let pageGlobalIndex = 1;

    state.uploadedFiles.forEach((f, fileIdx) => {
        const pageCount = f.pages || 1;
        for (let p = 1; p <= pageCount; p++) {
            const pageObj = {
                id: `page_${fileIdx}_${p}`,
                fileId: f.file_id,
                fileIndex: fileIdx,
                pageNumber: p,
                globalNumber: pageGlobalIndex++,
                rotation: 0,
                isDeleted: false
            };
            state.activePages.push(pageObj);

            const card = document.createElement('div');
            card.className = 'thumbnail-card';
            card.id = pageObj.id;
            card.setAttribute('data-page', pageObj.pageNumber);
            card.setAttribute('data-file-id', f.file_id);

            const previewUrl = f.is_pdf ? `/api/render-preview/${f.file_id}/${p}` : `/api/render-preview/${f.file_id}/1`;

            card.innerHTML = `
                <div class="thumbnail-img-wrap">
                    <img src="${previewUrl}" alt="Page ${p}" onerror="this.src='/static/img/pdf_fallback.png';">
                </div>
                <div class="thumb-page-num">Page ${p}</div>
                <div class="thumb-actions-bar">
                    <button class="btn-thumb-action" title="Rotate" onclick="rotateSinglePage('${pageObj.id}')">
                        <i class="fa-solid fa-rotate-right"></i>
                    </button>
                    <button class="btn-thumb-action delete" title="Delete" onclick="deleteSinglePage('${pageObj.id}')">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            `;
            grid.appendChild(card);
        }
    });

    document.getElementById('totalPagesBadge').textContent = `${state.activePages.length} Pages`;

    new Sortable(grid, {
        animation: 150,
        ghostClass: 'sortable-ghost',
        onEnd: () => {
            const items = grid.querySelectorAll('.thumbnail-card');
            const newOrder = [];
            items.forEach(it => {
                const found = state.activePages.find(p => p.id === it.id);
                if (found) newOrder.push(found);
            });
            state.activePages = newOrder;
        }
    });
}

function rotateSinglePage(pageId) {
    const p = state.activePages.find(item => item.id === pageId);
    if (!p) return;
    p.rotation = (p.rotation + 90) % 360;
    const card = document.getElementById(pageId);
    if (card) {
        const img = card.querySelector('img');
        if (img) img.style.transform = `rotate(${p.rotation}deg)`;
    }
}

function rotateAllPages(deg) {
    state.activePages.forEach(p => {
        p.rotation = (p.rotation + deg) % 360;
        const card = document.getElementById(p.id);
        if (card) {
            const img = card.querySelector('img');
            if (img) img.style.transform = `rotate(${p.rotation}deg)`;
        }
    });
}

function deleteSinglePage(pageId) {
    const idx = state.activePages.findIndex(p => p.id === pageId);
    if (idx !== -1) {
        state.activePages[idx].isDeleted = true;
        const card = document.getElementById(pageId);
        if (card) card.remove();
        document.getElementById('totalPagesBadge').textContent = `${state.activePages.filter(p => !p.isDeleted).length} Pages`;
    }
}

function selectAllPages() {
    alert('All active pages selected for processing.');
}

function renderDynamicToolOptions(toolKey) {
    const container = document.getElementById('dynamicToolOptions');
    container.innerHTML = '';

    switch (toolKey) {
        case 'create-pdf':
            container.innerHTML = `
                <div class="config-group">
                    <label class="config-label">Sayfa Boyutu (Page Size)</label>
                    <select id="createPageSizeSelect" class="config-select" onchange="toggleCustomSizeInputs(this.value)">
                        <optgroup label="Standart ISO / A Serisi">
                            <option value="a0">A0 (841 x 1189 mm)</option>
                            <option value="a1">A1 (594 x 841 mm)</option>
                            <option value="a2">A2 (420 x 594 mm)</option>
                            <option value="a3">A3 (297 x 420 mm)</option>
                            <option value="a4" selected>A4 (210 x 297 mm)</option>
                            <option value="a5">A5 (148 x 210 mm)</option>
                            <option value="a6">A6 (105 x 148 mm)</option>
                        </optgroup>
                        <optgroup label="B Serisi">
                            <option value="b4">B4 (250 x 353 mm)</option>
                            <option value="b5">B5 (176 x 250 mm)</option>
                        </optgroup>
                        <optgroup label="Amerikan / Uluslararası">
                            <option value="letter">US Letter (8.5 x 11 in)</option>
                            <option value="legal">US Legal (8.5 x 14 in)</option>
                            <option value="tabloid">Tabloid / Ledger (11 x 17 in)</option>
                            <option value="executive">Executive (7.25 x 10.5 in)</option>
                        </optgroup>
                        <optgroup label="Özel & Otomatik">
                            <option value="fit">🖼️ Resme Göre Otomatik (Fit to Image)</option>
                            <option value="custom">⚙️ Özel Boyut Belirle (Custom Size)...</option>
                        </optgroup>
                    </select>
                </div>

                <!-- Custom Size Inputs -->
                <div id="customSizeContainer" class="config-group" style="display: none; background: #f8fafc; padding: 12px; border-radius: 12px; border: 1.5px solid #cbd5e1;">
                    <label class="config-label" style="margin-bottom: 6px; font-size: 0.78rem;">Özel Genişlik & Yükseklik</label>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 85px; gap: 8px; align-items: center;">
                        <div>
                            <span style="font-size: 0.7rem; font-weight: 700; color: #64748b;">Genişlik (W)</span>
                            <input type="number" id="customWidthInput" class="config-input" value="210" min="1" step="any" placeholder="Genişlik">
                        </div>
                        <div>
                            <span style="font-size: 0.7rem; font-weight: 700; color: #64748b;">Yükseklik (H)</span>
                            <input type="number" id="customHeightInput" class="config-input" value="297" min="1" step="any" placeholder="Yükseklik">
                        </div>
                        <div>
                            <span style="font-size: 0.7rem; font-weight: 700; color: #64748b;">Birim</span>
                            <select id="customUnitSelect" class="config-select">
                                <option value="mm" selected>mm</option>
                                <option value="cm">cm</option>
                                <option value="in">inch</option>
                                <option value="pt">pt / px</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Margin / Kenar Boşluğu -->
                <div class="config-group">
                    <label class="config-label">Kenar Boşluğu (Margin)</label>
                    <select id="createMarginSelect" class="config-select" onchange="toggleCustomMarginInputs(this.value)">
                        <option value="none">Kenar Boşluğu Yok (0 mm - Tam Sayfa)</option>
                        <option value="small">Küçük (5 mm)</option>
                        <option value="standard" selected>Standart (12 mm)</option>
                        <option value="large">Geniş (20 mm)</option>
                        <option value="custom">⚙️ Özel Kenar Boşluğu (Custom Margin)...</option>
                    </select>
                </div>

                <!-- Custom Margin Input -->
                <div id="customMarginContainer" class="config-group" style="display: none; background: #f8fafc; padding: 12px; border-radius: 12px; border: 1.5px solid #cbd5e1;">
                    <label class="config-label" style="margin-bottom: 6px; font-size: 0.78rem;">Özel Boşluk Değeri</label>
                    <div style="display: grid; grid-template-columns: 1fr 85px; gap: 8px; align-items: center;">
                        <div>
                            <input type="number" id="customMarginValueInput" class="config-input" value="10" min="0" step="any" placeholder="Boşluk Değeri">
                        </div>
                        <div>
                            <select id="customMarginUnitSelect" class="config-select">
                                <option value="mm" selected>mm</option>
                                <option value="cm">cm</option>
                                <option value="in">inch</option>
                                <option value="pt">pt</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="config-group">
                    <label class="config-label">Sayfa Yönü (Orientation)</label>
                    <div style="display:flex; gap:10px;">
                        <button type="button" class="btn-tool-sm active" id="orientPortraitBtn" onclick="selectOrientation('portrait')"><i class="fa-solid fa-file"></i> Dikey (Portrait)</button>
                        <button type="button" class="btn-tool-sm" id="orientLandscapeBtn" onclick="selectOrientation('landscape')"><i class="fa-solid fa-file fa-rotate-90"></i> Yatay (Landscape)</button>
                    </div>
                </div>
                <div class="config-group">
                    <label class="config-label">Hızlı Belge Şablonları</label>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px;">
                        <button type="button" class="btn-tool-sm" onclick="applyTemplate('blank')">Boş Belge</button>
                        <button type="button" class="btn-tool-sm" onclick="applyTemplate('notes')">Toplantı Notları</button>
                        <button type="button" class="btn-tool-sm" onclick="applyTemplate('invoice')">Fatura / Makbuz</button>
                        <button type="button" class="btn-tool-sm" onclick="applyTemplate('report')">Proje Raporu</button>
                    </div>
                </div>
            `;
            break;

        case 'compress':
            container.innerHTML = `
                <div class="config-group">
                    <label class="config-label">Compression Level</label>
                    <div class="compression-cards">
                        <div class="comp-card active" onclick="selectCompLevel('recommended', this)">
                            <div class="comp-card-title"><i class="fa-solid fa-star text-amber-500"></i> Recommended</div>
                            <div class="comp-card-desc">Optimal balance between file size & high image quality (~50% smaller).</div>
                        </div>
                        <div class="comp-card" onclick="selectCompLevel('extreme', this)">
                            <div class="comp-card-title"><i class="fa-solid fa-fire text-rose-500"></i> Extreme Compression</div>
                            <div class="comp-card-desc">Maximum reduction for strict size limits (~70% smaller).</div>
                        </div>
                        <div class="comp-card" onclick="selectCompLevel('low', this)">
                            <div class="comp-card-title"><i class="fa-solid fa-gem text-blue-500"></i> Low Compression</div>
                            <div class="comp-card-desc">Lossless stream compression with zero visible quality loss.</div>
                        </div>
                    </div>
                </div>
            `;
            break;

        case 'watermark':
            container.innerHTML = `
                <div class="config-group">
                    <label class="config-label">Watermark Text</label>
                    <input type="text" id="wmTextInput" class="config-input" value="CONFIDENTIAL" placeholder="Enter text...">
                </div>
                <div class="config-group">
                    <label class="config-label">Position on Page</label>
                    <div class="position-grid-3x3">
                        <button class="pos-btn" onclick="selectWatermarkPos('top-left', this)">↖</button>
                        <button class="pos-btn" onclick="selectWatermarkPos('top-center', this)">↑</button>
                        <button class="pos-btn" onclick="selectWatermarkPos('top-right', this)">↗</button>
                        <button class="pos-btn" onclick="selectWatermarkPos('center-left', this)">←</button>
                        <button class="pos-btn active" onclick="selectWatermarkPos('center', this)">•</button>
                        <button class="pos-btn" onclick="selectWatermarkPos('center-right', this)">→</button>
                        <button class="pos-btn" onclick="selectWatermarkPos('bottom-left', this)">↙</button>
                        <button class="pos-btn" onclick="selectWatermarkPos('bottom-center', this)">↓</button>
                        <button class="pos-btn" onclick="selectWatermarkPos('bottom-right', this)">↘</button>
                    </div>
                </div>
                <div class="config-group">
                    <label class="config-label">Rotation Angle (°)</label>
                    <input type="range" id="wmRotationInput" min="0" max="360" value="45" class="config-input" oninput="document.getElementById('wmRotVal').textContent = this.value + '°'">
                    <span id="wmRotVal" class="text-xs text-muted">45°</span>
                </div>
                <div class="config-group">
                    <label class="config-label">Color & Font Size</label>
                    <div style="display:flex; gap:10px; align-items:center;">
                        <input type="color" id="wmColorInput" value="#E11D48" class="color-picker-input">
                        <input type="number" id="wmFontSizeInput" value="48" min="12" max="120" class="config-input" style="width: 100px;">
                    </div>
                </div>
            `;
            break;

        case 'page-numbers':
            container.innerHTML = `
                <div class="config-group">
                    <label class="config-label">Numbering Format</label>
                    <select id="pnFormatSelect" class="config-select">
                        <option value="{page} / {total}">Page 1 of 5 ({page} / {total})</option>
                        <option value="Page {page}">Page 1 (Page {page})</option>
                        <option value="{page}">{page}</option>
                        <option value="- {page} -">- 1 -</option>
                    </select>
                </div>
                <div class="config-group">
                    <label class="config-label">Position</label>
                    <div class="position-grid-3x3">
                        <button class="pos-btn" onclick="selectPnPos('top-left', this)">↖</button>
                        <button class="pos-btn" onclick="selectPnPos('top-center', this)">↑</button>
                        <button class="pos-btn" onclick="selectPnPos('top-right', this)">↗</button>
                        <button class="pos-btn disabled" style="opacity:0.2;">•</button>
                        <button class="pos-btn disabled" style="opacity:0.2;">•</button>
                        <button class="pos-btn disabled" style="opacity:0.2;">•</button>
                        <button class="pos-btn" onclick="selectPnPos('bottom-left', this)">↙</button>
                        <button class="pos-btn active" onclick="selectPnPos('bottom-center', this)">↓</button>
                        <button class="pos-btn" onclick="selectPnPos('bottom-right', this)">↘</button>
                    </div>
                </div>
                <div class="config-group">
                    <label class="config-label">Starting Page Number</label>
                    <input type="number" id="pnStartNumInput" value="1" min="1" class="config-input">
                </div>
            `;
            break;

        case 'protect':
            container.innerHTML = `
                <div class="config-group">
                    <label class="config-label">Encryption Password</label>
                    <input type="password" id="protectPwInput" class="config-input" placeholder="Enter strong password...">
                </div>
                <div class="config-group">
                    <label class="config-label"><i class="fa-solid fa-lock text-indigo-500"></i> AES-256 Security</label>
                    <div style="font-size:0.85rem; color:#64748b; margin-bottom:10px;">
                        Military grade encryption prevents unauthorized viewing or extraction.
                    </div>
                    <label style="display:flex; align-items:center; gap:8px; font-size:0.85rem; font-weight:600; margin-bottom:6px;">
                        <input type="checkbox" id="allowPrintCheck" checked> Allow Printing
                    </label>
                    <label style="display:flex; align-items:center; gap:8px; font-size:0.85rem; font-weight:600;">
                        <input type="checkbox" id="allowCopyCheck" checked> Allow Content Copying
                    </label>
                </div>
            `;
            break;

        case 'unlock':
            container.innerHTML = `
                <div class="config-group">
                    <label class="config-label">PDF Password</label>
                    <input type="password" id="unlockPwInput" class="config-input" placeholder="Enter document password to remove lock...">
                </div>
            `;
            break;

        case 'split':
            container.innerHTML = `
                <div class="config-group">
                    <label class="config-label">Split Mode</label>
                    <select id="splitModeSelect" class="config-select" onchange="toggleSplitInputs(this.value)">
                        <option value="all">Split Every Page (Separate Files / ZIP)</option>
                        <option value="ranges">By Custom Range (e.g. 1-3, 4-5)</option>
                        <option value="extract">Extract Specific Pages</option>
                    </select>
                </div>
                <div class="config-group" id="splitRangeGroup" style="display:none;">
                    <label class="config-label">Custom Page Ranges</label>
                    <input type="text" id="splitRangeInput" class="config-input" placeholder="Example: 1-2, 3-5">
                </div>
            `;
            break;

        case 'redact':
            container.innerHTML = `
                <div class="config-group">
                    <label class="config-label">Keyword Redaction</label>
                    <div style="display:flex; gap:6px;">
                        <input type="text" id="redactTermInput" class="config-input" placeholder="e.g. Confidential, SSN, IBAN">
                        <button class="btn-tool-sm" onclick="addRedactTerm()">Add</button>
                    </div>
                    <div id="redactTermsList" style="margin-top:10px; display:flex; flex-wrap:wrap; gap:6px;"></div>
                </div>
            `;
            break;

        case 'ocr':
            container.innerHTML = `
                <div class="config-group">
                    <label class="config-label">Document Language</label>
                    <select id="ocrLangSelect" class="config-select">
                        <option value="tur+eng">Turkish + English</option>
                        <option value="eng">English Only</option>
                        <option value="tur">Turkish Only</option>
                        <option value="fra">French</option>
                        <option value="deu">German</option>
                        <option value="spa">Spanish</option>
                    </select>
                </div>
            `;
            break;

        default:
            container.innerHTML = `
                <div class="config-group">
                    <p style="font-size:0.88rem; color:#64748b;">
                        Click <b>Process PDF</b> to execute this tool with optimal settings.
                    </p>
                </div>
            `;
    }
}

function selectCompLevel(level, elem) {
    state.compressLevel = level;
    document.querySelectorAll('.comp-card').forEach(c => c.classList.remove('active'));
    elem.classList.add('active');
}

function selectWatermarkPos(pos, elem) {
    state.watermarkPos = pos;
    document.querySelectorAll('.position-grid-3x3 .pos-btn').forEach(b => b.classList.remove('active'));
    elem.classList.add('active');
}

function selectPnPos(pos, elem) {
    state.pageNumberPos = pos;
    document.querySelectorAll('.position-grid-3x3 .pos-btn').forEach(b => b.classList.remove('active'));
    elem.classList.add('active');
}

function toggleSplitInputs(mode) {
    document.getElementById('splitRangeGroup').style.display = mode === 'ranges' ? 'block' : 'none';
}

function addRedactTerm() {
    const input = document.getElementById('redactTermInput');
    const term = input.value.trim();
    if (term && !state.redactTerms.includes(term)) {
        state.redactTerms.push(term);
        renderRedactTerms();
        input.value = '';
    }
}

function renderRedactTerms() {
    const list = document.getElementById('redactTermsList');
    list.innerHTML = '';
    state.redactTerms.forEach(t => {
        const badge = document.createElement('span');
        badge.className = 'badge-pages';
        badge.style.background = '#fee2e2';
        badge.style.color = '#dc2626';
        badge.innerHTML = `${t} <i class="fa-solid fa-xmark" style="cursor:pointer; margin-left:4px;" onclick="removeRedactTerm('${t}')"></i>`;
        list.appendChild(badge);
    });
}

function removeRedactTerm(term) {
    state.redactTerms = state.redactTerms.filter(t => t !== term);
    renderRedactTerms();
}

function toggleMobileDrawer() {
    const drawer = document.getElementById('mobileDrawer');
    if (drawer) {
        drawer.classList.toggle('active');
    }
}

function toggleFaq(item) {
    item.classList.toggle('active');
}

function initCanvas() {
    const canvas = document.getElementById('drawingCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const getPos = (e) => {
        const rect = canvas.getBoundingClientRect();
        if (e.touches && e.touches.length > 0) {
            return {
                x: e.touches[0].clientX - rect.left,
                y: e.touches[0].clientY - rect.top
            };
        }
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    };

    const startDraw = (e) => {
        state.isDrawing = true;
        ctx.beginPath();
        const pos = getPos(e);
        ctx.moveTo(pos.x, pos.y);
    };

    const draw = (e) => {
        if (!state.isDrawing) return;
        if (e.cancelable) e.preventDefault();
        const pos = getPos(e);
        ctx.strokeStyle = state.canvasColor;
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
    };

    const stopDraw = () => {
        state.isDrawing = false;
    };

    canvas.addEventListener('mousedown', startDraw);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDraw);
    canvas.addEventListener('mouseleave', stopDraw);

    canvas.addEventListener('touchstart', startDraw, { passive: false });
    canvas.addEventListener('touchmove', draw, { passive: false });
    canvas.addEventListener('touchend', stopDraw);

    const colorPicker = document.getElementById('canvasColorPicker');
    if (colorPicker) {
        colorPicker.addEventListener('change', (e) => {
            state.canvasColor = e.target.value;
        });
    }
}

function setCanvasMode(mode) {
    state.canvasMode = mode;
    ['drawPenBtn', 'drawRectBtn', 'drawTextBtn'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.classList.remove('active');
    });
    if (mode === 'pen') document.getElementById('drawPenBtn').classList.add('active');
    if (mode === 'rect') document.getElementById('drawRectBtn').classList.add('active');
    if (mode === 'text') document.getElementById('drawTextBtn').classList.add('active');
}

function clearCanvas() {
    const canvas = document.getElementById('drawingCanvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

state.docOrientation = 'portrait';
state.createImages = [];
state.createTab = 'images';

function switchCreateTab(tab) {
    state.createTab = tab;
    const imgView = document.getElementById('createImagesView');
    const txtView = document.getElementById('createTextView');
    const tabImg = document.getElementById('tabImagesMode');
    const tabTxt = document.getElementById('tabTextMode');

    if (tab === 'images') {
        if (imgView) imgView.style.display = 'flex';
        if (txtView) txtView.style.display = 'none';
        if (tabImg) tabImg.classList.add('active');
        if (tabTxt) tabTxt.classList.remove('active');
    } else {
        if (imgView) imgView.style.display = 'none';
        if (txtView) txtView.style.display = 'flex';
        if (tabImg) tabImg.classList.remove('active');
        if (tabTxt) tabTxt.classList.add('active');
    }
}

function handleCreatePdfImageAttach(input) {
    if (!input.files || input.files.length === 0) return;

    const files = Array.from(input.files);
    let loadedCount = 0;

    files.forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const imgObj = {
                id: 'img_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
                file: file,
                dataUrl: e.target.result,
                name: file.name,
                size: (file.size / 1024).toFixed(1) + ' KB'
            };
            state.createImages.push(imgObj);
            loadedCount++;
            if (loadedCount === files.length) {
                renderCreateImagesGrid();
            }
        };
        reader.readAsDataURL(file);
    });

    input.value = '';
}

function renderCreateImagesGrid() {
    const grid = document.getElementById('createImagesGrid');
    if (!grid) return;

    const badge = document.getElementById('createImagesCountBadge');
    if (badge) badge.textContent = `${state.createImages.length} Resim`;

    grid.innerHTML = '';

    state.createImages.forEach((img, idx) => {
        const card = document.createElement('div');
        card.className = 'create-image-card';
        card.setAttribute('data-id', img.id);
        card.innerHTML = `
            <button type="button" class="btn-delete-img" onclick="removeCreateImage('${img.id}', event)" title="Bu Resmi Sil">
                <i class="fa-solid fa-trash-can"></i>
            </button>
            <div class="create-image-thumb-wrap">
                <img src="${img.dataUrl}" class="create-image-thumb" alt="${img.name}">
            </div>
            <div class="create-image-meta">
                <span class="create-page-badge">Sayfa ${idx + 1}</span>
                <span style="font-size:0.75rem; color:#6366f1;"><i class="fa-solid fa-grip-vertical"></i></span>
            </div>
        `;
        grid.appendChild(card);
    });

    // Add "+ Yeni Resim Ekle" card
    const addCard = document.createElement('div');
    addCard.className = 'btn-add-more-img-card';
    addCard.onclick = () => document.getElementById('createDocImageInput').click();
    addCard.innerHTML = `
        <i class="fa-solid fa-cloud-arrow-up text-2xl text-indigo-500"></i>
        <span>+ Yeni Resim Ekle</span>
        <span style="font-size:0.7rem; color:#64748b;">(Sıralamaya eklenir)</span>
    `;
    grid.appendChild(addCard);

    // Initialize SortableJS
    if (window.Sortable && !grid._hasSortable) {
        Sortable.create(grid, {
            animation: 180,
            draggable: '.create-image-card',
            ghostClass: 'sortable-ghost',
            onEnd: function() {
                const domCards = Array.from(grid.querySelectorAll('.create-image-card'));
                const newOrderIds = domCards.map(c => c.getAttribute('data-id'));
                state.createImages.sort((a, b) => newOrderIds.indexOf(a.id) - newOrderIds.indexOf(b.id));
                renderCreateImagesGrid();
            }
        });
        grid._hasSortable = true;
    }
}

function removeCreateImage(id, event) {
    if (event) event.stopPropagation();
    state.createImages = state.createImages.filter(img => img.id !== id);
    renderCreateImagesGrid();
}

function selectOrientation(orient) {
    state.docOrientation = orient;
    const pBtn = document.getElementById('orientPortraitBtn');
    const lBtn = document.getElementById('orientLandscapeBtn');
    if (pBtn) pBtn.classList.toggle('active', orient === 'portrait');
    if (lBtn) lBtn.classList.toggle('active', orient === 'landscape');
}

function applyTemplate(type) {
    switchCreateTab('text');
    const titleInput = document.getElementById('createDocTitleInput');
    const contentInput = document.getElementById('createDocContentInput');
    if (!titleInput || !contentInput) return;
    
    if (type === 'blank') {
        titleInput.value = '';
        contentInput.value = '';
    } else if (type === 'notes') {
        titleInput.value = 'Toplantı Notları - ' + new Date().toLocaleDateString();
        contentInput.value = 'Tarih: ' + new Date().toLocaleDateString() + '\nKatılımcılar: \n\nGündem Maddeleri:\n1. Proje Gelişimi & Durum Değerlendirmesi\n2. Teknik İnceleme\n3. Görev Dağılımı\n\nAlınan Kararlar:\n- \n\nSonraki Adımlar:';
    } else if (type === 'invoice') {
        titleInput.value = 'FATURA / MAKBUZ #' + Math.floor(1000 + Math.random() * 9000);
        contentInput.value = 'Sayın:\nMüşteri / Şirket Adı\n\nTarih: ' + new Date().toLocaleDateString() + '\n\nAçıklama                          Tutar\n----------------------------------------\n1. Web & PDF Hizmetleri           ₺2,500.00\n2. Bakım ve Destek Hizmeti        ₺750.00\n----------------------------------------\nToplam Ödenecek:                  ₺3,250.00\n\nÖdeme Yöntemi: Havale / EFT / Kripto\nBizi tercih ettiğiniz için teşekkür ederiz!';
    } else if (type === 'report') {
        titleInput.value = 'Proje Değerlendirme Raporu';
        contentInput.value = '1. Yönetici Özeti\nBu doküman projenin mevcut durumu, metrikleri ve hedefleri hakkında ayrıntılı bilgi sunar.\n\n2. Önemli Kazanımlar\n- %100 Ücretsiz & Sınırsız PDF Üretim Mimarisi.\n- Mobil uyumlu ve tam responsive arayüz.\n- Yüksek hızlı vektör dönüşümleri ve güvenlik araçları.\n\n3. Sonuç ve Öneriler\nTüm hedefler sıfır hata ile başarıyla gerçekleştirildi.';
    }
}

function toggleCustomSizeInputs(val) {
    const customBox = document.getElementById('customSizeContainer');
    if (customBox) {
        customBox.style.display = (val === 'custom') ? 'block' : 'none';
    }
}

function toggleCustomMarginInputs(val) {
    const marginBox = document.getElementById('customMarginContainer');
    if (marginBox) {
        marginBox.style.display = (val === 'custom') ? 'block' : 'none';
    }
}

async function getImageForPdf(item, pdfDoc) {
    return new Promise((resolve) => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
            try {
                const canvas = document.createElement('canvas');
                canvas.width = img.naturalWidth || img.width;
                canvas.height = img.naturalHeight || img.height;
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);

                canvas.toBlob(async blob => {
                    if (!blob) {
                        resolve(null);
                        return;
                    }
                    try {
                        const buf = await blob.arrayBuffer();
                        const embedded = await pdfDoc.embedJpg(buf);
                        resolve({ embedded, width: canvas.width, height: canvas.height });
                    } catch (err) {
                        console.error('embedJpg error:', err);
                        resolve(null);
                    }
                }, 'image/jpeg', 0.95);
            } catch (err) {
                console.error('Canvas processing error:', err);
                resolve(null);
            }
        };
        img.onerror = () => {
            console.error('Image element failed to load:', item.name);
            resolve(null);
        };
        img.src = item.dataUrl || (item.file ? URL.createObjectURL(item.file) : '');
    });
}

async function generatePdfWithClientEngine(options) {
    const ptPerMm = 72 / 25.4;
    const ptPerCm = 72 / 2.54;
    const ptPerInch = 72;

    function getPoints(val, unit) {
        const v = parseFloat(val) || 0;
        const u = String(unit).toLowerCase();
        if (u === 'mm') return v * ptPerMm;
        if (u === 'cm') return v * ptPerCm;
        if (u === 'in' || u === 'inch') return v * ptPerInch;
        return v; // pt/px
    }

    const standardSizes = {
        'a0': [2384, 3370],
        'a1': [1684, 2384],
        'a2': [1191, 1684],
        'a3': [842, 1191],
        'a4': [595.28, 841.89],
        'a5': [419.53, 595.28],
        'a6': [297.64, 419.53],
        'b4': [708.66, 1000.63],
        'b5': [498.90, 708.66],
        'letter': [612, 792],
        'legal': [612, 1008],
        'tabloid': [792, 1224],
        'executive': [522, 756]
    };

    let baseW = 595.28;
    let baseH = 841.89;
    const pageKey = (options.pageSize || 'a4').toLowerCase();

    if (pageKey === 'custom' && options.customW && options.customH) {
        baseW = getPoints(options.customW, options.customUnit || 'mm') || 595.28;
        baseH = getPoints(options.customH, options.customUnit || 'mm') || 841.89;
    } else if (standardSizes[pageKey]) {
        [baseW, baseH] = standardSizes[pageKey];
    }

    let pageW = options.orientation === 'landscape' ? Math.max(baseW, baseH) : Math.min(baseW, baseH);
    let pageH = options.orientation === 'landscape' ? Math.min(baseW, baseH) : Math.max(baseW, baseH);

    // Margins
    let margin = 34.01; // standard ~12mm
    if (options.marginType === 'none') {
        margin = 0;
    } else if (options.marginType === 'small') {
        margin = 14.17; // 5mm
    } else if (options.marginType === 'large') {
        margin = 56.69; // 20mm
    } else if (options.marginType === 'custom' && options.customMargin !== undefined) {
        margin = getPoints(options.customMargin, options.marginUnit || 'mm');
    }

    // Engine 1: jsPDF (Fastest, ultra-reliable with images)
    if (window.jspdf && window.jspdf.jsPDF) {
        const { jsPDF } = window.jspdf;
        let doc = null;
        let isFirst = true;

        for (const item of (options.images || [])) {
            const canvas = document.createElement('canvas');
            const img = await new Promise((res) => {
                const i = new Image();
                i.crossOrigin = 'anonymous';
                i.onload = () => res(i);
                i.onerror = () => res(null);
                i.src = item.dataUrl || (item.file ? URL.createObjectURL(item.file) : '');
            });

            if (!img) continue;

            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);

            const imgDataUrl = canvas.toDataURL('image/jpeg', 0.92);
            const imgW = canvas.width;
            const imgH = canvas.height;

            let curPageW = pageW;
            let curPageH = pageH;
            let curOrient = options.orientation || 'portrait';

            if (pageKey === 'fit') {
                curPageW = imgW;
                curPageH = imgH;
                curOrient = imgW > imgH ? 'landscape' : 'portrait';
            }

            if (isFirst) {
                doc = new jsPDF({
                    orientation: curOrient,
                    unit: 'pt',
                    format: [curPageW, curPageH]
                });
                isFirst = false;
            } else {
                doc.addPage([curPageW, curPageH], curOrient);
            }

            if (pageKey === 'fit') {
                doc.addImage(imgDataUrl, 'JPEG', 0, 0, curPageW, curPageH, undefined, 'FAST');
            } else {
                const availW = Math.max(10, curPageW - (margin * 2));
                const availH = Math.max(10, curPageH - (margin * 2));
                const scale = Math.min(availW / imgW, availH / imgH);
                const drawW = imgW * scale;
                const drawH = imgH * scale;
                const drawX = margin + (availW - drawW) / 2;
                const drawY = margin + (availH - drawH) / 2;
                doc.addImage(imgDataUrl, 'JPEG', drawX, drawY, drawW, drawH, undefined, 'FAST');
            }
        }

        if (!doc) {
            doc = new jsPDF({
                orientation: options.orientation || 'portrait',
                unit: 'pt',
                format: [pageW, pageH]
            });
        }

        return doc.output('blob');
    }

    // Engine 2: PDFLib fallback
    const pdfLibObj = window.PDFLib || window.pdfLib;
    if (pdfLibObj) {
        const { PDFDocument } = pdfLibObj;
        const pdfDoc = await PDFDocument.create();
        for (const item of (options.images || [])) {
            const imgData = await getImageForPdf(item, pdfDoc);
            if (!imgData) continue;
            const imgW = imgData.width;
            const imgH = imgData.height;
            if (pageKey === 'fit') {
                const page = pdfDoc.addPage([imgW, imgH]);
                page.drawImage(imgData.embedded, { x: 0, y: 0, width: imgW, height: imgH });
            } else {
                const page = pdfDoc.addPage([pageW, pageH]);
                const availW = Math.max(10, pageW - (margin * 2));
                const availH = Math.max(10, pageH - (margin * 2));
                const scale = Math.min(availW / imgW, availH / imgH);
                const drawW = imgW * scale;
                const drawH = imgH * scale;
                const drawX = margin + (availW - drawW) / 2;
                const drawY = margin + (availH - drawH) / 2;
                page.drawImage(imgData.embedded, { x: drawX, y: drawY, width: drawW, height: drawH });
            }
        }
        if (pdfDoc.getPageCount() === 0) pdfDoc.addPage([pageW, pageH]);
        const bytes = await pdfDoc.save();
        return new Blob([bytes], { type: 'application/pdf' });
    }

    throw new Error('PDF motoru hazırlanıyor, lütfen 1 saniye sonra tekrar deneyin.');
}

function updateDownloadFilename(newVal) {
    const dlBtn = document.getElementById('downloadResultBtn');
    if (dlBtn) {
        let clean = newVal.trim();
        if (clean && !clean.toLowerCase().endsWith('.pdf')) {
            clean += '.pdf';
        }
        dlBtn.download = clean || 'MrGrimPDF_Document.pdf';
    }
}

async function executeCurrentTool() {
    const action = state.currentTool;
    const formData = new FormData();

    document.getElementById('btnProcessAction').style.display = 'none';
    document.getElementById('processProgressBar').style.display = 'block';

    if (action === 'create-pdf') {
        const title = (document.getElementById('createDocTitleInput') ? document.getElementById('createDocTitleInput').value : '') || '';
        const content = (document.getElementById('createDocContentInput') ? document.getElementById('createDocContentInput').value : '') || '';
        const pageSize = document.getElementById('createPageSizeSelect') ? document.getElementById('createPageSizeSelect').value : 'a4';
        const orientation = state.docOrientation || 'portrait';
        const marginType = document.getElementById('createMarginSelect') ? document.getElementById('createMarginSelect').value : 'standard';

        const customW = document.getElementById('customWidthInput') ? document.getElementById('customWidthInput').value : '210';
        const customH = document.getElementById('customHeightInput') ? document.getElementById('customHeightInput').value : '297';
        const customUnit = document.getElementById('customUnitSelect') ? document.getElementById('customUnitSelect').value : 'mm';
        const customMarg = document.getElementById('customMarginValueInput') ? document.getElementById('customMarginValueInput').value : '10';
        const margUnit = document.getElementById('customMarginUnitSelect') ? document.getElementById('customMarginUnitSelect').value : 'mm';

        // Format default date & time filename
        const now = new Date();
        const pad = (n) => String(n).padStart(2, '0');
        const dateStr = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;
        const defaultFilename = `MrGrimPDF_${dateStr}.pdf`;

        // 1. High-Performance Client-Side Generation (0 network lag, 0 file-size limit!)
        if (state.createImages.length > 0 || (!content && !title)) {
            try {
                const pdfBlob = await generatePdfWithClientEngine({
                    title, content, pageSize, orientation, marginType,
                    customW, customH, customUnit, customMargin: customMarg, marginUnit: margUnit,
                    images: state.createImages
                });
                const blobUrl = URL.createObjectURL(pdfBlob);
                showSuccessResult({
                    success: true,
                    download_url: blobUrl,
                    filename: defaultFilename
                });
                return;
            } catch (libErr) {
                console.error('Client PDF generation error:', libErr);
                alert('PDF oluşturulamadı: ' + (libErr.message || 'Hata oluştu'));
                document.getElementById('btnProcessAction').style.display = 'block';
                document.getElementById('processProgressBar').style.display = 'none';
                return;
            }
        }

        // Custom dimensions if selected
        if (pageSize === 'custom') {
            formData.append('custom_w', customW);
            formData.append('custom_h', customH);
            formData.append('custom_unit', customUnit);
        }

        // Margin settings
        formData.append('margin_type', marginType);
        if (marginType === 'custom') {
            formData.append('custom_margin', customMarg);
            formData.append('margin_unit', margUnit);
        }

        // Attach all gallery images
        if (state.createImages.length > 0) {
            state.createImages.forEach(item => {
                if (item.file) {
                    formData.append('images', item.file);
                }
            });
        }

        formData.append('title', title);
        formData.append('content', content);
        formData.append('page_size', pageSize);
        formData.append('orientation', orientation);
        formData.append('custom_name', defaultFilename);

    } else {
        if (state.uploadedFiles.length === 0 && (!state.rawFiles || state.rawFiles.length === 0)) {
            alert('Lütfen önce bir dosya seçin.');
            document.getElementById('btnProcessAction').style.display = 'block';
            document.getElementById('processProgressBar').style.display = 'none';
            return;
        }

        // Attach actual raw files for 100% serverless safety
        if (state.rawFiles && state.rawFiles.length > 0) {
            if (action === 'merge' || action === 'images-to-pdf') {
                state.rawFiles.forEach(f => formData.append('files', f));
            } else if (action === 'compare') {
                formData.append('file_1', state.rawFiles[0]);
                if (state.rawFiles[1]) formData.append('file_2', state.rawFiles[1]);
            } else {
                formData.append('file', state.rawFiles[0]);
            }
        }

        if (state.uploadedFiles && state.uploadedFiles.length > 0) {
            const primaryFile = state.uploadedFiles[0];
            if (action === 'merge' || action === 'images-to-pdf') {
                const fileIds = state.uploadedFiles.map(f => f.file_id);
                formData.append('file_ids', JSON.stringify(fileIds));
            } else {
                formData.append('file_id', primaryFile.file_id);
            }
        }
    }

    if (action === 'split') {
        const mode = document.getElementById('splitModeSelect').value;
        formData.append('mode', mode);
        if (mode === 'ranges') {
            formData.append('ranges', document.getElementById('splitRangeInput').value);
        }
    } else if (action === 'compress') {
        formData.append('level', state.compressLevel);
    } else if (action === 'watermark') {
        formData.append('wm_type', 'text');
        formData.append('text', document.getElementById('wmTextInput').value);
        formData.append('position', state.watermarkPos);
        formData.append('rotation', document.getElementById('wmRotationInput').value);
        formData.append('color', document.getElementById('wmColorInput').value);
        formData.append('font_size', document.getElementById('wmFontSizeInput').value);
    } else if (action === 'page-numbers') {
        formData.append('format', document.getElementById('pnFormatSelect').value);
        formData.append('position', state.pageNumberPos);
        formData.append('start_number', document.getElementById('pnStartNumInput').value);
    } else if (action === 'protect') {
        const pw = document.getElementById('protectPwInput').value;
        if (!pw) {
            alert('Lütfen bir şifre belirleyin.');
            document.getElementById('btnProcessAction').style.display = 'block';
            document.getElementById('processProgressBar').style.display = 'none';
            return;
        }
        formData.append('password', pw);
        formData.append('allow_print', document.getElementById('allowPrintCheck').checked);
        formData.append('allow_copy', document.getElementById('allowCopyCheck').checked);
    } else if (action === 'unlock') {
        formData.append('password', document.getElementById('unlockPwInput').value);
    } else if (action === 'rotate') {
        const rotMap = {};
        state.activePages.forEach(p => {
            if (p.rotation) rotMap[p.pageNumber] = p.rotation;
        });
        formData.append('rotations', JSON.stringify(rotMap));
    } else if (action === 'organize') {
        const activeRemaining = state.activePages.filter(p => !p.isDeleted).map(p => p.pageNumber);
        formData.append('order', JSON.stringify(activeRemaining));
    } else if (action === 'sign') {
        const canvas = document.getElementById('drawingCanvas');
        formData.append('signature_data', canvas.toDataURL());
        formData.append('page', 1);
    } else if (action === 'redact') {
        formData.append('terms', JSON.stringify(state.redactTerms));
    } else if (action === 'ocr') {
        formData.append('lang', document.getElementById('ocrLangSelect').value);
    }

    try {
        const res = await fetch(`/api/process/${action}`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.success) {
            showSuccessResult(data);
        } else {
            alert(data.error || 'İşlem gerçekleştirilemedi');
            document.getElementById('btnProcessAction').style.display = 'block';
            document.getElementById('processProgressBar').style.display = 'none';
        }
    } catch (err) {
        alert('Sunucu hatası: ' + err.message);
        document.getElementById('btnProcessAction').style.display = 'block';
        document.getElementById('processProgressBar').style.display = 'none';
    }
}

function showSuccessResult(data) {
    document.getElementById('dynamicToolOptions').style.display = 'none';
    document.getElementById('processProgressBar').style.display = 'none';
    document.getElementById('studioResultState').style.display = 'block';

    const dlBtn = document.getElementById('downloadResultBtn');
    dlBtn.href = data.download_url;
    dlBtn.download = data.filename;

    const nameInput = document.getElementById('resultFilenameInput');
    if (nameInput) {
        nameInput.value = data.filename;
    }

    if (data.stats) {
        const saved = data.stats.saved_percent;
        document.getElementById('resultDetailsText').textContent = 
            `Boyut ${(data.stats.original_size / 1024).toFixed(1)} KB'den ${(data.stats.new_size / 1024).toFixed(1)} KB'ye düşürüldü (%${saved} tasarruf!)`;
    } else {
        document.getElementById('resultDetailsText').textContent = `Dosyanız hazır: ${data.filename}`;
    }

    addToSessionHistory(data.filename, data.download_url);
}

function loadSessionHistory() {
    updateHistoryBadge();
}

function addToSessionHistory(filename, url) {
    state.sessionHistory.unshift({
        filename: filename,
        url: url,
        time: new Date().toLocaleTimeString()
    });
    updateHistoryBadge();
    renderHistoryList();
}

function updateHistoryBadge() {
    const count = state.sessionHistory.length;
    const badgeDesktop = document.getElementById('sessionFilesBadge');
    if (badgeDesktop) badgeDesktop.textContent = count;
    const badgeMobile = document.getElementById('sessionFilesBadgeMobile');
    if (badgeMobile) badgeMobile.textContent = count;
}

function openMyFilesModal() {
    renderHistoryList();
    document.getElementById('myFilesModal').classList.add('active');
}

function closeMyFilesModal() {
    document.getElementById('myFilesModal').classList.remove('active');
}

function renderHistoryList() {
    const list = document.getElementById('myFilesList');
    if (state.sessionHistory.length === 0) {
        list.innerHTML = '<p class="empty-history-text">No files processed in this session yet.</p>';
        return;
    }
    list.innerHTML = '';
    state.sessionHistory.forEach(item => {
        const card = document.createElement('div');
        card.className = 'history-item-card';
        card.innerHTML = `
            <div>
                <div class="history-file-name">${item.filename}</div>
                <div class="history-file-meta">${item.time}</div>
            </div>
            <a href="${item.url}" class="btn-tool-sm" download>
                <i class="fa-solid fa-download"></i>
            </a>
        `;
        list.appendChild(card);
    });
}
