/**
 * Frontend Application for College Result Analysis Agent.
 * Handles Chat interactions, Chart.js visualizations, Dashboard metrics,
 * Student Marksheets, Subject deep-dive, and SQL Studio.
 */

// Global state
let currentCharts = {};
let allStudentsList = [];
let allSubjectsList = [];

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initChat();
  initDashboard();
  initTranscriptTab();
  initSubjectTab();
  initSqlStudio();
  initSettingsModal();
});

// -------------------------------------------------------------------
// 1. Navigation & Tabs
// -------------------------------------------------------------------
function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');

      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add('active');
      }

      // Refresh charts or load data when switching
      if (targetId === 'tab-dashboard') {
        loadDashboardData();
      } else if (targetId === 'tab-transcript') {
        loadStudentListDropdown();
      } else if (targetId === 'tab-subject') {
        loadSubjectDropdown();
      } else if (targetId === 'tab-sql') {
        loadSchemaTree();
      }
    });
  });
}

// -------------------------------------------------------------------
// 2. AI Result Agent Chat
// -------------------------------------------------------------------
function initChat() {
  const sendBtn = document.getElementById('chat-send-btn');
  const chatInput = document.getElementById('chat-input');
  const queryChips = document.querySelectorAll('.query-chip');

  sendBtn.addEventListener('click', handleChatSubmit);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleChatSubmit();
    }
  });

  queryChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const q = chip.getAttribute('data-query');
      if (q) {
        chatInput.value = q;
        handleChatSubmit();
      }
    });
  });
}

async function handleChatSubmit() {
  const chatInput = document.getElementById('chat-input');
  const query = chatInput.value.trim();
  if (!query) return;

  chatInput.value = '';
  appendUserMessage(query);

  // Loading placeholder
  const loadingId = 'loading-' + Date.now();
  appendAgentLoading(loadingId);

  const apiKey = localStorage.getItem('college_agent_api_key') || null;
  const provider = localStorage.getItem('college_agent_provider') || null;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: query, api_key: apiKey, provider: provider })
    });
    const data = await res.json();
    removeLoading(loadingId);
    appendAgentResponse(data);
  } catch (err) {
    removeLoading(loadingId);
    appendAgentErrorMessage("Failed to communicate with agent service: " + err.message);
  }
}

function appendUserMessage(text) {
  const history = document.getElementById('chat-history');
  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-msg user';
  msgDiv.innerHTML = `
    <div class="msg-avatar">👤</div>
    <div class="msg-bubble">${escapeHtml(text)}</div>
  `;
  history.appendChild(msgDiv);
  history.scrollTop = history.scrollHeight;
}

function appendAgentLoading(loadingId) {
  const history = document.getElementById('chat-history');
  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-msg agent';
  msgDiv.id = loadingId;
  msgDiv.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-bubble">
      <em>Analyzing query & executing analytical SQL...</em>
    </div>
  `;
  history.appendChild(msgDiv);
  history.scrollTop = history.scrollHeight;
}

function removeLoading(loadingId) {
  const el = document.getElementById(loadingId);
  if (el) el.remove();
}

function appendAgentErrorMessage(text) {
  const history = document.getElementById('chat-history');
  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-msg agent';
  msgDiv.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-bubble" style="border-color: #ef4444;">
      <p style="color: #f87171;">⚠️ ${escapeHtml(text)}</p>
    </div>
  `;
  history.appendChild(msgDiv);
  history.scrollTop = history.scrollHeight;
}

function appendAgentResponse(data) {
  const history = document.getElementById('chat-history');
  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-msg agent';

  // Build KPI chips if present
  let kpisHtml = '';
  if (data.kpis && Object.keys(data.kpis).length > 0) {
    kpisHtml = '<div class="msg-kpis">';
    for (const [k, v] of Object.entries(data.kpis)) {
      kpisHtml += `<div class="kpi-chip"><strong>${escapeHtml(k)}:</strong> ${escapeHtml(String(v))}</div>`;
    }
    kpisHtml += '</div>';
  }

  // Chart Container
  const chartId = 'chat-chart-' + Date.now();
  let chartHtml = '';
  if (data.chart) {
    chartHtml = `
      <div class="msg-chart-box">
        <canvas id="${chartId}"></canvas>
      </div>
    `;
  }

  // SQL Details Accordion
  let sqlHtml = '';
  if (data.sql) {
    sqlHtml = `
      <details class="sql-details-accordion">
        <summary>
          <span>🔍 Executed SQL Query (⚡ ${data.execution_time_ms} ms)</span>
          <span style="font-size:0.7rem; color:#60a5fa;">Click to expand</span>
        </summary>
        <div class="sql-code-block">${escapeHtml(data.sql)}</div>
      </details>
    `;
  }

  // Data Table (if >= 2 rows and not a single roll report card)
  let tableHtml = '';
  if (data.data && data.data.length > 1 && data.data.length <= 15) {
    tableHtml = `
      <details class="sql-details-accordion" style="margin-top: 0.5rem;">
        <summary>
          <span>📋 Tabular Data View (${data.row_count} rows)</span>
          <span style="font-size:0.7rem; color:#60a5fa;">View Records</span>
        </summary>
        <div style="padding: 0.5rem; background:#070d19; overflow-x: auto;">
          ${renderHtmlTable(data.columns, data.data)}
        </div>
      </details>
    `;
  }

  const formattedAnswer = renderMarkdownText(data.answer);

  msgDiv.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-bubble">
      <div>${formattedAnswer}</div>
      ${kpisHtml}
      ${chartHtml}
      ${tableHtml}
      ${sqlHtml}
      <div class="msg-actions">
        <button class="action-chip-btn" onclick="speakText(this)">
          🔊 Listen
        </button>
        ${data.sql ? `<button class="action-chip-btn" onclick="copySql('${encodeURIComponent(data.sql)}')">📋 Copy SQL</button>` : ''}
      </div>
    </div>
  `;

  history.appendChild(msgDiv);
  history.scrollTop = history.scrollHeight;

  // Render chart if present
  if (data.chart) {
    renderChartJs(chartId, data.chart);
  }
}

function renderChartJs(canvasId, spec) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  new Chart(ctx, {
    type: spec.type || 'bar',
    data: {
      labels: spec.labels || [],
      datasets: spec.datasets || []
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: spec.type === 'doughnut' || (spec.datasets && spec.datasets.length > 1),
          labels: { color: '#cbd5e1' }
        },
        title: {
          display: Boolean(spec.title),
          text: spec.title || '',
          color: '#94a3b8',
          font: { size: 13, weight: 'bold' }
        }
      },
      scales: (spec.type === 'bar') ? {
        y: {
          ticks: { color: '#94a3b8' },
          grid: { color: 'rgba(255, 255, 255, 0.08)' }
        },
        x: {
          ticks: { color: '#94a3b8', maxRotation: 45, minRotation: 0 },
          grid: { display: false }
        }
      } : (spec.type === 'radar') ? {
        r: {
          angleLines: { color: 'rgba(255,255,255,0.1)' },
          grid: { color: 'rgba(255,255,255,0.1)' },
          pointLabels: { color: '#93c5fd', font: { size: 11 } },
          ticks: { backdropColor: 'transparent', color: '#94a3b8' },
          suggestedMin: 20,
          suggestedMax: 100
        }
      } : {}
    }
  });
}

function speakText(btn) {
  const bubble = btn.closest('.msg-bubble');
  const text = bubble.innerText.replace(/🔊 Listen|📋 Copy SQL|🔍 Executed SQL[\s\S]*/g, '');
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    window.speechSynthesis.speak(utterance);
    btn.innerHTML = '⏹️ Speaking...';
    utterance.onend = () => { btn.innerHTML = '🔊 Listen'; };
  } else {
    alert("Speech Synthesis is not supported in this browser.");
  }
}

function copySql(encodedSql) {
  const sql = decodeURIComponent(encodedSql);
  navigator.clipboard.writeText(sql).then(() => {
    alert("SQL copied to clipboard!");
  });
}

// -------------------------------------------------------------------
// 3. Analytics Dashboard
// -------------------------------------------------------------------
let dashboardLoaded = false;
async function initDashboard() {
  loadDashboardData();
}

async function loadDashboardData() {
  try {
    const res = await fetch('/api/dashboard/stats');
    const data = await res.json();
    if (!data.success) return;

    // Render KPI Cards
    const overall = data.overall || {};
    document.getElementById('dash-pass-rate').innerText = `${overall.pass_percentage || 0}%`;
    document.getElementById('dash-total-students').innerText = overall.total_students || 0;
    document.getElementById('dash-passed-students').innerText = overall.passed_students || 0;
    document.getElementById('dash-failed-students').innerText = overall.failed_students || 0;
    document.getElementById('dash-avg-sgpa').innerText = `${overall.college_average_sgpa || 0} / 10`;

    // 1. Department Comparison Chart
    renderDeptChart(data.departments || []);

    // 2. Student Classification / Grade Chart
    renderGradeChart(data.grades || []);

    // 3. Subject Pass Rate & Failure Chart
    renderSubjectBarChart(data.subjects || []);

    // 4. Toppers Table
    renderToppersTable(data.toppers || []);

    dashboardLoaded = true;
  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

function renderDeptChart(departments) {
  const ctx = document.getElementById('dash-dept-chart')?.getContext('2d');
  if (!ctx) return;
  if (currentCharts['dash-dept']) currentCharts['dash-dept'].destroy();

  const labels = departments.map(d => `${d.dept_code} (${d.total_students})`);
  const passRates = departments.map(d => d.pass_percentage);
  const avgScores = departments.map(d => d.average_percentage);

  currentCharts['dash-dept'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Pass %',
          data: passRates,
          backgroundColor: '#3b82f6',
          borderRadius: 4
        },
        {
          label: 'Average Score %',
          data: avgScores,
          backgroundColor: '#8b5cf6',
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#cbd5e1' } }
      },
      scales: {
        y: {
          min: 0,
          max: 100,
          ticks: { color: '#94a3b8' },
          grid: { color: 'rgba(255,255,255,0.06)' }
        },
        x: {
          ticks: { color: '#94a3b8' },
          grid: { display: false }
        }
      }
    }
  });
}

function renderGradeChart(grades) {
  const ctx = document.getElementById('dash-grade-chart')?.getContext('2d');
  if (!ctx) return;
  if (currentCharts['dash-grade']) currentCharts['dash-grade'].destroy();

  const labels = grades.map(g => g.result_status);
  const counts = grades.map(g => g.count);

  currentCharts['dash-grade'] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: counts,
        backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ef4444'],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#cbd5e1' } }
      }
    }
  });
}

function renderSubjectBarChart(subjects) {
  const ctx = document.getElementById('dash-subject-chart')?.getContext('2d');
  if (!ctx) return;
  if (currentCharts['dash-subj']) currentCharts['dash-subj'].destroy();

  const labels = subjects.map(s => s.subject_code);
  const passRates = subjects.map(s => s.pass_percentage);
  const failedCounts = subjects.map(s => s.failed_count);

  currentCharts['dash-subj'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Pass %',
          data: passRates,
          backgroundColor: '#10b981',
          borderRadius: 4
        },
        {
          label: 'Failures',
          data: failedCounts,
          backgroundColor: '#ef4444',
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#cbd5e1' } }
      },
      scales: {
        y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.06)' } },
        x: { ticks: { color: '#94a3b8' }, grid: { display: false } }
      }
    }
  });
}

function renderToppersTable(toppers) {
  const tbody = document.getElementById('dash-toppers-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  toppers.forEach((t, i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>#${i + 1}</strong></td>
      <td><code>${t.roll_no}</code></td>
      <td><strong>${t.student_name}</strong></td>
      <td><span class="badge badge-blue">${t.dept_code} (Sem ${t.semester})</span></td>
      <td><strong>${t.percentage}%</strong></td>
      <td><span class="badge badge-green">SGPA ${t.sgpa}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// -------------------------------------------------------------------
// 4. Student Marksheet / Report Card Generator
// -------------------------------------------------------------------
async function initTranscriptTab() {
  document.getElementById('transcript-student-select').addEventListener('change', (e) => {
    const rollNo = e.target.value;
    if (rollNo) loadStudentTranscript(rollNo);
  });

  document.getElementById('print-transcript-btn').addEventListener('click', () => {
    window.print();
  });
}

async function loadStudentListDropdown() {
  if (allStudentsList.length > 0) return;
  try {
    const res = await fetch('/api/students');
    const data = await res.json();
    if (data.success && data.rows) {
      allStudentsList = data.rows;
      const select = document.getElementById('transcript-student-select');
      select.innerHTML = '<option value="">-- Choose Student to View Marksheet --</option>';
      allStudentsList.forEach(s => {
        select.innerHTML += `<option value="${s.roll_no}">${s.roll_no} — ${s.student_name} (${s.dept_code} Sem ${s.semester})</option>`;
      });
      // Load first student by default
      if (allStudentsList.length > 0) {
        select.value = allStudentsList[0].roll_no;
        loadStudentTranscript(allStudentsList[0].roll_no);
      }
    }
  } catch (err) {
    console.error("Failed to load student list:", err);
  }
}

async function loadStudentTranscript(rollNo) {
  try {
    const res = await fetch(`/api/student/${encodeURIComponent(rollNo)}`);
    const data = await res.json();
    if (!data.success) {
      alert(data.error);
      return;
    }

    const s = data.student;
    const marks = data.marks || [];

    // Populate student metadata
    document.getElementById('tr-name').innerText = s.student_name;
    document.getElementById('tr-roll').innerText = s.roll_no;
    document.getElementById('tr-usn').innerText = s.usn;
    document.getElementById('tr-dept').innerText = `${s.dept_name} (${s.dept_code})`;
    document.getElementById('tr-sem').innerText = `Semester ${s.semester} (Section ${s.section})`;
    document.getElementById('tr-batch').innerText = s.batch_year;

    // Populate summary box
    document.getElementById('tr-tot-marks').innerText = `${s.total_marks_obtained} / ${s.total_max_marks}`;
    document.getElementById('tr-percentage').innerText = `${s.percentage}%`;
    document.getElementById('tr-sgpa').innerText = `${s.sgpa} / 10`;
    document.getElementById('tr-status').innerText = s.result_status;

    // Populate marks table
    const tbody = document.getElementById('transcript-marks-tbody');
    tbody.innerHTML = '';
    marks.forEach(m => {
      const isPassed = m.is_passed === 1;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${m.subject_code}</strong></td>
        <td>${m.subject_name}</td>
        <td>${m.credits}</td>
        <td>${m.internal_marks}</td>
        <td>${m.external_marks}</td>
        <td><strong>${m.total_marks}</strong></td>
        <td><strong>${m.grade}</strong></td>
        <td>${m.grade_point}</td>
        <td>
          <span style="font-weight: 700; color: ${isPassed ? '#10b981' : '#ef4444'};">
            ${isPassed ? 'PASS' : 'FAIL'}
          </span>
        </td>
      `;
      tbody.appendChild(tr);
    });

  } catch (err) {
    console.error("Failed to fetch student details:", err);
  }
}

// -------------------------------------------------------------------
// 5. Subject Deep Dive & Backlogs Tab
// -------------------------------------------------------------------
function initSubjectTab() {
  document.getElementById('subj-select').addEventListener('change', (e) => {
    const subCode = e.target.value;
    if (subCode) loadSubjectDetails(subCode);
  });
}

async function loadSubjectDropdown() {
  if (allSubjectsList.length > 0) return;
  try {
    const res = await fetch('/api/dashboard/stats');
    const data = await res.json();
    if (data.subjects) {
      allSubjectsList = data.subjects;
      const select = document.getElementById('subj-select');
      select.innerHTML = '<option value="">-- Select Subject to Analyze --</option>';
      allSubjectsList.forEach(s => {
        select.innerHTML += `<option value="${s.subject_code}">${s.subject_code} — ${s.subject_name} (${s.dept_code} Sem ${s.semester})</option>`;
      });
      if (allSubjectsList.length > 0) {
        select.value = allSubjectsList[0].subject_code;
        loadSubjectDetails(allSubjectsList[0].subject_code);
      }
    }
  } catch (err) {
    console.error("Subject load error:", err);
  }
}

async function loadSubjectDetails(subjectCode) {
  const subj = allSubjectsList.find(s => s.subject_code === subjectCode);
  if (!subj) return;

  document.getElementById('subj-name-title').innerText = `${subj.subject_name} (${subj.subject_code})`;
  document.getElementById('subj-pass-rate').innerText = `${subj.pass_percentage}%`;
  document.getElementById('subj-enrolled').innerText = subj.total_appeared;
  document.getElementById('subj-avg-marks').innerText = `${subj.average_marks} / 100`;
  document.getElementById('subj-high-marks').innerText = `${subj.highest_marks} / 100`;
  document.getElementById('subj-low-marks').innerText = `${subj.lowest_marks} / 100`;

  // Fetch failing students for this subject
  try {
    const res = await fetch('/api/sql/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sql: `SELECT s.roll_no, s.name as student_name, s.gender, s.section, m.internal_marks, m.external_marks, m.total_marks, m.grade 
              FROM marks m 
              JOIN students s ON m.student_id = s.student_id 
              JOIN subjects sub ON m.subject_id = sub.subject_id 
              WHERE sub.subject_code = '${subjectCode}' AND m.is_passed = 0 
              ORDER BY m.total_marks ASC`
      })
    });
    const data = await res.json();
    const tbody = document.getElementById('subj-failed-tbody');
    tbody.innerHTML = '';
    if (data.rows && data.rows.length > 0) {
      data.rows.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><code>${r.roll_no}</code></td>
          <td><strong>${r.student_name}</strong></td>
          <td>Sec ${r.section}</td>
          <td>${r.internal_marks}</td>
          <td>${r.external_marks}</td>
          <td><strong style="color: #ef4444;">${r.total_marks}</strong></td>
          <td><span class="badge badge-red">${r.grade}</span></td>
        `;
        tbody.appendChild(tr);
      });
      document.getElementById('subj-failed-count-badge').innerText = `${data.rows.length} Backlog Students`;
    } else {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #10b981; padding: 1.5rem;">🎉 Zero failures! All enrolled students cleared this subject.</td></tr>`;
      document.getElementById('subj-failed-count-badge').innerText = '0 Failures';
    }
  } catch (err) {
    console.error("Backlog load error:", err);
  }
}

// -------------------------------------------------------------------
// 6. SQL Studio
// -------------------------------------------------------------------
function initSqlStudio() {
  const btn = document.getElementById('btn-run-sql');
  const textarea = document.getElementById('sql-editor-textarea');
  const sampleSelect = document.getElementById('sql-sample-select');

  btn.addEventListener('click', runSqlStudioQuery);

  sampleSelect.addEventListener('change', (e) => {
    const val = e.target.value;
    if (val) textarea.value = val;
  });

  document.getElementById('btn-download-sql-csv').addEventListener('click', downloadSqlCsv);
}

let lastSqlResult = null;
async function runSqlStudioQuery() {
  const textarea = document.getElementById('sql-editor-textarea');
  const sql = textarea.value.trim();
  if (!sql) return;

  const resultContainer = document.getElementById('sql-result-container');
  resultContainer.innerHTML = '<p style="color: #94a3b8; padding: 1rem;">Executing query...</p>';

  try {
    const res = await fetch('/api/sql/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql })
    });
    const data = await res.json();
    lastSqlResult = data;

    if (!data.success) {
      resultContainer.innerHTML = `
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; padding: 1rem; border-radius: 8px; color: #f87171;">
          <strong>SQL Execution Error:</strong> ${escapeHtml(data.error)}
        </div>
      `;
      return;
    }

    document.getElementById('sql-meta-info').innerText = `Returned ${data.row_count} rows in ${data.execution_time_ms} ms`;
    resultContainer.innerHTML = renderHtmlTable(data.columns, data.rows);
  } catch (err) {
    resultContainer.innerHTML = `<p style="color: #ef4444;">Network error: ${err.message}</p>`;
  }
}

function downloadSqlCsv() {
  if (!lastSqlResult || !lastSqlResult.rows || lastSqlResult.rows.length === 0) {
    alert("No query results to export.");
    return;
  }
  const cols = lastSqlResult.columns;
  const rows = lastSqlResult.rows;

  let csvContent = "data:text/csv;charset=utf-8," + cols.join(",") + "\n";
  rows.forEach(r => {
    const line = cols.map(c => `"${String(r[c] ?? '').replace(/"/g, '""')}"`).join(",");
    csvContent += line + "\n";
  });

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `sql_query_result_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

async function loadSchemaTree() {
  const container = document.getElementById('schema-tree-container');
  try {
    const res = await fetch('/api/schema');
    const data = await res.json();
    if (!data.success) return;

    let html = '';
    for (const [name, entity] of Object.entries(data.schema)) {
      const isView = entity.type === 'view';
      const badge = isView ? '👁️ VIEW' : '🗄️ TABLE';
      html += `
        <div class="schema-entity-item">
          <div class="schema-entity-header" onclick="pasteTableToEditor('${name}')">
            <span>${badge}</span>
            <span><strong>${name}</strong></span>
          </div>
          <ul class="schema-columns-list">
            ${entity.columns.map(c => `<li>${c.name} <span style="opacity:0.6;">(${c.type || 'ANY'})</span>${c.pk ? ' 🔑' : ''}</li>`).join('')}
          </ul>
        </div>
      `;
    }
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<p style="color: #ef4444;">Failed to load schema: ${err.message}</p>`;
  }
}

function pasteTableToEditor(tableName) {
  const textarea = document.getElementById('sql-editor-textarea');
  textarea.value = `SELECT * FROM ${tableName} LIMIT 25;`;
  runSqlStudioQuery();
}

// -------------------------------------------------------------------
// 7. Settings Modal
// -------------------------------------------------------------------
function initSettingsModal() {
  const modal = document.getElementById('settings-modal');
  const openBtn = document.getElementById('btn-open-settings');
  const closeBtn = document.getElementById('btn-close-settings');
  const saveBtn = document.getElementById('btn-save-settings');

  const keyInput = document.getElementById('setting-api-key');
  const providerSelect = document.getElementById('setting-provider');

  openBtn.addEventListener('click', () => {
    keyInput.value = localStorage.getItem('college_agent_api_key') || '';
    providerSelect.value = localStorage.getItem('college_agent_provider') || 'gemini';
    modal.classList.add('active');
  });

  closeBtn.addEventListener('click', () => {
    modal.classList.remove('active');
  });

  saveBtn.addEventListener('click', () => {
    const k = keyInput.value.trim();
    const p = providerSelect.value;
    if (k) {
      localStorage.setItem('college_agent_api_key', k);
      localStorage.setItem('college_agent_provider', p);
    } else {
      localStorage.removeItem('college_agent_api_key');
      localStorage.removeItem('college_agent_provider');
    }
    modal.classList.remove('active');
    alert("Agent settings updated successfully!");
  });
}

// -------------------------------------------------------------------
// Utilities
// -------------------------------------------------------------------
function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function renderMarkdownText(md) {
  if (!md) return '';
  let html = escapeHtml(md);

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.08); padding:0.15rem 0.35rem; border-radius:4px; font-family:monospace; color:#38bdf8;">$1</code>');
  // Line breaks
  html = html.replace(/\n\n/g, '<br><br>');
  html = html.replace(/\n- /g, '<br>• ');
  html = html.replace(/\n/g, '<br>');

  return html;
}

function renderHtmlTable(columns, rows) {
  if (!rows || rows.length === 0) return '<p style="color: #94a3b8;">No data records.</p>';
  let table = '<table class="data-table"><thead><tr>';
  columns.forEach(c => {
    table += `<th>${escapeHtml(c)}</th>`;
  });
  table += '</tr></thead><tbody>';
  rows.forEach(r => {
    table += '<tr>';
    columns.forEach(c => {
      let val = r[c] ?? '';
      if (typeof val === 'number') val = Number.isInteger(val) ? val : val.toFixed(2);
      table += `<td>${escapeHtml(String(val))}</td>`;
    });
    table += '</tr>';
  });
  table += '</tbody></table>';
  return table;
}
