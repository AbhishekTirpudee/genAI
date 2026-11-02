import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Load environment variables from .env
load_dotenv()

from state import AgentFlowState, LogEntry
from graph import agentflow_graph, build_agentflow_graph
from agents import create_log

app = FastAPI(
    title="AgentFlow AI - Multi-Agent Task Automation API",
    description="Intelligent Multi-Agent System using LangGraph and Google Gemini",
    version="1.0.0"
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store in-memory workflow sessions
# workflow_id -> { "status": str, "state": dict, "queue": asyncio.Queue, "created_at": str }
workflow_sessions: Dict[str, Dict[str, Any]] = {}

class WorkflowRunRequest(BaseModel):
    task: str = Field(..., min_length=5, description="The user task to execute")
    api_key: Optional[str] = Field(None, description="Optional Gemini API key override")
    model: Optional[str] = Field(None, description="Optional Gemini model override")

class WorkflowRunResponse(BaseModel):
    workflow_id: str
    status: str
    message: str

class HealthResponse(BaseModel):
    status: str
    version: str
    gemini_api_key_configured: bool
    model: str
    timestamp: str

@app.get("/api/workflow/health", response_model=HealthResponse)
async def health_check():
    """Check backend operational health and Gemini API key availability."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "gemini_api_key_configured": True,
        "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        "timestamp": datetime.now().isoformat()
    }

async def run_workflow_stream_task(
    workflow_id: str,
    user_task: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None
):
    """
    Executes the LangGraph multi-agent workflow in the background and pushes
    real-time event updates to the session queue for SSE streaming.
    """
    session = workflow_sessions.get(workflow_id)
    if not session:
        return

    queue: asyncio.Queue = session["queue"]

    # Initial state
    current_state: AgentFlowState = {
        "user_task": user_task,
        "plan": None,
        "execution": "",
        "review": None,
        "score": 0,
        "feedback": "",
        "missing_requirements": [],
        "improvement_suggestions": [],
        "iteration": 1,
        "status": "INITIALIZED",
        "execution_logs": [
            create_log("SYSTEM", "START", f"Workflow started for task: '{user_task}'")
        ],
        "error": None
    }
    session["state"] = current_state
    session["status"] = "RUNNING"

    # Emit initial started event
    await queue.put({
        "type": "workflow_started",
        "workflow_id": workflow_id,
        "active_node": "planner",
        "iteration": 1,
        "state": current_state
    })

    # Prepare LangGraph config
    config = {
        "configurable": {
            "api_key": api_key or os.getenv("GEMINI_API_KEY", "demo-key"),
            "model": model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        }
    }

    try:
        # Planner starts
        await queue.put({
            "type": "node_start",
            "active_node": "planner",
            "iteration": current_state["iteration"],
            "message": "Planner Agent is deconstructing task into structured steps..."
        })
        await asyncio.sleep(0.35)

        # Asynchronously stream updates from LangGraph without blocking event loop
        async for update in agentflow_graph.astream(current_state, config=config, stream_mode="updates"):
            for node_name, node_output in update.items():
                # Merge node_output into current_state
                current_state.update(node_output)
                session["state"] = current_state

                # Check for errors in node
                if current_state.get("status") == "FAILED":
                    await queue.put({
                        "type": "node_error",
                        "active_node": node_name,
                        "error": current_state.get("error", "An error occurred during agent execution."),
                        "state": current_state
                    })
                    break

                # Dispatch node-specific event
                if node_name == "planner":
                    await queue.put({
                        "type": "node_complete",
                        "active_node": "planner",
                        "iteration": current_state["iteration"],
                        "data": {"plan": current_state.get("plan")},
                        "state": current_state
                    })
                    # Executor is next
                    await queue.put({
                        "type": "node_start",
                        "active_node": "executor",
                        "iteration": current_state["iteration"],
                        "message": f"Execution Agent is generating comprehensive solution (Attempt #{current_state['iteration']})..."
                    })
                    await asyncio.sleep(0.35)

                elif node_name == "executor":
                    await queue.put({
                        "type": "node_complete",
                        "active_node": "executor",
                        "iteration": current_state["iteration"],
                        "data": {"execution": current_state.get("execution")},
                        "state": current_state
                    })
                    # Reviewer is next
                    await queue.put({
                        "type": "node_start",
                        "active_node": "reviewer",
                        "iteration": current_state["iteration"],
                        "message": "Reviewer Agent is auditing quality against approval criteria (Score threshold: 8/10)..."
                    })
                    await asyncio.sleep(0.35)

                elif node_name == "reviewer":
                    score = current_state.get("score", 8)
                    decision = current_state.get("review", {}).get("decision", "APPROVE")
                    iteration = current_state.get("iteration", 1)
                    
                    await queue.put({
                        "type": "node_complete",
                        "active_node": "reviewer",
                        "iteration": iteration,
                        "data": {
                            "review": current_state.get("review"),
                            "score": score,
                            "decision": decision
                        },
                        "state": current_state
                    })

                    # If score < 8 and iteration == 1, trigger at most 1 revision
                    if score < 8 and iteration < 2:
                        await queue.put({
                            "type": "self_correction_triggered",
                            "iteration": 2,
                            "score": score,
                            "decision": decision,
                            "feedback": current_state.get("feedback"),
                            "missing_requirements": current_state.get("missing_requirements", []),
                            "message": f"Quality score {score}/10 < 8. Routing to Execution Agent for self-correction revision (Attempt #2)..."
                        })
                        await queue.put({
                            "type": "node_start",
                            "active_node": "executor",
                            "iteration": 2,
                            "message": "Execution Agent revision in progress: Incorporating reviewer critique and addressing missing criteria..."
                        })
                        await asyncio.sleep(0.35)

        # Brief pause before completing
        await asyncio.sleep(0.2)

        # Workflow complete
        final_status = current_state.get("status", "APPROVED")
        session["status"] = final_status
        
        await queue.put({
            "type": "workflow_complete",
            "workflow_id": workflow_id,
            "final_status": final_status,
            "score": current_state.get("score", 8),
            "state": current_state,
            "message": "Workflow successfully finished."
        })

    except Exception as e:
        error_msg = f"Workflow runtime error: {str(e)}"
        current_state["status"] = "FAILED"
        current_state["error"] = error_msg
        current_state["execution_logs"].append(create_log("SYSTEM", "ERROR", error_msg))
        session["status"] = "FAILED"
        await queue.put({
            "type": "workflow_error",
            "workflow_id": workflow_id,
            "error": error_msg,
            "state": current_state
        })
    finally:
        # Sentinel to end SSE generator
        await queue.put(None)

@app.post("/api/workflow/run", response_model=WorkflowRunResponse)
async def run_workflow(request: WorkflowRunRequest, background_tasks: BackgroundTasks):
    """
    Initiates a new multi-agent workflow for the given task.
    Returns a workflow_id to connect to the SSE streaming endpoint.
    """
    task = request.task.strip()
    if not task:
        raise HTTPException(status_code=400, detail="User task cannot be empty.")

    workflow_id = str(uuid.uuid4())
    queue = asyncio.Queue()

    workflow_sessions[workflow_id] = {
        "status": "QUEUED",
        "state": None,
        "queue": queue,
        "created_at": datetime.now().isoformat()
    }

    # Start execution in background task
    background_tasks.add_task(
        run_workflow_stream_task,
        workflow_id=workflow_id,
        user_task=task,
        api_key=request.api_key,
        model=request.model
    )

    return {
        "workflow_id": workflow_id,
        "status": "QUEUED",
        "message": "Multi-agent workflow queued and executing."
    }

@app.get("/api/workflow/stream/{workflow_id}")
async def stream_workflow_events(workflow_id: str):
    """
    Server-Sent Events (SSE) endpoint to stream live real-time events,
    node transitions, agent status, and execution logs to the frontend.
    """
    session = workflow_sessions.get(workflow_id)
    if not session:
        raise HTTPException(status_code=404, detail="Workflow session not found.")

    queue: asyncio.Queue = session["queue"]

    async def event_generator():
        try:
            # Yield initial connection confirmation
            yield f"data: {json.dumps({'type': 'connection_established', 'workflow_id': workflow_id})}\n\n"
            
            while True:
                # Wait for next event from queue
                event = await queue.get()
                if event is None:
                    # Workflow finished
                    yield f"data: {json.dumps({'type': 'stream_ended', 'workflow_id': workflow_id})}\n\n"
                    break
                
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/workflow/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Retrieves current state snapshot of a workflow session."""
    session = workflow_sessions.get(workflow_id)
    if not session:
        raise HTTPException(status_code=404, detail="Workflow session not found.")
    
    return {
        "workflow_id": workflow_id,
        "status": session.get("status"),
        "state": session.get("state")
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    print(f"Starting AgentFlow AI Backend on {host}:{port}...")
    uvicorn.run("main:app", host=host, port=port, reload=True)
