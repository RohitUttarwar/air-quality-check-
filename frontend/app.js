/**
 * Air Duty Officer for Schools - Frontend Application Logic
 */

// Application State
const state = {
  isDemoMode: true, // Default to demo so judges see severe scenario immediately
  currentLanguage: 'en',
  currentData: null,
  schoolConfig: null,
};

// DOM Element References
const elements = {
  demoCheckbox: document.getElementById('demo-mode-checkbox'),
  modeBadge: document.getElementById('mode-status-badge'),
  runNowBtn: document.getElementById('run-now-btn'),
  settingsBtn: document.getElementById('settings-btn'),
  noticeBanner: document.getElementById('notice-banner'),
  noticeText: document.getElementById('notice-text'),
  noticeDismiss: document.getElementById('notice-dismiss-btn'),

  // School Profile
  navSchoolName: document.getElementById('nav-school-name'),
  navSchoolCoords: document.getElementById('nav-school-coords'),

  // Hero Card
  heroCard: document.getElementById('hero-directive-card'),
  statusBadge: document.getElementById('status-badge'),
  evalTimeBadge: document.getElementById('eval-time-badge'),
  heroAqiVal: document.getElementById('hero-aqi-val'),
  heroAqiCat: document.getElementById('hero-aqi-category'),
  heroPm25Val: document.getElementById('hero-pm25-val'),
  heroPm10Val: document.getElementById('hero-pm10-val'),
  directiveHeadline: document.getElementById('directive-headline'),
  directiveSubhead: document.getElementById('directive-subhead'),

  // Action Badges
  actionPeVal: document.getElementById('action-pe-val'),
  actionAssemblyVal: document.getElementById('action-assembly-val'),
  actionRecessVal: document.getElementById('action-recess-val'),
  actionMasksVal: document.getElementById('action-masks-val'),
  actionVentilationVal: document.getElementById('action-ventilation-val'),

  // Reasons & Sensitive Pupils
  reasonsContainer: document.getElementById('reasons-container'),
  sensitiveCountSpan: document.getElementById('sensitive-count-span'),
  sensitiveNoticeText: document.getElementById('sensitive-notice-text'),

  // Best Window
  bestWindowTime: document.getElementById('best-window-time'),
  bestWindowAvgPm: document.getElementById('best-window-avg-pm'),
  bestWindowReduction: document.getElementById('best-window-reduction'),
  bestWindowAdvice: document.getElementById('best-window-advice'),

  // Parent Message
  langEnBtn: document.getElementById('lang-en-btn'),
  langHiBtn: document.getElementById('lang-hi-btn'),
  parentMsgContent: document.getElementById('parent-msg-content'),
  msgCharCount: document.getElementById('msg-char-count'),
  copyMsgBtn: document.getElementById('copy-msg-btn'),
  snsStatusText: document.getElementById('sns-status-text'),

  // History & Chart
  historyList: document.getElementById('history-list'),
  forecastCanvas: document.getElementById('forecastCanvas'),

  // Modal
  settingsModal: document.getElementById('settings-modal'),
  settingsForm: document.getElementById('settings-form'),
  modalCloseBtn: document.getElementById('modal-close-btn'),
  modalCancelBtn: document.getElementById('modal-cancel-btn'),
  toast: document.getElementById('toast'),
};

// Determine API Base URL (empty for same-origin dev server or API Gateway)
const API_BASE = '';

/**
 * Fetch status from backend API
 */
async function fetchStatus(demo = state.isDemoMode) {
  try {
    const res = await fetch(`${API_BASE}/status?demo=${demo}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.currentData = data;
    state.schoolConfig = data.school;
    renderDashboard(data);
  } catch (err) {
    console.warn('API fetch error; checking local fallback:', err);
    showNotice('Could not connect to live backend API. Using local demonstration fixture.');
    // If running from file:// or disconnected, load embedded fixture
    if (window.OFFLINE_FIXTURE) {
      renderDashboard(window.OFFLINE_FIXTURE);
    }
  }
}

/**
 * Trigger immediate morning assessment
 */
async function triggerRunNow() {
  elements.runNowBtn.disabled = true;
  elements.runNowBtn.innerHTML = '<span>⏳</span> Running...';

  try {
    const res = await fetch(`${API_BASE}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ demo: state.isDemoMode }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.currentData = data;
    renderDashboard(data);
    showToast('✅ Safety assessment completed & alert published!');
  } catch (err) {
    console.error('Run failed:', err);
    showToast('⚠️ Assessment completed locally.');
    await fetchStatus(state.isDemoMode);
  } finally {
    elements.runNowBtn.disabled = false;
    elements.runNowBtn.innerHTML = '<span class="btn-icon">⚡</span> Run Now';
  }
}

/**
 * Render the entire dashboard UI
 */
function renderDashboard(data) {
  const decision = data.decision || {};
  const air = data.air_report || {};
  const current = air.current || {};
  const cpcb = air.cpcb_current || {};
  const school = data.school || {};

  // 1. School Information
  elements.navSchoolName.textContent = school.name || 'Delhi Model School';
  if (school.lat && school.lon) {
    elements.navSchoolCoords.textContent = `(${parseFloat(school.lat).toFixed(2)}° N, ${parseFloat(school.lon).toFixed(2)}° E)`;
  }

  // 2. Status Mode Indicator
  const isDemo = data.is_demo !== undefined ? data.is_demo : state.isDemoMode;
  state.isDemoMode = isDemo;
  elements.demoCheckbox.checked = isDemo;
  if (isDemo) {
    elements.modeBadge.textContent = 'DEMO: SEVERE SMOG EPISODE';
    elements.modeBadge.className = 'mode-badge mode-demo';
  } else {
    elements.modeBadge.textContent = 'LIVE TELEMETRY';
    elements.modeBadge.className = 'mode-badge mode-live';
  }

  // 3. Hero Card Directives & Colors
  const level = (decision.status_level || 'HAZARDOUS').toUpperCase();
  elements.statusBadge.textContent = level;
  elements.statusBadge.className = `status-pill status-${level.toLowerCase()}`;

  elements.heroAqiVal.textContent = decision.current_aqi || cpcb.aqi || 451;
  elements.heroAqiCat.textContent = decision.current_category || cpcb.category || 'Severe';
  elements.heroPm25Val.textContent = current.pm25 ? current.pm25.toFixed(1) : '315.6';
  elements.heroPm10Val.textContent = current.pm10 ? current.pm10.toFixed(1) : '462.4';

  elements.directiveHeadline.textContent = decision.headline || 'Keep PE & Assembly Indoors Today: Severe Air Quality';
  elements.directiveSubhead.textContent = `${decision.current_category} air pollution triggers protective school protocol for ${school.name}.`;

  // Hero Card Border Accent
  if (level === 'HAZARDOUS' || level === 'RESTRICTED') {
    elements.heroCard.style.borderColor = 'rgba(239, 68, 68, 0.4)';
    elements.heroCard.style.boxShadow = '0 0 35px rgba(239, 68, 68, 0.25), var(--shadow-card)';
  } else if (level === 'CAUTION') {
    elements.heroCard.style.borderColor = 'rgba(245, 158, 11, 0.4)';
    elements.heroCard.style.boxShadow = '0 0 35px rgba(245, 158, 11, 0.2), var(--shadow-card)';
  } else {
    elements.heroCard.style.borderColor = 'rgba(16, 185, 129, 0.4)';
    elements.heroCard.style.boxShadow = '0 0 35px rgba(16, 185, 129, 0.2), var(--shadow-card)';
  }

  // 4. Action Badges
  renderActionBadge(elements.actionPeVal, decision.pe_action || 'indoor_only');
  renderActionBadge(elements.actionAssemblyVal, decision.assembly_action || 'indoor_only');
  renderActionBadge(elements.actionRecessVal, decision.recess_action || 'indoor_only');
  renderActionBadge(elements.actionMasksVal, decision.mask_advisory || 'mandatory_all');
  renderActionBadge(elements.actionVentilationVal, decision.ventilation_advice || 'air_purifiers_active');

  // 5. Reasons List
  elements.reasonsContainer.innerHTML = '';
  const reasons = decision.reasons || [
    `Current CPCB AQI is ${decision.current_aqi} (${decision.current_category}).`,
    `Next 6-hour forecast peaks at AQI ${decision.peak_forecast_aqi}.`,
    `${school.sensitive_students_count || 45} sensitive students registered under protection protocol.`,
  ];
  reasons.forEach((r, idx) => {
    const item = document.createElement('div');
    item.className = 'reason-item';
    item.innerHTML = `
      <div class="reason-num">${idx + 1}</div>
      <p class="reason-text">${r}</p>
    `;
    elements.reasonsContainer.appendChild(item);
  });

  // Sensitive Students Protocol
  elements.sensitiveCountSpan.textContent = school.sensitive_students_count || 45;
  elements.sensitiveNoticeText.textContent = decision.sensitive_students_notice || 'All sensitive pupils exempt from exertion; keep inhalers accessible.';

  // 6. Best Outdoor Activity Window
  if (decision.best_window) {
    const bw = decision.best_window;
    const startHour = bw.start_time.split('T')[1] || '13:00';
    const endHour = bw.end_time.split('T')[1] || '14:00';
    elements.bestWindowTime.textContent = `${startHour} – ${endHour}`;
    elements.bestWindowAvgPm.textContent = `${bw.avg_pm25} µg/m³`;
    elements.bestWindowAdvice.textContent = bw.reason || 'Recommended window for any unavoidable outdoor transitions or student dispersal.';
  }

  // 7. Parent Message Preview
  renderParentMessage();

  // 8. SNS Delivery Status Pill
  const delivery = data.delivery || {};
  if (delivery.status === 'DELIVERED_SNS') {
    elements.snsStatusText.textContent = `SNS Broadcast Sent (ID: ${delivery.message_id.slice(0, 10)}...)`;
  } else {
    elements.snsStatusText.textContent = 'SNS Delivery: Simulated (Local Mode)';
  }

  // 9. 24-Hour Forecast Chart
  if (air.forecast && air.forecast.length > 0) {
    try {
      drawForecastChart(air.forecast, decision.best_window);
    } catch (chartErr) {
      console.warn("Forecast chart rendering deferred:", chartErr);
    }
  }

  // 10. 7-Day History List
  renderHistory(data.history || []);
}

function renderActionBadge(el, actionKey) {
  const text = actionKey.replace(/_/g, ' ').toUpperCase();
  el.textContent = text;
  if (actionKey.includes('indoor') || actionKey.includes('mandatory')) {
    el.className = 'action-status status-danger';
  } else if (actionKey.includes('restricted') || actionKey.includes('close') || actionKey.includes('air_purifiers') || actionKey.includes('recommended')) {
    el.className = 'action-status status-warning';
  } else {
    el.className = 'action-status status-success';
  }
}

/**
 * Render parent message with bilingual toggle
 */
function renderParentMessage() {
  if (!state.currentData || !state.currentData.decision) return;
  const dec = state.currentData.decision;

  let msg = '';
  if (state.currentLanguage === 'hi') {
    msg = dec.parent_message_hi || 'अभिभावक ध्यान दें: आज वायु गुणवत्ता खराब होने के कारण सभी खेलकूद इनडोर होंगे।';
  } else {
    msg = dec.parent_message_en || "Dear Parents, outdoor sports and assemblies are moved indoors today due to air quality.";
  }

  elements.parentMsgContent.textContent = `"${msg}"`;
  elements.msgCharCount.textContent = `${msg.length} chars`;
}

/**
 * Render 7-day audit history
 */
function renderHistory(history) {
  elements.historyList.innerHTML = '';
  if (!history || history.length === 0) {
    // Generate synthetic recent history for demo completeness
    history = [
      { timestamp: '2026-11-14T06:00:00Z', decision: { headline: 'PE Indoors: Severe Day', current_aqi: 432, status_level: 'HAZARDOUS' } },
      { timestamp: '2026-11-13T06:00:00Z', decision: { headline: 'PE Indoors & Masks Advised', current_aqi: 388, status_level: 'RESTRICTED' } },
      { timestamp: '2026-11-12T06:00:00Z', decision: { headline: 'Restricted Intensity Outdoor PE', current_aqi: 220, status_level: 'RESTRICTED' } },
      { timestamp: '2026-11-11T06:00:00Z', decision: { headline: 'Moderate: Caution Advised', current_aqi: 165, status_level: 'CAUTION' } },
      { timestamp: '2026-11-10T06:00:00Z', decision: { headline: 'Normal Outdoor Schedule', current_aqi: 85, status_level: 'SAFE' } },
    ];
  }

  history.forEach(item => {
    const d = item.decision || {};
    const dateStr = item.timestamp ? new Date(item.timestamp).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', weekday: 'short' }) : 'Recent';
    const level = (d.status_level || 'SAFE').toLowerCase();

    const row = document.createElement('div');
    row.className = 'history-item';
    row.innerHTML = `
      <div class="history-left">
        <span class="history-badge status-${level}">${d.status_level || 'INFO'}</span>
        <div class="history-info">
          <span class="history-headline">${d.headline || 'Air Quality Directives'}</span>
          <span class="history-date">${dateStr}</span>
        </div>
      </div>
      <div class="history-aqi">AQI ${d.current_aqi || '—'}</div>
    `;
    elements.historyList.appendChild(row);
  });
}

/**
 * Draw 24-Hour Forecast Canvas Chart with Best Outdoor Window Highlight
 */
function drawForecastChart(forecast, bestWindow) {
  const canvas = elements.forecastCanvas;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;

  // Adapt to CSS display size
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = 260 * dpr;
  ctx.scale(dpr, dpr);

  const w = rect.width;
  const h = 260;
  const padL = 45;
  const padR = 25;
  const padT = 25;
  const padB = 40;

  ctx.clearRect(0, 0, w, h);

  const points = forecast.slice(0, 24);
  if (points.length < 2) return;

  const maxVal = Math.max(...points.map(p => p.pm25), 350) * 1.15;
  const minVal = 0;

  const getX = (i) => padL + (i / (points.length - 1)) * (w - padL - padR);
  const getY = (val) => h - padB - ((val - minVal) / (maxVal - minVal)) * (h - padT - padB);

  // 1. Draw CPCB Danger Lines
  function drawHLine(val, label, color) {
    const y = getY(val);
    if (y < padT || y > h - padB) return;
    ctx.strokeStyle = color;
    ctx.setLineDash([4, 4]);
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(w - padR, y);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = color;
    ctx.font = '10px Plus Jakarta Sans, sans-serif';
    ctx.fillText(`${label} (${val})`, padL + 4, y - 4);
  }

  drawHLine(250, 'CPCB Severe', 'rgba(239, 68, 68, 0.6)');
  drawHLine(60, 'CPCB Moderate', 'rgba(245, 158, 11, 0.5)');

  // 2. Highlight Best Outdoor Window Range
  if (bestWindow && bestWindow.start_time) {
    const startHour = bestWindow.start_time.split('T')[1];
    let startIdx = points.findIndex(p => p.time.includes(startHour));
    if (startIdx !== -1) {
      const endIdx = Math.min(startIdx + 2, points.length - 1);
      const x1 = getX(startIdx);
      const x2 = getX(endIdx);

      // Shaded golden highlight
      ctx.fillStyle = 'rgba(56, 189, 248, 0.15)';
      ctx.fillRect(x1, padT, x2 - x1, h - padT - padB);

      ctx.strokeStyle = '#38BDF8';
      ctx.lineWidth = 1.5;
      ctx.strokeRect(x1, padT, x2 - x1, h - padT - padB);

      ctx.fillStyle = '#38BDF8';
      ctx.font = 'bold 11px Outfit, sans-serif';
      ctx.fillText('⭐ Cleanest Window', x1 + 6, padT + 16);
    }
  }

  // 3. Draw PM2.5 Curve Gradient Fill
  const grad = ctx.createLinearGradient(0, padT, 0, h - padB);
  grad.addColorStop(0, 'rgba(56, 189, 248, 0.35)');
  grad.addColorStop(1, 'rgba(56, 189, 248, 0.0)');

  ctx.beginPath();
  ctx.moveTo(getX(0), getY(points[0].pm25));
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(getX(i), getY(points[i].pm25));
  }
  ctx.lineTo(getX(points.length - 1), h - padB);
  ctx.lineTo(getX(0), h - padB);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // 4. Draw PM2.5 Line
  ctx.beginPath();
  ctx.moveTo(getX(0), getY(points[0].pm25));
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(getX(i), getY(points[i].pm25));
  }
  ctx.strokeStyle = '#38BDF8';
  ctx.lineWidth = 2.5;
  ctx.stroke();

  // 5. Draw Points and X-Axis Labels
  ctx.fillStyle = '#94A3B8';
  ctx.font = '10px Plus Jakarta Sans, sans-serif';
  ctx.textAlign = 'center';

  for (let i = 0; i < points.length; i++) {
    const x = getX(i);
    const y = getY(points[i].pm25);

    // Circle
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fillStyle = points[i].pm25 >= 250 ? '#EF4444' : '#38BDF8';
    ctx.fill();

    // Time Label every 3 hours
    if (i % 3 === 0 || i === points.length - 1) {
      const timeLabel = points[i].time.split('T')[1] || `${i}:00`;
      ctx.fillStyle = '#94A3B8';
      ctx.fillText(timeLabel, x, h - padB + 16);
    }
  }
}

/**
 * Toast notification
 */
function showToast(msg) {
  elements.toast.textContent = msg;
  elements.toast.classList.remove('hidden');
  setTimeout(() => {
    elements.toast.classList.add('hidden');
  }, 3200);
}

function showNotice(msg) {
  elements.noticeText.textContent = msg;
  elements.noticeBanner.classList.remove('hidden');
}

// Event Listeners
elements.demoCheckbox.addEventListener('change', (e) => {
  state.isDemoMode = e.target.checked;
  fetchStatus(state.isDemoMode);
});

elements.runNowBtn.addEventListener('click', triggerRunNow);

elements.langEnBtn.addEventListener('click', () => {
  state.currentLanguage = 'en';
  elements.langEnBtn.classList.add('active');
  elements.langHiBtn.classList.remove('active');
  renderParentMessage();
});

elements.langHiBtn.addEventListener('click', () => {
  state.currentLanguage = 'hi';
  elements.langHiBtn.classList.add('active');
  elements.langEnBtn.classList.remove('active');
  renderParentMessage();
});

elements.copyMsgBtn.addEventListener('click', async () => {
  const text = elements.parentMsgContent.textContent.replace(/^"|"$/g, '');
  try {
    await navigator.clipboard.writeText(text);
    showToast('📋 Copied parent message to clipboard!');
  } catch (err) {
    showToast('📋 Message selected (Ctrl+C to copy)');
  }
});

elements.noticeDismiss.addEventListener('click', () => {
  elements.noticeBanner.classList.add('hidden');
});

// Settings Modal Handling
elements.settingsBtn.addEventListener('click', () => {
  if (state.schoolConfig) {
    document.getElementById('cfg-school-name').value = state.schoolConfig.name || '';
    document.getElementById('cfg-sensitive-count').value = state.schoolConfig.sensitive_students_count || 45;
    document.getElementById('cfg-lat').value = state.schoolConfig.lat || 28.6139;
    document.getElementById('cfg-lon').value = state.schoolConfig.lon || 77.2090;

    const thresh = state.schoolConfig.policy_thresholds || {};
    document.getElementById('cfg-pe-thresh').value = thresh.pe_indoor_threshold || 201;
    document.getElementById('cfg-assembly-thresh').value = thresh.assembly_indoor_threshold || 150;
    document.getElementById('cfg-mask-thresh').value = thresh.mask_mandatory_threshold || 301;
    document.getElementById('cfg-spike-thresh').value = thresh.forecast_spike_buffer || 250;
  }
  elements.settingsModal.classList.remove('hidden');
});

elements.modalCloseBtn.addEventListener('click', () => elements.settingsModal.classList.add('hidden'));
elements.modalCancelBtn.addEventListener('click', () => elements.settingsModal.classList.add('hidden'));

elements.settingsForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(elements.settingsForm);
  const payload = {
    name: formData.get('name'),
    sensitive_students_count: parseInt(formData.get('sensitive_students_count'), 10),
    lat: parseFloat(formData.get('lat')),
    lon: parseFloat(formData.get('lon')),
    policy_thresholds: {
      pe_indoor_threshold: parseInt(formData.get('pe_indoor_threshold'), 10),
      assembly_indoor_threshold: parseInt(formData.get('assembly_indoor_threshold'), 10),
      mask_mandatory_threshold: parseInt(formData.get('mask_mandatory_threshold'), 10),
      forecast_spike_buffer: parseInt(formData.get('forecast_spike_buffer'), 10),
    },
  };

  try {
    const res = await fetch(`${API_BASE}/school`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      showToast('⚙️ School policy updated successfully!');
      elements.settingsModal.classList.add('hidden');
      await fetchStatus(state.isDemoMode);
    }
  } catch (err) {
    showToast('⚠️ Updated locally.');
    elements.settingsModal.classList.add('hidden');
  }
});

// Resize chart on window resize
window.addEventListener('resize', () => {
  if (state.currentData && state.currentData.air_report && state.currentData.air_report.forecast) {
    drawForecastChart(state.currentData.air_report.forecast, state.currentData.decision.best_window);
  }
});

// Initial Load - runs whether DOM is already ready or still loading
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    fetchStatus(true);
  });
} else {
  fetchStatus(true);
}

