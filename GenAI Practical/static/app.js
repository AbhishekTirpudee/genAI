/* ==========================================================================
   WINE ENSEMBLE ML PRACTICAL - INTERACTIVE JAVASCRIPT ENGINE
   Controls dynamic training, Plotly visualization rendering, live predictions,
   dataset explorer, and boundary contour computations.
   ========================================================================== */

// Global State
const state = {
  datasetInfo: null,
  trainResults: null,
  boundaryData: null,
  isTraining: false,
  presetIndex: 0
};

// Wine Feature Metadata (Realistic ranges and defaults from Wine Dataset)
const FEATURE_META = {
  alcohol: { min: 11.0, max: 15.0, step: 0.1, default: 13.0, unit: "vol %", label: "Alcohol" },
  malic_acid: { min: 0.7, max: 6.0, step: 0.1, default: 2.3, unit: "g/L", label: "Malic Acid" },
  ash: { min: 1.3, max: 3.3, step: 0.05, default: 2.36, unit: "g/L", label: "Ash" },
  alcalinity_of_ash: { min: 10.0, max: 30.0, step: 0.5, default: 19.5, unit: "meq/L", label: "Alcalinity of Ash" },
  magnesium: { min: 70.0, max: 165.0, step: 1.0, default: 99.7, unit: "mg/L", label: "Magnesium" },
  total_phenols: { min: 0.9, max: 3.9, step: 0.05, default: 2.3, unit: "g/L", label: "Total Phenols" },
  flavanoids: { min: 0.3, max: 5.1, step: 0.05, default: 2.0, unit: "g/L", label: "Flavanoids" },
  nonflavanoid_phenols: { min: 0.1, max: 0.7, step: 0.02, default: 0.36, unit: "g/L", label: "Non-flavanoid Phenols" },
  proanthocyanins: { min: 0.4, max: 3.6, step: 0.05, default: 1.6, unit: "g/L", label: "Proanthocyanins" },
  color_intensity: { min: 1.2, max: 13.0, step: 0.1, default: 5.0, unit: "A420/520", label: "Color Intensity" },
  hue: { min: 0.4, max: 1.8, step: 0.02, default: 0.95, unit: "ratio", label: "Hue" },
  "od280/od315_of_diluted_wines": { min: 1.2, max: 4.0, step: 0.05, default: 2.6, unit: "ratio", label: "OD280/OD315" },
  proline: { min: 270.0, max: 1700.0, step: 10.0, default: 746.0, unit: "mg/L", label: "Proline" }
};

// Preset Profiles for 3 Cultivars
const PRESET_CULTIVARS = [
  {
    name: "Barolo (Class 0)",
    features: [14.23, 1.71, 2.43, 15.6, 127.0, 2.80, 3.06, 0.28, 2.29, 5.64, 1.04, 3.92, 1065.0]
  },
  {
    name: "Grignolino (Class 1)",
    features: [12.37, 0.94, 1.36, 10.6, 88.0, 1.98, 0.57, 0.28, 0.42, 1.95, 1.05, 1.82, 520.0]
  },
  {
    name: "Barbera (Class 2)",
    features: [13.17, 2.59, 2.37, 20.0, 120.0, 1.65, 0.68, 0.53, 1.46, 9.30, 0.60, 1.62, 840.0]
  }
];

// Dark Theme Plotly Template
const PLOT_THEME = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { family: 'Inter, sans-serif', color: '#94a3b8' },
  margin: { l: 50, r: 25, t: 35, b: 45 },
  xaxis: {
    gridcolor: 'rgba(255, 255, 255, 0.06)',
    zerolinecolor: 'rgba(255, 255, 255, 0.1)'
  },
  yaxis: {
    gridcolor: 'rgba(255, 255, 255, 0.06)',
    zerolinecolor: 'rgba(255, 255, 255, 0.1)'
  }
};

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
  setupTabs();
  setupSliders();
  setupEventListeners();
  setupVivaAccordion();

  // Load Initial Dataset Info
  await fetchDatasetInfo();

  // Build Live Predictor Sliders
  renderPredictorSliders();

  // Run initial training benchmark
  await runBenchmark();

  // Render initial decision boundary
  await renderDecisionBoundary();
});

// Setup Navigation Tabs
function setupTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");
      tabButtons.forEach(b => b.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add("active");

      // Trigger Plotly relayout on tab switch to fix sizing
      window.dispatchEvent(new Event('resize'));
    });
  });
}

// Setup Sliders & Dynamic Text Updates
function setupSliders() {
  const sync = (id, targetId, formatFn) => {
    const el = document.getElementById(id);
    const target = document.getElementById(targetId);
    if (el && target) {
      el.addEventListener("input", () => {
        target.textContent = formatFn(el.value);
      });
    }
  };

  sync("sliderTestSize", "valTestSize", v => `${v} (${Math.round(v * 100)}%)`);
  sync("sliderCvFolds", "valCvFolds", v => `${v} Folds`);
  sync("sliderTreeDepth", "valTreeDepth", v => v == 0 ? "None (Full Depth)" : v);
  sync("sliderTreeMinSamples", "valTreeMinSamples", v => v);
  sync("sliderBagEstimators", "valBagEstimators", v => v);
  sync("sliderBagSamples", "valBagSamples", v => v);
  sync("sliderAdaEstimators", "valAdaEstimators", v => v);
  sync("sliderAdaLr", "valAdaLr", v => parseFloat(v).toFixed(1));
  sync("sliderAdaDepth", "valAdaDepth", v => v);

  // Voting weights sync
  const updateVotingWeights = () => {
    const wTree = document.getElementById("weightTree").value;
    const wBag = document.getElementById("weightBag").value;
    const wAda = document.getElementById("weightAda").value;
    document.getElementById("valVotingWeights").textContent = `${wTree} : ${wBag} : ${wAda}`;
  };
  ["weightTree", "weightBag", "weightAda"].forEach(id => {
    document.getElementById(id).addEventListener("input", updateVotingWeights);
  });
}

// Setup Event Listeners
function setupEventListeners() {
  document.getElementById("btnTrainHeader").addEventListener("click", runBenchmark);
  document.getElementById("btnTrainSidebar").addEventListener("click", runBenchmark);
  document.getElementById("btnRecomputeBoundary").addEventListener("click", renderDecisionBoundary);
  document.getElementById("btnPredictPreset").addEventListener("click", cyclePreset);
  document.getElementById("btnPrintReport").addEventListener("click", () => window.print());

  // Reset defaults button
  document.getElementById("btnResetDefaults").addEventListener("click", () => {
    document.getElementById("sliderTestSize").value = 0.25;
    document.getElementById("valTestSize").textContent = "0.25 (25%)";
    document.getElementById("selectScaler").value = "standard";
    document.getElementById("sliderCvFolds").value = 5;
    document.getElementById("valCvFolds").textContent = "5 Folds";
    document.getElementById("selectTreeCriterion").value = "gini";
    document.getElementById("sliderTreeDepth").value = 0;
    document.getElementById("valTreeDepth").textContent = "None (Full Depth)";
    document.getElementById("sliderBagEstimators").value = 50;
    document.getElementById("valBagEstimators").textContent = "50";
    document.getElementById("sliderAdaEstimators").value = 50;
    document.getElementById("valAdaEstimators").textContent = "50";
    document.getElementById("sliderAdaLr").value = 1.0;
    document.getElementById("valAdaLr").textContent = "1.0";
    document.getElementById("selectVotingType").value = "soft";
    document.getElementById("weightTree").value = 1;
    document.getElementById("weightBag").value = 2;
    document.getElementById("weightAda").value = 2;
    document.getElementById("valVotingWeights").textContent = "1 : 2 : 2";
    showToast("Reset hyperparameters to standard baseline.", "info");
  });
}

// Setup Viva Voce Accordion
function setupVivaAccordion() {
  document.querySelectorAll(".viva-item").forEach(item => {
    const q = item.querySelector(".viva-question");
    q.addEventListener("click", () => {
      item.classList.toggle("open");
    });
  });
}

// Fetch Dataset Meta & Preview
async function fetchDatasetInfo() {
  try {
    const res = await fetch("/api/dataset-info");
    const data = await res.json();
    state.datasetInfo = data;

    // Populate dataset stats row
    const statsRow = document.getElementById("datasetStatsRow");
    statsRow.innerHTML = `
      <div class="meta-card">
        <div class="meta-card-num">${data.total_samples}</div>
        <div class="meta-card-lbl">Total Samples</div>
      </div>
      <div class="meta-card">
        <div class="meta-card-num">${data.feature_names.length}</div>
        <div class="meta-card-lbl">Chemical Features</div>
      </div>
      <div class="meta-card">
        <div class="meta-card-num">${Object.keys(data.class_counts).length}</div>
        <div class="meta-card-lbl">Wine Cultivars</div>
      </div>
      <div class="meta-card">
        <div class="meta-card-num">${data.class_counts['Class_0 (Barolo)'] || 59}</div>
        <div class="meta-card-lbl">Class 0 (Barolo)</div>
      </div>
      <div class="meta-card">
        <div class="meta-card-num">${data.class_counts['Class_1 (Grignolino)'] || 71}</div>
        <div class="meta-card-lbl">Class 1 (Grignolino)</div>
      </div>
      <div class="meta-card">
        <div class="meta-card-num">${data.class_counts['Class_2 (Barbera)'] || 48}</div>
        <div class="meta-card-lbl">Class 2 (Barbera)</div>
      </div>
    `;

    // Populate dataset table
    renderDatasetTable(data.preview, data.feature_names);

    // Populate boundary dropdowns
    populateBoundaryDropdowns(data.feature_names);

    // Render correlation heatmap
    renderCorrelationHeatmap(data.correlation, data.feature_names);

  } catch (err) {
    console.error("Failed to fetch dataset info:", err);
  }
}

// Render Dataset Preview Table
function renderDatasetTable(records, featureNames) {
  const thead = document.getElementById("theadDataset");
  const tbody = document.getElementById("tbodyDataset");

  const cols = ["target_name", ...featureNames];
  thead.innerHTML = `<tr>${cols.map(c => `<th>${c.replace(/_/g, ' ')}</th>`).join('')}</tr>`;

  tbody.innerHTML = records.map(r => `
    <tr>
      <td><strong>${r.target_name}</strong></td>
      ${featureNames.map(f => `<td>${typeof r[f] === 'number' ? r[f].toFixed(2) : r[f]}</td>`).join('')}
    </tr>
  `).join('');
}

// Populate 2D Boundary Feature Selectors
function populateBoundaryDropdowns(features) {
  const selX = document.getElementById("selectBoundaryFeatureX");
  const selY = document.getElementById("selectBoundaryFeatureY");

  features.forEach(f => {
    const optX = document.createElement("option");
    optX.value = f;
    optX.textContent = f.replace(/_/g, ' ');
    if (f === "flavanoids") optX.selected = false;
    selX.appendChild(optX);

    const optY = document.createElement("option");
    optY.value = f;
    optY.textContent = f.replace(/_/g, ' ');
    if (f === "color_intensity") optY.selected = false;
    selY.appendChild(optY);
  });
}

// Main Training Benchmark Call
async function runBenchmark() {
  if (state.isTraining) return;
  state.isTraining = true;
  setTrainButtonLoading(true);

  const depthVal = parseInt(document.getElementById("sliderTreeDepth").value);
  const config = {
    test_size: parseFloat(document.getElementById("sliderTestSize").value),
    random_state: 42,
    scaler_type: document.getElementById("selectScaler").value,
    cv_folds: parseInt(document.getElementById("sliderCvFolds").value),
    dt_criterion: document.getElementById("selectTreeCriterion").value,
    dt_max_depth: depthVal === 0 ? null : depthVal,
    dt_min_samples_split: parseInt(document.getElementById("sliderTreeMinSamples").value),
    bag_n_estimators: parseInt(document.getElementById("sliderBagEstimators").value),
    bag_bootstrap: document.getElementById("chkBagBootstrap").checked,
    bag_max_samples: parseFloat(document.getElementById("sliderBagSamples").value),
    ada_n_estimators: parseInt(document.getElementById("sliderAdaEstimators").value),
    ada_learning_rate: parseFloat(document.getElementById("sliderAdaLr").value),
    ada_base_max_depth: parseInt(document.getElementById("sliderAdaDepth").value),
    voting_type: document.getElementById("selectVotingType").value,
    weight_tree: parseFloat(document.getElementById("weightTree").value),
    weight_bagging: parseFloat(document.getElementById("weightBag").value),
    weight_adaboost: parseFloat(document.getElementById("weightAda").value)
  };

  try {
    const res = await fetch("/api/train", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config)
    });
    const data = await res.json();
    state.trainResults = data.results;

    // Render all visual components
    renderLeaderboardCards(data.results);
    renderMetricsBarChart(data.results);
    renderRadarChart(data.results);
    renderOverfitChart(data.results);
    renderRocCurves(data.results);
    renderBenchmarkTable(data.results);
    renderConfusionMatrices(data.results);
    renderFeatureImportanceChart(data.results);

    showToast("Model benchmark completed successfully!", "success");
  } catch (err) {
    console.error("Training error:", err);
    showToast("Error running benchmark: " + err.message, "error");
  } finally {
    state.isTraining = false;
    setTrainButtonLoading(false);
  }
}

// Render Leaderboard Metric Cards
function renderLeaderboardCards(results) {
  const container = document.getElementById("leaderboardCards");
  const models = Object.values(results);
  
  // Sort by Test Acc then CV Mean
  const sorted = [...models].sort((a, b) => (b.test_acc + b.cv_mean) - (a.test_acc + a.cv_mean));
  const bestModelName = sorted[0].name;

  const colorMap = {
    "Single Decision Tree": { accent: "#f43f5e", icon: "fa-tree" },
    "Bagging Classifier": { accent: "#38bdf8", icon: "fa-cubes" },
    "AdaBoost Classifier": { accent: "#c084fc", icon: "fa-bolt-lightning" },
    "Voting Classifier": { accent: "#34d399", icon: "fa-check-to-slot" }
  };

  container.innerHTML = models.map((m, idx) => {
    const isBest = m.name === bestModelName;
    const styleObj = colorMap[m.name] || { accent: "#38bdf8", icon: "fa-brain" };

    return `
      <div class="model-card ${isBest ? 'featured' : ''}" style="--card-accent: ${styleObj.accent}">
        <div class="card-top">
          <h4><i class="fa-solid ${styleObj.icon}" style="color: ${styleObj.accent}; margin-right: 6px;"></i>${m.name}</h4>
          <span class="rank-badge ${isBest ? 'rank-1' : ''}">${isBest ? 'TOP PERFORMER' : `Rank #${idx + 1}`}</span>
        </div>

        <div class="card-main-metric">
          <div class="metric-number">${(m.test_acc * 100).toFixed(1)}%</div>
          <div class="metric-label">Test Set Accuracy</div>
        </div>

        <div class="card-sub-metrics">
          <div class="sub-metric">
            <span>CV Mean</span>
            <strong>${(m.cv_mean * 100).toFixed(1)}% &plusmn; ${(m.cv_std * 100).toFixed(1)}%</strong>
          </div>
          <div class="sub-metric">
            <span>Macro F1</span>
            <strong>${m.f1_macro.toFixed(3)}</strong>
          </div>
          <div class="sub-metric">
            <span>Overfit Gap</span>
            <strong style="color: ${m.overfit_gap > 0.03 ? '#fbbf24' : '#34d399'}">${(m.overfit_gap * 100).toFixed(1)}%</strong>
          </div>
          <div class="sub-metric">
            <span>Fit Latency</span>
            <strong>${m.train_time_ms} ms</strong>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// Render Grouped Bar Chart
function renderMetricsBarChart(results) {
  const models = Object.values(results);
  const names = models.map(m => m.name.replace(" Classifier", ""));

  const traceTest = {
    x: names,
    y: models.map(m => m.test_acc),
    name: 'Test Accuracy',
    type: 'bar',
    marker: { color: '#38bdf8' }
  };

  const traceCV = {
    x: names,
    y: models.map(m => m.cv_mean),
    name: 'CV Mean',
    type: 'bar',
    error_y: {
      type: 'data',
      array: models.map(m => m.cv_std),
      visible: true,
      color: '#cbd5e1'
    },
    marker: { color: '#34d399' }
  };

  const traceF1 = {
    x: names,
    y: models.map(m => m.f1_macro),
    name: 'Macro F1',
    type: 'bar',
    marker: { color: '#c084fc' }
  };

  const layout = {
    ...PLOT_THEME,
    barmode: 'group',
    yaxis: { ...PLOT_THEME.yaxis, range: [0.75, 1.02], title: 'Score (0 - 1.0)' },
    legend: { orientation: 'h', y: 1.15, x: 0 }
  };

  Plotly.newPlot('chartMetricsBar', [traceTest, traceCV, traceF1], layout, { responsive: true, displayModeBar: false });
}

// Render Radar Chart
function renderRadarChart(results) {
  const models = Object.values(results);
  const categories = ['Test Acc', 'CV Consistency', 'Macro Precision', 'Macro Recall', 'F1-Score'];

  const colors = ['#f43f5e', '#38bdf8', '#c084fc', '#34d399'];

  const data = models.map((m, i) => {
    const cvConsistency = Math.max(0, 1 - (m.cv_std * 3));
    return {
      type: 'scatterpolar',
      r: [m.test_acc, cvConsistency, m.precision_macro, m.recall_macro, m.f1_macro, m.test_acc],
      theta: [...categories, categories[0]],
      fill: 'toself',
      name: m.name.replace(" Classifier", ""),
      line: { color: colors[i] },
      opacity: 0.7
    };
  });

  const layout = {
    ...PLOT_THEME,
    polar: {
      radialaxis: { visible: true, range: [0.7, 1.0], gridcolor: 'rgba(255,255,255,0.08)' },
      angularaxis: { gridcolor: 'rgba(255,255,255,0.08)' },
      bgcolor: 'transparent'
    },
    legend: { orientation: 'h', y: -0.15, x: 0 },
    margin: { l: 30, r: 30, t: 20, b: 40 }
  };

  Plotly.newPlot('chartRadar', data, layout, { responsive: true, displayModeBar: false });
}

// Render Overfitting Gap Analysis Chart
function renderOverfitChart(results) {
  const models = Object.values(results);
  const names = models.map(m => m.name.replace(" Classifier", ""));

  const traceTrain = {
    x: names,
    y: models.map(m => m.train_acc),
    name: 'Train Accuracy',
    type: 'bar',
    marker: { color: '#818cf8' }
  };

  const traceTest = {
    x: names,
    y: models.map(m => m.test_acc),
    name: 'Test Accuracy',
    type: 'bar',
    marker: { color: '#38bdf8' }
  };

  const traceGap = {
    x: names,
    y: models.map(m => m.overfit_gap),
    name: 'Overfit Gap (Delta)',
    type: 'scatter',
    mode: 'lines+markers',
    yaxis: 'y2',
    line: { color: '#fbbf24', width: 3 },
    marker: { size: 9, color: '#fbbf24' }
  };

  const layout = {
    ...PLOT_THEME,
    barmode: 'group',
    yaxis: { ...PLOT_THEME.yaxis, range: [0.85, 1.02], title: 'Accuracy' },
    yaxis2: {
      title: 'Overfit Gap',
      overlaying: 'y',
      side: 'right',
      range: [-0.02, 0.15],
      gridcolor: 'transparent',
      font: { color: '#fbbf24' }
    },
    legend: { orientation: 'h', y: 1.15, x: 0 }
  };

  Plotly.newPlot('chartOverfit', [traceTrain, traceTest, traceGap], layout, { responsive: true, displayModeBar: false });
}

// Render Multiclass ROC Curves
function renderRocCurves(results) {
  const traces = [];
  const colors = ['#f43f5e', '#38bdf8', '#c084fc', '#34d399'];

  // Plot Class 0 ROC for all 4 models
  Object.values(results).forEach((m, idx) => {
    if (m.roc_curves && m.roc_curves.length > 0) {
      const c0 = m.roc_curves[0];
      traces.push({
        x: c0.fpr,
        y: c0.tpr,
        mode: 'lines',
        name: `${m.name.split(' ')[0]} (AUC: ${m.roc_auc || 1.0})`,
        line: { color: colors[idx], width: 2.5 }
      });
    }
  });

  // Reference diagonal line
  traces.push({
    x: [0, 1],
    y: [0, 1],
    mode: 'lines',
    name: 'Chance (0.50)',
    line: { dash: 'dash', color: 'rgba(255,255,255,0.2)' }
  });

  const layout = {
    ...PLOT_THEME,
    xaxis: { ...PLOT_THEME.xaxis, title: 'False Positive Rate' },
    yaxis: { ...PLOT_THEME.yaxis, title: 'True Positive Rate' },
    legend: { orientation: 'h', y: -0.2, x: 0 }
  };

  Plotly.newPlot('chartRoc', traces, layout, { responsive: true, displayModeBar: false });
}

// Render Benchmark Detailed Table
function renderBenchmarkTable(results) {
  const tbody = document.getElementById("tbodyBenchmark");
  tbody.innerHTML = Object.values(results).map(m => `
    <tr>
      <td><strong>${m.name}</strong></td>
      <td>${m.train_acc.toFixed(4)}</td>
      <td><strong>${m.test_acc.toFixed(4)}</strong></td>
      <td style="color: ${m.overfit_gap > 0.03 ? '#fbbf24' : '#34d399'}">${m.overfit_gap.toFixed(4)}</td>
      <td>${m.precision_macro.toFixed(4)}</td>
      <td>${m.recall_macro.toFixed(4)}</td>
      <td><strong>${m.f1_macro.toFixed(4)}</strong></td>
      <td>${m.cv_mean.toFixed(4)} &plusmn; ${m.cv_std.toFixed(4)}</td>
      <td>${m.roc_auc !== null ? m.roc_auc.toFixed(4) : 'N/A (Hard)'}</td>
      <td>${m.train_time_ms} ms</td>
    </tr>
  `).join('');
}

// Render Confusion Matrices Heatmaps
function renderConfusionMatrices(results) {
  const models = Object.values(results);
  const domIds = {
    "Single Decision Tree": { chart: "cmChartTree", badge: "cmBadgeTree" },
    "Bagging Classifier": { chart: "cmChartBag", badge: "cmBadgeBag" },
    "AdaBoost Classifier": { chart: "cmChartAda", badge: "cmBadgeAda" },
    "Voting Classifier": { chart: "cmChartVote", badge: "cmBadgeVote" }
  };

  const classLabels = ['Barolo', 'Grignolino', 'Barbera'];

  models.forEach(m => {
    const config = domIds[m.name];
    if (!config) return;

    document.getElementById(config.badge).textContent = `Acc: ${(m.test_acc * 100).toFixed(1)}%`;

    const cm = m.confusion_matrix;
    const annotations = [];
    for (let i = 0; i < 3; i++) {
      for (let j = 0; j < 3; j++) {
        annotations.push({
          x: classLabels[j],
          y: classLabels[i],
          text: String(cm[i][j]),
          font: { color: cm[i][j] > 8 ? '#0f172a' : '#f8fafc', size: 14, weight: 'bold' },
          showarrow: false
        });
      }
    }

    const data = [{
      z: cm,
      x: classLabels,
      y: classLabels,
      type: 'heatmap',
      colorscale: [
        [0, 'rgba(15, 23, 42, 0.9)'],
        [0.5, 'rgba(56, 189, 248, 0.6)'],
        [1, '#38bdf8']
      ],
      showscale: false
    }];

    const layout = {
      ...PLOT_THEME,
      margin: { l: 65, r: 25, t: 20, b: 45 },
      annotations: annotations,
      xaxis: { title: 'Predicted Cultivar', ...PLOT_THEME.xaxis },
      yaxis: { title: 'Actual Cultivar', ...PLOT_THEME.yaxis, autorange: 'reversed' }
    };

    Plotly.newPlot(config.chart, data, layout, { responsive: true, displayModeBar: false });
  });

  // Observations Text
  const treeAcc = results["Single Decision Tree"].test_acc;
  const bagAcc = results["Bagging Classifier"].test_acc;
  const adaAcc = results["AdaBoost Classifier"].test_acc;
  const voteAcc = results["Voting Classifier"].test_acc;

  document.getElementById("cmInsightsText").innerHTML = `
    <strong>Practical Takeaway:</strong> The Single Decision Tree achieves ${(treeAcc*100).toFixed(1)}% test accuracy.
    Ensemble methods like <strong>Bagging (${(bagAcc*100).toFixed(1)}%)</strong> and <strong>Voting Classifier (${(voteAcc*100).toFixed(1)}%)</strong>
    consistently eliminate off-diagonal misclassification errors, especially between Class 1 (Grignolino) and Class 2 (Barbera) which share subtle phenolic profiles.
  `;
}

// Render Feature Importance Chart
function renderFeatureImportanceChart(results) {
  const treeImp = results["Single Decision Tree"].feature_importances;
  const bagImp = results["Bagging Classifier"].feature_importances;
  const adaImp = results["AdaBoost Classifier"].feature_importances;

  if (!treeImp || !state.datasetInfo) return;

  const features = state.datasetInfo.feature_names.map(f => f.replace(/_/g, ' '));

  const traceTree = {
    y: features,
    x: treeImp,
    name: 'Decision Tree',
    type: 'bar',
    orientation: 'h',
    marker: { color: '#f43f5e' }
  };

  const traceBag = {
    y: features,
    x: bagImp,
    name: 'Bagging (Ensemble Avg)',
    type: 'bar',
    orientation: 'h',
    marker: { color: '#38bdf8' }
  };

  const traceAda = {
    y: features,
    x: adaImp,
    name: 'AdaBoost',
    type: 'bar',
    orientation: 'h',
    marker: { color: '#c084fc' }
  };

  const layout = {
    ...PLOT_THEME,
    barmode: 'group',
    xaxis: { ...PLOT_THEME.xaxis, title: 'Relative Importance Score' },
    margin: { l: 150, r: 25, t: 20, b: 45 },
    legend: { orientation: 'h', y: 1.05, x: 0 }
  };

  Plotly.newPlot('chartFeatureImportance', [traceTree, traceBag, traceAda], layout, { responsive: true, displayModeBar: false });
}

// Render 2D Decision Boundaries
async function renderDecisionBoundary() {
  const selX = document.getElementById("selectBoundaryFeatureX").value;
  const selY = document.getElementById("selectBoundaryFeatureY").value;
  const depthVal = parseInt(document.getElementById("sliderTreeDepth").value);

  const req = {
    feature_x: selX,
    feature_y: selY,
    dt_max_depth: depthVal === 0 ? null : depthVal,
    bag_n_estimators: parseInt(document.getElementById("sliderBagEstimators").value),
    ada_n_estimators: parseInt(document.getElementById("sliderAdaEstimators").value),
    voting_type: document.getElementById("selectVotingType").value,
    resolution: 65
  };

  try {
    const res = await fetch("/api/decision-boundary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req)
    });
    const data = await res.json();
    state.boundaryData = data;

    const domConfigs = [
      { name: "Single Decision Tree", domId: "chartBoundaryTree" },
      { name: "Bagging Classifier", domId: "chartBoundaryBag" },
      { name: "AdaBoost Classifier", domId: "chartBoundaryAda" },
      { name: "Voting Classifier", domId: "chartBoundaryVote" }
    ];

    const classColors = ['#38bdf8', '#34d399', '#f43f5e'];

    domConfigs.forEach(cfg => {
      const surfaceZ = data.surfaces[cfg.name];
      if (!surfaceZ) return;

      // Decision surface contour
      const contourTrace = {
        x: data.grid_x,
        y: data.grid_y,
        z: surfaceZ,
        type: 'contour',
        colorscale: [
          [0, 'rgba(56, 189, 248, 0.25)'],
          [0.5, 'rgba(52, 211, 153, 0.25)'],
          [1, 'rgba(244, 63, 94, 0.25)']
        ],
        showscale: false,
        contours: { coloring: 'fill', showlines: false }
      };

      // Scatter points
      const scatterTraces = [0, 1, 2].map(cIdx => {
        const pts = data.points.filter(p => p.label === cIdx);
        return {
          x: pts.map(p => p.x),
          y: pts.map(p => p.y),
          mode: 'markers',
          type: 'scatter',
          name: `Class ${cIdx}`,
          marker: {
            color: classColors[cIdx],
            size: 6,
            line: { color: '#ffffff', width: 0.8 }
          }
        };
      });

      const layout = {
        ...PLOT_THEME,
        margin: { l: 45, r: 20, t: 15, b: 40 },
        xaxis: { ...PLOT_THEME.xaxis, title: data.xlabel },
        yaxis: { ...PLOT_THEME.yaxis, title: data.ylabel },
        showlegend: false
      };

      Plotly.newPlot(cfg.domId, [contourTrace, ...scatterTraces], layout, { responsive: true, displayModeBar: false });
    });

  } catch (err) {
    console.error("Boundary error:", err);
  }
}

// Render Correlation Heatmap
function renderCorrelationHeatmap(corr, featureNames) {
  const z = featureNames.map(f1 => featureNames.map(f2 => corr[f1][f2]));
  const labels = featureNames.map(f => f.replace(/_/g, ' '));

  const data = [{
    z: z,
    x: labels,
    y: labels,
    type: 'heatmap',
    colorscale: 'Viridis',
    showscale: true
  }];

  const layout = {
    ...PLOT_THEME,
    margin: { l: 150, r: 30, t: 25, b: 120 },
    xaxis: { ...PLOT_THEME.xaxis, tickangle: -45 }
  };

  Plotly.newPlot('chartCorrelation', data, layout, { responsive: true, displayModeBar: false });
}

// Live Predictor Sliders Creation
function renderPredictorSliders() {
  const container = document.getElementById("featureSlidersContainer");
  if (!container) return;

  container.innerHTML = Object.entries(FEATURE_META).map(([key, meta]) => `
    <div class="param-control">
      <div class="param-label-row">
        <label for="pred_${key}">${meta.label} <small>(${meta.unit})</small></label>
        <span class="param-value" id="val_pred_${key}">${meta.default}</span>
      </div>
      <input type="range" id="pred_${key}" min="${meta.min}" max="${meta.max}" step="${meta.step}" value="${meta.default}">
    </div>
  `).join('');

  // Attach input listener to each slider to run live prediction
  Object.keys(FEATURE_META).forEach(key => {
    const el = document.getElementById(`pred_${key}`);
    const valEl = document.getElementById(`val_pred_${key}`);
    el.addEventListener("input", () => {
      valEl.textContent = el.value;
      debounce(runPrediction, 250)();
    });
  });

  // Run initial prediction
  runPrediction();
}

// Live Prediction API Call
async function runPrediction() {
  const features = Object.keys(FEATURE_META).map(key => {
    return parseFloat(document.getElementById(`pred_${key}`).value);
  });

  try {
    const res = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ features })
    });
    const data = await res.json();
    renderPredictionOutputs(data.predictions);
  } catch (err) {
    console.error("Prediction error:", err);
  }
}

// Render Prediction Outputs List
function renderPredictionOutputs(predictions) {
  const container = document.getElementById("predictionResultsList");
  if (!container) return;

  const classColors = ['#38bdf8', '#34d399', '#f43f5e'];

  container.innerHTML = Object.entries(predictions).map(([name, pred]) => {
    const probBars = pred.probabilities ? pred.probabilities.map((prob, idx) => `
      <div class="proba-bar-row">
        <span style="width: 65px; color: ${classColors[idx]}">Class ${idx}:</span>
        <div class="proba-bar-track">
          <div class="proba-bar-fill" style="width: ${(prob * 100).toFixed(1)}%; background: ${classColors[idx]}"></div>
        </div>
        <span style="width: 45px; text-align: right; font-family: monospace;">${(prob * 100).toFixed(0)}%</span>
      </div>
    `).join('') : '<p style="font-size: 0.75rem; color: #64748b;">Hard voting (discrete decision)</p>';

    return `
      <div class="pred-result-card">
        <div class="pred-result-card-header">
          <h4>${name}</h4>
          <span class="pred-pill pred-pill-${pred.predicted_class}">${pred.class_name}</span>
        </div>
        <div class="pred-probabilities">
          ${probBars}
        </div>
      </div>
    `;
  }).join('');
}

// Preset Cycler
function cyclePreset() {
  state.presetIndex = (state.presetIndex + 1) % PRESET_CULTIVARS.length;
  const preset = PRESET_CULTIVARS[state.presetIndex];

  const keys = Object.keys(FEATURE_META);
  preset.features.forEach((val, idx) => {
    const key = keys[idx];
    const el = document.getElementById(`pred_${key}`);
    const valEl = document.getElementById(`val_pred_${key}`);
    if (el && valEl) {
      el.value = val;
      valEl.textContent = val;
    }
  });

  runPrediction();
  showToast(`Loaded preset profile: ${preset.name}`, "info");
}

// Helper: Toast Notifications
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  
  const icon = type === "success" ? "fa-circle-check" : type === "error" ? "fa-circle-exclamation" : "fa-circle-info";
  toast.innerHTML = `<i class="fa-solid ${icon}"></i><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Helper: Button Loading State
function setTrainButtonLoading(isLoading) {
  const btns = [document.getElementById("btnTrainHeader"), document.getElementById("btnTrainSidebar")];
  btns.forEach(btn => {
    if (isLoading) {
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i><span>Benchmarking...</span>`;
      btn.disabled = true;
    } else {
      btn.innerHTML = btn.id === "btnTrainHeader" 
        ? `<i class="fa-solid fa-play"></i><span>Run Benchmark</span>`
        : `<i class="fa-solid fa-bolt"></i><span>Train & Evaluate</span>`;
      btn.disabled = false;
    }
  });
}

// Helper: Debounce
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
