"""
CrewAI Multi-Agent Workflow Orchestrator
Coordinates Destination Researcher, Itinerary Planner, and Budget Estimator
into a sequential CrewAI execution pipeline.
"""

import time
from typing import Dict, Any, Optional
from crewai import Crew, Process
from agents import (
    get_configured_llm,
    create_destination_researcher_agent,
    create_itinerary_planner_agent,
    create_budget_estimator_agent
)
from tasks import (
    create_destination_research_task,
    create_itinerary_planning_task,
    create_budget_estimation_task
)
from budget import (
    estimate_trip_budget,
    parse_agent_budget,
    ExpenseBreakdown
)


class TravelPlannerCrew:
    """
    Manages the lifecycle and execution of the multi-agent travel planning crew.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini/gemini-1.5-flash",
        force_demo: bool = False
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.force_demo = force_demo
        self.llm = get_configured_llm(
            api_key=api_key,
            model_name=model_name,
            force_demo=force_demo
        )

        # Initialize the 3 Specialized AI Agents
        self.destination_researcher = create_destination_researcher_agent(self.llm)
        self.itinerary_planner = create_itinerary_planner_agent(self.llm)
        self.budget_estimator = create_budget_estimator_agent(self.llm)

    def plan_trip(
        self,
        starting_location: str,
        budget: float,
        num_travellers: int,
        duration_days: int,
        preference: str,
        transport_mode: str
    ) -> Dict[str, Any]:
        """
        Executes the sequential multi-agent travel planning workflow:
        1. Destination Researcher suggests 3 destinations
        2. Itinerary Planner creates day-wise schedule for top destination
        3. Budget Estimator calculates itemized expenses and financial viability
        """
        start_time = time.time()

        # Step 1: Create sequential tasks with explicit context passing
        task1 = create_destination_research_task(
            agent=self.destination_researcher,
            starting_location=starting_location,
            budget=budget,
            duration_days=duration_days,
            num_travellers=num_travellers,
            preference=preference,
            transport_mode=transport_mode
        )

        task2 = create_itinerary_planning_task(
            agent=self.itinerary_planner,
            destination_task=task1,
            duration_days=duration_days,
            num_travellers=num_travellers,
            preference=preference
        )

        task3 = create_budget_estimation_task(
            agent=self.budget_estimator,
            destination_task=task1,
            itinerary_task=task2,
            starting_location=starting_location,
            budget=budget,
            duration_days=duration_days,
            num_travellers=num_travellers,
            transport_mode=transport_mode
        )

        # Step 2: Assemble CrewAI sequential crew
        crew = Crew(
            agents=[
                self.destination_researcher,
                self.itinerary_planner,
                self.budget_estimator
            ],
            tasks=[task1, task2, task3],
            process=Process.sequential,
            verbose=True
        )

        # Step 3: Execute multi-agent collaboration
        crew_output = crew.kickoff()

        # Step 4: Extract individual task outputs
        raw_output1 = str(task1.output.raw if hasattr(task1, "output") and task1.output else "")
        raw_output2 = str(task2.output.raw if hasattr(task2, "output") and task2.output else "")
        raw_output3 = str(task3.output.raw if hasattr(task3, "output") and task3.output else "")
        raw_combined = str(crew_output.raw if hasattr(crew_output, "raw") else str(crew_output))

        # Fallback safeguard: if individual task outputs weren't set, use combined
        if not raw_output1 and not raw_output2 and not raw_output3:
            raw_output3 = raw_combined

        # Step 5: Compute baseline financial breakdown & parse agent financial numbers
        baseline_breakdown = estimate_trip_budget(
            starting_location=starting_location,
            destination="Selected Destination",
            duration_days=duration_days,
            num_travellers=num_travellers,
            transport_mode=transport_mode,
            preference=preference,
            user_budget=budget
        )

        parsed_breakdown = parse_agent_budget(
            agent_output_text=raw_output3,
            fallback_breakdown=baseline_breakdown
        )

        elapsed_time = round(time.time() - start_time, 2)
        is_demo_mode = isinstance(self.llm, type(get_configured_llm(force_demo=True)))

        return {
            "success": True,
            "destinations_text": raw_output1 or "Destinations research completed.",
            "itinerary_text": raw_output2 or "Itinerary planning completed.",
            "budget_text": raw_output3 or "Budget estimation completed.",
            "combined_output": raw_combined,
            "expense_breakdown": parsed_breakdown,
            "inputs": {
                "starting_location": starting_location,
                "budget": budget,
                "num_travellers": num_travellers,
                "duration_days": duration_days,
                "preference": preference,
                "transport_mode": transport_mode
            },
            "meta": {
                "execution_seconds": elapsed_time,
                "is_demo_mode": is_demo_mode,
                "model_used": getattr(self.llm, "model", self.model_name)
            }
        }
