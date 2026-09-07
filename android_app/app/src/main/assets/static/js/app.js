// Onion Lens - Main Application Controller

// ── Mobile detection ──────────────────────────────────────────────────────────
// Run immediately (before DOM ready) so CSS sees the class from first paint.
(function detectMobile() {
    const ua = navigator.userAgent || '';
    const isMobileUA = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|webOS/i.test(ua);
    const isTouchOnly = navigator.maxTouchPoints > 1 && window.innerWidth <= 768;
    if (isMobileUA || isTouchOnly) {
        document.documentElement.classList.add('real-mobile');
        document.body && document.body.classList.add('real-mobile');
        // Also apply once body is ready
        document.addEventListener('DOMContentLoaded', function() {
            document.body.classList.add('real-mobile');
        });
    }
})();
// ─────────────────────────────────────────────────────────────────────────────

const App = {
    currentLang: 'en',
    currentScreen: 'screen-splash',
    historyFilter: 'all',
    searchQuery: '',
    viewMode: 'mobile', // 'mobile' or 'fullscreen'
    activeLotDetails: {},
    inspections: [],
    currentUser: null,

    init: async function() {
        // Load saved language
        const savedLang = localStorage.getItem('onion_lens_lang');
        if (savedLang && TRANSLATIONS[savedLang]) {
            App.currentLang = savedLang;
        }

        // Load saved user session
        const savedUser = localStorage.getItem('onion_lens_user');
        if (savedUser) {
            try {
                App.currentUser = JSON.parse(savedUser);
            } catch (e) {
                App.currentUser = null;
            }
        }

        // Fetch real inspections from FastAPI database
        try {
            const resp = await fetch('/api/inspections');
            if (resp.ok) {
                const data = await resp.json();
                App.inspections = data.inspections || [];
            }
        } catch (e) {
            console.warn('Could not fetch remote inspections, using local storage fallback:', e);
            const stored = localStorage.getItem('onion_lens_inspections');
            App.inspections = stored ? JSON.parse(stored) : [];
        }

        // Apply translations
        App.applyTranslations();

        // Update inspector profile details
        App.updateInspectorProfileUI();

        // Setup Event Listeners
        App.bindEvents();

        // Update dashboard statistics
        App.updateDashboardStats();

        // Set radio for language selection screen
        const langRadio = document.querySelector(`input[name="language-radio"][value="${App.currentLang}"]`);
        if (langRadio) langRadio.checked = true;

        // Flow: Splash -> Language -> Login -> Home
        const seenWelcome = localStorage.getItem('onion_lens_seen_welcome');
        if (!seenWelcome) {
            App.navigateTo('screen-splash');
        } else if (!App.currentUser) {
            App.navigateTo('screen-login');
        } else {
            App.navigateTo('screen-home');
        }
    },

    saveInspectionsToStorage: function() {
        localStorage.setItem('onion_lens_inspections', JSON.stringify(App.inspections));
    },

    handleLogin: async function() {
        const idInput = document.getElementById('login-input-id');
        const pinInput = document.getElementById('login-input-pin');
        const mandiSelect = document.getElementById('login-input-mandi');

        const inspectorId = idInput ? idInput.value.trim() : 'INSP-APMC-8492';
        const pin = pinInput ? pinInput.value.trim() : '1234';
        const mandi = mandiSelect ? mandiSelect.value : 'Nashik APMC Main Yard';

        if (!inspectorId) {
            App.showToast('Please enter Inspector ID');
            return;
        }

        try {
            const resp = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    inspector_id: inspectorId,
                    pin: pin || '1234',
                    yard: mandi
                })
            });

            if (resp.ok) {
                const data = await resp.json();
                App.currentUser = {
                    id: data.user.inspector_id,
                    name: data.user.name,
                    yard: data.user.yard,
                    role: data.user.role,
                    token: data.access_token,
                    loginTime: new Date().toISOString()
                };
            } else {
                // Fallback for demo credentials
                App.currentUser = {
                    id: inspectorId,
                    yard: mandi,
                    role: 'Inspector',
                    loginTime: new Date().toISOString()
                };
            }
        } catch (e) {
            App.currentUser = {
                id: inspectorId,
                yard: mandi,
                role: 'Inspector',
                loginTime: new Date().toISOString()
            };
        }

        localStorage.setItem('onion_lens_user', JSON.stringify(App.currentUser));
        localStorage.setItem('onion_lens_seen_welcome', 'true');
        App.updateInspectorProfileUI();
        App.showToast('Signed in successfully as ' + inspectorId);
        App.navigateTo('screen-home');
    },

    handleGuestLogin: async function() {
        const guestId = 'INSP-DEMO-2026';
        try {
            const resp = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    inspector_id: guestId,
                    pin: '1234',
                    yard: 'Nashik APMC Main Yard #4'
                })
            });
            if (resp.ok) {
                const data = await resp.json();
                App.currentUser = {
                    id: data.user.inspector_id,
                    yard: data.user.yard,
                    role: data.user.role,
                    token: data.access_token,
                    loginTime: new Date().toISOString()
                };
            } else {
                App.currentUser = {
                    id: guestId,
                    yard: 'Nashik APMC Main Yard #4',
                    role: 'Guest Inspector',
                    loginTime: new Date().toISOString()
                };
            }
        } catch (e) {
            App.currentUser = {
                id: guestId,
                yard: 'Nashik APMC Main Yard #4',
                role: 'Guest Inspector',
                loginTime: new Date().toISOString()
            };
        }

        localStorage.setItem('onion_lens_user', JSON.stringify(App.currentUser));
        localStorage.setItem('onion_lens_seen_welcome', 'true');
        App.updateInspectorProfileUI();
        App.showToast('Welcome, Guest Inspector!');
        App.navigateTo('screen-home');
    },

    handleLogout: function() {
        App.currentUser = null;
        localStorage.removeItem('onion_lens_user');
        App.showToast('Logged out successfully');
        App.navigateTo('screen-login');
    },

    updateInspectorProfileUI: function() {
        if (!App.currentUser) return;
        const roleEls = document.querySelectorAll('.inspector-text-group h3');
        const centreEls = document.querySelectorAll('.inspector-text-group p');
        roleEls.forEach(el => el.textContent = 'Inspector (' + App.currentUser.id + ')');
        centreEls.forEach(el => el.textContent = App.currentUser.yard);
    },

    bindEvents: function() {
        // Splash get started
        const splashBtn = document.getElementById('btn-splash-start');
        if (splashBtn) {
            splashBtn.addEventListener('click', () => {
                App.navigateTo('screen-language');
            });
        }

        // Language screen save
        const saveLangBtn = document.getElementById('btn-save-language');
        if (saveLangBtn) {
            saveLangBtn.addEventListener('click', () => {
                const selected = document.querySelector('input[name="language-radio"]:checked');
                if (selected) {
                    App.setLanguage(selected.value);
                }
                // Show language updated toast
                App.showToast(App.t('lang_updated'));
                localStorage.setItem('onion_lens_seen_welcome', 'true');
                setTimeout(() => {
                    if (App.currentUser) {
                        App.navigateTo('screen-home');
                    } else {
                        App.navigateTo('screen-login');
                    }
                }, 800);
            });
        }

        // Voice language button
        const voiceBtn = document.getElementById('btn-voice-lang');
        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => {
                App.triggerVoiceLanguagePicker();
            });
        }

        // Bottom Navigation items
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const target = tab.dataset.target;
                if (target) App.navigateTo(target);
            });
        });

        // Home action cards
        const btnLiveCheck = document.getElementById('card-live-check');
        if (btnLiveCheck) {
            btnLiveCheck.addEventListener('click', () => {
                App.startInspection('live');
            });
        }

        const btnPhotoCheck = document.getElementById('card-photo-check');
        if (btnPhotoCheck) {
            btnPhotoCheck.addEventListener('click', () => {
                const fileInput = document.getElementById('gallery-file-input');
                if (fileInput) fileInput.click();
            });
        }

        const btnNewBatch = document.getElementById('card-batch-inspection');
        if (btnNewBatch) {
            btnNewBatch.addEventListener('click', () => {
                App.openBatchModal();
            });
        }

        const btnReports = document.getElementById('card-quality-reports');
        if (btnReports) {
            btnReports.addEventListener('click', () => {
                App.navigateTo('screen-history');
            });
        }

        const btnStartInspection = document.getElementById('btn-start-inspection');
        if (btnStartInspection) {
            btnStartInspection.addEventListener('click', () => {
                App.startInspection('live');
            });
        }



        // Camera Screen Controls
        const btnCameraBack = document.getElementById('btn-camera-back');
        if (btnCameraBack) {
            btnCameraBack.addEventListener('click', () => {
                CameraModule.stopCamera();
                App.navigateTo('screen-home');
            });
        }

        const btnToggleFlash = document.getElementById('btn-toggle-flash');
        if (btnToggleFlash) {
            btnToggleFlash.addEventListener('click', () => {
                const isFlash = CameraModule.toggleFlash(document.getElementById('camera-viewfinder-box'));
                btnToggleFlash.classList.toggle('active', isFlash);
            });
        }

        const btnFlipCamera = document.getElementById('btn-flip-camera');
        if (btnFlipCamera) {
            btnFlipCamera.addEventListener('click', async () => {
                const videoEl = document.getElementById('camera-video');
                const fallbackEl = document.getElementById('camera-fallback-view');
                await CameraModule.flipCamera(videoEl, fallbackEl);
            });
        }

        const btnGallery = document.getElementById('btn-open-gallery');
        if (btnGallery) {
            btnGallery.addEventListener('click', () => {
                document.getElementById('gallery-file-input').click();
            });
        }

        const fileInput = document.getElementById('gallery-file-input');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files[0]) {
                    App.handleImageUpload(e.target.files[0]);
                }
            });
        }

        const phoneCamInput = document.getElementById('phone-camera-input');
        if (phoneCamInput) {
            phoneCamInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files[0]) {
                    App.handleImageUpload(e.target.files[0]);
                }
            });
        }

        const btnShutter = document.getElementById('btn-shutter');
        if (btnShutter) {
            btnShutter.addEventListener('click', () => {
                // If live video is active and playing, capture it. Otherwise, open native phone camera!
                const videoEl = document.getElementById('camera-video');
                if (CameraModule.stream && videoEl && videoEl.videoWidth > 0) {
                    App.captureAndAnalyze();
                } else {
                    App.triggerPhoneCamera();
                }
            });
        }

        // Viewfinder click: tapping anywhere on the camera viewfinder opens the camera directly
        const viewfinderBox = document.getElementById('camera-viewfinder-box');
        if (viewfinderBox) {
            viewfinderBox.addEventListener('click', (e) => {
                if (e.target.closest('button') || e.target.tagName === 'BUTTON') return;
                const videoEl = document.getElementById('camera-video');
                if (CameraModule.stream && videoEl && videoEl.videoWidth > 0) {
                    App.captureAndAnalyze();
                } else {
                    App.triggerPhoneCamera();
                }
            });
        }


        // Results Screen Actions
        const btnSaveResult = document.getElementById('btn-save-result');
        if (btnSaveResult) {
            btnSaveResult.addEventListener('click', () => {
                App.showToast('Inspection saved to history');
                App.navigateTo('screen-history');
            });
        }

        const btnInspectAnother = document.getElementById('btn-inspect-another');
        if (btnInspectAnother) {
            btnInspectAnother.addEventListener('click', () => {
                App.startInspection('live');
            });
        }

        const btnPrintReport = document.getElementById('btn-print-report');
        if (btnPrintReport) {
            btnPrintReport.addEventListener('click', () => {
                window.print();
            });
        }

        // History Filters & Search
        document.querySelectorAll('.history-filter-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                document.querySelectorAll('.history-filter-pill').forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                App.historyFilter = pill.dataset.filter;
                App.renderHistory();
            });
        });

        const historySearch = document.getElementById('history-search-input');
        if (historySearch) {
            historySearch.addEventListener('input', (e) => {
                App.searchQuery = e.target.value.trim().toLowerCase();
                App.renderHistory();
            });
        }

        // Settings actions
        const btnSettingsLang = document.getElementById('setting-item-language');
        if (btnSettingsLang) {
            btnSettingsLang.addEventListener('click', () => {
                App.navigateTo('screen-language');
            });
        }

        const btnCustomerCare = document.getElementById('setting-item-customer-care');
        if (btnCustomerCare) {
            btnCustomerCare.addEventListener('click', () => {
                App.openCustomerCareModal();
            });
        }

        const btnAccountDetails = document.getElementById('setting-item-account');
        if (btnAccountDetails) {
            btnAccountDetails.addEventListener('click', () => {
                App.openAccountModal();
            });
        }

        // Connect phone button
        const btnConnectPhone = document.getElementById('btn-connect-phone');
        if (btnConnectPhone) {
            btnConnectPhone.addEventListener('click', () => {
                const m = document.getElementById('phone-connect-modal');
                if (m) m.classList.add('active');
            });
        }

        // Frame view toggle (Phone Mockup vs Full Responsive)
        const btnViewToggle = document.getElementById('btn-toggle-view-mode');
        if (btnViewToggle) {
            btnViewToggle.addEventListener('click', () => {
                App.toggleViewMode();
            });
        }
    },

    navigateTo: function(screenId) {
        CameraModule.stopCamera();

        // Authentication guard for protected screens
        const protectedScreens = ['screen-home', 'screen-camera', 'screen-history', 'screen-settings', 'screen-analyzing', 'screen-results'];
        if (protectedScreens.includes(screenId) && !App.currentUser) {
            screenId = 'screen-login';
        }

        // Adjust bottom navigation bar visibility: ONLY show on main views
        const bottomNav = document.querySelector('.phone-bottom-nav');
        const mainTabs = ['screen-home', 'screen-history', 'screen-settings'];
        if (bottomNav) {
            if (mainTabs.includes(screenId)) {
                bottomNav.classList.remove('nav-hidden');
            } else {
                bottomNav.classList.add('nav-hidden');
            }
        }

        // Update active screen
        document.querySelectorAll('.app-screen').forEach(s => s.classList.remove('active'));
        const target = document.getElementById(screenId);
        if (target) {
            target.classList.add('active');
            App.currentScreen = screenId;
        }

        // Update bottom navigation bar active state
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.target === screenId);
        });

        // If navigating to History, refresh list
        if (screenId === 'screen-history') {
            App.renderHistory();
        }

        // If navigating to Home, refresh stats
        if (screenId === 'screen-home') {
            App.updateDashboardStats();
        }

        // Scroll to top of phone frame
        const frameContainer = document.querySelector('.phone-screen-content');
        if (frameContainer) frameContainer.scrollTop = 0;
    },

    setLanguage: function(lang) {
        if (!TRANSLATIONS[lang]) lang = 'en';
        App.currentLang = lang;
        localStorage.setItem('onion_lens_lang', lang);
        App.applyTranslations();
    },

    t: function(key) {
        const langData = TRANSLATIONS[App.currentLang] || TRANSLATIONS.en;
        return langData[key] || TRANSLATIONS.en[key] || key;
    },

    applyTranslations: function() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.dataset.i18n;
            const translated = App.t(key);
            if (translated) {
                if (el.tagName === 'INPUT' && el.placeholder) {
                    el.placeholder = translated;
                } else {
                    el.textContent = translated;
                }
            }
        });
        
        // Update active language indicator in settings
        const langDisplay = document.getElementById('settings-active-lang-label');
        if (langDisplay) {
            const names = {
                en: 'English',
                te: 'Telugu (తెలుగు)',
                hi: 'Hindi (हिंदी)',
                ta: 'Tamil (தமிழ்)',
                kn: 'Kannada (ಕನ್ನಡ)',
                mr: 'Marathi (मराठी)'
            };
            langDisplay.textContent = names[App.currentLang] || 'English';
        }
    },

    triggerVoiceLanguagePicker: function() {
        const voiceModal = document.getElementById('voice-lang-modal');
        if (voiceModal) {
            voiceModal.classList.add('active');
            // Simulate voice recognition after 2.2 seconds
            setTimeout(() => {
                // Cycle to next language or Telugu as featured in Figma
                const nextLang = App.currentLang === 'en' ? 'te' : (App.currentLang === 'te' ? 'hi' : 'en');
                const radio = document.querySelector(`input[name="language-radio"][value="${nextLang}"]`);
                if (radio) radio.checked = true;
                voiceModal.classList.remove('active');
                App.showToast('Recognized: ' + (nextLang === 'te' ? 'తెలుగు (Telugu)' : (nextLang === 'hi' ? 'हिंदी (Hindi)' : 'English')));
            }, 2200);
        }
    },

    startInspection: async function(mode = 'live') {
        App.navigateTo('screen-camera');
        const videoEl = document.getElementById('camera-video');
        const fallbackEl = document.getElementById('camera-fallback-view');
        
        // Initialize real camera
        await CameraModule.initCamera(videoEl, fallbackEl);
    },

    captureAndAnalyze: function() {
        const videoEl = document.getElementById('camera-video');
        const fallbackImg = document.getElementById('camera-sample-preview-img');
        const captured = CameraModule.captureFrame(videoEl, fallbackImg);

        if (!captured) {
            App.triggerPhoneCamera();
            return;
        }

        App.runAnalysisOnImage(captured.dataUrl, captured.type);
    },

    runSampleTest: function() {
        App.runAnalysisOnImage('/static/images/samples/sample-lot-grade-a.jpg', 'grade-a');
    },


    handleImageUpload: function(file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const dataUrl = e.target.result;
            App.runAnalysisOnImage(dataUrl, 'upload');
        };
        reader.readAsDataURL(file);
    },

    runAnalysisOnImage: async function(imageDataUrl, sampleType = 'auto') {
        CameraModule.stopCamera();
        App.navigateTo('screen-analyzing');

        // Set analyzing preview thumbnail
        const thumb = document.getElementById('analyzing-thumb-img');
        if (thumb) thumb.src = imageDataUrl;

        const progressPercent = document.getElementById('analyzing-progress-percent');
        const progressStatus = document.getElementById('analyzing-status-step');
        const progressBar = document.getElementById('analyzing-progress-fill');

        const img = new Image();
        img.src = imageDataUrl;
        img.dataset.sampleType = sampleType;
        await img.decode();

        const analysis = await AIEngine.analyzeImage(img, App.activeLotDetails, (pct, msgKey) => {
            if (progressPercent) progressPercent.textContent = pct + '%';
            if (progressBar) progressBar.style.width = pct + '%';
            if (progressStatus) progressStatus.textContent = App.t(msgKey);
        });

        // STRICT ONION VALIDATION GUARD: Reject non-onions immediately
        if (!analysis.isOnion) {
            const err = analysis.errorMessage || 'No onions detected! Please scan only onion bulbs.';
            App.showToast('⚠️ ' + err);

            if (progressStatus) {
                progressStatus.textContent = '❌ ' + err;
                progressStatus.style.color = '#EF4444';
                progressStatus.style.fontWeight = '700';
            }
            if (progressBar) {
                progressBar.style.background = '#EF4444';
            }

            setTimeout(() => {
                App.navigateTo('screen-camera');
                if (progressStatus) {
                    progressStatus.style.color = '';
                    progressStatus.style.fontWeight = '';
                }
                if (progressBar) {
                    progressBar.style.background = '';
                }
            }, 2600);
            return;
        }

        analysis.image = imageDataUrl;
        App.currentInspection = analysis;

        // Automatically prepend to inspection history
        App.inspections.unshift(analysis);
        App.saveInspectionsToStorage();
        App.updateDashboardStats();

        // Render Results
        App.renderResultsScreen(analysis);
        setTimeout(() => {
            App.navigateTo('screen-results');
        }, 500);
    },

    renderResultsScreen: function(result) {
        // Image preview
        const resImg = document.getElementById('result-onion-image');
        if (resImg) resImg.src = result.image;

        // Render individual-bulb hotspots (numbered pins per onion)
        const hotspotContainer = document.getElementById('result-hotspots-container');
        if (hotspotContainer) {
            hotspotContainer.innerHTML = '';
            (result.hotspots || []).forEach(spot => {
                const el = document.createElement('div');
                el.className = 'defect-hotspot hotspot-' + spot.type;
                el.style.left = spot.x + '%';
                el.style.top = spot.y + '%';
                el.dataset.bulbId = spot.id;

                // Numbered badge
                const badge = document.createElement('span');
                badge.className = 'hotspot-badge';
                badge.textContent = spot.id;

                // Pulse ring
                const pulse = document.createElement('span');
                pulse.className = 'hotspot-pulse';

                // Tooltip
                const tag = document.createElement('span');
                tag.className = 'hotspot-tag';
                tag.textContent = '#' + spot.id + ' ' + spot.gradeName + ' — ' + (spot.diameter || '') + 'mm';

                el.appendChild(pulse);
                el.appendChild(badge);
                el.appendChild(tag);
                hotspotContainer.appendChild(el);

                // Click pin → highlight matching bulb row
                el.addEventListener('click', () => {
                    document.querySelectorAll('.defect-hotspot').forEach(h => h.classList.remove('highlighted'));
                    document.querySelectorAll('.bulb-row').forEach(r => r.classList.remove('highlighted'));
                    el.classList.add('highlighted');
                    const matchRow = document.querySelector(`.bulb-row[data-bulb-id="${spot.id}"]`);
                    if (matchRow) {
                        matchRow.classList.add('highlighted');
                        matchRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                });
            });
        }

        // Quality grade badge
        const gradeBadge = document.getElementById('result-grade-badge');
        if (gradeBadge) {
            gradeBadge.className = 'grade-badge-large ' + result.gradeBadgeClass;
            gradeBadge.textContent = result.gradeName;
        }

        // Key stats
        const scoreEl = document.getElementById('result-quality-score');
        if (scoreEl) scoreEl.textContent = result.qualityScore + '%';

        const lotEl = document.getElementById('result-lot-id');
        if (lotEl) lotEl.textContent = result.lotId;

        const bulbsEl = document.getElementById('result-bulb-count');
        if (bulbsEl) bulbsEl.textContent = result.bulbCount;

        const diamEl = document.getElementById('result-avg-diameter');
        if (diamEl) diamEl.textContent = result.avgDiameter;

        const colorEl = document.getElementById('result-color-uniformity');
        if (colorEl) colorEl.textContent = result.colorUniformity;

        // ── Individual Onion Recognition Card ──────────────────────────────
        const gc = result.gradeCounts || {};
        const total = gc.total || result.bulbCount || 1;
        const cA   = gc.gradeA      || 0;
        const cU   = gc.urs         || 0;
        const cNE  = gc.notEligible || 0;
        const pctA  = Math.round((cA  / total) * 100);
        const pctU  = Math.round((cU  / total) * 100);
        const pctNE = Math.round((cNE / total) * 100);

        // Totals
        const elTotal = document.getElementById('count-total-bulbs');
        if (elTotal) elTotal.textContent = total;

        // Count boxes
        const elCA = document.getElementById('count-grade-a-bulbs'); if (elCA) elCA.textContent = cA;
        const elCU = document.getElementById('count-urs-bulbs');     if (elCU) elCU.textContent = cU;
        const elCN = document.getElementById('count-ne-bulbs');      if (elCN) elCN.textContent = cNE;

        // Percentages
        const elPA = document.getElementById('pct-grade-a-bulbs'); if (elPA) elPA.textContent = pctA + '%';
        const elPU = document.getElementById('pct-urs-bulbs');     if (elPU) elPU.textContent = pctU + '%';
        const elPN = document.getElementById('pct-ne-bulbs');      if (elPN) elPN.textContent = pctNE + '%';

        // Distribution bar
        const segA  = document.getElementById('dist-seg-a');   if (segA)  { segA.style.width = pctA + '%';  segA.title  = 'Grade A: ' + pctA + '%'; }
        const segU  = document.getElementById('dist-seg-urs'); if (segU)  { segU.style.width = pctU + '%';  segU.title  = 'URS: ' + pctU + '%'; }
        const segNE = document.getElementById('dist-seg-ne');  if (segNE) { segNE.style.width = pctNE + '%'; segNE.title = 'Not Eligible: ' + pctNE + '%'; }

        // Filter chip counts
        const fcAll = document.getElementById('filter-count-all'); if (fcAll) fcAll.textContent = total;
        const fcA   = document.getElementById('filter-count-a');   if (fcA)   fcA.textContent  = cA;
        const fcU   = document.getElementById('filter-count-urs'); if (fcU)   fcU.textContent  = cU;
        const fcNE  = document.getElementById('filter-count-ne');  if (fcNE)  fcNE.textContent = cNE;

        // Store bulbs on App for filter use
        App._currentBulbs = result.individualBulbs || [];

        // Render bulb rows
        App.renderBulbList('all');

        // Wire filter chips
        document.querySelectorAll('.bulb-chip-filter').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.bulb-chip-filter').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                App.renderBulbList(btn.dataset.bulbFilter || 'all');
            });
        });

        // Defect breakdown (PRIMARY COUNT FIRST!)
        const counts = result.defectCounts || {};
        const sproutCount = counts.sprouting || 0;
        const moldCount = counts.mold || 0;
        const rotCount = counts.mold ? Math.round(counts.mold * 0.5) : 0;
        const cutsCount = counts.mechanical_damage || 0;
        const skinCount = counts.skin_peeling || 0;

        const sproutEl = document.getElementById('defect-val-sprouting');
        if (sproutEl) sproutEl.innerHTML = `<span style="font-weight:700;">${sproutCount} of ${total} onions</span> <span style="font-size:0.75rem;opacity:0.75;">(${result.defects.sprouting || '0%'})</span>`;

        const moldEl = document.getElementById('defect-val-black-mold');
        if (moldEl) moldEl.innerHTML = `<span style="font-weight:700;">${moldCount} of ${total} onions</span> <span style="font-size:0.75rem;opacity:0.75;">(${result.defects.blackMold || '0%'})</span>`;

        const rotEl = document.getElementById('defect-val-rot');
        if (rotEl) rotEl.innerHTML = `<span style="font-weight:700;">${rotCount} of ${total} onions</span> <span style="font-size:0.75rem;opacity:0.75;">(${result.defects.rotDecay || '0%'})</span>`;

        const cutsEl = document.getElementById('defect-val-cuts');
        if (cutsEl) cutsEl.innerHTML = `<span style="font-weight:700;">${cutsCount} of ${total} onions</span> <span style="font-size:0.75rem;opacity:0.75;">(${result.defects.cutsBruises || '0%'})</span>`;

        const skinEl = document.getElementById('defect-val-skin');
        if (skinEl) skinEl.innerHTML = `<span style="font-weight:700;">${skinCount} of ${total} onions</span> <span style="font-size:0.75rem;opacity:0.75;">(${result.defects.skinPeeling || '0%'})</span>`;

        // Recommendations
        const recsContainer = document.getElementById('result-recommendations-list');
        if (recsContainer) {
            recsContainer.innerHTML = '';
            (result.recommendations || []).forEach(r => {
                const li = document.createElement('li');
                li.textContent = r;
                recsContainer.appendChild(li);
            });
        }
    },

    // Render filtered bulb row list
    renderBulbList: function(filter) {
        const container = document.getElementById('individual-bulbs-list');
        if (!container) return;
        container.innerHTML = '';
        const bulbs = App._currentBulbs || [];
        const filtered = (filter === 'all') ? bulbs : bulbs.filter(b => b.grade === filter);

        if (filtered.length === 0) {
            container.innerHTML = '<div style="text-align:center;padding:14px;color:var(--text-muted);font-size:0.8rem;">No bulbs in this category</div>';
            return;
        }

        filtered.forEach(bulb => {
            const isPinA  = bulb.grade === 'GRADE_A';
            const isPinU  = bulb.grade === 'URS';
            const pinClass   = isPinA ? 'bulb-row-pin-a'    : (isPinU ? 'bulb-row-pin-urs'  : 'bulb-row-pin-ne');
            const badgeClass = isPinA ? 'bulb-row-badge-a'  : (isPinU ? 'bulb-row-badge-urs' : 'bulb-row-badge-ne');

            const row = document.createElement('div');
            row.className = 'bulb-row';
            row.dataset.bulbId = bulb.id;
            row.innerHTML = `
                <div class="bulb-row-pin ${pinClass}">#${bulb.id}</div>
                <div class="bulb-row-details">
                    <div class="bulb-row-name">Onion #${bulb.id}</div>
                    <div class="bulb-row-sub">${bulb.diameter}mm &bull; ${bulb.issues}</div>
                </div>
                <span class="bulb-row-badge ${badgeClass}">${bulb.gradeName}</span>
            `;

            // Click row → highlight matching pin
            row.addEventListener('click', () => {
                document.querySelectorAll('.bulb-row').forEach(r => r.classList.remove('highlighted'));
                document.querySelectorAll('.defect-hotspot').forEach(h => h.classList.remove('highlighted'));
                row.classList.add('highlighted');
                const matchPin = document.querySelector(`.defect-hotspot[data-bulb-id="${bulb.id}"]`);
                if (matchPin) matchPin.classList.add('highlighted');
            });

            container.appendChild(row);
        });
    },



    updateDashboardStats: function() {
        const total = App.inspections.length;
        let gradeA = 0;
        let urs = 0;
        let notEligible = 0;

        App.inspections.forEach(item => {
            if (item.grade === 'GRADE_A') gradeA++;
            else if (item.grade === 'URS') urs++;
            else if (item.grade === 'NOT_ELIGIBLE') notEligible++;
        });

        const totalEl = document.getElementById('dash-stat-total');
        if (totalEl) totalEl.textContent = total;

        const gradeAEl = document.getElementById('dash-stat-grade-a');
        if (gradeAEl) gradeAEl.textContent = gradeA;

        const ursEl = document.getElementById('dash-stat-urs');
        if (ursEl) ursEl.textContent = urs;

        const neEl = document.getElementById('dash-stat-not-eligible');
        if (neEl) neEl.textContent = notEligible;
    },

    renderHistory: function() {
        const container = document.getElementById('history-records-list');
        if (!container) return;

        container.innerHTML = '';

        let filtered = App.inspections.filter(item => {
            // Filter pill match
            if (App.historyFilter === 'grade-a' && item.grade !== 'GRADE_A') return false;
            if (App.historyFilter === 'urs' && item.grade !== 'URS') return false;
            if (App.historyFilter === 'not-eligible' && item.grade !== 'NOT_ELIGIBLE') return false;

            // Search query match
            if (App.searchQuery && !item.lotId.toLowerCase().includes(App.searchQuery)) {
                return false;
            }
            return true;
        });

        if (filtered.length === 0) {
            container.innerHTML = `<div class="empty-state-card"><p>${App.t('empty_history')}</p></div>`;
            return;
        }

        filtered.forEach(item => {
            const card = document.createElement('div');
            card.className = 'history-lot-card';
            card.innerHTML = `
                <div class="history-card-header">
                    <span class="history-lot-id">${item.lotId}</span>
                    <span class="history-badge ${item.gradeBadgeClass}">${item.gradeName}</span>
                </div>
                <div class="history-card-meta">
                    <span class="history-qty">${App.t('qty')}: ${item.quantityKg}</span>
                    <span class="history-date">• ${item.dateFormatted}</span>
                </div>
            `;
            card.addEventListener('click', () => {
                App.renderResultsScreen(item);
                App.navigateTo('screen-results');
            });
            container.appendChild(card);
        });
    },

    openBatchModal: function() {
        const modal = document.getElementById('batch-lot-modal');
        if (modal) {
            const inputLot = document.getElementById('batch-input-lot-id');
            if (inputLot) inputLot.value = 'LOT-' + new Date().getFullYear() + '-' + String(Date.now()).slice(-4);
            modal.classList.add('active');
        }
    },

    closeModals: function() {
        document.querySelectorAll('.app-modal').forEach(m => m.classList.remove('active'));
    },

    openCustomerCareModal: function() {
        const m = document.getElementById('customer-care-modal');
        if (m) m.classList.add('active');
    },

    openAccountModal: function() {
        const m = document.getElementById('account-modal');
        if (m) m.classList.add('active');
    },

    toggleViewMode: function() {
        const wrapper = document.getElementById('app-wrapper');
        const btn = document.getElementById('btn-toggle-view-mode');
        if (!wrapper) return;

        if (App.viewMode === 'mobile') {
            App.viewMode = 'fullscreen';
            wrapper.classList.remove('view-mobile-frame');
            wrapper.classList.add('view-fullscreen');
            if (btn) btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg> Phone View`;
        } else {
            App.viewMode = 'mobile';
            wrapper.classList.remove('view-fullscreen');
            wrapper.classList.add('view-mobile-frame');
            if (btn) btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path></svg> Fullscreen`;
        }
    },

    showToast: function(message) {
        let toast = document.getElementById('app-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'app-toast';
            toast.className = 'app-toast';
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.classList.add('show');
        if (this._toastTimeout) clearTimeout(this._toastTimeout);
        this._toastTimeout = setTimeout(() => toast.classList.remove('show'), 3500);
    }
};

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
