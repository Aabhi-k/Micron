import sys
import anyio
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_server.server import (
    create_server,
    list_project_files,
    get_function_ast,
    get_dependencies,
)


async def test_all_tools():
    print("=" * 65)
    print("MCP EXTENDED TOOLS VERIFICATION: AST, File Tree & Dependencies")
    print("=" * 65)

    server = create_server()

    # 1. Verify list_project_files direct and via server
    print("\n--- Test 1: Project File Tree Listing (sample_legacy) ---")
    files = list_project_files("sample_legacy", "")
    print(f"Discovered {len(files)} files in 'sample_legacy':")
    for f in files:
        print(f"  - {f['name']} ({f['type']}, {f['size']} bytes, path='{f['path']}')")

    file_names = [f["name"] for f in files]
    assert "sample_auth.c" in file_names, "sample_auth.c must be listed"
    assert "sample_payment.c" in file_names, "sample_payment.c must be listed"
    print("[OK] Direct list_project_files passed.")

    # Call via MCP server tool
    res_list = await server.call_tool("list_project_files", {"project_id": "sample_legacy", "sub_dir": ""})
    res_data = res_list.structured_content.get("result", res_list.structured_content)
    assert len(res_data) >= 2, "MCP call to list_project_files must return entries"
    print("[OK] MCP protocol call_tool('list_project_files') passed.")

    # 2. Verify get_function_ast direct and via server
    print("\n--- Test 2: AST Function Extraction & In-Flight Redaction ---")
    ast_res = get_function_ast("sample_legacy", "sample_auth.c", "authenticate_user")
    print(f"Function found: {ast_res.get('found')}")
    print(f"Lines: {ast_res.get('start_line')} - {ast_res.get('end_line')}")
    print(f"Snippet preview:\n{ast_res.get('code_snippet')}")

    assert ast_res.get("found") is True, "authenticate_user function must be found"
    assert "authenticate_user" in ast_res.get("code_snippet", "")
    # Check that secrets in code snippet are redacted
    assert "AdminPassword#2024" not in ast_res.get("code_snippet", "")
    print("[OK] Direct get_function_ast passed with redactions applied.")

    # Test non-existent function
    missing_ast = get_function_ast("sample_legacy", "sample_auth.c", "non_existent_function_xyz")
    assert missing_ast.get("found") is False
    print("[OK] Graceful fallback on missing function passed.")

    # Call via MCP server tool
    res_ast = await server.call_tool(
        "get_function_ast",
        {"project_id": "sample_legacy", "file_path": "sample_auth.c", "function_name": "authenticate_user"}
    )
    res_ast_data = res_ast.structured_content.get("result", res_ast.structured_content)
    assert res_ast_data.get("found") is True
    print("[OK] MCP protocol call_tool('get_function_ast') passed.")

    # 3. Verify get_dependencies direct and via server
    print("\n--- Test 3: Dependency Graph & Include Resolution ---")
    deps_res = get_dependencies("sample_legacy", "sample_auth.c")
    deps = deps_res.get("dependencies", [])
    print(f"Dependencies detected in sample_auth.c: {deps}")
    assert "stdio.h" in deps, "'stdio.h' must be detected in sample_auth.c"
    assert "string.h" in deps, "'string.h' must be detected in sample_auth.c"
    print("[OK] Direct get_dependencies passed.")

    # Call via MCP server tool
    res_deps = await server.call_tool(
        "get_dependencies",
        {"project_id": "sample_legacy", "file_path": "sample_auth.c"}
    )
    res_deps_data = res_deps.structured_content.get("result", res_deps.structured_content)
    assert "stdio.h" in res_deps_data.get("dependencies", [])
    print("[OK] MCP protocol call_tool('get_dependencies') passed.")

    print("\n" + "=" * 65)
    print("ALL EXTENDED MCP TOOLS VERIFIED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    anyio.run(test_all_tools)
