
import streamlit as st

from core.decision_engine import run_decision_engine
from utils.visualizer import render_tree


# Page configuration
st.set_page_config(
    page_title="Tree of Thoughts | Decision Support",
    page_icon="🌳",
    layout="wide"
)


# Header
st.title("🌳 Tree of Thoughts")
st.subheader("AI-Powered Business Decision Support System")

st.write(
    "Explore multiple business strategies, evaluate alternatives "
    "and identify the most effective decision using AI."
)

st.divider()


# Sidebar
with st.sidebar:
    st.header("⚙️ About the System")
    st.write("""
    This application uses the Tree of Thoughts reasoning approach.

    **Process:**
    1. Analyze business problem
    2. Generate strategic thoughts
    3. Expand solution branches
    4. Evaluate each branch
    5. Prune weak strategies
    6. Recommend the best decision
    """)

    st.info("Powered by Google Gemini + Python")


# Business problem input
st.header("📌 Enter Your Business Problem")

problem = st.text_area(
    "Describe your business challenge:",
    placeholder=(
        "Example: Our company has experienced a 30% decline "
        "in sales over the last six months. Customer retention "
        "is decreasing and marketing costs are increasing."
    ),
    height=160
)

# Run decision engine
if st.button("🚀 Analyze & Generate Decisions", type="primary"):

    if not problem.strip():
        st.warning("Please enter a business problem.")

    else:
        try:
            with st.spinner(
                "AI is exploring and evaluating possible strategies..."
            ):
                result = run_decision_engine(problem)

            st.session_state["decision_result"] = result

            st.success("Business decision analysis completed!")

        except Exception as error:
            st.error(f"Analysis failed: {error}")


# Display results
if "decision_result" in st.session_state:

    result = st.session_state["decision_result"]
    tree = result["tree"]

    st.divider()

    # Problem analysis
    st.header("🔍 Business Problem Analysis")
    st.markdown(result["analysis"])

    st.divider()

    # Tree visualization
    render_tree(tree)

    st.divider()

    # Selected strategies
    st.header("🏆 Selected Strategies")

    for index, branch in enumerate(
        tree["selected_branches"], start=1
    ):
        thought = branch["thought"]
        evaluation = branch["evaluation"]

        st.markdown(f"### {index}. {thought.get('title', 'Strategy')}")

        st.write(thought.get("strategy", ""))

        st.metric(
            "Weighted Score",
            f"{evaluation['weighted_score']}/10"
        )

    st.divider()

    # Pruned strategies
    st.header("✂️ Pruned Strategies")

    pruned = tree["pruned_branches"]

    if pruned:
        for branch in pruned:
            st.write(
                f"• {branch['thought'].get('title', 'Strategy')} "
                f"({branch['evaluation']['weighted_score']}/10)"
            )
    else:
        st.write("No strategies were pruned.")

    st.divider()

    # Final decision
    st.header("🎯 Final Business Recommendation")
    st.markdown(result["final_decision"])

    # Download report
    report = f"""
TREE OF THOUGHTS - BUSINESS DECISION REPORT

BUSINESS PROBLEM:
{result['problem']}

PROBLEM ANALYSIS:
{result['analysis']}

FINAL RECOMMENDATION:
{result['final_decision']}
"""

    st.download_button(
        label="📥 Download Decision Report",
        data=report,
        file_name="business_decision_report.txt",
        mime="text/plain"
    )
