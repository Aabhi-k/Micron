import json
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from app.services.mcp_client import call_mcp_tool
from app.services.rag_engine import query_business_docs
from app.services.synthesizer import generate_explanation
from app.db.tenant_guard import validate_tenant_id

logger = logging.getLogger("backend.api.v1.chat")
router = APIRouter()

class ExplainRequest(BaseModel):
    project_id: str
    file_path: str
    function_name: str
    user_query: str
    tenant_id: Optional[str] = Field(default=None, description="Target tenant identifier for isolation")

class ChatQueryRequest(BaseModel):
    project_id: str
    query: str
    file_path: Optional[str] = None
    function_name: Optional[str] = None
    tenant_id: Optional[str] = Field(default=None, description="Target tenant identifier for isolation")

def get_effective_tenant_id(body_tenant: Optional[str], header_tenant: Optional[str], default_tenant: str = "default-tenant") -> str:
    """Enforces tenant identification from body, header, or validated default fallback."""
    candidate = body_tenant or header_tenant or default_tenant
    return validate_tenant_id(candidate)

@router.post("/explain-function")
async def explain_function_endpoint(
    req: ExplainRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """Orchestrates MCP AST extraction, RAG business document retrieval, and LLM synthesis with tenant isolation."""
    tenant_id = get_effective_tenant_id(req.tenant_id, x_tenant_id)
    logger.info(
        f"Explaining function '{req.function_name}' in '{req.file_path}' "
        f"for project '{req.project_id}' [Tenant: {tenant_id}]"
    )

    # 1. MCP Call: Extract deterministic AST code block
    mcp_res_raw = await call_mcp_tool("get_function_ast", {
        "project_id": req.project_id,
        "file_path": req.file_path,
        "function_name": req.function_name
    })

    try:
        ast_data = json.loads(mcp_res_raw) if isinstance(mcp_res_raw, str) else mcp_res_raw
    except Exception as e:
        logger.error(f"Failed to parse MCP response: {e}")
        raise HTTPException(status_code=500, detail="Invalid AST response from MCP server.")

    if not ast_data.get("found"):
        raise HTTPException(status_code=404, detail=ast_data.get("message", "Function not found"))

    # 2. Vector DB & RAG Call: Retrieve authoritative business rules strictly scoped to this tenant
    business_context = await query_business_docs(
        tenant_id=tenant_id,
        project_id=req.project_id,
        query=f"{req.function_name} {req.file_path} {req.user_query}"
    )

    # 3. LLM Synthesis
    explanation = await generate_explanation(
        code_data=ast_data,
        business_context=business_context,
        user_query=req.user_query
    )

    return {
        "tenant_id": tenant_id,
        "ast_metadata": {
            "start_line": ast_data.get("start_line"),
            "end_line": ast_data.get("end_line"),
            "file": ast_data.get("file_path"),
            "function_name": ast_data.get("function_name")
        },
        "response": explanation
    }

@router.post("/")
async def chat_endpoint(
    req: ChatQueryRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """General chat & inquiry endpoint across projects and files under tenant isolation."""
    tenant_id = get_effective_tenant_id(req.tenant_id, x_tenant_id)

    if req.file_path and req.function_name:
        return await explain_function_endpoint(
            ExplainRequest(
                project_id=req.project_id,
                file_path=req.file_path,
                function_name=req.function_name,
                user_query=req.query,
                tenant_id=tenant_id
            ),
            x_tenant_id=x_tenant_id
        )

    # General query without specific function
    business_context = await query_business_docs(
        tenant_id=tenant_id,
        project_id=req.project_id,
        query=req.query
    )

    code_data = {
        "function_name": req.function_name or "General",
        "file_path": req.file_path or "Project Level",
        "code_snippet": "",
        "start_line": 0,
        "end_line": 0
    }

    explanation = await generate_explanation(
        code_data=code_data,
        business_context=business_context,
        user_query=req.query
    )

    return {
        "tenant_id": tenant_id,
        "ast_metadata": None,
        "response": explanation
    }
