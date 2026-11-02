"""
================================================================================
MACHINE LEARNING LAB PRACTICAL
Topic: Comparative Study of Single Decision Tree, Bagging Classifier,
       AdaBoost Classifier, and Voting Classifier on the Wine Dataset
================================================================================
Practical Objectives:
1. Load and explore the Wine recognition dataset (13 chemical attributes, 3 cultivars).
2. Train a Single Decision Tree Classifier and observe variance/overfitting tendencies.
3. Train a Bagging Classifier (Bootstrap Aggregation) to reduce variance.
4. Train an AdaBoost Classifier to reduce bias through sequential boosting.
5. Train an Ensemble Voting Classifier (combining Tree, Bagging, and AdaBoost).
6. Evaluate all four models using:
   - Train & Test Accuracy (Overfitting Delta)
   - Precision, Recall, F1-Score (Macro & Weighted)
   - 10-Fold Stratified Cross-Validation (Mean +/- Std)
   - Execution / Training Time
   - Confusion Matrices
   - 2D Decision Boundaries (PCA space)
   - Multi-class ROC-AUC (One-vs-Rest)
================================================================================
"""

import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import BaggingClassifier, AdaBoostClassifier, VotingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score
)
from sklearn.decomposition import PCA


def run_practical():
    print("=" * 80)
    print("STEP 1: LOADING & EXPLORING WINE DATASET")
    print("=" * 80)

    csv_path = "wine_dataset.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        print(f"Loaded dataset from {csv_path}")
        feature_cols = [c for c in df.columns if c not in ['target', 'target_name']]
        X = df[feature_cols].values
        y = df['target'].values
        target_names = ['Class 0 (Barolo)', 'Class 1 (Grignolino)', 'Class 2 (Barbera)']
    else:
        wine = load_wine()
        X, y = wine.data, wine.target
        feature_cols = wine.feature_names
        target_names = wine.target_names

    print(f"Total Samples: {X.shape[0]}")
    print(f"Number of Features: {X.shape[1]}")
    print(f"Classes: {np.unique(y)} ({target_names})")
    print(f"Class Distribution: {np.bincount(y)}")

    # Step 2: Train/Test Split
    print("\n" + "=" * 80)
    print("STEP 2: STRATIFIED TRAIN / TEST SPLIT & PREPROCESSING")
    print("=" * 80)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    print(f"Train set size: {X_train.shape[0]} samples")
    print(f"Test set size:  {X_test.shape[0]} samples")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Step 3: Model Definitions
    print("\n" + "=" * 80)
    print("STEP 3: DEFINING THE FOUR CLASSIFIERS")
    print("=" * 80)

    # 1. Single Decision Tree
    dt_clf = DecisionTreeClassifier(
        criterion="gini",
        max_depth=None,
        random_state=42
    )

    # 2. Bagging Classifier (with Decision Tree base estimators)
    bag_clf = BaggingClassifier(
        estimator=DecisionTreeClassifier(random_state=42),
        n_estimators=50,
        max_samples=1.0,
        max_features=1.0,
        bootstrap=True,
        random_state=42
    )

    # 3. AdaBoost Classifier (with Decision Tree decision stumps / weak learners)
    ada_clf = AdaBoostClassifier(
        estimator=DecisionTreeClassifier(max_depth=1, random_state=42),
        n_estimators=50,
        learning_rate=1.0,
        random_state=42
    )

    # 4. Voting Classifier (combines Decision Tree, Bagging, AdaBoost)
    voting_clf = VotingClassifier(
        estimators=[
            ('decision_tree', dt_clf),
            ('bagging', bag_clf),
            ('adaboost', ada_clf)
        ],
        voting='soft',
        weights=[1, 2, 2]
    )

    models = {
        "Single Decision Tree": dt_clf,
        "Bagging Classifier": bag_clf,
        "AdaBoost Classifier": ada_clf,
        "Voting Classifier (Soft)": voting_clf
    }

    # Step 4: Training, Evaluation & Benchmarking
    print("\n" + "=" * 80)
    print("STEP 4: TRAINING & EVALUATING BENCHMARKS")
    print("=" * 80)

    results = []
    confusion_matrices = {}
    cv_scores_dict = {}

    cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

    for name, model in models.items():
        # Measure training time
        t0 = time.perf_counter()
        model.fit(X_train_scaled, y_train)
        train_time = (time.perf_counter() - t0) * 1000  # in ms

        # Predictions
        y_train_pred = model.predict(X_train_scaled)
        y_test_pred = model.predict(X_test_scaled)
        
        # Probabilities for ROC AUC
        if hasattr(model, "predict_proba"):
            y_test_proba = model.predict_proba(X_test_scaled)
            roc_auc = roc_auc_score(y_test, y_test_proba, multi_class='ovr')
        else:
            roc_auc = np.nan

        # Metrics
        train_acc = accuracy_score(y_train, y_train_pred)
        test_acc = accuracy_score(y_test, y_test_pred)
        overfitting_gap = train_acc - test_acc
        precision_macro = precision_score(y_test, y_test_pred, average="macro")
        recall_macro = recall_score(y_test, y_test_pred, average="macro")
        f1_macro = f1_score(y_test, y_test_pred, average="macro")
        f1_weighted = f1_score(y_test, y_test_pred, average="weighted")

        # 10-Fold Stratified Cross-Validation on entire dataset (scaled)
        X_all_scaled = scaler.fit_transform(X)
        cv_scores = cross_val_score(model, X_all_scaled, y, cv=cv, scoring="accuracy")
        cv_scores_dict[name] = cv_scores
        cv_mean = cv_scores.mean()
        cv_std = cv_scores.std()

        confusion_matrices[name] = confusion_matrix(y_test, y_test_pred)

        results.append({
            "Model": name,
            "Train Acc": train_acc,
            "Test Acc": test_acc,
            "Overfit Gap": overfitting_gap,
            "Macro Precision": precision_macro,
            "Macro Recall": recall_macro,
            "Macro F1": f1_macro,
            "Weighted F1": f1_weighted,
            "10-Fold CV Mean": cv_mean,
            "10-Fold CV Std": cv_std,
            "ROC-AUC (OvR)": roc_auc,
            "Train Time (ms)": train_time
        })

    results_df = pd.DataFrame(results)

    # Format table for clean console display
    print("\nSUMMARY COMPARISON TABLE:")
    print("-" * 115)
    print(f"{'Model':<26} | {'Train Acc':<10} | {'Test Acc':<10} | {'Gap':<7} | {'Macro F1':<9} | {'10-Fold CV':<15} | {'ROC-AUC':<8} | {'Time (ms)':<9}")
    print("-" * 115)
    for _, row in results_df.iterrows():
        print(f"{row['Model']:<26} | {row['Train Acc']:<10.4f} | {row['Test Acc']:<10.4f} | {row['Overfit Gap']:<7.4f} | {row['Macro F1']:<9.4f} | {row['10-Fold CV Mean']:.4f} +/- {row['10-Fold CV Std']:.4f} | {row['ROC-AUC (OvR)']:<8.4f} | {row['Train Time (ms)']:<9.2f}")
    print("-" * 115)

    # Step 5: Visualizations
    print("\n" + "=" * 80)
    print("STEP 5: GENERATING LAB VISUALIZATIONS & PLOTS")
    print("=" * 80)

    # Set aesthetics
    sns.set_theme(style="whitegrid", palette="muted")
    os.makedirs("output_plots", exist_ok=True)

    # Plot 1: Performance Metrics Comparison
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # 1A: Test Accuracy & CV Mean
    x_pos = np.arange(len(results_df))
    width = 0.35
    axes[0].bar(x_pos - width/2, results_df['Test Acc'], width, label='Test Accuracy', color='#3b82f6', alpha=0.9)
    axes[0].bar(x_pos + width/2, results_df['10-Fold CV Mean'], width, yerr=results_df['10-Fold CV Std'], capsize=5, label='10-Fold CV Mean', color='#10b981', alpha=0.9)
    axes[0].set_ylabel('Score')
    axes[0].set_title('Test Accuracy vs 10-Fold Cross-Validation', fontsize=13, fontweight='bold')
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels(results_df['Model'], rotation=15, ha='right', fontsize=10)
    axes[0].set_ylim(0.8, 1.02)
    axes[0].legend(loc='lower right')
    for i in x_pos:
        axes[0].text(i - width/2, results_df['Test Acc'].iloc[i] + 0.005, f"{results_df['Test Acc'].iloc[i]:.3f}", ha='center', fontsize=9)
        axes[0].text(i + width/2, results_df['10-Fold CV Mean'].iloc[i] + 0.005, f"{results_df['10-Fold CV Mean'].iloc[i]:.3f}", ha='center', fontsize=9)

    # 1B: Macro F1 and Overfitting Gap
    axes[1].bar(x_pos - width/2, results_df['Macro F1'], width, label='Macro F1-Score', color='#8b5cf6', alpha=0.9)
    axes[1].bar(x_pos + width/2, results_df['Overfit Gap'], width, label='Overfit Gap (Train - Test)', color='#f59e0b', alpha=0.9)
    axes[1].set_ylabel('Score / Gap')
    axes[1].set_title('Macro F1-Score and Overfitting Gap', fontsize=13, fontweight='bold')
    axes[1].set_xticks(x_pos)
    axes[1].set_xticklabels(results_df['Model'], rotation=15, ha='right', fontsize=10)
    axes[1].legend(loc='upper right')

    plt.tight_layout()
    metrics_path = os.path.join("output_plots", "metrics_comparison.png")
    plt.savefig(metrics_path, dpi=300)
    plt.close()
    print(f"Saved: {metrics_path}")

    # Plot 2: Confusion Matrices (2x2 Grid)
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.ravel()
    class_labels = ['Class 0', 'Class 1', 'Class 2']

    for idx, (name, cm) in enumerate(confusion_matrices.items()):
        sns.heatmap(
            cm, annot=True, fmt='d', cmap='Blues', cbar=False,
            xticklabels=class_labels, yticklabels=class_labels,
            ax=axes[idx], annot_kws={"size": 14, "weight": "bold"}
        )
        axes[idx].set_title(f"{name}\nAccuracy: {results_df.loc[results_df['Model'] == name, 'Test Acc'].values[0]:.4f}", fontsize=12, fontweight='bold')
        axes[idx].set_xlabel("Predicted Label")
        axes[idx].set_ylabel("True Label")

    plt.suptitle("Confusion Matrix Comparison Across Models", fontsize=15, fontweight='bold', y=0.99)
    plt.tight_layout()
    cm_path = os.path.join("output_plots", "confusion_matrices.png")
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"Saved: {cm_path}")

    # Plot 3: 2D Decision Boundaries (PCA Projected Space)
    print("Computing 2D PCA decision boundaries...")
    pca = PCA(n_components=2, random_state=42)
    X_train_pca = pca.fit_transform(X_train_scaled)
    X_test_pca = pca.transform(X_test_scaled)

    # Meshgrid over 2D PCA space
    x_min, x_max = X_train_pca[:, 0].min() - 1, X_train_pca[:, 0].max() + 1
    y_min, y_max = X_train_pca[:, 1].min() - 1, X_train_pca[:, 1].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.05), np.arange(y_min, y_max, 0.05))
    grid_points = np.c_[xx.ravel(), yy.ravel()]

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.ravel()
    colors = ['#ef4444', '#3b82f6', '#10b981']
    cmap_light = plt.matplotlib.colors.ListedColormap(['#fecaca', '#bfdbfe', '#a7f3d0'])

    for idx, (name, model) in enumerate(models.items()):
        # Fit 2D surrogate model on PCA projection
        model_clone = None
        if name == "Single Decision Tree":
            model_clone = DecisionTreeClassifier(random_state=42)
        elif name == "Bagging Classifier":
            model_clone = BaggingClassifier(estimator=DecisionTreeClassifier(random_state=42), n_estimators=50, random_state=42)
        elif name == "AdaBoost Classifier":
            model_clone = AdaBoostClassifier(estimator=DecisionTreeClassifier(max_depth=1, random_state=42), n_estimators=50, random_state=42)
        else:
            model_clone = VotingClassifier(
                estimators=[
                    ('dt', DecisionTreeClassifier(random_state=42)),
                    ('bag', BaggingClassifier(estimator=DecisionTreeClassifier(random_state=42), n_estimators=50, random_state=42)),
                    ('ada', AdaBoostClassifier(estimator=DecisionTreeClassifier(max_depth=1, random_state=42), n_estimators=50, random_state=42))
                ],
                voting='soft'
            )
        model_clone.fit(X_train_pca, y_train)
        Z = model_clone.predict(grid_points)
        Z = Z.reshape(xx.shape)

        axes[idx].contourf(xx, yy, Z, cmap=cmap_light, alpha=0.6)
        scatter = axes[idx].scatter(
            X_train_pca[:, 0], X_train_pca[:, 1],
            c=y_train, cmap=plt.matplotlib.colors.ListedColormap(colors),
            edgecolor='k', s=45, alpha=0.9
        )
        axes[idx].scatter(
            X_test_pca[:, 0], X_test_pca[:, 1],
            c=y_test, cmap=plt.matplotlib.colors.ListedColormap(colors),
            edgecolor='yellow', linewidth=1.5, s=60, marker='^', alpha=0.9
        )
        axes[idx].set_title(f"{name}\nDecision Boundary (PCA Space)", fontsize=12, fontweight='bold')
        axes[idx].set_xlabel("Principal Component 1")
        axes[idx].set_ylabel("Principal Component 2")

    plt.suptitle("Decision Boundary Surface Comparison in 2D PCA Space\n(Circles = Train, Triangles = Test)", fontsize=15, fontweight='bold', y=0.99)
    plt.tight_layout()
    db_path = os.path.join("output_plots", "decision_boundaries.png")
    plt.savefig(db_path, dpi=300)
    plt.close()
    print(f"Saved: {db_path}")

    # Plot 4: 10-Fold CV Score Distribution Boxplot
    fig, ax = plt.subplots(figsize=(10, 6))
    cv_df = pd.DataFrame(cv_scores_dict)
    sns.boxplot(data=cv_df, ax=ax, palette="Set2", width=0.45)
    sns.stripplot(data=cv_df, ax=ax, color='black', alpha=0.5, jitter=0.2, size=6)
    ax.set_title("10-Fold Cross-Validation Accuracy Distribution", fontsize=14, fontweight='bold')
    ax.set_ylabel("Accuracy Score")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha='right', fontsize=11)
    ax.set_ylim(0.85, 1.02)
    plt.tight_layout()
    cv_path = os.path.join("output_plots", "cv_distribution.png")
    plt.savefig(cv_path, dpi=300)
    plt.close()
    print(f"Saved: {cv_path}")

    # Step 6: Practical Lab Conclusions & Viva Discussion
    print("\n" + "=" * 80)
    print("STEP 6: LAB PRACTICAL INFERENCES & VIVA DISCUSSION")
    print("=" * 80)
    print("""
Key Analytical Inferences:
1. Single Decision Tree:
   - Tends to create axis-parallel, rigid orthogonal decision boundaries.
   - Suffers from high variance and prone to overfitting (100% train accuracy with non-trivial gap on test).
2. Bagging Classifier:
   - Aggregates multiple deep trees trained on bootstrap samples (with replacement).
   - Drastically reduces variance without increasing bias, producing smoother boundary contours and higher CV consistency.
3. AdaBoost Classifier:
   - Sequentially boosts weak decision stumps by elevating sample weights of misclassified instances.
   - Focuses heavily on boundary edge cases and reduces bias, yielding high precision and recall.
4. Voting Classifier:
   - Combines individual algorithmic strengths (single tree speed, bagging stability, boosting focus).
   - Soft voting leverages predicted class probability distributions, achieving the most resilient generalization.
    """)
    print("=" * 80)
    print(f"All practical outputs and comparison plots saved to: {os.path.abspath('output_plots')}")
    print("=" * 80)

    return results_df


if __name__ == "__main__":
    run_practical()
