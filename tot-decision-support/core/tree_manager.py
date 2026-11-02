
from core.thought_expander import expand_thought
from core.evaluator import evaluate_thought


def build_decision_tree(thoughts: list, top_n: int = 2) -> dict:
    """
    Build the Tree of Thoughts by expanding, evaluating,
    ranking and pruning strategic branches.
    """

    evaluated_branches = []

    for thought in thoughts:

        # Step 1: Expand each main thought
        sub_thoughts = expand_thought(thought)

        # Step 2: Evaluate the branch
        evaluation = evaluate_thought(
            thought,
            sub_thoughts
        )

        branch = {
            "thought": thought,
            "sub_thoughts": sub_thoughts,
            "evaluation": evaluation
        }

        evaluated_branches.append(branch)

    # Step 3: Rank branches by weighted score
    ranked_branches = sorted(
        evaluated_branches,
        key=lambda x: x["evaluation"]["weighted_score"],
        reverse=True
    )

    # Step 4: Prune weaker branches
    selected_branches = ranked_branches[:top_n]

    pruned_branches = ranked_branches[top_n:]

    return {
        "all_branches": ranked_branches,
        "selected_branches": selected_branches,
        "pruned_branches": pruned_branches
    }
