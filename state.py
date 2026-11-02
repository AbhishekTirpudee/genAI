from typing import TypedDict, List, Dict, Any, Optional

class PlanStep(TypedDict):
    step_number: int
    title: str
    description: str
    expected_deliverable: str

class PlanOutput(TypedDict):
    identified_objectives: List[str]
    target_requirements: List[str]
    steps: List[PlanStep]

class ReviewOutput(TypedDict):
    score: int                     # 1 to 10
    decision: str                  # "APPROVE" or "REVISE"
    feedback: str                  # Detailed assessment
    missing_requirements: List[str]# List of gaps or unfulfilled requirements
    improvement_suggestions: List[str] # Actionable fixes

class LogEntry(TypedDict):
    timestamp: str
    agent: str                     # "SYSTEM", "PLANNER", "EXECUTOR", "REVIEWER", "ROUTER"
    event_type: str                # "INFO", "START", "SUCCESS", "REVISE", "APPROVED", "WARN", "ERROR"
    message: str
    details: Optional[Dict[str, Any]]

class AgentFlowState(TypedDict):
    user_task: str
    plan: Optional[PlanOutput]
    execution: str
    review: Optional[ReviewOutput]
    score: int
    feedback: str
    missing_requirements: List[str]
    improvement_suggestions: List[str]
    iteration: int
    status: str                    # "IDLE", "PLANNING", "EXECUTING", "REVIEWING", "REVISING", "APPROVED", "MAX_ITERATIONS_REACHED", "FAILED"
    execution_logs: List[LogEntry]
    error: Optional[str]
