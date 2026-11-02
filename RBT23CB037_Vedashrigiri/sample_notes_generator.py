"""
sample_notes_generator.py
Generates realistic multi-page academic PDF notes for immediate testing of the RAG Chatbot.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_cs_notes(output_path: str):
    """Generates a 4-page academic study guide on CS & AI Foundations."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#2563EB'),
        spaceBefore=12,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#1E3A8A'),
        backColor=colors.HexColor('#EFF6FF'),
        borderColor=colors.HexColor('#93C5FD'),
        borderWidth=1,
        borderPadding=8,
        spaceBefore=6,
        spaceAfter=10
    )

    story = []

    # PAGE 1: Course Overview & Operating Systems
    story.append(Paragraph("CS401: Advanced Computer Science & AI Systems", title_style))
    story.append(Paragraph("Lecture Notes & Exam Study Guide — Department of Computer Science", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=15))

    story.append(Paragraph("Module 1: Operating Systems & Concurrency", h1_style))
    story.append(Paragraph(
        "Operating systems act as an intermediary between user applications and bare computer hardware. "
        "A process is a program in execution containing a program counter, stack, data section, and heap.",
        body_style
    ))

    story.append(Paragraph("1.1 Deadlock Characterization (Coffman Conditions)", h2_style))
    story.append(Paragraph(
        "A deadlock occurs when a set of processes are blocked because each process is holding a resource and "
        "waiting for another resource held by some other process. A deadlock situation can arise if and only if "
        "all four Coffman conditions hold simultaneously:",
        body_style
    ))
    story.append(Paragraph(
        "1. <b>Mutual Exclusion:</b> At least one resource must be held in a non-shareable mode.<br/>"
        "2. <b>Hold and Wait:</b> A process must be currently holding at least one resource and requesting additional resources.<br/>"
        "3. <b>No Preemption:</b> Resources cannot be forcibly preempted from a process holding them.<br/>"
        "4. <b>Circular Wait:</b> A closed loop of processes exists, where each process holds at least one resource needed by the next.",
        callout_style
    ))

    story.append(Paragraph("1.2 Virtual Memory & Page Replacement", h2_style))
    story.append(Paragraph(
        "Virtual memory separates user logical memory from physical memory. The Memory Management Unit (MMU) translates "
        "virtual addresses into physical addresses using page tables. When a requested page is not resident in physical RAM, "
        "the OS triggers a <b>page fault interrupt</b>. Common page replacement algorithms include FIFO (First-In-First-Out), "
        "LRU (Least Recently Used), and Optimal (Belady's Algorithm). Belady's Anomaly demonstrates that for FIFO, increasing "
        "the number of page frames can counterintuitively increase page faults.",
        body_style
    ))

    # PAGE 2: Algorithms & Complexity
    story.append(PageBreak())
    story.append(Paragraph("Module 2: Algorithmic Complexity & Graph Search", h1_style))
    story.append(Paragraph(
        "Asymptotic analysis evaluates algorithm efficiency as input size n approaches infinity. "
        "Big-O represents the asymptotic upper bound: f(n) = O(g(n)) if there exist positive constants c and n0 "
        "such that 0 <= f(n) <= c*g(n) for all n >= n0.",
        body_style
    ))

    # Table of complexities
    table_data = [
        ["Algorithm", "Data Structure", "Average Time", "Worst Case Time", "Space Complexity"],
        ["Quicksort", "Array", "O(n log n)", "O(n^2)", "O(log n)"],
        ["Mergesort", "Array / Linked List", "O(n log n)", "O(n log n)", "O(n)"],
        ["Dijkstra's", "Adjacency List + Min-Heap", "O((V + E) log V)", "O((V + E) log V)", "O(V)"],
        ["Bellman-Ford", "Edge List", "O(V * E)", "O(V * E)", "O(V)"],
        ["Binary Search", "Sorted Array", "O(log n)", "O(log n)", "O(1)"]
    ]
    t = Table(table_data, colWidths=[90, 130, 85, 95, 90])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#F8FAFC')),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("2.1 Dijkstra's Shortest Path Algorithm", h2_style))
    story.append(Paragraph(
        "Dijkstra's algorithm solves the single-source shortest path problem for directed or undirected graphs with non-negative edge weights. "
        "It maintains a priority queue of unvisited vertices sorted by tentative distance from the source vertex. "
        "Crucial Note: Dijkstra's fails when graphs contain <b>negative edge weights</b>; for graphs with negative weights, "
        "the <b>Bellman-Ford algorithm</b> must be used instead.",
        body_style
    ))

    # PAGE 3: Artificial Intelligence & Machine Learning
    story.append(PageBreak())
    story.append(Paragraph("Module 3: Artificial Intelligence & Machine Learning", h1_style))
    story.append(Paragraph(
        "Machine Learning focuses on algorithms that learn patterns from empirical data rather than relying strictly on rule-based programming.",
        body_style
    ))

    story.append(Paragraph("3.1 Supervised vs Unsupervised Learning", h2_style))
    story.append(Paragraph(
        "<b>Supervised Learning:</b> The training dataset contains both feature inputs X and ground-truth labels Y. "
        "Tasks are categorized into Regression (predicting continuous real-valued outputs) and Classification (predicting discrete category labels). "
        "Examples include Linear Regression, Logistic Regression, Support Vector Machines (SVM), and Random Forests.<br/><br/>"
        "<b>Unsupervised Learning:</b> The dataset contains only feature vectors X with no target labels. "
        "The model must discover latent structure, groupings, or representations. Primary tasks include Clustering (K-Means, DBSCAN) "
        "and Dimensionality Reduction (Principal Component Analysis - PCA, t-SNE).",
        body_style
    ))

    story.append(Paragraph("3.2 The Bias-Variance Tradeoff & Overfitting", h2_style))
    story.append(Paragraph(
        "The total expected generalization error of a machine learning model is composed of three components: "
        "<b>Error = Bias^2 + Variance + Irreducible Error</b>.",
        body_style
    ))
    story.append(Paragraph(
        "• <b>High Bias (Underfitting):</b> Occurs when the hypothesis class is too restrictive to capture underlying relationships. "
        "The model suffers high training error and high validation error.<br/>"
        "• <b>High Variance (Overfitting):</b> Occurs when the model fits training noise and random fluctuations rather than the true signal. "
        "The model shows extremely low training error but high validation/test error.<br/>"
        "• <b>Mitigation Strategies:</b> Regularization (L1 Lasso for feature sparsity, L2 Ridge for weight shrinkage), "
        "Cross-Validation (k-fold), Dropout in neural networks, and increasing training data volume.",
        callout_style
    ))

    # PAGE 4: Database Systems & Exam Review Formulas
    story.append(PageBreak())
    story.append(Paragraph("Module 4: Database Normalization & ACID Properties", h1_style))
    story.append(Paragraph(
        "Database normalization organizes relational schema to reduce data redundancy and eliminate update, insertion, and deletion anomalies.",
        body_style
    ))

    story.append(Paragraph("4.1 Normal Forms Hierarchy", h2_style))
    story.append(Paragraph(
        "1. <b>First Normal Form (1NF):</b> Each column contains atomic (indivisible) values, and each record is unique.<br/>"
        "2. <b>Second Normal Form (2NF):</b> In 1NF and no non-prime attribute is partially dependent on any candidate key (eliminates partial dependency).<br/>"
        "3. <b>Third Normal Form (3NF):</b> In 2NF and no non-prime attribute depends transitively on a candidate key (X -> Y where Y is non-prime implies X is superkey or Y is prime).<br/>"
        "4. <b>Boyce-Codd Normal Form (BCNF):</b> For every functional dependency X -> Y, X must strictly be a superkey.",
        body_style
    ))

    story.append(Paragraph("4.2 ACID Transaction Guarantees", h2_style))
    story.append(Paragraph(
        "• <b>Atomicity:</b> 'All or nothing' — transactions execute entirely or roll back cleanly.<br/>"
        "• <b>Consistency:</b> Transitions the database strictly from one valid state to another satisfying all schema invariants.<br/>"
        "• <b>Isolation:</b> Concurrent transactions execute without interfering with one another (serializability).<br/>"
        "• <b>Durability:</b> Committed transactions persist permanently across power outages and crashes using write-ahead logs (WAL).",
        callout_style
    ))

    story.append(Paragraph("High-Yield Exam Review Summary", h1_style))
    story.append(Paragraph(
        "<b>Key Formula 1 (Amdahl's Law):</b> Speedup = 1 / ((1 - p) + (p / s)), where p is parallel proportion and s is speedup.<br/>"
        "<b>Key Formula 2 (F1 Score):</b> F1 = 2 * (Precision * Recall) / (Precision + Recall).<br/>"
        "<b>Key Formula 3 (Cross-Entropy Loss):</b> L = - sum(y_i * log(p_i)) for multi-class classification.",
        callout_style
    ))

    doc.build(story)
    print(f"Generated sample CS notes: {output_path}")


def generate_ml_notes(output_path: str):
    """Generates a 3-page academic study guide on Machine Learning & Deep Learning."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle2',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6
    )

    h1_style = ParagraphStyle(
        'H1_2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#7C3AED'),
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'Body2',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    callout_style = ParagraphStyle(
        'Callout2',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#4C1D95'),
        backColor=colors.HexColor('#F5F3FF'),
        borderColor=colors.HexColor('#C4B5FD'),
        borderWidth=1,
        borderPadding=7,
        spaceBefore=4,
        spaceAfter=8
    )

    story = []

    # PAGE 1: Gradient Descent & Loss Functions
    story.append(Paragraph("EE520: Deep Learning & Optimization Theory", title_style))
    story.append(Paragraph("Lecture Notes: Optimization, Backpropagation, and Transformers", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#7C3AED'), spaceAfter=10))

    story.append(Paragraph("Section 1: Gradient Descent Optimization", h1_style))
    story.append(Paragraph(
        "Gradient Descent iteratively updates model parameters theta in the direction opposite to the gradient "
        "of the loss function: theta = theta - eta * grad(L(theta)), where eta is the learning rate.",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Batch Gradient Descent:</b> Computes gradients over the entire dataset. Deterministic updates but computationally prohibitive for large datasets.<br/>"
        "• <b>Stochastic Gradient Descent (SGD):</b> Updates weights after computing loss on a single random training sample. High noise allows escaping local minima.<br/>"
        "• <b>Mini-Batch Gradient Descent:</b> Uses batches of 32-512 examples, balancing vectorization GPU hardware efficiency with update stability.<br/>"
        "• <b>Adam Optimizer:</b> Adaptive Moment Estimation tracks both first raw moment (momentum, beta1=0.9) and second uncentered moment (RMSProp variance, beta2=0.999).",
        callout_style
    ))

    # PAGE 2: Neural Network Architectures
    story.append(PageBreak())
    story.append(Paragraph("Section 2: Transformer Architecture & Attention Mechanism", h1_style))
    story.append(Paragraph(
        "Vaswani et al. (2017) introduced 'Attention Is All You Need', replacing recurrence and convolutions with self-attention. "
        "The core mathematical formulation of Scaled Dot-Product Attention is:",
        body_style
    ))
    story.append(Paragraph(
        "<b>Attention(Q, K, V) = softmax( (Q * K^T) / sqrt(d_k) ) * V</b><br/>"
        "Where Q represents Queries, K represents Keys, V represents Values, and d_k is the dimension of keys. "
        "The scaling factor 1 / sqrt(d_k) prevents dot products from growing excessively large, which would push the softmax "
        "function into regions with vanishingly small gradients.",
        callout_style
    ))
    story.append(Paragraph(
        "Multi-Head Attention projects Q, K, and V into h distinct lower-dimensional representation subspaces, "
        "allowing the model to jointly attend to information from different positions and representation subspaces simultaneously.",
        body_style
    ))

    # PAGE 3: Retrieval-Augmented Generation (RAG)
    story.append(PageBreak())
    story.append(Paragraph("Section 3: Retrieval-Augmented Generation (RAG) Foundations", h1_style))
    story.append(Paragraph(
        "Retrieval-Augmented Generation (Lewis et al., 2020) addresses LLM limitations including hallucination, "
        "lack of domain knowledge, and static knowledge cutoff dates. A standard RAG pipeline operates in three phases:",
        body_style
    ))
    story.append(Paragraph(
        "1. <b>Indexing:</b> Documents are cleaned, chunked into semantically coherent segments, and embedded into high-dimensional vector representations.<br/>"
        "2. <b>Retrieval:</b> When a user asks a query, the system retrieves top-k relevant chunks using vector cosine similarity, dense embeddings, or hybrid BM25 + dense search.<br/>"
        "3. <b>Generation:</b> The retrieved context chunks are inserted into a structured prompt alongside the user prompt, instructing the LLM to generate grounded answers with source citations.",
        callout_style
    ))
    story.append(Paragraph(
        "<b>Evaluation Metrics for RAG:</b><br/>"
        "• <b>Faithfulness / Groundedness:</b> Whether the generated answer can be strictly inferred from the retrieved context.<br/>"
        "• <b>Answer Relevance:</b> Whether the answer directly addresses the user query.<br/>"
        "• <b>Context Precision & Recall:</b> How relevant and complete the retrieved context chunks are relative to the ground truth.",
        body_style
    ))

    doc.build(story)
    print(f"Generated sample ML notes: {output_path}")


if __name__ == "__main__":
    os.makedirs("sample_notes", exist_ok=True)
    generate_cs_notes("sample_notes/CS_Foundations_Notes.pdf")
    generate_ml_notes("sample_notes/Deep_Learning_RAG_Notes.pdf")
