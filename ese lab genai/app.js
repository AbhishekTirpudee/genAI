// ElectroRAG Client-Side Controller
let componentsData = [];
let currentFilter = 'all';

// DOM Elements
const componentList = document.getElementById('componentList');
const componentCount = document.getElementById('componentCount');
const catalogueSearchInput = document.getElementById('catalogueSearchInput');
const categoryFilters = document.getElementById('categoryFilters');
const chatHistory = document.getElementById('chatHistory');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const welcomeHero = document.getElementById('welcomeHero');
const detailModal = document.getElementById('detailModal');
const modalPartNumber = document.getElementById('modalPartNumber');
const modalDetailContent = document.getElementById('modalDetailContent');
const closeDetailModalBtn = document.getElementById('closeDetailModalBtn');
const settingsModal = document.getElementById('settingsModal');
const openSettingsBtn = document.getElementById('openSettingsBtn');
const closeSettingsModalBtn = document.getElementById('closeSettingsModalBtn');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');
const apiKeyInput = document.getElementById('apiKeyInput');
const engineModeSelect = document.getElementById('engineModeSelect');
const dropZone = document.getElementById('dropZone');
const catalogueFileInput = document.getElementById('catalogueFileInput');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  // Load saved settings
  const savedKey = localStorage.getItem('gemini_api_key');
  if (savedKey) apiKeyInput.value = savedKey;
  const savedMode = localStorage.getItem('rag_engine_mode');
  if (savedMode) engineModeSelect.value = savedMode;

  loadComponents();
  setupEventListeners();
});

// Load Components from Backend API
async function loadComponents() {
  try {
    const res = await fetch('/api/components');
    if (!res.ok) throw new Error('API not responding');
    componentsData = await res.json();
    renderComponentList();
  } catch (err) {
    console.warn('Backend API unavailable, loading from local JSON database...', err);
    try {
      const res = await fetch('electronic_components_catalogue.json');
      componentsData = await res.json();
      renderComponentList();
    } catch (e) {
      console.error('Failed to load catalogue:', e);
    }
  }
}

// Render Component Cards in Sidebar
function renderComponentList() {
  const searchTerm = catalogueSearchInput.value.toLowerCase().trim();
  
  const filtered = componentsData.filter(comp => {
    const matchesCat = currentFilter === 'all' || 
      (comp.category && comp.category.toLowerCase().includes(currentFilter.toLowerCase()));
    const matchesSearch = !searchTerm || 
      comp.part_number.toLowerCase().includes(searchTerm) || 
      (comp.description && comp.description.toLowerCase().includes(searchTerm)) ||
      (comp.category && comp.category.toLowerCase().includes(searchTerm));
    return matchesCat && matchesSearch;
  });

  componentCount.textContent = `${filtered.length} Components`;

  if (filtered.length === 0) {
    componentList.innerHTML = `
      <div style="text-align: center; color: var(--text-dim); padding: 24px; font-size: 0.82rem;">
        No components match your search filter.
      </div>
    `;
    return;
  }

  componentList.innerHTML = filtered.map(comp => `
    <div class="component-card" onclick="openComponentDetail('${comp.part_number}')">
      <div class="comp-header">
        <span class="comp-mpn">${comp.part_number}</span>
        <span class="comp-price-badge">$${comp.pricing?.qty_1 ?? '-'} / 1pc</span>
      </div>
      <div class="comp-cat">${comp.category || 'General'}</div>
      <div class="comp-desc">${comp.description || ''}</div>
      <div class="comp-footer">
        <span>Pkg: ${comp.specifications?.package || 'N/A'}</span>
        <span>Page ${comp.page_number || 1}</span>
      </div>
    </div>
  `).join('');
}

// Open Component Details Modal
window.openComponentDetail = function(partNumber) {
  const comp = componentsData.find(c => c.part_number.toLowerCase() === partNumber.toLowerCase());
  if (!comp) return;

  modalPartNumber.textContent = `${comp.part_number} — Technical Datasheet`;
  
  let specsRows = '';
  if (comp.specifications) {
    for (const [key, val] of Object.entries(comp.specifications)) {
      specsRows += `
        <tr>
          <td style="font-weight: 600; color: var(--accent-cyan); width: 40%; text-transform: capitalize;">${key.replace(/_/g, ' ')}</td>
          <td>${val}</td>
        </tr>
      `;
    }
  }

  const appsList = (comp.applications || []).map(a => `<li>${a}</li>`).join('');

  modalDetailContent.innerHTML = `
    <div style="margin-bottom: 16px;">
      <span style="font-family: var(--font-mono); font-size: 0.75rem; background: rgba(79, 172, 254, 0.15); color: var(--accent-cyan); padding: 3px 8px; border-radius: 4px;">${comp.category}</span>
      <span style="font-family: var(--font-mono); font-size: 0.75rem; background: rgba(72, 187, 120, 0.15); color: #68d391; padding: 3px 8px; border-radius: 4px; margin-left: 8px;">${comp.stock_status || 'In Stock'}</span>
      <span style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted); margin-left: 8px;">Catalogue Page ${comp.page_number}</span>
    </div>
    <p style="font-size: 0.88rem; color: #cbd5e0; line-height: 1.5; margin-bottom: 20px;">${comp.description}</p>

    <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--accent-amber); margin-bottom: 8px;">Technical Specifications</h4>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.82rem; background: rgba(10, 15, 27, 0.5); border: 1px solid var(--border-subtle); border-radius: 8px;">
      <tbody>${specsRows}</tbody>
    </table>

    <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--accent-amber); margin-bottom: 8px;">Recommended Applications</h4>
    <ul style="padding-left: 20px; font-size: 0.84rem; color: var(--text-main); margin-bottom: 20px; line-height: 1.6;">
      ${appsList}
    </ul>

    <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--accent-amber); margin-bottom: 8px;">Volume Pricing Tiers</h4>
    <table style="width: 100%; border-collapse: collapse; font-size: 0.82rem; background: rgba(10, 15, 27, 0.5); border: 1px solid var(--border-subtle); border-radius: 8px;">
      <thead>
        <tr style="background: rgba(79, 172, 254, 0.1); color: var(--accent-cyan);">
          <th style="padding: 6px 12px; text-align: left;">Quantity Break</th>
          <th style="padding: 6px 12px; text-align: left;">Unit Price (USD)</th>
        </tr>
      </thead>
      <tbody>
        <tr><td style="padding: 6px 12px;">1 - 9 pcs</td><td style="padding: 6px 12px; font-family: var(--font-mono); font-weight: 600; color: #68d391;">$${comp.pricing?.qty_1 ?? '-'}</td></tr>
        <tr><td style="padding: 6px 12px;">10 - 99 pcs</td><td style="padding: 6px 12px; font-family: var(--font-mono); font-weight: 600; color: #68d391;">$${comp.pricing?.qty_10 ?? '-'}</td></tr>
        <tr><td style="padding: 6px 12px;">100 - 999 pcs</td><td style="padding: 6px 12px; font-family: var(--font-mono); font-weight: 600; color: #68d391;">$${comp.pricing?.qty_100 ?? '-'}</td></tr>
        <tr><td style="padding: 6px 12px;">1000+ pcs</td><td style="padding: 6px 12px; font-family: var(--font-mono); font-weight: 600; color: #68d391;">$${comp.pricing?.qty_1000 ?? '-'}</td></tr>
      </tbody>
    </table>
  `;

  detailModal.classList.add('active');
};

// Event Listeners Setup
function setupEventListeners() {
  // Search filter
  catalogueSearchInput.addEventListener('input', renderComponentList);

  // Category filter pills
  categoryFilters.addEventListener('click', (e) => {
    if (e.target.classList.contains('cat-pill')) {
      document.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
      e.target.classList.add('active');
      currentFilter = e.target.getAttribute('data-cat');
      renderComponentList();
    }
  });

  // Suggestion chips
  document.querySelectorAll('.suggestion-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const query = btn.getAttribute('data-query');
      chatInput.value = query;
      handleChatSubmit(query);
    });
  });

  // Chat submit form
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (query) {
      handleChatSubmit(query);
    }
  });

  // Modal controls
  closeDetailModalBtn.addEventListener('click', () => detailModal.classList.remove('active'));
  detailModal.addEventListener('click', (e) => {
    if (e.target === detailModal) detailModal.classList.remove('active');
  });

  openSettingsBtn.addEventListener('click', () => settingsModal.classList.add('active'));
  closeSettingsModalBtn.addEventListener('click', () => settingsModal.classList.remove('active'));
  settingsModal.addEventListener('click', (e) => {
    if (e.target === settingsModal) settingsModal.classList.remove('active');
  });

  saveSettingsBtn.addEventListener('click', () => {
    localStorage.setItem('gemini_api_key', apiKeyInput.value.trim());
    localStorage.setItem('rag_engine_mode', engineModeSelect.value);
    settingsModal.classList.remove('active');
  });

  // File Upload handling
  catalogueFileInput.addEventListener('change', handleFileUpload);
  dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = 'var(--accent-cyan)'; });
  dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = 'rgba(79, 172, 254, 0.35)'; });
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'rgba(79, 172, 254, 0.35)';
    if (e.dataTransfer.files.length) {
      catalogueFileInput.files = e.dataTransfer.files;
      handleFileUpload();
    }
  });
}

function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = '';
  let insideQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (char === '"') {
      if (insideQuotes && text[i + 1] === '"') {
        field += '"';
        i += 1;
      } else {
        insideQuotes = !insideQuotes;
      }
    } else if (char === ',' && !insideQuotes) {
      row.push(field);
      field = '';
    } else if ((char === '\n' || char === '\r') && !insideQuotes) {
      if (char === '\r' && text[i + 1] === '\n') i += 1;
      row.push(field);
      if (row.some(value => value.trim())) rows.push(row);
      row = [];
      field = '';
    } else {
      field += char;
    }
  }

  row.push(field);
  if (row.some(value => value.trim())) rows.push(row);
  return rows;
}

function normalizeComponent(record, index) {
  const normalizedKeys = Object.fromEntries(
    Object.entries(record).map(([key, value]) => [
      key.toLowerCase().replace(/[^a-z0-9]/g, ''),
      value
    ])
  );
  const read = (...keys) => {
    for (const key of keys) {
      const value = normalizedKeys[key.toLowerCase().replace(/[^a-z0-9]/g, '')];
      if (value !== undefined && value !== null && String(value).trim() !== '') return value;
    }
    return undefined;
  };
  const partNumber = read('part_number', 'partnumber', 'mpn', 'part');
  if (!partNumber) throw new Error(`Row ${index + 1} is missing a part number.`);

  const rawSpecifications = record.specifications;
  const specifications = rawSpecifications && typeof rawSpecifications === 'object' && !Array.isArray(rawSpecifications)
    ? { ...rawSpecifications }
    : {};
  const voltage = read('operating_voltage', 'operatingvoltage', 'input_voltage', 'inputvoltage');
  const keySpecs = read('key_specs', 'keyspecs', 'key_specifications', 'specifications');
  if (voltage !== undefined) specifications.operating_voltage = voltage;
  if (keySpecs !== undefined && typeof keySpecs !== 'object') specifications.key_specifications = keySpecs;

  const rawApplications = record.applications ?? read('applications', 'application');
  const applications = Array.isArray(rawApplications)
    ? rawApplications
    : String(rawApplications || '').split(/[;,]/).map(value => value.trim()).filter(Boolean);

  const pricing = record.pricing && typeof record.pricing === 'object' ? { ...record.pricing } : {};
  for (const quantity of [1, 10, 100, 1000]) {
    const price = read(`qty_${quantity}`, `priceqty${quantity}`, `price_qty_${quantity}`, `price${quantity}`);
    if (price !== undefined) pricing[`qty_${quantity}`] = Number(price) || price;
  }

  return {
    part_number: String(partNumber).trim(),
    category: read('category') || 'General',
    description: read('description') || '',
    specifications,
    applications,
    pricing,
    stock_status: read('stock_status', 'stockstatus', 'stock') || 'Unknown',
    page_number: Number(read('page_number', 'pagenumber', 'page')) || 1
  };
}

// Handle Catalogue File Upload (JSON / CSV)
async function handleFileUpload() {
  const file = catalogueFileInput.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = async (e) => {
    try {
      const text = String(e.target.result || '');
      const extension = file.name.split('.').pop().toLowerCase();
      let records;
      if (extension === 'json') {
        const parsed = JSON.parse(text);
        records = Array.isArray(parsed) ? parsed : parsed.components;
      } else if (extension === 'csv') {
        const rows = parseCSV(text);
        if (rows.length < 2) throw new Error('The CSV must contain a header and at least one component row.');
        const headers = rows[0].map(header => header.trim());
        records = rows.slice(1).map(values => Object.fromEntries(
          headers.map((header, i) => [header, values[i] || ''])
        ));
      } else {
        throw new Error('Please select a JSON or CSV catalogue.');
      }

      if (!Array.isArray(records) || records.length === 0) {
        throw new Error('The catalogue must contain at least one component.');
      }
      const newComponents = records.map((record, index) => normalizeComponent(record, index + 1));
      const response = await fetch('/api/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ components: newComponents })
        });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'The server could not index this catalogue.');

      componentsData = newComponents;
      renderComponentList();
      alert(`Successfully uploaded & indexed ${result.count} components. You can now ask questions about their specifications, applications, and prices.`);
    } catch (err) {
      alert('Catalogue upload failed: ' + err.message);
    }
  };
  reader.onerror = () => alert('Catalogue upload failed: the selected file could not be read.');
  reader.readAsText(file);
}

// Handle Chat Message Execution
async function handleChatSubmit(query) {
  chatInput.value = '';
  sendBtn.disabled = true;

  // Append user message
  appendMessage('user', query);

  // Append temporary loading message
  const loadingId = 'loading-' + Date.now();
  appendLoadingMessage(loadingId);

  const apiKey = localStorage.getItem('gemini_api_key') || '';
  const mode = localStorage.getItem('rag_engine_mode') || 'offline';

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        api_key: mode === 'gemini' ? apiKey : null
      })
    });

    removeMessage(loadingId);

    if (response.ok) {
      const data = await response.json();
      appendBotMessage(data.answer, data.citations, data.mode);
    } else {
      // Fallback to local in-browser search if server returns error
      const fallback = localRagQuery(query);
      appendBotMessage(fallback.answer, fallback.citations, "Client-Side Browser RAG");
    }
  } catch (err) {
    removeMessage(loadingId);
    // Offline local browser RAG
    const fallback = localRagQuery(query);
    appendBotMessage(fallback.answer, fallback.citations, "Local Offline RAG Fallback");
  } finally {
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

// Append User Message to Chat History
function appendMessage(role, text) {
  const row = document.createElement('div');
  row.className = `message-row ${role}`;
  row.innerHTML = `
    <div class="message-avatar ${role === 'user' ? 'user-avatar' : 'bot-avatar'}">
      ${role === 'user' ? '👤' : '⚡'}
    </div>
    <div class="message-content">
      ${escapeHtml(text)}
    </div>
  `;
  chatHistory.appendChild(row);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Append Loading Indicator
function appendLoadingMessage(id) {
  const row = document.createElement('div');
  row.className = 'message-row bot';
  row.id = id;
  row.innerHTML = `
    <div class="message-avatar bot-avatar">⚡</div>
    <div class="message-content" style="color: var(--accent-cyan); font-family: var(--font-mono); font-size: 0.8rem;">
      <span class="loading-dots"><span></span><span></span><span></span></span>
      &nbsp; Retrieving catalogue specs & computing hybrid score...
    </div>
  `;
  chatHistory.appendChild(row);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

function removeMessage(id) {
  const elem = document.getElementById(id);
  if (elem) elem.remove();
}

// Append Bot Response with Markdown Formatting & Citations
function appendBotMessage(markdownText, citations = [], mode = "") {
  const row = document.createElement('div');
  row.className = 'message-row bot';

  const htmlContent = renderMarkdown(markdownText);

  let citationsHtml = '';
  if (citations && citations.length > 0) {
    const pills = citations.map(c => `
      <span class="citation-pill" onclick="openComponentDetail('${c.part_number}')" title="Relevance Score: ${c.relevance_score}">
        📖 Page ${c.page}: ${c.part_number} (${Math.round(c.relevance_score * 100)}%)
      </span>
    `).join('');
    citationsHtml = `
      <div class="citations-box">
        <span class="citation-title">Catalogue Sources:</span>
        ${pills}
      </div>
    `;
  }

  row.innerHTML = `
    <div class="message-avatar bot-avatar">⚡</div>
    <div class="message-content">
      ${htmlContent}
      ${citationsHtml}
    </div>
  `;
  chatHistory.appendChild(row);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Simple Markdown to HTML Parser (supporting tables, bold, headers, lists)
function renderMarkdown(md) {
  if (!md) return '';

  let html = md;

  // Tables
  const tableRegex = /\|(.+)\|[\r\n]+\|([-:| ]+)\|[\r\n]+((?:\|.*\|[\r\n]*)+)/g;
  html = html.replace(tableRegex, (match, headerRow, separatorRow, bodyRows) => {
    const headers = headerRow.split('|').filter(h => h.trim().length > 0);
    const ths = headers.map(h => `<th>${h.trim()}</th>`).join('');

    const rows = bodyRows.trim().split('\n').map(row => {
      const cells = row.split('|').filter(c => c.trim().length > 0);
      return `<tr>${cells.map(c => `<td>${c.trim()}</td>`).join('')}</tr>`;
    }).join('');

    return `<table><thead><tr>${ths}</tr></thead><tbody>${rows}</tbody></table>`;
  });

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');

  // Bold & Italic
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Bullet Lists
  html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

  // Line breaks
  html = html.replace(/\n\n/g, '<p style="margin-bottom: 8px;"></p>');

  return html;
}

function escapeHtml(str) {
  return str.replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[m]);
}

// Client-Side RAG fallback (pure JS) if backend is offline
function localRagQuery(query) {
  const qLower = query.toLowerCase();
  const matched = componentsData.map(c => {
    let score = 0;
    const mpn = c.part_number.toLowerCase();
    if (qLower.includes(mpn) || mpn.includes(qLower)) score += 3.0;
    const desc = (c.description || '').toLowerCase();
    const words = qLower.split(/\s+/);
    words.forEach(w => {
      if (w.length > 2 && (desc.includes(w) || (c.category||'').toLowerCase().includes(w))) score += 0.5;
    });
    return { comp: c, score };
  }).sort((a, b) => b.score - a.score);

  const top = matched[0]?.comp || componentsData[0];
  const p = top.pricing || {};

  return {
    answer: `### ${top.part_number} (${top.category})\n\n${top.description}\n\n#### Specifications\n| Spec | Value |\n| :--- | :--- |\n| Operating Voltage | ${top.specifications?.operating_voltage || top.specifications?.input_voltage || 'N/A'} |\n| Package | ${top.specifications?.package || 'N/A'} |\n\n#### Pricing\n| Qty | Price |\n| :--- | :--- |\n| 1 pc | $${p.qty_1 || '-'} |\n| 100 pcs | $${p.qty_100 || '-'} |\n\n- Catalogue Page: ${top.page_number}`,
    citations: [{ part_number: top.part_number, page: top.page_number, relevance_score: 0.95 }]
  };
}
