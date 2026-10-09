from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from backend.ai.agent import InventoryAgent
from backend.ai.forecasting import get_product_forecast
from backend.ai.dead_stock_engine import analyze_dead_and_slow_stock
from backend.ai.expiry_engine import evaluate_expiry_risks
from backend.ai.chat_assistant import NaturalLanguageAssistant
from backend.ai.llm_engine import LLMEngine
from backend.ai.feedback_loop import record_recommendation_outcome, get_feedback_metrics
from backend.auth.roles import get_current_user, require_roles, ROLE_ADMIN, ROLE_MANAGER

from backend.ai.conversation_memory import ConversationMemoryManager

router = APIRouter(prefix="/api/ai", tags=["Agentic AI Decision Engine"])

agent = InventoryAgent()

class ModifyRecomRequest(BaseModel):
    new_quantity: float

class RejectRecomRequest(BaseModel):
    reason: Optional[str] = None

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    user_id: Optional[int] = None

class FeedbackRecordRequest(BaseModel):
    recommendation_id: int
    actual_sales: float
    notes: Optional[str] = None

@router.post("/scan")
def trigger_agent_scan(current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))):
    """Triggers the full autonomous Agentic AI cycle across the catalog."""
    return agent.run_cycle()

@router.get("/recommendations")
def list_recommendations(status: Optional[str] = Query(None)):
    """Lists AI recommendations with transparent formula breakdowns."""
    return agent.list_recommendations(status=status)

@router.post("/recommendations/{recom_id}/approve")
def approve_recommendation(
    recom_id: int,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Human-in-the-loop: Approves AI recommendation and automatically creates draft PO."""
    try:
        return agent.approve_recommendation(recom_id, user_id=current_user["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/recommendations/{recom_id}/modify")
def modify_recommendation(
    recom_id: int,
    req: ModifyRecomRequest,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Human-in-the-loop: Modifies recommended order quantity and approves."""
    try:
        return agent.modify_and_approve(recom_id, req.new_quantity, user_id=current_user["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/recommendations/{recom_id}/reject")
def reject_recommendation(
    recom_id: int,
    req: RejectRecomRequest,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Human-in-the-loop: Rejects AI recommendation with shopkeeper override reason."""
    try:
        return agent.reject_recommendation(recom_id, user_id=current_user["id"], reason=req.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/forecast/{product_id}")
def get_forecast(product_id: int):
    """Runs ML demand forecast comparing Moving Average, Linear Regression, and Random Forest."""
    try:
        return get_product_forecast(product_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/dead-stock")
def get_dead_stock(days: int = Query(45, ge=14, le=120)):
    """Retrieves dead stock and blocked capital analysis."""
    return analyze_dead_and_slow_stock(days_threshold=days)

@router.get("/expiry")
def get_expiry_risks(days: int = Query(45, ge=7, le=120)):
    """Retrieves FEFO batch shelf-life risks and markdown suggestions."""
    return evaluate_expiry_risks(days_window=days)

@router.get("/llm-status")
def get_llm_status():
    """Returns active LLM provider metadata and configuration status."""
    return LLMEngine.get_active_provider()

@router.post("/chat")
def chat_with_assistant(req: ChatRequest):
    """Answers natural language questions about inventory using LLM Agent Tool Calling with multi-turn memory & local fallback."""
    return LLMEngine.chat(
        query=req.query,
        session_id=req.session_id,
        user_id=req.user_id
    )

@router.get("/conversations")
def list_conversations(
    user_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Lists persistent conversation sessions."""
    return ConversationMemoryManager.list_conversations(user_id=user_id, limit=limit, offset=offset)

@router.get("/conversations/{session_id}")
def get_conversation_details(session_id: str, user_id: Optional[int] = Query(None)):
    """Retrieves full conversation message history for a given session."""
    conv = ConversationMemoryManager.get_conversation_history(session_id=session_id, user_id=user_id)
    if not conv:
        raise HTTPException(status_code=404, detail=f"Conversation session '{session_id}' not found.")
    return conv

@router.delete("/conversations/{session_id}")
def delete_conversation(session_id: str, user_id: Optional[int] = Query(None)):
    """Deletes a conversation session and all related message history."""
    deleted = ConversationMemoryManager.delete_conversation(session_id=session_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Conversation session '{session_id}' not found or unauthorized.")
    return {"status": "DELETED", "session_id": session_id}

@router.get("/feedback")
def get_feedback():
    """Retrieves continuous learning accuracy metrics and historical errors."""
    return get_feedback_metrics()

@router.post("/feedback")
def record_feedback(
    req: FeedbackRecordRequest,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Records real-world outcome for an AI recommendation to train model weights."""
    try:
        return record_recommendation_outcome(
            recommendation_id=req.recommendation_id,
            actual_sales_observed=req.actual_sales,
            outcome_notes=req.notes or ""
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
