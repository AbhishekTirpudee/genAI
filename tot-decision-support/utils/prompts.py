
ANALYZE_PROMPT = """
You are an experienced business strategy consultant.

Analyze the following business problem:

{problem}

Return a structured analysis containing:
1. Problem Summary
2. Root Causes
3. Business Objectives
4. Constraints
5. Success Metrics

Return the result in clear, structured Markdown.
"""


GENERATE_THOUGHTS_PROMPT = """
You are a strategic decision-making AI.

Business Problem:
{problem}

Analysis:
{analysis}

Generate exactly 4 DISTINCT strategic solutions.

Each solution must contain:
- id
- title
- strategy
- expected_outcome
- implementation_approach

Avoid duplicate or similar solutions.

Return ONLY valid JSON in this format:
{{
  "thoughts": [
    {{
      "id": 1,
      "title": "Strategy name",
      "strategy": "Description",
      "expected_outcome": "Expected result",
      "implementation_approach": "How to implement"
    }}
  ]
}}
"""


EXPAND_THOUGHT_PROMPT = """
You are a business strategy expert.

Expand this strategic solution into exactly 3 actionable sub-strategies.

Solution:
{thought}

Return ONLY valid JSON:
{{
  "sub_thoughts": [
    {{
      "title": "Sub-strategy",
      "action": "Specific action",
      "expected_result": "Expected result"
    }}
  ]
}}
"""


EVALUATE_PROMPT = """
Evaluate this business strategy.

Strategy:
{thought}

Sub-strategies:
{sub_thoughts}

Score each criterion from 1 to 10:
- Impact: Higher is better
- Feasibility: Higher is better
- Cost Efficiency: Higher is better
- Risk Management: Higher is better
- Time Efficiency: Higher is better

Return ONLY valid JSON:
{{
  "impact": 8,
  "feasibility": 7,
  "cost_efficiency": 6,
  "risk_management": 8,
  "time_efficiency": 7,
  "reason": "Brief explanation"
}}
"""


FINAL_DECISION_PROMPT = """
You are a senior business decision consultant.

Business Problem:
{problem}

Ranked Strategies:
{strategies}

Based on the evaluation, provide:

1. Best Recommended Strategy
2. Why this strategy is best
3. Implementation Roadmap
4. Expected Business Outcomes
5. Major Risks and Mitigation
6. Final Conclusion

Be practical, specific and business-oriented.
"""
