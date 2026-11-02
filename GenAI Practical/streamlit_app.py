"""
================================================================================
STREAMLIT COMPANION APP: WINE ENSEMBLE CLASSIFIER PRACTICAL
Decision Tree vs. Bagging vs. AdaBoost vs. Voting Classifier
================================================================================
"""

import time
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import BaggingClassifier, AdaBoostClassifier, VotingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score
)
from sklearn.decomposition import PCA

st.set_page_config(
    page_title="Wine Ensemble ML Practical",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #334155;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# Load Dataset
@st.cache_data
def get_wine_data():
    wine = load_wine(as_frame=True)
    df = wine.frame
    df['target_name'] = df['target'].map({0: 'Class 0 (Barolo)', 1: 'Class 1 (Grignolino)', 2: 'Class 2 (Barbera)'})
    feature_cols = [c for c in df.columns if c not in ['target', 'target_name']]
    return df, feature_cols, wine.target_names

df, feature_cols, target_names = get_wine_data()
X = df[feature_cols].values
y = df['target'].values

# Title & Banner
st.title("🍷 Wine Ensemble Classifier Practical")
st.markdown("### Comparing Single Decision Tree, Bagging, AdaBoost & Voting Classifiers")
st.caption(f"Dataset: UCI Wine Recognition | Samples: {len(df)} | Features: {len(feature_cols)} | Classes: 3")

# Sidebar Configuration
st.sidebar.header("⚙️ Practical Hyperparameters")

test_size = st.sidebar.slider("Test Set Split Ratio", 0.10, 0.40, 0.25, 0.05)
cv_folds = st.sidebar.slider("Stratified CV Folds", 3, 10, 5)

st.sidebar.subheader("1. Decision Tree")
criterion = st.sidebar.selectbox("Splitting Criterion", ["gini", "entropy", "log_loss"])
max_depth = st.sidebar.slider("Tree Max Depth (0 = Full)", 0, 10, 0)
tree_depth = None if max_depth == 0 else max_depth

st.sidebar.subheader("2. Bagging Classifier")
bag_estimators = st.sidebar.slider("Bagging Trees (Estimators)", 10, 150, 50, 10)
bag_bootstrap = st.sidebar.checkbox("Bootstrap (With Replacement)", value=True)

st.sidebar.subheader("3. AdaBoost Classifier")
ada_estimators = st.sidebar.slider("AdaBoost Boosting Rounds", 10, 150, 50, 10)
ada_lr = st.sidebar.slider("AdaBoost Learning Rate", 0.1, 2.0, 1.0, 0.1)

st.sidebar.subheader("4. Voting Classifier")
voting_type = st.sidebar.selectbox("Voting Rule", ["soft", "hard"])
w_tree = st.sidebar.slider("Weight: Decision Tree", 0, 5, 1)
w_bag = st.sidebar.slider("Weight: Bagging", 0, 5, 2)
w_ada = st.sidebar.slider("Weight: AdaBoost", 0, 5, 2)

# Train Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=test_size, random_state=42, stratify=y
)
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc = scaler.transform(X_test)
X_all_sc = scaler.fit_transform(X)

# Model Building
dt = DecisionTreeClassifier(criterion=criterion, max_depth=tree_depth, random_state=42)
bag = BaggingClassifier(estimator=DecisionTreeClassifier(criterion=criterion, max_depth=tree_depth, random_state=42), n_estimators=bag_estimators, bootstrap=bag_bootstrap, random_state=42)
ada = AdaBoostClassifier(estimator=DecisionTreeClassifier(max_depth=1, random_state=42), n_estimators=ada_estimators, learning_rate=ada_lr, random_state=42)
voting = VotingClassifier(
    estimators=[('dt', dt), ('bag', bag), ('ada', ada)],
    voting=voting_type,
    weights=[w_tree, w_bag, w_ada] if (w_tree + w_bag + w_ada > 0) else None
)

models = {
    "Single Decision Tree": dt,
    "Bagging Classifier": bag,
    "AdaBoost Classifier": ada,
    "Voting Classifier": voting
}

# Run Training
results = []
cms = {}
cv_dict = {}

cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)

for name, model in models.items():
    t0 = time.perf_counter()
    model.fit(X_train_sc, y_train)
    fit_time = (time.perf_counter() - t0) * 1000

    y_train_pred = model.predict(X_train_sc)
    y_test_pred = model.predict(X_test_sc)

    tr_acc = accuracy_score(y_train, y_train_pred)
    te_acc = accuracy_score(y_test, y_test_pred)
    prec = precision_score(y_test, y_test_pred, average='macro', zero_division=0)
    rec = recall_score(y_test, y_test_pred, average='macro', zero_division=0)
    f1 = f1_score(y_test, y_test_pred, average='macro', zero_division=0)

    cv_scores = cross_val_score(model, X_all_sc, y, cv=cv, scoring='accuracy')
    cv_dict[name] = cv_scores

    if hasattr(model, "predict_proba") and voting_type != "hard":
        try:
            auc = roc_auc_score(y_test, model.predict_proba(X_test_sc), multi_class='ovr')
        except:
            auc = np.nan
    else:
        auc = np.nan

    cms[name] = confusion_matrix(y_test, y_test_pred)

    results.append({
        "Model": name,
        "Train Acc": tr_acc,
        "Test Acc": te_acc,
        "Overfit Gap": tr_acc - te_acc,
        "Macro Precision": prec,
        "Macro Recall": rec,
        "Macro F1": f1,
        "CV Mean": cv_scores.mean(),
        "CV Std": cv_scores.std(),
        "ROC-AUC": auc,
        "Fit Time (ms)": fit_time
    })

res_df = pd.DataFrame(results)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Benchmarks & Leaderboard",
    "🗺️ 2D Decision Surfaces",
    "🎯 Confusion Matrices",
    "🧪 Live Wine Predictor",
    "📖 Practical Lab Manual"
])

with tab1:
    cols = st.columns(4)
    for idx, row in res_df.iterrows():
        with cols[idx]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{row['Model']}</div>
                <div class="metric-value">{row['Test Acc']*100:.1f}%</div>
                <div class="metric-label">CV: {row['CV Mean']*100:.1f}% &plusmn; {row['CV Std']*100:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    c1, c2 = st.columns([1.5, 1])

    with c1:
        st.subheader("Performance Comparison")
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=res_df['Model'], y=res_df['Test Acc'], name='Test Accuracy', marker_color='#38bdf8'))
        fig_bar.add_trace(go.Bar(x=res_df['Model'], y=res_df['CV Mean'], name=f'{cv_folds}-Fold CV Mean', marker_color='#34d399',
                                 error_y=dict(type='data', array=res_df['CV Std'], visible=True)))
        fig_bar.add_trace(go.Bar(x=res_df['Model'], y=res_df['Macro F1'], name='Macro F1', marker_color='#c084fc'))
        fig_bar.update_layout(barmode='group', yaxis_range=[0.75, 1.02], template="plotly_dark", height=400)
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        st.subheader("Overfitting Analysis (Gap)")
        fig_gap = px.bar(res_df, x='Model', y='Overfit Gap', color='Model',
                         title='Train Accuracy - Test Accuracy Gap', template="plotly_dark", height=400)
        st.plotly_chart(fig_gap, use_container_width=True)

    st.subheader("📋 Detailed Laboratory Evaluation Table")
    st.dataframe(res_df.style.format({
        "Train Acc": "{:.4f}",
        "Test Acc": "{:.4f}",
        "Overfit Gap": "{:.4f}",
        "Macro Precision": "{:.4f}",
        "Macro Recall": "{:.4f}",
        "Macro F1": "{:.4f}",
        "CV Mean": "{:.4f}",
        "CV Std": "{:.4f}",
        "ROC-AUC": "{:.4f}",
        "Fit Time (ms)": "{:.2f}"
    }), use_container_width=True)

with tab2:
    st.subheader("2D Decision Boundary Landscapes (PCA Projected Space)")
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_all_sc)
    
    x_min, x_max = X_pca[:, 0].min() - 0.8, X_pca[:, 0].max() + 0.8
    y_min, y_max = X_pca[:, 1].min() - 0.8, X_pca[:, 1].max() + 0.8
    grid_x, grid_y = np.linspace(x_min, x_max, 60), np.linspace(y_min, y_max, 60)
    xx, yy = np.meshgrid(grid_x, grid_y)
    grid_pts = np.c_[xx.ravel(), yy.ravel()]

    cols2 = st.columns(2)
    for idx, (m_name, m_obj) in enumerate(models.items()):
        col = cols2[idx % 2]
        with col:
            # Fit clone on 2D
            if m_name == "Single Decision Tree":
                m2 = DecisionTreeClassifier(max_depth=tree_depth, random_state=42)
            elif m_name == "Bagging Classifier":
                m2 = BaggingClassifier(estimator=DecisionTreeClassifier(max_depth=tree_depth, random_state=42), n_estimators=bag_estimators, random_state=42)
            elif m_name == "AdaBoost Classifier":
                m2 = AdaBoostClassifier(estimator=DecisionTreeClassifier(max_depth=1, random_state=42), n_estimators=ada_estimators, random_state=42)
            else:
                m2 = VotingClassifier(
                    estimators=[
                        ('dt', DecisionTreeClassifier(max_depth=tree_depth, random_state=42)),
                        ('bag', BaggingClassifier(estimator=DecisionTreeClassifier(max_depth=tree_depth, random_state=42), n_estimators=bag_estimators, random_state=42)),
                        ('ada', AdaBoostClassifier(estimator=DecisionTreeClassifier(max_depth=1, random_state=42), n_estimators=ada_estimators, random_state=42))
                    ],
                    voting=voting_type
                )
            m2.fit(X_pca, y)
            zz = m2.predict(grid_pts).reshape(xx.shape)

            fig_bound = go.Figure()
            fig_bound.add_trace(go.Contour(
                x=grid_x, y=grid_y, z=zz,
                colorscale=[[0, 'rgba(56, 189, 248, 0.3)'], [0.5, 'rgba(52, 211, 153, 0.3)'], [1, 'rgba(244, 63, 94, 0.3)']],
                showscale=False, contours_coloring='fill'
            ))
            for c_idx, color in zip(range(3), ['#38bdf8', '#34d399', '#f43f5e']):
                pts = X_pca[y == c_idx]
                fig_bound.add_trace(go.Scatter(
                    x=pts[:, 0], y=pts[:, 1], mode='markers',
                    name=f'Class {c_idx}', marker=dict(color=color, size=6, line=dict(color='white', width=0.5))
                ))
            fig_bound.update_layout(title=m_name, template="plotly_dark", height=380, showlegend=False,
                                    margin=dict(l=30, r=20, t=35, b=30))
            st.plotly_chart(fig_bound, use_container_width=True)

with tab3:
    st.subheader("Confusion Matrices (Test Set)")
    cm_cols = st.columns(4)
    labels = ['Barolo', 'Grignolino', 'Barbera']
    for idx, (m_name, cm_mat) in enumerate(cms.items()):
        with cm_cols[idx]:
            fig_cm = px.imshow(cm_mat, text_auto=True, x=labels, y=labels,
                               color_continuous_scale='Blues', title=m_name, template="plotly_dark")
            fig_cm.update_layout(height=320, coloraxis_showscale=False, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_cm, use_container_width=True)

with tab4:
    st.subheader("🧪 Live Wine Cultivar Predictor")
    st.write("Adjust chemical attributes to see live classification across all four models:")
    
    col_in, col_out = st.columns([1.5, 1])
    with col_in:
        s_alc = st.slider("Alcohol (vol %)", 11.0, 15.0, 13.0, 0.1)
        s_mal = st.slider("Malic Acid (g/L)", 0.7, 6.0, 2.3, 0.1)
        s_flav = st.slider("Flavanoids (g/L)", 0.3, 5.1, 2.0, 0.1)
        s_col = st.slider("Color Intensity", 1.2, 13.0, 5.0, 0.1)
        s_pro = st.slider("Proline (mg/L)", 270.0, 1700.0, 746.0, 10.0)
    
    # Fill remaining features with mean
    sample_full = np.array([s_alc, s_mal, 2.36, 19.5, 99.7, 2.3, s_flav, 0.36, 1.6, s_col, 0.95, 2.6, s_pro]).reshape(1, -1)
    sample_sc = scaler.transform(sample_full)

    with col_out:
        st.markdown("### Ensemble Predictions")
        for m_name, m_obj in models.items():
            pred = m_obj.predict(sample_sc)[0]
            st.success(f"**{m_name}:** Class {pred} ({target_names[pred]})")

with tab5:
    st.subheader("📖 Practical Lab Manual & Viva Voce Q&A")
    st.markdown("""
    #### 1. Practical Aim
    Comparative analysis of Single Decision Tree, Bagging Classifier, AdaBoost, and Voting Classifier on the UCI Wine Recognition dataset.

    #### 2. Key Observations
    - **Single Decision Tree** suffers from high variance (100% training accuracy with noticeable drops on test/cross-validation).
    - **Bagging** reduces variance through bootstrap aggregation, smoothing the sharp orthogonal boundaries.
    - **AdaBoost** sequential boosting emphasizes misclassified points, effectively reducing bias.
    - **Voting Classifier** harnesses diverse model outputs, yielding reliable ensemble consensus.
    """)
