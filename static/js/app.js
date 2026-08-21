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
    document.getElementById('processBtnText').textContent = `${tool.title} Now`;

    const fileInput = document.getElementById('studioFileInput');
    fileInput.accept = tool.accept;
    fileInput.multiple = tool.multiple;

    resetStudioWorkspace();
    renderDynamicToolOptions(toolKey);

    document.getElementById('studioModal').classList.add('active');
}

function closeStudio() {
    document.getElementById('studioModal').classList.remove('active');
    state.currentTool = null;
    state.uploadedFiles = [];
    state.activePages = [];
}

function resetStudioWorkspace() {
    document.getElementById('stageDropHint').style.display = 'block';
    document.getElementById('stagePreviewContainer').style.display = 'none';
    document.getElementById('stageCanvasContainer').style.display = 'none';
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

function initCanvas() {
    const canvas = document.getElementById('drawingCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const startDraw = (e) => {
        state.isDrawing = true;
        ctx.beginPath();
        const rect = canvas.getBoundingClientRect();
        ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
    };

    const draw = (e) => {
        if (!state.isDrawing) return;
        const rect = canvas.getBoundingClientRect();
        ctx.strokeStyle = state.canvasColor;
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';
        ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
        ctx.stroke();
    };

    const stopDraw = () => {
        state.isDrawing = false;
    };

    canvas.addEventListener('mousedown', startDraw);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDraw);
    canvas.addEventListener('mouseleave', stopDraw);

    document.getElementById('canvasColorPicker').addEventListener('change', (e) => {
        state.canvasColor = e.target.value;
    });
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

async function executeCurrentTool() {
    if (state.uploadedFiles.length === 0) {
        alert('Please upload a PDF file first.');
        return;
    }

    const action = state.currentTool;
    const formData = new FormData();
    const primaryFile = state.uploadedFiles[0];

    document.getElementById('btnProcessAction').style.display = 'none';
    document.getElementById('processProgressBar').style.display = 'block';

    if (action === 'merge' || action === 'images-to-pdf') {
        const fileIds = state.uploadedFiles.map(f => f.file_id);
        formData.append('file_ids', JSON.stringify(fileIds));
    } else {
        formData.append('file_id', primaryFile.file_id);
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
            alert('Please enter an encryption password.');
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
            alert(data.error || 'Processing failed');
            document.getElementById('btnProcessAction').style.display = 'block';
            document.getElementById('processProgressBar').style.display = 'none';
        }
    } catch (err) {
        alert('Server error: ' + err.message);
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

    if (data.stats) {
        const saved = data.stats.saved_percent;
        document.getElementById('resultDetailsText').textContent = 
            `Compressed from ${(data.stats.original_size / 1024).toFixed(1)} KB to ${(data.stats.new_size / 1024).toFixed(1)} KB (${saved}% saved!)`;
    } else {
        document.getElementById('resultDetailsText').textContent = `File ready: ${data.filename}`;
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
    document.getElementById('sessionFilesBadge').textContent = state.sessionHistory.length;
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
