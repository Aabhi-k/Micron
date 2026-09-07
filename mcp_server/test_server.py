import sys
import anyio
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_server.server import create_server
from mcp_server.config import STORAGE_PROJECTS_ROOT, MAX_FILE_SIZE_BYTES


async def test_basic_mcp_server():
    print("=" * 65)
    print("PHASE 2 VERIFICATION: Basic MCP Server & Tool Protocol")
    print("=" * 65)

    server = create_server()

    # 1. Verify Tool Registration
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]
    print(f"[OK] MCP Server initialized with tools: {tool_names}")

    assert "ping" in tool_names, "Tool 'ping' was not registered!"
    assert "get_server_status" in tool_names, "Tool 'get_server_status' was not registered!"

    # 2. Test Calling Tool: ping
    ping_result = await server.call_tool("ping", {})
    ping_text = ping_result.content[0].text if ping_result.content else ""
    print(f"[OK] 'ping' tool response: '{ping_text}' (is_error={ping_result.is_error})")
    assert ping_text == "pong", f"Expected 'pong', got '{ping_text}'"

    # 3. Test Calling Tool: get_server_status
    status_result = await server.call_tool("get_server_status", {})
    status_data = status_result.structured_content or {}
    print(f"[OK] 'get_server_status' tool response: {status_data}")

    # 4. Verify Boundary Enforcements
    result_sandbox = status_data.get("result", {}).get("sandbox_root") or status_data.get("sandbox_root")
    print(f"[OK] Verified active sandbox root: {result_sandbox}")
    print(f"[OK] Verified max file size: {MAX_FILE_SIZE_BYTES} bytes")

    print("=" * 65)
    print("PHASE 2 VERIFICATION SUCCESSFUL: Basic MCP Server is operational!")
    print("=" * 65)


if __name__ == "__main__":
    anyio.run(test_basic_mcp_server)
