import os
from pathlib import Path
from typing import Dict, Any
from mcp_server.tools.file_explorer import resolve_safe_path

try:
    import tree_sitter_languages
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False

LANG_MAP = {
    ".c": "c",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".cc": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript"
}

def extract_function_ast(project_id: str, file_path: str, function_name: str, storage_base: Path) -> Dict[str, Any]:
    """Extracts exact function code, byte offsets, and lines using Tree-sitter."""
    file_real_path = resolve_safe_path(project_id, file_path, storage_base)

    if not file_real_path.exists() or not file_real_path.is_file():
        return {"found": False, "message": f"File not found: {file_path}"}

    with open(file_real_path, "r", encoding="utf-8", errors="ignore") as f:
        code_content = f.read()

    suffix = file_real_path.suffix.lower()
    lang = LANG_MAP.get(suffix, "c")

    if HAS_TREE_SITTER:
        try:
            parser = tree_sitter_languages.get_parser(lang)
            language = tree_sitter_languages.get_language(lang)
            tree = parser.parse(bytes(code_content, "utf8"))

            query_str = """
            (function_definition
                name: (identifier) @name
                (#eq? @name "{func_name}")) @body
            """.replace("{func_name}", function_name)

            query = language.query(query_str)
            matches = query.matches(tree.root_node)

            if matches:
                node = matches[0][1]["body"]
                return {
                    "found": True,
                    "project_id": project_id,
                    "file_path": file_path,
                    "function_name": function_name,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "code_snippet": code_content[node.start_byte:node.end_byte]
                }
        except Exception:
            pass  # Fallback to text matching if tree-sitter query fails

    # Fallback search if tree-sitter is unavailable or didn't match
    lines = code_content.splitlines()
    for idx, line in enumerate(lines):
        if function_name in line and ("(" in line):
            # Capture a simple window for fallback
            start = idx
            end = min(len(lines), start + 30)
            return {
                "found": True,
                "project_id": project_id,
                "file_path": file_path,
                "function_name": function_name,
                "start_line": start + 1,
                "end_line": end,
                "code_snippet": "\n".join(lines[start:end])
            }

    return {"found": False, "message": f"Function '{function_name}' not found in {file_path}"}
