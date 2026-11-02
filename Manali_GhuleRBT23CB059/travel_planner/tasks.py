"""
CrewAI Tasks Module for Multi-Agent Travel Planner
Defines sequential tasks for Destination Research, Itinerary Planning, and Budget Estimation.
"""

from crewai import Task
from typing import Dict, Any


def create_destination_research_task(
    agent,
    starting_location: str,
    budget: float,
    duration_days: int,
    num_travellers: int,
    preference: str,
    transport_mode: str
) -> Task:
    """
    Task 1: Research 3 optimal destinations starting from the user's location.
    """
    description = (
        f"You are tasked with researching and recommending 3 ideal travel destinations starting from '{starting_location}'.\n"
        f"User Requirements:\n"
        f"- Target Budget: ₹{budget:,.0f} INR total for {num_travellers} travellers\n"
        f"- Duration: {duration_days} days\n"
        f"- Number of Travellers: {num_travellers}\n"
        f"- Travel Style / Preference: {preference}\n"
        f"- Preferred Transport Mode: {transport_mode}\n\n"
        f"Your analysis must include for each of the 3 destinations:\n"
        f"1. Destination Name & Distance/Travel Time from {starting_location} using {transport_mode}\n"
        f"2. Core Reason for Recommendation (highlighting why it fits the '{preference}' style and ₹{budget:,.0f} budget)\n"
        f"3. Top Attractions & Signature Highlights\n"
        f"4. Popularity, Best Season, and Affordability Rating (Budget-Friendly / Moderate / Premium)\n"
        f"5. A clear declaration of which destination is the #1 TOP PICK for the itinerary planning step, with rationale.\n\n"
        f"IMPORTANT GUIDELINE: Never claim unverified or estimated travel details are live booking data. "
        f"Format your response with clear markdown headings, bullet points, and an executive summary."
    )
    expected_output = (
        "A structured markdown report detailing 3 recommended destinations from the starting location, "
        "their distance, key attractions, affordability score, and a designated #1 recommended destination."
    )
    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent
    )


def create_itinerary_planning_task(
    agent,
    destination_task: Task,
    duration_days: int,
    num_travellers: int,
    preference: str
) -> Task:
    """
    Task 2: Generate a complete day-wise itinerary for the top recommended destination.
    """
    description = (
        f"Using the top recommended destination identified by the Destination Researcher, "
        f"design an exceptional, practical, day-wise travel itinerary for exactly {duration_days} days "
        f"tailored for {num_travellers} travellers with a preference for '{preference}'.\n\n"
        f"For each day (Day 1 to Day {duration_days}), provide:\n"
        f"- **Morning (08:00 - 12:30)**: Sightseeing, arrival logistics, scenic spots, or outdoor activities.\n"
        f"- **Afternoon (12:30 - 16:30)**: Recommended local cuisine/lunch stop, followed by cultural or leisurely exploration.\n"
        f"- **Evening & Night (16:30 - 21:00+)**: Sunset viewpoint, evening markets, cultural performances, and dinner suggestions.\n"
        f"- **Local Flavors to Try**: 2-3 signature regional dishes or beverages.\n"
        f"- **Practical Travel Sequencing**: Arrange visits geographically to avoid unnecessary commute backtrack.\n\n"
        f"Keep the schedule realistic, exciting, and well-paced."
    )
    expected_output = (
        f"A thorough, engaging {duration_days}-day itinerary broken down into Morning, Afternoon, "
        f"and Evening segments with authentic dining recommendations and practical transit sequencing."
    )
    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=[destination_task]
    )


def create_budget_estimation_task(
    agent,
    destination_task: Task,
    itinerary_task: Task,
    starting_location: str,
    budget: float,
    duration_days: int,
    num_travellers: int,
    transport_mode: str
) -> Task:
    """
    Task 3: Calculate comprehensive travel expenses, compare with budget, and advise.
    """
    description = (
        f"Conduct a thorough travel financial analysis for the {duration_days}-day trip "
        f"from {starting_location} for {num_travellers} travellers with transport '{transport_mode}'.\n"
        f"User Allocated Budget: ₹{budget:,.0f} INR.\n\n"
        f"Review the recommended destination and day-wise itinerary, then calculate realistic estimates in INR for:\n"
        f"- **Transportation**: ₹[Amount] (Round trip from {starting_location} + local autos/taxis for {num_travellers} people)\n"
        f"- **Accommodation**: ₹[Amount] (Clean, comfortable lodging for {duration_days - 1 if duration_days > 1 else 1} nights)\n"
        f"- **Food**: ₹[Amount] (Breakfast, lunch, dinner, snacks for {num_travellers} people across {duration_days} days)\n"
        f"- **Activities**: ₹[Amount] (Entry fees, guided tours, adventure charges)\n"
        f"- **Miscellaneous**: ₹[Amount] (Emergency buffer, tips, souvenirs, bottled water)\n"
        f"- **Total Estimated Cost**: ₹[Sum of all 5 categories]\n\n"
        f"Next, compare the Total Estimated Cost with the user's budget of ₹{budget:,.0f}:\n"
        f"- Clearly state whether the trip is **Within Budget** or **Exceeding Budget**.\n"
        f"- State the exact difference: Surplus of ₹X or Deficit of ₹X.\n"
        f"- Calculate Cost per Person and Cost per Day.\n"
        f"- Provide 3-5 high-impact cost-saving alternatives and actionable financial tips.\n\n"
        f"MANDATORY DISCLAIMER: Clearly state that all prices are realistic planning estimates and NOT guaranteed live booking rates."
    )
    expected_output = (
        "A structured financial report in INR containing itemized expenses (Transportation, Accommodation, "
        "Food, Activities, Miscellaneous), Total Estimated Cost, Budget Status ('Within Budget' or 'Exceeding Budget'), "
        "difference vs user budget, cost per person/day, cost-saving strategies, and a disclaimer."
    )
    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=[destination_task, itinerary_task]
    )
