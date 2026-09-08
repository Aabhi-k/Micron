import os
import logging
from typing import Dict, Any, AsyncGenerator
from app.core.config import settings

from app.core.observability import observe

logger = logging.getLogger("backend.services.synthesizer")
SYSTEM_PROMPT = """You are a Senior Enterprise Systems Architect and Technical Auditor documentation assistant.
Your objective is to analyze legacy codebase implementations and explain them strictly through the lens of the provided authoritative Business Process Documents (BPD).

STRICT DIRECTIVES:
1. NO HALLUCINATION: If the code does something not mentioned in the BPD, or the BPD mentions a rule not in the code, you MUST highlight this discrepancy. 
2. ZERO EXTERNAL KNOWLEDGE: Base your business logic mapping ONLY on the provided BPD context.
3. STRICT MARKDOWN FORMAT: You must output your response in exact Markdown format. Use actual carriage returns (blank lines) to separate sections. ABSOLUTELY DO NOT type the literal characters "\\n" in your response. Do not use string escape sequences.

REQUIRED OUTPUT STRUCTURE:

## 📄 Component: `[Function Name]`
**Location:** `[File Path]` (Lines [Start]-[End])

### 1. 🎯 Executive Overview
[Provide a concise, 2-3 sentence summary answering the user's query and explaining the primary purpose of the code block.]

### 2. ⚙️ Interface & Parameters
[Use a Markdown table to define parameters, return types, and their purposes. If none exist, state "No explicit parameters."]

### 3. 🧠 Business Logic Mapping
[Provide a step-by-step breakdown of how the code's logic maps directly to the provided BPD rules. Quote the BPD where applicable.]

### 4. 🛡️ Compliance & Deviation Analysis
[Analyze the code against the BPD. Identify any security risks, missing business rules, or undocumented code behaviors (rogue logic). If perfectly compliant, state "Fully Compliant with provided BPD."]
"""

@observe(name="generate_explanation", as_type="generation")
async def generate_explanation(code_data: dict, business_context: str, user_query: str) -> str:
    function_name = code_data.get("function_name", "Unknown Function")
    file_path = code_data.get("file_path", "Unknown File")
    code_snippet = code_data.get("code_snippet", "")
    start_line = code_data.get("start_line", 1)
    end_line = code_data.get("end_line", 1)

    user_prompt = f"""<TARGET_FUNCTION>
Name: {function_name}
File: {file_path}
Lines: {start_line}-{end_line}
</TARGET_FUNCTION>

<USER_QUERY>
{user_query}
</USER_QUERY>

<AUTHORITATIVE_BPD_CONTEXT>
{business_context}
</AUTHORITATIVE_BPD_CONTEXT>

<REDACTED_CODE_SNIPPET>
{code_snippet}
</REDACTED_CODE_SNIPPET>

Execute the documentation synthesis following the strict Markdown schema."""

    openai_api_key = os.getenv("OPENAI_API_KEY")

    if openai_api_key:
        try:
            try:
                from langfuse.openai import AsyncOpenAI
            except ImportError:
                from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=openai_api_key)
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1 
            )
            return response.choices[0].message.content or "No response generated."
        except Exception as e:
            logger.debug(f"OpenAI generation skipped: {e}")

    return f"""## 📄 Component: `{function_name}`
**Location:** `{file_path}` (Lines {start_line}-{end_line})

### 1. 🎯 Executive Overview
The function `{function_name}` implements operational logic for the system.
User Query Addressed: *"{user_query}"*

### 2. ⚙️ Interface & Parameters
*No parameters extracted in fallback mode.*

### 3. 🧠 Business Logic Mapping
Based on authoritative business process guidelines:
{business_context}

### 4. 🛡️ Compliance & Deviation Analysis
- **Execution Range:** Lines {start_line} through {end_line}
- **Status:** Automated analysis unavailable. Fallback template rendered.
"""