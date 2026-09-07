import json
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.mcp_client import call_mcp_tool
from app.services.rag_engine import query_business_docs
from app.services.synthesizer import generate_explanation

logger = logging.getLogger("backend.api.v1.chat")
router = APIRouter()

class ExplainRequest(BaseModel):
    project_id: str
    file_path: str
    function_name: str
    user_query: str

class ChatQueryRequest(BaseModel):
    project_id: str
    query: str
    file_path: Optional[str] = None
    function_name: Optional[str] = None

@router.post("/explain-function")
async def explain_function_endpoint(req: ExplainRequest):
    """Orchestrates MCP AST extraction, RAG business document retrieval, and LLM synthesis."""
    logger.info(f"Explaining function {req.function_name} in {req.file_path} for project {req.project_id}")

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

    # 2. Vector DB Call: Retrieve relevant business rules for this project
    business_context = await query_business_docs(
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
        "ast_metadata": {
            "start_line": ast_data.get("start_line"),
            "end_line": ast_data.get("end_line"),
            "file": ast_data.get("file_path"),
            "function_name": ast_data.get("function_name")
        },
        "response": explanation
    }

@router.post("/")
async def chat_endpoint(req: ChatQueryRequest):
    """General chat & inquiry endpoint across projects and files."""
    if req.file_path and req.function_name:
        return await explain_function_endpoint(
            ExplainRequest(
                project_id=req.project_id,
                file_path=req.file_path,
                function_name=req.function_name,
                user_query=req.query
            )
        )

    # General query without specific function
    business_context = await query_business_docs(
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
        "ast_metadata": None,
        "response": explanation
    }
