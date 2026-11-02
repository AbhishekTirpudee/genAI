
import streamlit as st


def render_tree(tree: dict):
    """
    Visualize the generated Tree of Thoughts.
    Displays selected and pruned branches with scores.
    """

    all_branches = tree.get("all_branches", [])
    selected = tree.get("selected_branches", [])
    pruned = tree.get("pruned_branches", [])

    st.subheader("🌳 Tree of Thoughts Visualization")

    st.caption(
        f"Total Branches: {len(all_branches)} | "
        f"Selected: {len(selected)} | "
        f"Pruned: {len(pruned)}"
    )

    for index, branch in enumerate(all_branches, start=1):

        thought = branch["thought"]
        sub_thoughts = branch["sub_thoughts"]
        evaluation = branch["evaluation"]

        is_selected = branch in selected

        status = "✅ Selected" if is_selected else "✂️ Pruned"

        with st.expander(
            f"Branch {index}: {thought.get('title', 'Strategy')} "
            f"| {status} "
            f"| Score: {evaluation['weighted_score']}/10",
            expanded=is_selected
        ):

            st.markdown(f"**Strategy:** {thought.get('strategy', '')}")

            st.markdown("#### Sub-strategies")

            for sub_index, sub in enumerate(sub_thoughts, start=1):
                st.markdown(
                    f"**{sub_index}. {sub.get('title', 'Action')}**"
                )
                st.write(sub.get("action", ""))
                st.caption(
                    f"Expected Result: {sub.get('expected_result', '')}"
                )

            st.markdown("#### Evaluation Scores")

            criteria = {
                "Impact": "impact",
                "Feasibility": "feasibility",
                "Cost Efficiency": "cost_efficiency",
                "Risk Management": "risk_management",
                "Time Efficiency": "time_efficiency"
            }

            for label, key in criteria.items():
                score = evaluation[key]

                st.write(f"**{label}: {score}/10**")
                st.progress(score / 10)

            st.metric(
                "Weighted Score",
                f"{evaluation['weighted_score']}/10"
            )

            st.caption(evaluation.get("reason", ""))
