import re
from pathlib import Path
from typing import Dict, Any, List
from mcp_server.tools.file_explorer import resolve_safe_path

INCLUDE_REGEX = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', re.MULTILINE)
IMPORT_REGEX = re.compile(r'^\s*(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))', re.MULTILINE)

def resolve_file_dependencies(project_id: str, file_path: str, storage_base: Path) -> Dict[str, Any]:
    """Extracts dependency imports/includes and calls from a source file."""
    file_real_path = resolve_safe_path(project_id, file_path, storage_base)

    if not file_real_path.exists() or not file_real_path.is_file():
        return {"project_id": project_id, "file_path": file_path, "dependencies": []}

    with open(file_real_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    dependencies: List[str] = []

    # C/C++ includes
    for match in INCLUDE_REGEX.finditer(content):
        dependencies.append(match.group(1))

    # Python imports
    for match in IMPORT_REGEX.finditer(content):
        dep = match.group(1) or match.group(2)
        if dep:
            dependencies.append(dep)

    return {
        "project_id": project_id,
        "file_path": file_path,
        "dependencies": sorted(list(set(dependencies)))
    }
