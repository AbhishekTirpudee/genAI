"""
New Evaluation Page for LLM Evaluation Studio.
Interactive form to configure prompts, models, and custom rubrics,
generate candidate responses, run LLM-as-a-Judge evaluation, and visualize results.
"""

import streamlit as st
import time
from backend.config import (
    AVAILABLE_MODELS,
    MODEL_IDS,
    DEFAULT_MODEL_A,
    DEFAULT_MODEL_B,
    DEFAULT_JUDGE_MODEL,
    DEFAULT_RUBRIC_WEIGHTS,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    get_api_key
)
from backend.model_generator import generate_parallel_responses
from backend.evaluator import evaluate_both_models
from backend.comparison import (
    create_score_comparison_df,
    create_bar_chart,
    create_radar_chart,
    create_history_trend_chart
)
from backend.database import save_evaluation, get_all_evaluations
from utils.validators import validate_rubric_weights, validate_evaluation_input


# Sample Presets for quick evaluation
BENCHMARK_PRESETS = {
    "Select a benchmark preset...": None,
    "💻 CS & Algorithms: LRU Cache Implementation": {
        "question": "Implement an LRU (Least Recently Used) cache in Python with O(1) get and put time complexity. Explain the internal data structures used and provide complexity proofs.",
        "reference": "Use a hash map paired with a doubly linked list (or collections.OrderedDict). The hash map provides O(1) key-to-node lookup, while the doubly linked list allows O(1) node removal and relocation to the most recently used position. The algorithm must handle eviction when capacity is exceeded."
    },
    "🩺 Medicine: Type 1 vs Type 2 Diabetes": {
        "question": "Explain the primary pathophysiological distinctions between Type 1 and Type 2 Diabetes Mellitus, focusing on immune etiology, insulin secretion status, and typical acute metabolic complications.",
        "reference": "Type 1 is an autoimmune destruction of pancreatic beta cells leading to absolute insulin deficiency, often presenting acutely in young individuals with diabetic ketoacidosis (DKA). Type 2 involves peripheral insulin resistance with a progressive relative secretory defect, strongly associated with metabolic syndrome, often presenting with hyperosmolar hyperglycemic state (HHS)."
    },
    "🏛️ Architecture: Monolith vs Microservices for Fintech": {
        "question": "Provide an executive architectural briefing on the trade-offs of a Modular Monolith vs Distributed Microservices for a seed-stage fintech startup handling high-value payment transactions.",
        "reference": "Monoliths offer rapid time-to-market, simple transactional ACID compliance across a single database, and lower DevOps overhead. Microservices enable independent scaling and isolated failure domains, but introduce distributed transaction complexity (eventual consistency, 2-phase commit), network latency, and audit trail fragmentation."
    },
    "⚛️ Physics: Quantum Superposition vs Entanglement": {
        "question": "What is the difference between quantum superposition and quantum entanglement? Give a concise analogy for each.",
        "reference": "Superposition refers to a single quantum state existing as a linear combination of multiple eigenstates until measured (e.g., a spinning coin in a blur of heads and tails). Entanglement is a correlation between two or more particles such that the quantum state of one instantaneously determines the other regardless of distance (e.g., a pair of matched shoes separated into two sealed boxes)."
    }
}


def render_evaluation_page():
    """Render the evaluation configuration and interactive execution interface."""
    st.markdown("""
        <div style="padding: 1rem 0 0.5rem 0;">
            <h2 style="margin: 0; font-size: 1.85rem; font-weight: 700; color: #1E293B;">
                ⚖️ New LLM Model Evaluation
            </h2>
            <p style="margin: 0.2rem 0 1rem 0; color: #64748B;">
                Configure candidate models, define weighted rubric criteria, generate independent responses, and execute automated LLM-as-a-Judge benchmarking.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Preset Loader Dropdown
    selected_preset = st.selectbox(
        "⚡ Quick Benchmark Preset (Optional)",
        options=list(BENCHMARK_PRESETS.keys()),
        index=0,
        help="Quickly populate the prompt and reference answer with curated domain benchmarks."
    )

    preset_data = BENCHMARK_PRESETS.get(selected_preset)
    default_q = preset_data["question"] if preset_data else ""
    default_ref = preset_data["reference"] if preset_data else ""

    # Form layout
    col_input, col_config = st.columns([1.1, 0.9], gap="large")

    with col_input:
        st.markdown("#### 1. Evaluation Prompt & Reference")
        
        question = st.text_area(
            "Prompt / Question *",
            value=default_q,
            height=130,
            placeholder="Enter the task, coding challenge, or question both models must answer independently...",
            help="This exact prompt will be sent identically to Model A and Model B."
        )

        reference_answer = st.text_area(
            "Expected / Reference Answer (Ground Truth) *",
            value=default_ref,
            height=130,
            placeholder="Provide the gold-standard reference answer that the judge model will evaluate responses against...",
            help="The LLM Judge uses this reference answer as the authoritative truth benchmark."
        )

    with col_config:
        st.markdown("#### 2. Model Selection")
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            idx_a = MODEL_IDS.index(DEFAULT_MODEL_A) if DEFAULT_MODEL_A in MODEL_IDS else 0
            model_a = st.selectbox(
                "Model A",
                options=MODEL_IDS,
                index=idx_a,
                format_func=lambda m: next((item["name"] for item in AVAILABLE_MODELS if item["id"] == m), m),
                help="First candidate model to benchmark."
            )

        with m_col2:
            idx_b = MODEL_IDS.index(DEFAULT_MODEL_B) if DEFAULT_MODEL_B in MODEL_IDS else min(1, len(MODEL_IDS)-1)
            model_b = st.selectbox(
                "Model B",
                options=MODEL_IDS,
                index=idx_b,
                format_func=lambda m: next((item["name"] for item in AVAILABLE_MODELS if item["id"] == m), m),
                help="Second candidate model to benchmark."
            )

        idx_judge = MODEL_IDS.index(DEFAULT_JUDGE_MODEL) if DEFAULT_JUDGE_MODEL in MODEL_IDS else 1
        judge_model = st.selectbox(
            "👨‍⚖️ LLM Judge Model",
            options=MODEL_IDS,
            index=idx_judge,
            format_func=lambda m: f"{next((item['name'] for item in AVAILABLE_MODELS if item['id'] == m), m)} (Evaluator)",
            help="High-capacity reasoning model acting as the impartial judge."
        )

        # Advanced Settings Expander
        with st.expander("⚙️ Advanced Evaluation Settings", expanded=False):
            temp = st.slider("Temperature", min_value=0.0, max_value=1.0, value=DEFAULT_TEMPERATURE, step=0.05,
                             help="Lower values produce more deterministic responses; higher values encourage creativity.")
            max_tokens = st.number_input("Max Output Tokens", min_value=128, max_value=8192, value=DEFAULT_MAX_TOKENS, step=256)
            blind_eval = st.checkbox("Blinded Evaluation (Mitigate Brand/Position Bias)", value=True,
                                     help="Masks model names as Candidate 1 and Candidate 2 during evaluation.")

    st.write("")
    st.markdown("#### 3. Custom Scoring Rubric & Weights")
    st.caption("Customize the relative importance of each dimension. The weights must total exactly 100%.")

    r_col1, r_col2, r_col3, r_col4 = st.columns(4)

    with r_col1:
        w_acc = st.slider("Accuracy Weight", min_value=0, max_value=100, value=40, step=5, format="%d%%",
                          help="Factual correctness, precision, and adherence to truths.")
    with r_col2:
        w_rel = st.slider("Relevance Weight", min_value=0, max_value=100, value=25, step=5, format="%d%%",
                          help="Directly addressing the user's specific prompt without deviating.")
    with r_col3:
        w_comp = st.slider("Completeness Weight", min_value=0, max_value=100, value=25, step=5, format="%d%%",
                           help="Addressing all sub-questions and necessary depth.")
    with r_col4:
        w_clar = st.slider("Clarity Weight", min_value=0, max_value=100, value=10, step=5, format="%d%%",
                           help="Logical readability, presentation, and concise formatting.")

    total_weight = w_acc + w_rel + w_comp + w_clar
    rubric_weights = {
        "accuracy": w_acc / 100.0,
        "relevance": w_rel / 100.0,
        "completeness": w_comp / 100.0,
        "clarity": w_clar / 100.0
    }

    # Rubric weight sum validator indicator
    weights_valid, weight_msg, normalized = validate_rubric_weights(rubric_weights)

    if weights_valid:
        st.success(f"✅ Total Rubric Weight: **{total_weight}%** (Valid)")
    else:
        st.error(f"⚠️ Total Rubric Weight: **{total_weight}%** — {weight_msg}")

    st.write("")

    # Evaluate Button
    btn_disabled = not weights_valid or not question.strip() or not reference_answer.strip()
    
    if st.button("🚀 Evaluate Models", type="primary", use_container_width=True, disabled=btn_disabled):
        is_valid, validation_msg = validate_evaluation_input(question, reference_answer, model_a, model_b, judge_model)
        if not is_valid:
            st.error(validation_msg)
            return

        # Execute Evaluation Workflow with progress indicators
        with st.status("Executing Comprehensive Model Evaluation...", expanded=True) as status:
            st.write(f"📡 Generating responses from **{model_a}** and **{model_b}** simultaneously...")
            res_a, res_b = generate_parallel_responses(
                model_a=model_a,
                model_b=model_b,
                prompt=question,
                temperature=temp,
                max_tokens=max_tokens,
                api_key=get_api_key()
            )

            if not res_a.get("success") and not res_a.get("response"):
                st.warning(f"Notice for Model A: {res_a.get('error')}")
            if not res_b.get("success") and not res_b.get("response"):
                st.warning(f"Notice for Model B: {res_b.get('error')}")

            st.write(f"👨‍⚖️ Conducting independent LLM-as-a-Judge evaluation with **{judge_model}**...")
            eval_a, eval_b, winner, judge_summary = evaluate_both_models(
                question=question,
                reference_answer=reference_answer,
                response_a=res_a.get("response", ""),
                response_b=res_b.get("response", ""),
                model_a_name=model_a,
                model_b_name=model_b,
                rubric_weights=rubric_weights,
                judge_model=judge_model,
                api_key=get_api_key(),
                blind_evaluation=blind_eval
            )

            st.write("💾 Persisting evaluation record to SQLite database...")
            record = {
                "question": question,
                "reference_answer": reference_answer,
                "model_a": model_a,
                "model_b": model_b,
                "judge_model": judge_model,
                "response_a": res_a.get("response", ""),
                "response_b": res_b.get("response", ""),
                "latency_a": res_a.get("latency_sec", 0.0),
                "latency_b": res_b.get("latency_sec", 0.0),
                "tokens_a": res_a.get("tokens", {}).get("total_tokens", 0),
                "tokens_b": res_b.get("tokens", {}).get("total_tokens", 0),
                "accuracy_a": eval_a.get("accuracy", 0.0),
                "relevance_a": eval_a.get("relevance", 0.0),
                "completeness_a": eval_a.get("completeness", 0.0),
                "clarity_a": eval_a.get("clarity", 0.0),
                "overall_a": eval_a.get("overall_score", 0.0),
                "accuracy_b": eval_b.get("accuracy", 0.0),
                "relevance_b": eval_b.get("relevance", 0.0),
                "completeness_b": eval_b.get("completeness", 0.0),
                "clarity_b": eval_b.get("clarity", 0.0),
                "overall_b": eval_b.get("overall_score", 0.0),
                "winner": winner,
                "strengths_a": eval_a.get("strengths", ""),
                "weaknesses_a": eval_a.get("weaknesses", ""),
                "strengths_b": eval_b.get("strengths", ""),
                "weaknesses_b": eval_b.get("weaknesses", ""),
                "reasoning_a": eval_a.get("reasoning", ""),
                "reasoning_b": eval_b.get("reasoning", ""),
                "judge_summary": judge_summary,
                "rubric_weights": rubric_weights,
                "is_blinded": blind_eval
            }

            eval_id = save_evaluation(record)
            status.update(label="Evaluation Complete and Saved! 🎉", state="complete", expanded=False)

        # Store in session state for instant inspection
        st.session_state["latest_eval"] = {
            "record": record,
            "eval_id": eval_id,
            "res_a": res_a,
            "res_b": res_b,
            "eval_a": eval_a,
            "eval_b": eval_b,
            "winner": winner,
            "judge_summary": judge_summary
        }

    # Render Evaluation Results Section if available
    if "latest_eval" in st.session_state:
        latest = st.session_state["latest_eval"]
        _render_evaluation_results(latest)


def _render_evaluation_results(data: dict):
    """Render the comprehensive comparison dashboard for the current evaluation."""
    rec = data["record"]
    eval_a = data["eval_a"]
    eval_b = data["eval_b"]
    winner = data["winner"]
    summary = data["judge_summary"]

    score_a = eval_a.get("overall_score", 0.0)
    score_b = eval_b.get("overall_score", 0.0)

    st.write("---")
    st.markdown("## 📊 Evaluation Results & Model Comparison")

    # Winner Announcement Banner
    if winner == "Model A":
        winner_card = f"""
            <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(37, 99, 235, 0.08) 100%); border: 2px solid #3B82F6; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <div style="font-size: 0.9rem; font-weight: 700; color: #3B82F6; text-transform: uppercase; letter-spacing: 0.05em;">Evaluation Verdict</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #1E293B; margin: 0.3rem 0;">🏆 Winner: Model A ({rec['model_a']})</div>
                <div style="font-size: 1rem; color: #475569;">{summary}</div>
            </div>
        """
    elif winner == "Model B":
        winner_card = f"""
            <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(5, 150, 105, 0.08) 100%); border: 2px solid #10B981; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <div style="font-size: 0.9rem; font-weight: 700; color: #10B981; text-transform: uppercase; letter-spacing: 0.05em;">Evaluation Verdict</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #1E293B; margin: 0.3rem 0;">🏆 Winner: Model B ({rec['model_b']})</div>
                <div style="font-size: 1rem; color: #475569;">{summary}</div>
            </div>
        """
    else:
        winner_card = f"""
            <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(217, 119, 6, 0.08) 100%); border: 2px solid #F59E0B; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <div style="font-size: 0.9rem; font-weight: 700; color: #F59E0B; text-transform: uppercase; letter-spacing: 0.05em;">Evaluation Verdict</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #1E293B; margin: 0.3rem 0;">🤝 Result: Statistical Tie</div>
                <div style="font-size: 1rem; color: #475569;">{summary}</div>
            </div>
        """
    st.markdown(winner_card, unsafe_allow_html=True)

    # Score Cards
    sc_col1, sc_col2 = st.columns(2)
    with sc_col1:
        st.markdown(f"""
            <div style="border: 1px solid #CBD5E1; border-radius: 10px; padding: 1.2rem; background: #FFFFFF; text-align: center;">
                <div style="color: #64748B; font-weight: 600; font-size: 0.95rem;">Model A: {rec['model_a']}</div>
                <div style="font-size: 3rem; font-weight: 800; color: #2563EB; margin: 0.2rem 0;">{score_a:.2f}<span style="font-size: 1.3rem; color: #94A3B8;">/10</span></div>
                <div style="font-size: 0.85rem; color: #64748B;">Latency: {rec['latency_a']:.2f}s | Tokens: {rec['tokens_a']}</div>
            </div>
        """, unsafe_allow_html=True)

    with sc_col2:
        st.markdown(f"""
            <div style="border: 1px solid #CBD5E1; border-radius: 10px; padding: 1.2rem; background: #FFFFFF; text-align: center;">
                <div style="color: #64748B; font-weight: 600; font-size: 0.95rem;">Model B: {rec['model_b']}</div>
                <div style="font-size: 3rem; font-weight: 800; color: #059669; margin: 0.2rem 0;">{score_b:.2f}<span style="font-size: 1.3rem; color: #94A3B8;">/10</span></div>
                <div style="font-size: 0.85rem; color: #64748B;">Latency: {rec['latency_b']:.2f}s | Tokens: {rec['tokens_b']}</div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Visualizations: Bar chart & Radar chart
    st.markdown("### 📈 Visual Score Comparison")
    v_col1, v_col2 = st.columns(2)
    with v_col1:
        fig_bar = create_bar_chart(eval_a, eval_b, rec["model_a"], rec["model_b"])
        st.plotly_chart(fig_bar, use_container_width=True)

    with v_col2:
        fig_radar = create_radar_chart(eval_a, eval_b, rec["model_a"], rec["model_b"])
        st.plotly_chart(fig_radar, use_container_width=True)

    # Detailed Metric Table
    st.markdown("### 📋 Dimensional Breakdown")
    df_comp = create_score_comparison_df(eval_a, eval_b, rec["model_a"], rec["model_b"])
    st.dataframe(df_comp, use_container_width=True, hide_index=True)

    # Side-by-Side Model Responses
    st.write("---")
    st.markdown("### 💬 Generated Model Responses")
    
    r_tab1, r_tab2, r_tab_ref = st.tabs([f"Model A: {rec['model_a']}", f"Model B: {rec['model_b']}", "Reference Ground Truth"])
    with r_tab1:
        st.markdown(rec["response_a"])
        st.caption(f"Latency: {rec['latency_a']:.2f}s | Tokens: {rec['tokens_a']}")

    with r_tab2:
        st.markdown(rec["response_b"])
        st.caption(f"Latency: {rec['latency_b']:.2f}s | Tokens: {rec['tokens_b']}")

    with r_tab_ref:
        st.markdown(rec["reference_answer"])

    # Detailed Qualitative Feedback
    st.write("---")
    st.markdown("### 🔍 Qualitative Judge Feedback")
    f_col1, f_col2 = st.columns(2)

    with f_col1:
        st.markdown(f"#### Model A ({rec['model_a']})")
        st.markdown(f"**Strengths:**\n{eval_a.get('strengths')}")
        st.markdown(f"**Weaknesses:**\n{eval_a.get('weaknesses')}")
        st.markdown(f"**Evaluation Rationale:**\n{eval_a.get('reasoning')}")

    with f_col2:
        st.markdown(f"#### Model B ({rec['model_b']})")
        st.markdown(f"**Strengths:**\n{eval_b.get('strengths')}")
        st.markdown(f"**Weaknesses:**\n{eval_b.get('weaknesses')}")
        st.markdown(f"**Evaluation Rationale:**\n{eval_b.get('reasoning')}")

    # Historical Model Trend Chart
    st.write("---")
    st.markdown("### 📉 Historical Performance Context")
    all_evals = get_all_evaluations(limit=25)
    trend_chart = create_history_trend_chart(all_evals)
    if trend_chart:
        st.plotly_chart(trend_chart, use_container_width=True)

    # Evaluation Disclaimer
    st.caption("ℹ️ **Methodology Disclaimer:** Automated LLM-as-a-Judge scores represent algorithmic heuristics based on the configured prompt, reference answer, and rubric weights. They do not constitute absolute ground truth.")

