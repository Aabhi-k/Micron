import os
import json
import logging
from app.core.config import settings
from app.core.observability import observe

logger = logging.getLogger("backend.services.mcp_client")

def get_server_params():
    from mcp import StdioServerParameters
    from pathlib import Path
    
    # Resolve the root repository path (two levels up from backend/app)
    repo_root = str(Path(__file__).resolve().parent.parent.parent.parent)
    env = os.environ.copy()
    env["STORAGE_BASE"] = str(settings.STORAGE_BASE)
    
    # Inject repo root into PYTHONPATH so 'python -m mcp_server.server' works!
    env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{env.get('PYTHONPATH', '')}"

    return StdioServerParameters(
        command=settings.MCP_SERVER_COMMAND,
        args=settings.MCP_SERVER_ARGS,
        env=env
    )

@observe(name="call_mcp_tool", as_type="tool")
async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Invokes a tool on the sandboxed MCP server via stdio transport."""
    try:
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client
        server_params = get_server_params()

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                if result and result.content:
                    first_content = result.content[0]
                    # content can be TextContent with .text
                    return getattr(first_content, "text", str(first_content))
                return json.dumps({"status": "no content"})
    except Exception as e:
        logger.warning(f"MCP subprocess invocation failed: {e}. Attempting direct tool execution...")
        # Direct execution fallback for environments without stdio mcp runners
        try:
            from mcp_server.server import list_project_files, get_function_ast, get_dependencies
            tool_map = {
                "list_project_files": list_project_files,
                "get_function_ast": get_function_ast,
                "get_dependencies": get_dependencies
            }
            if tool_name in tool_map:
                res = tool_map[tool_name](**arguments)
                return json.dumps(res)
        except Exception as direct_err:
            logger.error(f"Direct fallback also failed: {direct_err}")
        raise RuntimeError(f"Failed to execute MCP tool '{tool_name}': {e}")
