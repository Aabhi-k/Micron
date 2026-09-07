import logging
from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse
from app.core.observability import observe

logger = logging.getLogger("backend.api")

router = APIRouter()

# Pydantic model for the incoming request from React
class DocumentationQuery(BaseModel):
    query: str
    target_path: str = "" # Optional: specific file or folder they are asking about
    code_version: str = "main" # For the code base versions requirement

@router.post("/generate-docs", response_class=PlainTextResponse)
@observe(name="generate_docs_prototype", as_type="generation")
async def generate_documentation(request: DocumentationQuery):
    """
    Main orchestration endpoint.
    Receives what the user wants to understand, orchestrates RAG and MCP, 
    and returns Markdown documentation.
    """
    logger.info(f"Received query: {request.query} for path: {request.target_path}")

    # STEP 1: Execute RAG
    # Query Qdrant for relevant Business Process Documentation
    bpd_context = "Mock BPD context: This module handles transaction processing."
    
    # STEP 2: Execute MCP
    # Use the MCP client to read the relevant legacy code
    legacy_code_context = "Mock Code: function processTx() { return true; }"

    # STEP 3: LLM Synthesis (with Langfuse tracking)
    # Pass both bpd_context and legacy_code_context to the LLM
    
    # Mock Response
    generated_md = f"""# Documentation Report
    
## Query Analysis
You asked about: **{request.query}**

## Business Logic (from BPD)
{bpd_context}

## Code Implementation
```javascript
{legacy_code_context}
```

## Summary
The legacy code correctly implements the transaction processing business rule.
"""

    # STEP 4: Save Response to DB (for caching / history)
    
    return generated_md


