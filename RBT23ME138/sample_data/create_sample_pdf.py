#!/usr/bin/env python3
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def create_sample_academic_pdf(output_path: str = "sample_data/Machine_Learning_Lecture_Notes.pdf"):
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(out),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1E293B'),
        alignment=1,  # Centered
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#64748B'),
        alignment=1,
    )
    h1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=8,
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2563EB'),
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6,
    )
    formula_style = ParagraphStyle(
        'Formula',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#0F172A'),
        backColor=colors.HexColor('#F1F5F9'),
        borderPadding=6,
        spaceAfter=8,
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("CS-501: Machine Learning Foundations", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Comprehensive Academic Lecture Notes & Study Guide", subtitle_style))
    story.append(Paragraph("Department of Computer Science & Engineering | Semester Fall", subtitle_style))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=14))

    # Page 1: Chapter 1 - Supervised Learning & Problem Formulation
    story.append(Paragraph("Chapter 1: Supervised Learning & Foundations", h1_style))
    story.append(Paragraph("1.1 Definition and Objective", h2_style))
    story.append(Paragraph(
        "Supervised learning is the machine learning task of learning a function that maps an input to an output based on example input-output pairs. "
        "The training dataset consists of N pairs: D = {(x_1, y_1), (x_2, y_2), ..., (x_N, y_N)}, where each x_i is a feature vector in R^d, "
        "and y_i is the target ground truth label.",
        body_style
    ))
    story.append(Paragraph(
        "When y_i is continuous, the problem is termed <b>Regression</b> (e.g., predicting housing prices). "
        "When y_i is discrete and categorical, the problem is termed <b>Classification</b> (e.g., medical diagnosis, spam filtering).",
        body_style
    ))
    story.append(Paragraph("1.2 Linear Regression Formulation", h2_style))
    story.append(Paragraph(
        "In linear regression, the hypothesis model assumes a linear relationship between features and target:",
        body_style
    ))
    story.append(Paragraph("Hypothesis: h_theta(x) = theta_0 + theta_1*x_1 + ... + theta_d*x_d = theta^T * x", formula_style))
    story.append(Paragraph(
        "The primary goal is to find the parameter vector theta that minimizes the discrepancy between predictions h_theta(x) and actual labels y.",
        body_style
    ))
    story.append(PageBreak())

    # Page 2: Chapter 2 - Loss Functions & Gradient Descent
    story.append(Paragraph("Chapter 2: Loss Functions & Optimization", h1_style))
    story.append(Paragraph("2.1 Mean Squared Error (MSE)", h2_style))
    story.append(Paragraph(
        "For continuous regression targets, the standard objective function is the Mean Squared Error (MSE) cost function:",
        body_style
    ))
    story.append(Paragraph("J(theta) = (1 / (2 * N)) * sum_{i=1}^N (h_theta(x_i) - y_i)^2", formula_style))
    story.append(Paragraph(
        "The factor of 1/2 is mathematically convenient because it cancels out when taking the partial derivative with respect to theta.",
        body_style
    ))
    story.append(Paragraph("2.2 Cross-Entropy Loss for Classification", h2_style))
    story.append(Paragraph(
        "For binary classification where y in {0, 1}, we use the Binary Cross-Entropy (Log Loss) function derived from maximum likelihood estimation:",
        body_style
    ))
    story.append(Paragraph("L(theta) = - (1/N) * sum_{i=1}^N [ y_i * log(p_i) + (1 - y_i) * log(1 - p_i) ]", formula_style))
    story.append(Paragraph(
        "where p_i = sigmoid(theta^T * x_i). This penalty grows exponentially as predicted probability diverges from actual label.",
        body_style
    ))
    story.append(Paragraph("2.3 Gradient Descent Algorithm", h2_style))
    story.append(Paragraph(
        "Gradient Descent is an iterative first-order optimization algorithm. At each step, parameters are updated in the direction of steepest descent:",
        body_style
    ))
    story.append(Paragraph("Update Rule: theta := theta - alpha * grad(J(theta))", formula_style))
    story.append(Paragraph(
        "Here, <b>alpha</b> denotes the <b>learning rate</b>. If alpha is too small, convergence is painfully slow. "
        "If alpha is too large, gradient descent can overshoot the minimum and diverge.",
        body_style
    ))
    story.append(PageBreak())

    # Page 3: Chapter 3 - Overfitting & Regularization
    story.append(Paragraph("Chapter 3: Overfitting, Bias-Variance, & Regularization", h1_style))
    story.append(Paragraph("3.1 The Bias-Variance Tradeoff", h2_style))
    story.append(Paragraph(
        "Total expected prediction error decomposes into three fundamental components: Bias^2 + Variance + Irreducible Error. "
        "<b>High Bias (Underfitting)</b> occurs when a model is overly simplistic and cannot capture the underlying structure of the data. "
        "<b>High Variance (Overfitting)</b> occurs when a model fits the training data noise rather than general patterns, failing on test data.",
        body_style
    ))
    story.append(Paragraph("3.2 L2 Regularization (Ridge)", h2_style))
    story.append(Paragraph(
        "Ridge regression penalizes large weights by appending the squared L2 norm to the cost function:",
        body_style
    ))
    story.append(Paragraph("J_ridge(theta) = J(theta) + (lambda / (2 * N)) * sum_{j=1}^d theta_j^2", formula_style))
    story.append(Paragraph(
        "L2 regularization shrinks coefficients smoothly toward zero but rarely makes them exactly zero.",
        body_style
    ))
    story.append(Paragraph("3.3 L1 Regularization (Lasso)", h2_style))
    story.append(Paragraph(
        "Lasso regression penalizes the sum of absolute values of parameters:",
        body_style
    ))
    story.append(Paragraph("J_lasso(theta) = J(theta) + (lambda / N) * sum_{j=1}^d |theta_j|", formula_style))
    story.append(Paragraph(
        "L1 regularization drives irrelevant feature weights exactly to zero, functioning as an automatic <b>feature selection</b> technique.",
        body_style
    ))
    story.append(PageBreak())

    # Page 4: Chapter 4 - Evaluation Metrics & Neural Networks
    story.append(Paragraph("Chapter 4: Evaluation Metrics & Deep Learning", h1_style))
    story.append(Paragraph("4.1 Classification Metrics: Precision, Recall, and F1", h2_style))
    story.append(Paragraph(
        "Accuracy alone is misleading on imbalanced datasets. We rely on the Confusion Matrix comprising True Positives (TP), "
        "False Positives (FP), True Negatives (TN), and False Negatives (FN).",
        body_style
    ))
    story.append(Paragraph(
        "<b>Precision:</b> TP / (TP + FP) — Fraction of relevant instances among retrieved instances. Measures quality of positive predictions.<br/>"
        "<b>Recall (Sensitivity):</b> TP / (TP + FN) — Fraction of actual positives that were correctly identified.<br/>"
        "<b>F1 Score:</b> 2 * (Precision * Recall) / (Precision + Recall) — The harmonic mean of Precision and Recall.",
        body_style
    ))
    story.append(Paragraph("4.2 Neural Network Activation Functions", h2_style))
    story.append(Paragraph(
        "Activation functions introduce non-linearity, allowing networks to learn complex decision boundaries:<br/>"
        "• <b>Sigmoid:</b> sigma(z) = 1 / (1 + exp(-z)). Maps to (0, 1). Susceptible to vanishing gradient problem in deep layers.<br/>"
        "• <b>ReLU (Rectified Linear Unit):</b> f(z) = max(0, z). Most popular in hidden layers; computationally efficient and mitigates vanishing gradients.<br/>"
        "• <b>Softmax:</b> Normalizes logits into a valid probability distribution over K mutually exclusive classes: P(y=k) = exp(z_k) / sum_j exp(z_j).",
        body_style
    ))

    doc.build(story)
    print(f"Sample academic PDF generated successfully at: {out.resolve()}")
    return str(out.resolve())


if __name__ == "__main__":
    create_sample_academic_pdf()
