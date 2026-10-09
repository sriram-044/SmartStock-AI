import time
import json
import logging
from typing import Dict, Any, List, Optional, Type, Callable
from pydantic import BaseModel, Field, ValidationError

from backend.database.db import get_db, transaction
from backend.auth.roles import ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER
from backend.ai.task_state import TaskManager

logger = logging.getLogger("StockMind.ToolRegistry")


class ToolContext(BaseModel):
    user_id: Optional[int] = None
    user_role: str = ROLE_CASHIER
    task_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class ToolResult(BaseModel):
    success: bool
    tool_name: str
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool:
    """Base class for all registered Agentic AI tools."""
    name: str = ""
    description: str = ""
    input_schema: Type[BaseModel] = BaseModel
    output_schema: Optional[Type[BaseModel]] = None
    required_roles: List[str] = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]
    is_consequential: bool = False  # If True, mutates database or financial state
    requires_approval: bool = False  # If True, must not be run without explicit user approval

    def run(self, validated_input: BaseModel, context: ToolContext) -> Any:
        """Subclasses must implement their business logic here."""
        raise NotImplementedError


class ToolRegistry:
    """
    Central, secure Tool Registry enforcing:
    1. Strict Pydantic input/output validation
    2. Role-based backend authorization checks
    3. Consequential action gating & idempotency tracking
    4. Execution timing, error containment, and audit logging
    """

    _tools: Dict[str, BaseTool] = {}
    _executed_idempotency_keys: Dict[str, ToolResult] = {}

    @classmethod
    def register(cls, tool_instance: BaseTool) -> None:
        """Registers a tool instance in the registry."""
        cls._tools[tool_instance.name] = tool_instance

    @classmethod
    def get(cls, name: str) -> Optional[BaseTool]:
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> List[Dict[str, Any]]:
        """Returns schemas and metadata for all registered tools."""
        out = []
        for name, t in cls._tools.items():
            schema_json = t.input_schema.model_json_schema() if hasattr(t.input_schema, "model_json_schema") else {}
            out.append({
                "name": t.name,
                "description": t.description,
                "required_roles": t.required_roles,
                "is_consequential": t.is_consequential,
                "requires_approval": t.requires_approval,
                "parameters": schema_json
            })
        return out

    @classmethod
    def execute(
        cls,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[ToolContext] = None
    ) -> ToolResult:
        """
        Validates, authorizes, and executes a tool deterministically.
        """
        start_time = time.time()
        ctx = context or ToolContext()

        tool = cls.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=f"Tool '{tool_name}' is not registered in the system.",
                execution_time_ms=0
            )

        # 1. Authorization check
        effective_role = ctx.user_role.lower()
        if effective_role not in [r.lower() for r in tool.required_roles] and effective_role != ROLE_ADMIN:
            err_msg = f"Unauthorized: Role '{ctx.user_role}' cannot execute consequential tool '{tool_name}'. Requires one of: {tool.required_roles}"
            logger.warning(err_msg)
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=err_msg,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

        # 2. Idempotency Check for Consequential Operations
        if tool.is_consequential and ctx.idempotency_key:
            if ctx.idempotency_key in cls._executed_idempotency_keys:
                cached = cls._executed_idempotency_keys[ctx.idempotency_key]
                logger.info(f"Idempotency cache hit for key: {ctx.idempotency_key}")
                return cached

        # 3. Input Validation via Pydantic
        try:
            validated_input = tool.input_schema(**arguments)
        except ValidationError as ve:
            error_details = "; ".join([f"{e['loc']}: {e['msg']}" for e in ve.errors()])
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=f"Invalid arguments for tool '{tool_name}': {error_details}",
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=f"Failed to parse arguments for '{tool_name}': {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

        # 4. Safe Deterministic Execution
        try:
            result_data = tool.run(validated_input, ctx)
            elapsed_ms = int((time.time() - start_time) * 1000)

            res = ToolResult(
                success=True,
                tool_name=tool_name,
                data=result_data,
                execution_time_ms=elapsed_ms
            )

            # Save idempotency key if present
            if tool.is_consequential and ctx.idempotency_key:
                cls._executed_idempotency_keys[ctx.idempotency_key] = res

            # Log audit event
            if tool.is_consequential or ctx.task_id:
                TaskManager.log_audit_event(
                    task_id=ctx.task_id,
                    user_id=ctx.user_id,
                    event_type="TOOL_EXECUTED",
                    agent_name="ToolRegistry",
                    details={
                        "tool_name": tool_name,
                        "success": True,
                        "duration_ms": elapsed_ms,
                        "is_consequential": tool.is_consequential
                    }
                )

            return res

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.exception(f"Error executing tool '{tool_name}': {e}")

            TaskManager.log_audit_event(
                task_id=ctx.task_id,
                user_id=ctx.user_id,
                event_type="TOOL_FAILED",
                agent_name="ToolRegistry",
                details={
                    "tool_name": tool_name,
                    "error": str(e),
                    "duration_ms": elapsed_ms
                }
            )

            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=str(e),
                execution_time_ms=elapsed_ms
            )
