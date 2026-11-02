
import json
import re

from config import generate_response


WEIGHTS = {
    "impact": 0.30,
    "feasibility": 0.25,
    "cost_efficiency": 0.15,
    "risk_management": 0.15,
    "time_efficiency": 0.15
}


def extract_json(response):
    response = response.strip()
    response = re.sub(r"^```json\s*", "", response)
    response = re.sub(r"^```\s*", "", response)
    response = re.sub(r"\s*```$", "", response)
    return json.loads(response)


def run_decision_engine(problem: str) -> dict:

    if not problem.strip():
        raise ValueError("Business problem cannot be empty.")

    prompt = f"""
You are an expert business decision-making AI
using the Tree of Thoughts methodology.

BUSINESS PROBLEM:
{problem}

Perform the following in ONE response:

1. Analyze the problem, root causes, objectives and constraints.

2. Generate exactly 4 independent strategic solution branches.

3. For each branch, generate 3 actionable sub-strategies.

4. Evaluate every branch using scores from 1 to 10:
   - impact
   - feasibility
   - cost_efficiency
   - risk_management
   - time_efficiency

5. Give a brief evaluation reason for each branch.

Return ONLY valid JSON in this exact structure:

{{
  "analysis": "Business problem analysis",
  "thoughts": [
    {{
      "id": 1,
      "title": "Strategy title",
      "strategy": "Strategy explanation",
      "expected_outcome": "Expected business outcome",
      "sub_thoughts": [
        {{
          "title": "Action title",
          "action": "Specific action",
          "expected_result": "Expected result"
        }}
      ],
      "evaluation": {{
        "impact": 8,
        "feasibility": 7,
        "cost_efficiency": 8,
        "risk_management": 7,
        "time_efficiency": 8,
        "reason": "Evaluation explanation"
      }}
    }}
  ]
}}

Important:
- Generate exactly 4 different strategies.
- Generate exactly 3 sub-strategies per branch.
- All scores must be between 1 and 10.
- Do not include Markdown or text outside JSON.
"""

    # ONE Gemini API call
    response = generate_response(prompt)
    data = extract_json(response)

    thoughts = data.get("thoughts", [])

    if len(thoughts) != 4:
        raise ValueError("Gemini did not generate exactly 4 branches.")

    branches = []

    # Python calculates weighted scores
    for thought in thoughts:

        evaluation = thought["evaluation"]

        scores = {}

        for criterion in WEIGHTS:
            score = float(evaluation[criterion])

            if not 1 <= score <= 10:
                raise ValueError(f"Invalid score: {criterion}")

            scores[criterion] = score

        weighted_score = sum(
            scores[key] * weight
            for key, weight in WEIGHTS.items()
        )

        evaluation.update(scores)
        evaluation["weighted_score"] = round(
            weighted_score, 2
        )

        branches.append({
            "thought": {
                key: value
                for key, value in thought.items()
                if key not in ("sub_thoughts", "evaluation")
            },
            "sub_thoughts": thought["sub_thoughts"],
            "evaluation": evaluation
        })

    # Rank branches
    ranked = sorted(
        branches,
        key=lambda x: x["evaluation"]["weighted_score"],
        reverse=True
    )

    # Prune weaker branches
    selected = ranked[:2]
    pruned = ranked[2:]

    # Generate final recommendation locally
    best = selected[0]

    roadmap = "\n".join(
        f"{i}. {item['title']}: {item['action']}"
        for i, item in enumerate(
            best["sub_thoughts"], start=1
        )
    )

    final_decision = f"""
## Recommended Strategy

{best['thought']['title']}

{best['thought']['strategy']}

### Why this strategy?

{best['evaluation']['reason']}

Weighted Score: {best['evaluation']['weighted_score']}/10

### Implementation Roadmap

{roadmap}

### Expected Outcome

{best['thought']['expected_outcome']}

### Alternative Strategy

{selected[1]['thought']['title']}
"""

    return {
        "problem": problem,
        "analysis": data["analysis"],
        "tree": {
            "all_branches": ranked,
            "selected_branches": selected,
            "pruned_branches": pruned
        },
        "final_decision": final_decision
    }
