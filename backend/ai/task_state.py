import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.database.db import get_db, transaction


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TaskConstraints(BaseModel):
    budget_limit_inr: Optional[float] = None
    days_horizon: int = 7
    lead_time_buffer_days: Optional[int] = None
    priority_categories: List[str] = Field(default_factory=list)
    preferred_suppliers_only: bool = False
    expiry_threshold_days: int = 30
    require_approval_above_inr: float = 0.0  # 0.0 means all PO creations require approval


class TaskStep(BaseModel):
    step_number: int
    agent_name: str
    action_type: str  # PLAN, EXECUTE_TOOL, VERIFY, REASON, APPROVAL_REQUEST
    description: str
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Any] = None
    step_status: StepStatus = StepStatus.PENDING
    reflection: Optional[str] = None
    duration_ms: int = 0


class TaskManager:
    """
    Thread-safe, database-backed state persistence for Agentic AI workflows.
    Tracks tasks, steps, tool traces, approval requests, and audit logs.
    """

    @classmethod
    def create_task(
        cls,
        objective: str,
        user_id: Optional[int] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> str:
        """Creates and persists a new agent task."""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        constraints_json = json.dumps(constraints or {})

        with transaction() as conn:
            conn.execute(
                """
                INSERT INTO agent_tasks (
                    id, user_id, objective, status, constraints_json, current_step, total_steps, approval_status
                ) VALUES (?, ?, ?, ?, ?, 0, 0, 'NOT_REQUIRED')
                """,
                (task_id, user_id, objective.strip(), TaskStatus.PENDING.value, constraints_json)
            )

        cls.log_audit_event(
            task_id=task_id,
            user_id=user_id,
            event_type="TASK_CREATED",
            agent_name="SupervisorAgent",
            details={"objective": objective, "constraints": constraints}
        )
        return task_id

    @classmethod
    def get_task(cls, task_id: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a task with all execution steps, approvals, and audit logs."""
        conn = get_db()
        try:
            query = "SELECT * FROM agent_tasks WHERE id = ?"
            params: List[Any] = [task_id]
            if user_id is not None:
                query += " AND (user_id = ? OR user_id IS NULL)"
                params.append(user_id)

            cur = conn.execute(query, params)
            task_row = cur.fetchone()
            if not task_row:
                return None

            task = dict(task_row)
            task["constraints"] = json.loads(task.get("constraints_json") or "{}")
            task["plan"] = json.loads(task.get("plan_json") or "[]")
            task["final_output"] = json.loads(task.get("final_output_json") or "{}")

            # Attach steps
            cur_steps = conn.execute(
                """
                SELECT * FROM agent_task_steps
                WHERE task_id = ?
                ORDER BY step_number ASC, id ASC
                """,
                (task_id,)
            )
            steps = []
            for s in cur_steps.fetchall():
                step_dict = dict(s)
                step_dict["tool_input"] = json.loads(step_dict.get("tool_input_json") or "null")
                step_dict["tool_output"] = json.loads(step_dict.get("tool_output_json") or "null")
                steps.append(step_dict)
            task["steps"] = steps

            # Attach approvals
            cur_appr = conn.execute(
                """
                SELECT a.*, u.full_name as decided_by_name
                FROM agent_task_approvals a
                LEFT JOIN users u ON a.decided_by_user_id = u.id
                WHERE a.task_id = ?
                ORDER BY a.id DESC
                """,
                (task_id,)
            )
            approvals = []
            for a in cur_appr.fetchall():
                appr_dict = dict(a)
                appr_dict["proposed_payload"] = json.loads(appr_dict.get("proposed_payload_json") or "{}")
                appr_dict["execution_result"] = json.loads(appr_dict.get("execution_result_json") or "null")
                approvals.append(appr_dict)
            task["approvals"] = approvals

            return task
        finally:
            conn.close()

    @classmethod
    def list_tasks(
        cls,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Lists recent tasks with summary metrics."""
        conn = get_db()
        try:
            query = """
                SELECT t.*, u.full_name as user_full_name,
                       (SELECT COUNT(*) FROM agent_task_steps WHERE task_id = t.id) as step_count
                FROM agent_tasks t
                LEFT JOIN users u ON t.user_id = u.id
                WHERE 1=1
            """
            params: List[Any] = []
            if user_id is not None:
                query += " AND (t.user_id = ? OR t.user_id IS NULL)"
                params.append(user_id)
            if status:
                query += " AND t.status = ?"
                params.append(status)

            query += " ORDER BY t.created_at DESC LIMIT ?"
            params.append(limit)

            cur = conn.execute(query, params)
            tasks = []
            for r in cur.fetchall():
                d = dict(r)
                d["constraints"] = json.loads(d.get("constraints_json") or "{}")
                d["plan"] = json.loads(d.get("plan_json") or "[]")
                d["final_output"] = json.loads(d.get("final_output_json") or "{}")
                tasks.append(d)
            return tasks
        finally:
            conn.close()

    @classmethod
    def set_task_plan(cls, task_id: str, plan: List[Dict[str, Any]]) -> None:
        """Stores the structured plan generated by the agent."""
        plan_json = json.dumps(plan)
        with transaction() as conn:
            conn.execute(
                """
                UPDATE agent_tasks SET
                    plan_json = ?,
                    total_steps = ?,
                    status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (plan_json, len(plan), TaskStatus.RUNNING.value, task_id)
            )

    @classmethod
    def update_task_status(
        cls,
        task_id: str,
        status: TaskStatus,
        error_details: Optional[str] = None,
        result_summary: Optional[str] = None,
        final_output: Optional[Dict[str, Any]] = None,
        approval_status: Optional[ApprovalStatus] = None
    ) -> None:
        """Updates task execution status and outcomes."""
        with transaction() as conn:
            updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
            params: List[Any] = [status.value]

            if error_details is not None:
                updates.append("error_details = ?")
                params.append(error_details)
            if result_summary is not None:
                updates.append("result_summary = ?")
                params.append(result_summary)
            if final_output is not None:
                updates.append("final_output_json = ?")
                params.append(json.dumps(final_output))
            if approval_status is not None:
                updates.append("approval_status = ?")
                params.append(approval_status.value)
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                updates.append("completed_at = CURRENT_TIMESTAMP")

            params.append(task_id)
            query = f"UPDATE agent_tasks SET {', '.join(updates)} WHERE id = ?"
            conn.execute(query, params)

    @classmethod
    def add_task_step(
        cls,
        task_id: str,
        step_number: int,
        agent_name: str,
        action_type: str,
        description: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_input: Optional[Dict[str, Any]] = None,
        tool_output: Optional[Any] = None,
        step_status: StepStatus = StepStatus.PENDING,
        reflection: Optional[str] = None,
        duration_ms: int = 0
    ) -> int:
        """Records an execution step for full auditability and frontend visualization."""
        tool_in_json = json.dumps(tool_input) if tool_input is not None else None
        tool_out_json = json.dumps(tool_output) if tool_output is not None else None
        effective_reflection = reflection or description

        with transaction() as conn:
            cur = conn.execute(
                """
                INSERT INTO agent_task_steps (
                    task_id, step_number, agent_name, action_type, tool_name,
                    tool_input_json, tool_output_json, step_status, reflection, duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id, step_number, agent_name, action_type, tool_name,
                    tool_in_json, tool_out_json, step_status.value, effective_reflection, duration_ms
                )
            )
            step_id = cur.lastrowid
            conn.execute(
                "UPDATE agent_tasks SET current_step = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (step_number, task_id)
            )
            return step_id

    @classmethod
    def update_task_step(
        cls,
        step_id: int,
        step_status: StepStatus,
        tool_output: Optional[Any] = None,
        reflection: Optional[str] = None,
        duration_ms: int = 0
    ) -> None:
        """Updates a step upon completion."""
        with transaction() as conn:
            tool_out_json = json.dumps(tool_output) if tool_output is not None else None
            conn.execute(
                """
                UPDATE agent_task_steps SET
                    step_status = ?,
                    tool_output_json = COALESCE(?, tool_output_json),
                    reflection = COALESCE(?, reflection),
                    duration_ms = ?,
                    created_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (step_status.value, tool_out_json, reflection, duration_ms, step_id)
            )

    @classmethod
    def request_approval(
        cls,
        task_id: str,
        action_name: str,
        proposed_payload: Dict[str, Any],
        justification: str,
        estimated_cost: float,
        requested_by_agent: str
    ) -> int:
        """Pauses a task and creates a human approval request."""
        with transaction() as conn:
            cur = conn.execute(
                """
                INSERT INTO agent_task_approvals (
                    task_id, action_name, proposed_payload_json, justification,
                    estimated_cost, status, requested_by_agent
                ) VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
                """,
                (
                    task_id,
                    action_name,
                    json.dumps(proposed_payload),
                    justification,
                    estimated_cost,
                    requested_by_agent
                )
            )
            approval_id = cur.lastrowid

            conn.execute(
                """
                UPDATE agent_tasks SET
                    status = ?,
                    approval_status = 'PENDING',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (TaskStatus.WAITING_FOR_APPROVAL.value, task_id)
            )

        cls.log_audit_event(
            task_id=task_id,
            user_id=None,
            event_type="APPROVAL_REQUESTED",
            agent_name=requested_by_agent,
            details={
                "approval_id": approval_id,
                "action_name": action_name,
                "estimated_cost": estimated_cost,
                "justification": justification
            }
        )
        return approval_id

    @classmethod
    def resolve_approval(
        cls,
        task_id: str,
        approval_id: int,
        approved: bool,
        user_id: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Resolves an approval decision by an authenticated user."""
        status_val = "APPROVED" if approved else "REJECTED"
        task_approval_val = ApprovalStatus.APPROVED.value if approved else ApprovalStatus.REJECTED.value

        with transaction() as conn:
            cur = conn.execute(
                "SELECT * FROM agent_task_approvals WHERE id = ? AND task_id = ?",
                (approval_id, task_id)
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Approval request {approval_id} not found for task {task_id}.")
            if row["status"] != "PENDING":
                raise ValueError(f"Approval request {approval_id} is already {row['status']}.")

            conn.execute(
                """
                UPDATE agent_task_approvals SET
                    status = ?,
                    decided_by_user_id = ?,
                    decision_reason = ?,
                    decided_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status_val, user_id, reason, approval_id)
            )

            conn.execute(
                """
                UPDATE agent_tasks SET
                    approval_status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (task_approval_val, task_id)
            )

        cls.log_audit_event(
            task_id=task_id,
            user_id=user_id,
            event_type="APPROVAL_DECIDED",
            agent_name="SupervisorAgent",
            details={
                "approval_id": approval_id,
                "decision": status_val,
                "reason": reason
            }
        )

        return {
            "task_id": task_id,
            "approval_id": approval_id,
            "status": status_val,
            "decided_by_user_id": user_id,
            "reason": reason
        }

    @classmethod
    def cancel_task(cls, task_id: str, user_id: Optional[int] = None, reason: str = "User cancelled") -> bool:
        """Cancels a pending or running task."""
        with transaction() as conn:
            cur = conn.execute("SELECT status FROM agent_tasks WHERE id = ?", (task_id,))
            row = cur.fetchone()
            if not row:
                return False
            if row["status"] in [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value]:
                return False

            conn.execute(
                """
                UPDATE agent_tasks SET
                    status = ?,
                    error_details = ?,
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (TaskStatus.CANCELLED.value, f"Cancelled: {reason}", task_id)
            )

        cls.log_audit_event(
            task_id=task_id,
            user_id=user_id,
            event_type="TASK_CANCELLED",
            agent_name="SupervisorAgent",
            details={"reason": reason}
        )
        return True

    @classmethod
    def log_audit_event(
        cls,
        task_id: Optional[str],
        user_id: Optional[int],
        event_type: str,
        agent_name: Optional[str],
        details: Dict[str, Any]
    ) -> None:
        """Records an immutable audit event."""
        try:
            with transaction() as conn:
                conn.execute(
                    """
                    INSERT INTO agent_audit_logs (
                        task_id, user_id, event_type, agent_name, details_json
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (task_id, user_id, event_type, agent_name, json.dumps(details))
                )
        except Exception as e:
            print(f"[TaskManager Audit Error] {e}")
