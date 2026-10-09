from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field

from backend.auth.roles import get_current_user, require_roles, ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER
from backend.ai.task_state import TaskManager
from backend.ai.tool_registry import ToolRegistry, ToolContext
from backend.ai.agents.supervisor_agent import SupervisorAgent

router = APIRouter(prefix="/api/agent", tags=["Agentic AI Multi-Agent Operations"])

supervisor = SupervisorAgent()


class CreateTaskRequest(BaseModel):
    objective: str = Field(..., min_length=3, description="Natural language business objective")
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional explicit constraints (budget, days, etc.)")


class ApprovalDecisionRequest(BaseModel):
    approval_id: int
    reason: Optional[str] = None


class ToolExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_agent_task(
    req: CreateTaskRequest,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER]))
):
    """
    Submits a natural language business objective.
    The Supervisor Agent interprets the goal, creates a plan, assigns specialized agents,
    evaluates live database tools, and creates approval gateways when needed.
    """
    try:
        task = supervisor.execute_goal(
            objective=req.objective,
            user_id=current_user["id"],
            user_role=current_user.get("role", ROLE_CASHIER),
            custom_constraints=req.constraints
        )
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute agent task: {str(e)}")


@router.get("/tasks")
def list_agent_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Lists recent agent tasks with execution step counts and approval statuses."""
    # Admins and managers see all tasks; cashiers see only their own tasks
    filter_user_id = None if current_user.get("role") in [ROLE_ADMIN, ROLE_MANAGER] else current_user["id"]
    return TaskManager.list_tasks(user_id=filter_user_id, status=status_filter, limit=limit)


@router.get("/tasks/{task_id}")
def get_agent_task_details(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Retrieves full task execution record including plan, step traces, approvals, and outputs."""
    filter_user_id = None if current_user.get("role") in [ROLE_ADMIN, ROLE_MANAGER] else current_user["id"]
    task = TaskManager.get_task(task_id, user_id=filter_user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or access denied.")
    return task


@router.post("/tasks/{task_id}/approve")
def approve_agent_task(
    task_id: str,
    req: ApprovalDecisionRequest,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """
    Human-In-The-Loop Approval:
    Authorizes a pending consequential action (e.g., submitting an approved purchase order).
    """
    try:
        return supervisor.process_approval_decision(
            task_id=task_id,
            approval_id=req.approval_id,
            approved=True,
            user_id=current_user["id"],
            user_role=current_user.get("role", ROLE_MANAGER),
            reason=req.reason
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/reject")
def reject_agent_task(
    task_id: str,
    req: ApprovalDecisionRequest,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """
    Human-In-The-Loop Rejection:
    Rejects a pending consequential action with recorded business justification.
    """
    try:
        return supervisor.process_approval_decision(
            task_id=task_id,
            approval_id=req.approval_id,
            approved=False,
            user_id=current_user["id"],
            user_role=current_user.get("role", ROLE_MANAGER),
            reason=req.reason
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/cancel")
def cancel_agent_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancels a pending or running task."""
    filter_user_id = None if current_user.get("role") in [ROLE_ADMIN, ROLE_MANAGER] else current_user["id"]
    cancelled = TaskManager.cancel_task(task_id, user_id=filter_user_id)
    if not cancelled:
        raise HTTPException(status_code=400, detail="Task cannot be cancelled (either not found or already finished).")
    return {"status": "CANCELLED", "task_id": task_id}


@router.get("/tools")
def list_available_tools(
    current_user: dict = Depends(get_current_user)
):
    """Returns schemas and access permissions for all registered tools."""
    return ToolRegistry.list_tools()


@router.post("/tools/execute")
def execute_tool_directly(
    req: ToolExecuteRequest,
    current_user: dict = Depends(get_current_user)
):
    """Direct, authenticated tool execution through the secure ToolRegistry."""
    ctx = ToolContext(
        user_id=current_user["id"],
        user_role=current_user.get("role", ROLE_CASHIER)
    )
    res = ToolRegistry.execute(req.tool_name, req.arguments, context=ctx)
    if not res.success:
        raise HTTPException(status_code=400, detail=res.error)
    return res


@router.get("/audit-logs")
def get_agent_audit_logs(
    task_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Returns immutable audit logs of agent actions, tool executions, and approvals."""
    from backend.database.db import get_db
    conn = get_db()
    try:
        sql = """
            SELECT l.*, u.full_name as user_full_name
            FROM agent_audit_logs l
            LEFT JOIN users u ON l.user_id = u.id
            WHERE 1=1
        """
        params = []
        if task_id:
            sql += " AND l.task_id = ?"
            params.append(task_id)
        if event_type:
            sql += " AND l.event_type = ?"
            params.append(event_type)

        sql += " ORDER BY l.id DESC LIMIT ?"
        params.append(limit)

        cur = conn.execute(sql, params)
        import json
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            d["details"] = json.loads(d.get("details_json") or "{}")
            rows.append(d)
        return rows
    finally:
        conn.close()


@router.get("/metrics")
def get_agent_observability_metrics(
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Calculates live operational metrics from real task and tool executions."""
    from backend.database.db import get_db
    conn = get_db()
    try:
        # 1. Task counts
        cur_tasks = conn.execute(
            """
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed_tasks,
                SUM(CASE WHEN status = 'WAITING_FOR_APPROVAL' THEN 1 ELSE 0 END) as pending_approvals,
                SUM(CASE WHEN status = 'CANCELLED' THEN 1 ELSE 0 END) as cancelled_tasks
            FROM agent_tasks
            """
        )
        task_stats = dict(cur_tasks.fetchone())

        total = task_stats.get("total_tasks", 0)
        completed = task_stats.get("completed_tasks", 0)
        completion_rate = round((completed / total * 100), 1) if total > 0 else 100.0

        # 2. Tool executions from audit logs
        cur_tools = conn.execute(
            """
            SELECT 
                COUNT(*) as total_tool_calls,
                SUM(CASE WHEN event_type = 'TOOL_EXECUTED' THEN 1 ELSE 0 END) as successful_tool_calls,
                SUM(CASE WHEN event_type = 'TOOL_FAILED' THEN 1 ELSE 0 END) as failed_tool_calls
            FROM agent_audit_logs
            WHERE event_type IN ('TOOL_EXECUTED', 'TOOL_FAILED')
            """
        )
        tool_stats = dict(cur_tools.fetchone())
        tool_total = tool_stats.get("total_tool_calls", 0)
        tool_succ = tool_stats.get("successful_tool_calls", 0)
        tool_success_rate = round((tool_succ / tool_total * 100), 1) if tool_total > 0 else 100.0

        # 3. Model feedback metrics
        from backend.ai.feedback_loop import get_feedback_metrics
        feedback_stats = get_feedback_metrics()

        return {
            "tasks": {
                **task_stats,
                "completion_rate_percent": completion_rate
            },
            "tools": {
                **tool_stats,
                "success_rate_percent": tool_success_rate
            },
            "feedback": feedback_stats
        }
    finally:
        conn.close()

