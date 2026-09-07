import logging
from typing import List, Dict, Any

logger = logging.getLogger("backend.services.parser")

def extract_symbols_from_ast(ast_data: Dict[str, Any]) -> Dict[str, Any]:
    """Formats and summarizes extracted AST nodes into a structured symbol table."""
    return {
        "function_name": ast_data.get("function_name"),
        "file_path": ast_data.get("file_path"),
        "start_line": ast_data.get("start_line"),
        "end_line": ast_data.get("end_line"),
        "has_snippet": bool(ast_data.get("code_snippet")),
    }
