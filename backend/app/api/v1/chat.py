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

async def explain_function_internal(
    req: ExplainRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """Orchestrates MCP AST extraction, RAG business document retrieval, and LLM synthesis with tenant isolation."""
    tenant_id = get_effective_tenant_id(req.tenant_id, x_tenant_id)
    logger.info(
        f"Explaining function '{req.function_name}' in '{req.file_path}' "
        f"for project '{req.project_id}' [Tenant: {tenant_id}]"
    )

    # 1. MCP Call: Extract precisely the AST function snippet via new MCP tool
    mcp_res_raw = await call_mcp_tool("get_function_ast", {
        "project_id": req.project_id,
        "file_path": req.file_path,
        "function_name": req.function_name
    })

    try:
        ast_data = json.loads(mcp_res_raw) if isinstance(mcp_res_raw, str) else mcp_res_raw
    except Exception as e:
        logger.error(f"Failed to parse MCP response: {e}")
        raise HTTPException(status_code=500, detail="Invalid response from MCP server.")

    # If the function wasn't found in the AST, gracefully fall back to full file read or return an error
    if ast_data.get("status") == "error" or not ast_data.get("found"):
        raise HTTPException(status_code=404, detail=ast_data.get("error_message", f"Function {req.function_name} not found in AST."))

    # 2. Vector DB & RAG Call: Retrieve authoritative business rules strictly scoped to this tenant
    business_context = await query_business_docs(
        tenant_id=tenant_id,
        project_id=req.project_id,
        query=f"{req.function_name} {req.file_path} {req.user_query}"
    )

    # 3. LLM Synthesis using the exact AST bounds
    code_data = {
        "function_name": req.function_name,
        "file_path": req.file_path,
        "code_snippet": ast_data.get("code_snippet", ""),
        "start_line": ast_data.get("start_line", 1),
        "end_line": ast_data.get("end_line", 1)
    }
    
    explanation = await generate_explanation(
        code_data=code_data,
        business_context=business_context,
        user_query=req.user_query
    )

    return {
        "tenant_id": tenant_id,
        "ast_metadata": {
            "file": req.file_path,
            "function_name": req.function_name,
            "redactions": ast_data.get("redactions_applied", [])
        },
        "response": explanation
    }

async def auto_discover_code(query: str, authority_level: int = 3):
    import httpx
    from qdrant_client import QdrantClient
    from qdrant_client.http import models

    # Embed the search query using Sentence Transformers
    from app.services.embeddings import embedding_service
    try:
        query_vector, _ = await embedding_service.get_embedding(query)
    except Exception as e:
        logger.error(f"Embedding Error in auto_discover_code: {e}")
        return None, None, None
        
    try:
        q_client = QdrantClient(url="http://localhost:6333")
        rbac_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="minimum_authority_level",
                    range=models.Range(lte=authority_level)
                )
            ]
        )
        search_result = q_client.query_points(
            collection_name="codebase_index",
            query=query_vector,
            query_filter=rbac_filter,
            limit=1,
            with_payload=True
        ).points
        
        if search_result:
            payload = search_result[0].payload
            file_path = payload.get("file_path", "")
            functions = payload.get("functions", [])
            function_name = functions[0] if functions else "Unknown Function"
            
            storage_root = "/home/hb/code/mi/storage/projects/"
            if file_path.startswith(storage_root):
                file_path = file_path[len(storage_root):]
                
            # Extract the project_id (first directory component) and the relative file path
            parts = file_path.split("/", 1)
            if len(parts) == 2:
                project_id = parts[0]
                file_path = parts[1]
            else:
                project_id = ""
                
            return project_id, file_path, function_name
    except Exception as e:
        logger.warning(f"Auto-discovery failed: {e}")
        
    return None, None, None

@router.post("/")
async def chat_endpoint(
    req: ChatQueryRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """General chat & inquiry endpoint across projects and files under tenant isolation."""
    tenant_id = get_effective_tenant_id(req.tenant_id, x_tenant_id)

    # 1. Auto-discover the best code file if the user didn't specify one
    if not req.file_path:
        logger.info(f"Auto-discovering codebase index for query: '{req.query}'")
        discovered_proj, discovered_path, discovered_func = await auto_discover_code(req.query)
        if discovered_path:
            logger.info(f"Discovered relevant file: {discovered_proj}/{discovered_path}")
            if discovered_proj:
                req.project_id = discovered_proj
            req.file_path = discovered_path
            req.function_name = discovered_func

    # 2. If we have a file (either provided or auto-discovered), run the full MCP + BPD pipeline
    if req.file_path and req.function_name:
        return await explain_function_internal(
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
