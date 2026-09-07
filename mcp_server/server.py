import os
from pathlib import Path
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP
from mcp_server.tools.file_explorer import safe_list_project_files, resolve_safe_path, get_project_root
from mcp_server.tools.ast_extractor import extract_function_ast
from mcp_server.tools.dependency_graph import resolve_file_dependencies

mcp = FastMCP("NexSolve-Codebase-Engine")

STORAGE_BASE = Path(os.getenv("STORAGE_BASE", "./storage/projects")).resolve()

@mcp.tool()
def list_project_files(project_id: str, sub_dir: str = "") -> List[Dict[str, Any]]:
    """Generates the hierarchical file structure for the UI file tree."""
    return safe_list_project_files(project_id, sub_dir, STORAGE_BASE)

@mcp.tool()
def get_function_ast(project_id: str, file_path: str, function_name: str) -> Dict[str, Any]:
    """Extracts exact function code, byte offsets, and lines using Tree-sitter."""
    return extract_function_ast(project_id, file_path, function_name, STORAGE_BASE)

@mcp.tool()
def get_dependencies(project_id: str, file_path: str) -> Dict[str, Any]:
    """Extracts dependency imports, includes, and external references."""
    return resolve_file_dependencies(project_id, file_path, STORAGE_BASE)

if __name__ == "__main__":
    mcp.run(transport="stdio")
