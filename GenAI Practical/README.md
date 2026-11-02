# 🍷 Wine Ensemble Machine Learning Practical

**Comparative Study of Single Decision Tree, Bagging Classifier, AdaBoost, and Voting Classifier on the Wine Dataset**

---

## 🎯 Practical Objectives
1. **Single Decision Tree (`DecisionTreeClassifier`)**: Analyze the baseline CART algorithm, its propensity for axis-parallel splits, and high variance (overfitting).
2. **Bagging Classifier (`BaggingClassifier`)**: Implement Bootstrap Aggregation across 50 deep decision trees to reduce variance without inflating bias.
3. **AdaBoost Classifier (`AdaBoostClassifier`)**: Implement sequential boosting with adaptive sample weight adjustments to reduce bias.
4. **Voting Classifier (`VotingClassifier`)**: Ensemble combination comparing hard majority voting and soft probability weighted averaging.
5. **Interactive Visualization UI**: Full interactive web dashboard with 2D decision boundary landscapes, real-time hyperparameter tuning, confusion matrix heatmaps, and a live wine predictor.

---

## 📁 Repository Structure

```
├── wine_dataset.csv                # UCI Wine Dataset (178 samples, 13 chemical features, 3 cultivars)
├── practical_script.py             # Standalone terminal lab practical script (generates benchmark tables & plots)
├── practical_wine_ensemble.ipynb   # Jupyter Notebook with step-by-step cells & math formulas
├── app.py                          # FastAPI backend serving live training & prediction endpoints
├── static/                         # Web Application Frontend
│   ├── index.html                  # Responsive HTML5 layout
│   ├── style.css                   # Modern dark glassmorphic styling
│   └── app.js                      # Interactive Plotly engine & real-time prediction sliders
├── streamlit_app.py                # Dual UI option: Streamlit interactive lab dashboard
├── output_plots/                   # High-resolution benchmark comparison charts
│   ├── metrics_comparison.png      # Test accuracy vs. CV score bar charts
│   ├── confusion_matrices.png      # 2x2 confusion matrix heatmaps
│   ├── decision_boundaries.png     # 2D PCA decision surface boundaries
│   └── cv_distribution.png         # 10-fold cross-validation distribution boxplot
└── requirements.txt                # Python package dependencies
```

---

## 🚀 How to Run

### Option 1: Modern Interactive Web Application (Recommended)
The server is currently running at **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.
To start or restart manually:
```bash
python app.py
# Or using uvicorn:
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in any modern browser.

### Option 2: Streamlit Companion Dashboard
```bash
streamlit run streamlit_app.py
```

### Option 3: Standalone Terminal Lab Script
```bash
python practical_script.py
```
Outputs the complete benchmark summary table directly to the console and generates all plots in `output_plots/`.

### Option 4: Jupyter Notebook
Open and run [`practical_wine_ensemble.ipynb`](file:///c:/Users/amark/Desktop/GenAI%20Practical/practical_wine_ensemble.ipynb) in VS Code, JupyterLab, or Google Colab.

---

## 📊 Benchmark Evaluation Results

| Classifier Model | Train Acc | Test Acc | Overfit Gap | Macro F1 | 10-Fold Stratified CV | Multi-Class ROC-AUC (OvR) | Fit Time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Single Decision Tree** | 1.0000 | 0.9556 | 0.0444 | 0.9565 | 0.8997 &plusmn; 0.0776 | 0.9627 | ~1.4 ms |
| **Bagging Classifier** | 1.0000 | **1.0000** | **0.0000** | **1.0000** | **0.9611 &plusmn; 0.0660** | **1.0000** | ~76.7 ms |
| **AdaBoost Classifier** | 1.0000 | 0.9556 | 0.0444 | 0.9596 | 0.9327 &plusmn; 0.0892 | 0.9979 | ~57.4 ms |
| **Voting Classifier (Soft)** | 1.0000 | 0.9778 | 0.0222 | 0.9795 | 0.9167 &plusmn; 0.0870 | **1.0000** | ~150.6 ms |

---

## 🧠 Key Analytical Inferences & Viva Voce

1. **Why does Bagging outperform a Single Tree?**
   - Single decision trees have low bias but high variance (unstable partitions). Bagging trains $B$ independent trees on bootstrap subsets with replacement; averaging uncorrelated predictions cancels out variance according to:
     $$\text{Var}(\bar{f}) = \rho\sigma^2 + \frac{1-\rho}{B}\sigma^2$$
2. **How does AdaBoost reduce bias?**
   - AdaBoost fits shallow decision stumps sequentially. At each iteration, instances that were misclassified have their weights increased, forcing subsequent stumps to prioritize hard-to-classify boundary points.
3. **Soft vs. Hard Voting:**
   - Soft voting calculates the weighted average of predicted class probabilities $\sum w_j P(Y=k \mid C_j, x)$, capturing model confidence far better than a simple majority vote (Hard Voting).
