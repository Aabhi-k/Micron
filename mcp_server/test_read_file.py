import sys
import anyio
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_server.server import create_server
from mcp_server.models import ReadFileResponse


async def test_read_file_tool():
    print("=" * 65)
    print("PHASE 3 VERIFICATION: Secure read_file Tool Implementation")
    print("=" * 65)

    server = create_server()

    # 1. Verify read_file registration
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]
    print(f"[OK] Available MCP tools: {tool_names}")
    assert "read_file" in tool_names, "Tool 'read_file' must be registered on the MCP server!"

    # 2. Test reading a valid legacy file: sample_auth.c
    print("\n--- Test 1: Reading Legitimate Legacy File (sample_auth.c) ---")
    auth_result = await server.call_tool("read_file", {"file_path": "sample_legacy/sample_auth.c"})
    data = auth_result.structured_content.get("result", auth_result.structured_content)

    print(f"Status: {data.get('status')}")
    print(f"File Path: {data.get('file_path')}")
    print(f"File Size: {data.get('size_bytes')} bytes")
    print(f"Code Preview (first 100 chars): {data.get('sanitized_code', '')[:100]}...")

    assert data.get("status") == "success", "Expected status 'success' for existing file"
    assert "authenticate_user" in data.get("sanitized_code", ""), "Failed to read file content"
    assert data.get("size_bytes") > 0, "Expected non-zero file size"

    # Validate against Pydantic schema
    validated_auth = ReadFileResponse(**data)
    print(f"[OK] Response conforms to Pydantic ReadFileResponse schema: {validated_auth.file_path}")

    # 3. Test reading another valid file: sample_payment.c
    print("\n--- Test 2: Reading Legitimate Legacy File (sample_payment.c) ---")
    pay_result = await server.call_tool("read_file", {"file_path": "sample_legacy/sample_payment.c"})
    pay_data = pay_result.structured_content.get("result", pay_result.structured_content)
    assert pay_data.get("status") == "success"
    assert "process_legacy_payment" in pay_data.get("sanitized_code", "")
    print(f"[OK] Successfully read sample_payment.c ({pay_data.get('size_bytes')} bytes)")

    # 4. Test reading non-existent file
    print("\n--- Test 3: Reading Non-Existent File (graceful error handling) ---")
    ghost_result = await server.call_tool("read_file", {"file_path": "sample_legacy/non_existent.c"})
    ghost_data = ghost_result.structured_content.get("result", ghost_result.structured_content)
    print(f"Response status: {ghost_data.get('status')}")
    print(f"Error message: {ghost_data.get('error_message')}")
    assert ghost_data.get("status") == "error", "Expected error status for missing file"
    assert "not found" in ghost_data.get("error_message", "").lower()
    print("[OK] Non-existent file handled safely without crashing.")

    # 5. Test reading a directory path as a file
    print("\n--- Test 4: Rejecting Directory as File Target ---")
    dir_result = await server.call_tool("read_file", {"file_path": "sample_legacy"})
    dir_data = dir_result.structured_content.get("result", dir_result.structured_content)
    print(f"Response status: {dir_data.get('status')}")
    print(f"Error message: {dir_data.get('error_message')}")
    assert dir_data.get("status") == "error", "Expected error status when targeting directory"
    assert "not a regular file" in dir_data.get("error_message", "").lower()
    print("[OK] Directory target rejected safely.")

    print("\n" + "=" * 65)
    print("PHASE 3 VERIFICATION SUCCESSFUL: read_file tool is robust & operational!")
    print("=" * 65)


if __name__ == "__main__":
    anyio.run(test_read_file_tool)
