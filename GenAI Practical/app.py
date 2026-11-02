import os
import time
import numpy as np
import pandas as pd
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import BaggingClassifier, AdaBoostClassifier, VotingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score, roc_curve
)
from sklearn.decomposition import PCA

app = FastAPI(title="Wine Ensemble ML Practical API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load dataset once
DATASET_PATH = "wine_dataset.csv"
if os.path.exists(DATASET_PATH):
    DF = pd.read_csv(DATASET_PATH)
else:
    wine = load_wine(as_frame=True)
    DF = wine.frame
    DF['target_name'] = DF['target'].map({0: 'Class_0 (Barolo)', 1: 'Class_1 (Grignolino)', 2: 'Class_2 (Barbera)'})
    DF.to_csv(DATASET_PATH, index=False)

FEATURE_NAMES = [c for c in DF.columns if c not in ['target', 'target_name']]
TARGET_NAMES = ['Class 0 (Barolo)', 'Class 1 (Grignolino)', 'Class 2 (Barbera)']
X_FULL = DF[FEATURE_NAMES].values
Y_FULL = DF['target'].values


class TrainConfig(BaseModel):
    test_size: float = 0.25
    random_state: int = 42
    scaler_type: str = "standard"  # "standard", "minmax", "none"
    
    # Decision Tree parameters
    dt_criterion: str = "gini"  # "gini", "entropy", "log_loss"
    dt_max_depth: Optional[int] = None
    dt_min_samples_split: int = 2
    
    # Bagging parameters
    bag_n_estimators: int = 50
    bag_bootstrap: bool = True
    bag_max_samples: float = 1.0
    
    # AdaBoost parameters
    ada_n_estimators: int = 50
    ada_learning_rate: float = 1.0
    ada_base_max_depth: int = 1
    
    # Voting parameters
    voting_type: str = "soft"  # "soft" or "hard"
    weight_tree: float = 1.0
    weight_bagging: float = 2.0
    weight_adaboost: float = 2.0
    cv_folds: int = 5


class PredictRequest(BaseModel):
    features: List[float]


class DecisionBoundaryRequest(BaseModel):
    feature_x: str = "pca_1"  # "pca_1" or actual feature name
    feature_y: str = "pca_2"  # "pca_2" or actual feature name
    dt_max_depth: Optional[int] = None
    bag_n_estimators: int = 50
    ada_n_estimators: int = 50
    voting_type: str = "soft"
    resolution: int = 60


def build_models(config: TrainConfig):
    dt = DecisionTreeClassifier(
        criterion=config.dt_criterion,
        max_depth=config.dt_max_depth,
        min_samples_split=config.dt_min_samples_split,
        random_state=config.random_state
    )

    bag = BaggingClassifier(
        estimator=DecisionTreeClassifier(
            criterion=config.dt_criterion,
            max_depth=config.dt_max_depth,
            random_state=config.random_state
        ),
        n_estimators=config.bag_n_estimators,
        max_samples=config.bag_max_samples,
        bootstrap=config.bag_bootstrap,
        random_state=config.random_state
    )

    ada = AdaBoostClassifier(
        estimator=DecisionTreeClassifier(
            max_depth=config.ada_base_max_depth,
            random_state=config.random_state
        ),
        n_estimators=config.ada_n_estimators,
        learning_rate=config.ada_learning_rate,
        random_state=config.random_state
    )

    weights = [config.weight_tree, config.weight_bagging, config.weight_adaboost]
    voting = VotingClassifier(
        estimators=[
            ('decision_tree', dt),
            ('bagging', bag),
            ('adaboost', ada)
        ],
        voting=config.voting_type,
        weights=weights if any(w > 0 for w in weights) else None
    )

    return {
        "Single Decision Tree": dt,
        "Bagging Classifier": bag,
        "AdaBoost Classifier": ada,
        "Voting Classifier": voting
    }


@app.get("/api/dataset-info")
def get_dataset_info():
    preview = DF.head(20).to_dict(orient="records")
    summary = DF[FEATURE_NAMES].describe().to_dict()
    corr = DF[FEATURE_NAMES].corr().round(3).to_dict()
    class_counts = DF['target_name'].value_counts().to_dict()

    return {
        "total_samples": len(DF),
        "feature_names": FEATURE_NAMES,
        "target_names": TARGET_NAMES,
        "class_counts": class_counts,
        "preview": preview,
        "summary": summary,
        "correlation": corr
    }


@app.post("/api/train")
def train_and_evaluate(config: TrainConfig):
    # Preprocessing
    X = X_FULL.copy()
    y = Y_FULL.copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.test_size, random_state=config.random_state, stratify=y
    )

    if config.scaler_type == "standard":
        scaler = StandardScaler()
        X_train_proc = scaler.fit_transform(X_train)
        X_test_proc = scaler.transform(X_test)
        X_all_proc = scaler.fit_transform(X)
    elif config.scaler_type == "minmax":
        scaler = MinMaxScaler()
        X_train_proc = scaler.fit_transform(X_train)
        X_test_proc = scaler.transform(X_test)
        X_all_proc = scaler.fit_transform(X)
    else:
        X_train_proc = X_train
        X_test_proc = X_test
        X_all_proc = X

    models = build_models(config)
    results = {}
    cv = StratifiedKFold(n_splits=config.cv_folds, shuffle=True, random_state=config.random_state)

    for name, model in models.items():
        t0 = time.perf_counter()
        model.fit(X_train_proc, y_train)
        fit_time_ms = round((time.perf_counter() - t0) * 1000, 2)

        y_train_pred = model.predict(X_train_proc)
        y_test_pred = model.predict(X_test_proc)

        train_acc = float(accuracy_score(y_train, y_train_pred))
        test_acc = float(accuracy_score(y_test, y_test_pred))
        overfit_gap = float(train_acc - test_acc)

        precision = float(precision_score(y_test, y_test_pred, average="macro", zero_division=0))
        recall = float(recall_score(y_test, y_test_pred, average="macro", zero_division=0))
        f1_macro = float(f1_score(y_test, y_test_pred, average="macro", zero_division=0))
        f1_weighted = float(f1_score(y_test, y_test_pred, average="weighted", zero_division=0))

        # Cross Validation
        cv_scores = cross_val_score(model, X_all_proc, y, cv=cv, scoring="accuracy")
        cv_mean = float(cv_scores.mean())
        cv_std = float(cv_scores.std())

        # Confusion Matrix
        cm = confusion_matrix(y_test, y_test_pred).tolist()

        # ROC AUC
        roc_auc = None
        roc_curves = []
        if hasattr(model, "predict_proba") and config.voting_type != "hard":
            try:
                y_prob = model.predict_proba(X_test_proc)
                roc_auc = float(roc_auc_score(y_test, y_prob, multi_class='ovr'))
                for c_idx in range(3):
                    fpr, tpr, _ = roc_curve(y_test == c_idx, y_prob[:, c_idx])
                    roc_curves.append({
                        "class": TARGET_NAMES[c_idx],
                        "fpr": fpr.round(4).tolist(),
                        "tpr": tpr.round(4).tolist()
                    })
            except Exception:
                roc_auc = None

        # Feature importances if available
        feature_importances = None
        if hasattr(model, "feature_importances_"):
            feature_importances = model.feature_importances_.round(4).tolist()
        elif name == "Bagging Classifier":
            # Average feature importances of base estimators
            try:
                importances = np.mean([tree.feature_importances_ for tree in model.estimators_], axis=0)
                feature_importances = importances.round(4).tolist()
            except Exception:
                feature_importances = None

        results[name] = {
            "name": name,
            "train_acc": round(train_acc, 4),
            "test_acc": round(test_acc, 4),
            "overfit_gap": round(overfit_gap, 4),
            "precision_macro": round(precision, 4),
            "recall_macro": round(recall, 4),
            "f1_macro": round(f1_macro, 4),
            "f1_weighted": round(f1_weighted, 4),
            "cv_mean": round(cv_mean, 4),
            "cv_std": round(cv_std, 4),
            "cv_scores": [round(float(s), 4) for s in cv_scores],
            "train_time_ms": fit_time_ms,
            "confusion_matrix": cm,
            "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
            "roc_curves": roc_curves,
            "feature_importances": feature_importances
        }

    return {
        "success": True,
        "results": results,
        "sample_split": {
            "train_count": len(X_train),
            "test_count": len(X_test)
        },
        "feature_names": FEATURE_NAMES
    }


@app.post("/api/decision-boundary")
def get_decision_boundary(req: DecisionBoundaryRequest):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_FULL)
    y = Y_FULL

    if req.feature_x == "pca_1" or req.feature_y == "pca_2":
        pca = PCA(n_components=2, random_state=42)
        X_2d = pca.fit_transform(X_scaled)
        xlabel = "PCA Component 1 (Chemical Variance)"
        ylabel = "PCA Component 2 (Phenolic Variance)"
    else:
        try:
            idx_x = FEATURE_NAMES.index(req.feature_x)
            idx_y = FEATURE_NAMES.index(req.feature_y)
            X_2d = X_scaled[:, [idx_x, idx_y]]
            xlabel = req.feature_x
            ylabel = req.feature_y
        except ValueError:
            pca = PCA(n_components=2, random_state=42)
            X_2d = pca.fit_transform(X_scaled)
            xlabel = "PCA Component 1"
            ylabel = "PCA Component 2"

    x_min, x_max = X_2d[:, 0].min() - 0.8, X_2d[:, 0].max() + 0.8
    y_min, y_max = X_2d[:, 1].min() - 0.8, X_2d[:, 1].max() + 0.8
    res = min(req.resolution, 80)
    grid_x = np.linspace(x_min, x_max, res)
    grid_y = np.linspace(y_min, y_max, res)
    xx, yy = np.meshgrid(grid_x, grid_y)
    grid_points = np.c_[xx.ravel(), yy.ravel()]

    models_2d = {
        "Single Decision Tree": DecisionTreeClassifier(max_depth=req.dt_max_depth, random_state=42),
        "Bagging Classifier": BaggingClassifier(
            estimator=DecisionTreeClassifier(max_depth=req.dt_max_depth, random_state=42),
            n_estimators=req.bag_n_estimators,
            random_state=42
        ),
        "AdaBoost Classifier": AdaBoostClassifier(
            estimator=DecisionTreeClassifier(max_depth=1, random_state=42),
            n_estimators=req.ada_n_estimators,
            random_state=42
        ),
        "Voting Classifier": VotingClassifier(
            estimators=[
                ('dt', DecisionTreeClassifier(max_depth=req.dt_max_depth, random_state=42)),
                ('bag', BaggingClassifier(estimator=DecisionTreeClassifier(max_depth=req.dt_max_depth, random_state=42), n_estimators=req.bag_n_estimators, random_state=42)),
                ('ada', AdaBoostClassifier(estimator=DecisionTreeClassifier(max_depth=1, random_state=42), n_estimators=req.ada_n_estimators, random_state=42))
            ],
            voting=req.voting_type
        )
    }

    surfaces = {}
    for name, m in models_2d.items():
        m.fit(X_2d, y)
        z = m.predict(grid_points).reshape(xx.shape)
        surfaces[name] = z.tolist()

    # Points data
    points = [
        {"x": round(float(X_2d[i, 0]), 3), "y": round(float(X_2d[i, 1]), 3), "label": int(y[i]), "class_name": TARGET_NAMES[y[i]]}
        for i in range(len(X_2d))
    ]

    return {
        "grid_x": [round(float(v), 3) for v in grid_x],
        "grid_y": [round(float(v), 3) for v in grid_y],
        "surfaces": surfaces,
        "points": points,
        "xlabel": xlabel,
        "ylabel": ylabel
    }


@app.post("/api/predict")
def predict_sample(req: PredictRequest):
    if len(req.features) != len(FEATURE_NAMES):
        raise HTTPException(status_code=400, detail=f"Expected {len(FEATURE_NAMES)} features, received {len(req.features)}")

    sample = np.array(req.features).reshape(1, -1)
    scaler = StandardScaler()
    scaler.fit(X_FULL)
    sample_scaled = scaler.transform(sample)

    # Train base default models
    dt = DecisionTreeClassifier(random_state=42).fit(scaler.transform(X_FULL), Y_FULL)
    bag = BaggingClassifier(estimator=DecisionTreeClassifier(random_state=42), n_estimators=50, random_state=42).fit(scaler.transform(X_FULL), Y_FULL)
    ada = AdaBoostClassifier(estimator=DecisionTreeClassifier(max_depth=1, random_state=42), n_estimators=50, random_state=42).fit(scaler.transform(X_FULL), Y_FULL)
    voting = VotingClassifier(estimators=[('dt', dt), ('bag', bag), ('ada', ada)], voting='soft').fit(scaler.transform(X_FULL), Y_FULL)

    predictions = {}
    for name, m in [("Single Decision Tree", dt), ("Bagging Classifier", bag), ("AdaBoost Classifier", ada), ("Voting Classifier", voting)]:
        pred_class = int(m.predict(sample_scaled)[0])
        proba = m.predict_proba(sample_scaled)[0].round(4).tolist() if hasattr(m, "predict_proba") else None
        predictions[name] = {
            "predicted_class": pred_class,
            "class_name": TARGET_NAMES[pred_class],
            "probabilities": proba
        }

    return {
        "predictions": predictions,
        "classes": TARGET_NAMES
    }


# Mount static files
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
