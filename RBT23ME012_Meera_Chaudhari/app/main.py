"""
FastAPI Application Entry Point for Onyx.
Coordinates resume parsing, Gemini analysis, Neon database persistence,
and serves the Claude-inspired web UI.
"""

import os
from typing import Optional, List
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .config import PORT, ENVIRONMENT
from .database import get_db, engine, Base
from .models import Conversation, Message, ResumeRecord, AnalysisReport
from .parser import extract_resume_text
from .ai_engine import analyze_resume_fit, chat_with_gemini

# Initialize Database Schema if not already initialized
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Onyx: AI Career Architect & Job Matcher",
    description="Claude-aesthetic job description and resume semantic analyzer",
    version="1.0.0"
)

# Ensure directories exist
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("static/img", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Base Directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "templates", "index.html")

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


# --- Pydantic Request Models ---
class AnalyzeRequest(BaseModel):
    conversation_id: Optional[str] = None
    resume_id: Optional[str] = None
    target_position: str
    custom_resume_text: Optional[str] = None


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


# --- Web UI Routes ---
@app.get("/", response_class=FileResponse)
async def serve_home():
    """Renders the main Onyx Claude-inspired UI."""
    return FileResponse(INDEX_PATH)


# --- API Routes ---
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Onyx AI", "env": ENVIRONMENT}


@app.get("/api/conversations")
def list_conversations(db: Session = Depends(get_db)):
    """Fetches past chat/analysis sessions for the sidebar."""
    convs = db.query(Conversation).order_by(Conversation.updated_at.desc()).limit(30).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        }
        for c in convs
    ]


@app.post("/api/conversations")
def create_conversation(title: Optional[str] = "New Career Analysis", db: Session = Depends(get_db)):
    """Creates a fresh conversation thread."""
    conv = Conversation(title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {"id": conv.id, "title": conv.title}


@app.get("/api/conversations/{conversation_id}")
def get_conversation_details(conversation_id: str, db: Session = Depends(get_db)):
    """Loads a specific conversation with all past messages and analysis."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = [
        {
            "id": m.id,
            "sender": m.sender,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in conv.messages
    ]

    analyses = [
        {
            "id": a.id,
            "target_position": a.target_position,
            "overall_score": a.overall_score,
            "sectors_data": a.sectors_data,
            "strengths": a.strengths,
            "missing_skills": a.missing_skills,
            "what_to_remove": a.what_to_remove,
            "recommended_bullets": a.recommended_bullets,
            "summary_markdown": a.summary_markdown
        }
        for a in conv.analyses
    ]

    resumes = [
        {
            "id": r.id,
            "filename": r.filename,
            "file_type": r.file_type
        }
        for r in conv.resumes
    ]

    return {
        "id": conv.id,
        "title": conv.title,
        "messages": messages,
        "analyses": analyses,
        "resumes": resumes
    }


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Deletes a conversation from the database."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return {"status": "deleted", "id": conversation_id}


@app.post("/api/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Uploads and parses a candidate resume file (.pdf, .docx, .txt)."""
    try:
        contents = await file.read()
        extracted_text, file_type = extract_resume_text(file.filename, contents)
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract readable text from document.")

        # Ensure conversation exists or create one
        if not conversation_id or conversation_id == "null":
            conv = Conversation(title=f"Resume: {file.filename[:28]}")
            db.add(conv)
            db.commit()
            db.refresh(conv)
            conversation_id = conv.id

        resume_rec = ResumeRecord(
            conversation_id=conversation_id,
            filename=file.filename,
            file_type=file_type,
            extracted_text=extracted_text
        )
        db.add(resume_rec)
        db.commit()
        db.refresh(resume_rec)

        return {
            "status": "success",
            "resume_id": resume_rec.id,
            "conversation_id": conversation_id,
            "filename": file.filename,
            "char_count": len(extracted_text),
            "preview": extracted_text[:280] + "..." if len(extracted_text) > 280 else extracted_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/analyze")
def run_fit_analysis(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """Runs multi-sector job fit analysis using Gemini and stores results in Neon DB."""
    # Find conversation or create
    conversation_id = req.conversation_id
    if not conversation_id or conversation_id == "null":
        conv = Conversation(title=f"Analysis: {req.target_position[:28]}")
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conversation_id = conv.id
    else:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            conv = Conversation(id=conversation_id, title=f"Analysis: {req.target_position[:28]}")
            db.add(conv)
            db.commit()

    # Get resume text
    resume_text = req.custom_resume_text or ""
    if not resume_text and req.resume_id:
        resume_rec = db.query(ResumeRecord).filter(ResumeRecord.id == req.resume_id).first()
        if resume_rec:
            resume_text = resume_rec.extracted_text

    if not resume_text:
        # Check if conversation already has an uploaded resume
        latest_resume = db.query(ResumeRecord).filter(ResumeRecord.conversation_id == conversation_id).order_by(ResumeRecord.created_at.desc()).first()
        if latest_resume:
            resume_text = latest_resume.extracted_text

    if not resume_text:
        raise HTTPException(status_code=400, detail="No resume found. Please upload a resume first.")

    # Execute Gemini Analysis
    analysis_data = analyze_resume_fit(resume_text=resume_text, target_position=req.target_position)

    # Save Analysis Report to Neon DB
    report = AnalysisReport(
        conversation_id=conversation_id,
        target_position=req.target_position,
        overall_score=float(analysis_data.get("overall_score", 0)),
        sectors_data=analysis_data.get("sectors_data", []),
        strengths=analysis_data.get("strengths", []),
        missing_skills=analysis_data.get("missing_skills", []),
        what_to_remove=analysis_data.get("what_to_remove", []),
        recommended_bullets=analysis_data.get("recommended_bullets", []),
        summary_markdown=analysis_data.get("summary", "")
    )
    db.add(report)

    # Create user and assistant messages for chat thread
    user_msg = Message(
        conversation_id=conversation_id,
        sender="user",
        content=f"Please analyze my uploaded resume for the position of **{req.target_position}** across market sectors."
    )
    db.add(user_msg)

    # Build assistant message
    asst_content = f"### Analysis for **{req.target_position}** (Overall Match: {report.overall_score}%)\n\n"
    asst_content += f"**{analysis_data.get('verdict_title', 'Market Fit Assessment')}**\n\n"
    asst_content += f"{report.summary_markdown}\n"
    
    asst_msg = Message(
        conversation_id=conversation_id,
        sender="gemini",
        content=asst_content
    )
    db.add(asst_msg)

    # Update conversation title
    conv.title = f"{req.target_position} Match ({int(report.overall_score)}%)"
    db.commit()
    db.refresh(report)

    return {
        "status": "success",
        "conversation_id": conversation_id,
        "report": {
            "id": report.id,
            "target_position": report.target_position,
            "overall_score": report.overall_score,
            "verdict_title": analysis_data.get("verdict_title", "Fit Assessment"),
            "summary": report.summary_markdown,
            "sectors_data": report.sectors_data,
            "strengths": report.strengths,
            "missing_skills": report.missing_skills,
            "what_to_remove": report.what_to_remove,
            "recommended_bullets": report.recommended_bullets
        }
    }


@app.post("/api/chat")
def handle_chat_message(req: ChatRequest, db: Session = Depends(get_db)):
    """Handles conversational follow-up questions within the session context."""
    conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get resume text context
    resume_rec = db.query(ResumeRecord).filter(ResumeRecord.conversation_id == req.conversation_id).order_by(ResumeRecord.created_at.desc()).first()
    resume_context = resume_rec.extracted_text if resume_rec else None

    # Get target position context
    analysis_rec = db.query(AnalysisReport).filter(AnalysisReport.conversation_id == req.conversation_id).order_by(AnalysisReport.created_at.desc()).first()
    position_context = analysis_rec.target_position if analysis_rec else None

    # Load history
    history = [
        {"sender": m.sender, "content": m.content}
        for m in conv.messages
    ]

    # Save user message
    user_msg = Message(
        conversation_id=conv.id,
        sender="user",
        content=req.message
    )
    db.add(user_msg)
    db.commit()

    # Call Gemini
    response_text = chat_with_gemini(
        user_message=req.message,
        conversation_history=history,
        resume_context=resume_context,
        position_context=position_context
    )

    # Save Gemini message
    asst_msg = Message(
        conversation_id=conv.id,
        sender="gemini",
        content=response_text
    )
    db.add(asst_msg)
    db.commit()

    return {
        "status": "success",
        "response": response_text
    }
