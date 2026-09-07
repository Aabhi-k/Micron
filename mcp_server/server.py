import logging
from typing import Dict, Any, List
from pathlib import Path

# Compatible import across FastMCP, MCP 2.x (MCPServer), and FastMCP v1
try:
    from fastmcp import FastMCP
    MCPServer = FastMCP
except ImportError:
    try:
        from mcp.server.mcpserver import MCPServer
        FastMCP = MCPServer
    except ImportError:
        from mcp.server.fastmcp import FastMCP
        MCPServer = FastMCP

from mcp_server.config import (
    STORAGE_PROJECTS_ROOT,
    MAX_FILE_SIZE_BYTES,
    MCP_SERVER_NAME,
    ALLOWED_EXTENSIONS,
    ensure_storage_directories,
)

# Configure logging
logger = logging.getLogger("mcp_server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# -------------------------------------------------------------------------
# Standalone tool implementations (callable directly or via MCP)
# -------------------------------------------------------------------------
def ping() -> str:
    """Health-check tool to verify that the MCP server is responsive."""
    return "pong"


def get_server_status() -> Dict[str, Any]:
    """Returns the security status, storage boundary, and configuration of the MCP Server."""
    return {
        "status": "healthy",
        "server_name": MCP_SERVER_NAME,
        "sandbox_root": str(STORAGE_PROJECTS_ROOT),
        "max_file_size_bytes": MAX_FILE_SIZE_BYTES,
        "allowed_extensions_count": len(ALLOWED_EXTENSIONS),
        "transport": "stdio/in-process",
        "security_mode": "strict-sandbox",
    }


def read_file(file_path: str) -> Dict[str, Any]:
    """
    Securely reads and returns the content of a file located within the legacy repository.
    Validates path traversal, checks file size, and enforces the sandbox boundary.
    """
    from mcp_server.tools.file_explorer import execute_read_file
    return execute_read_file(file_path)


def list_project_files(project_id: str, sub_dir: str = "") -> List[Dict[str, Any]]:
    """Generates the hierarchical file structure for the UI file tree safely."""
    from mcp_server.tools.file_explorer import safe_list_project_files
    return safe_list_project_files(project_id, sub_dir, STORAGE_PROJECTS_ROOT)


def get_function_ast(project_id: str, file_path: str, function_name: str) -> Dict[str, Any]:
    """Extracts exact function code, byte offsets, and lines using Tree-sitter with secret redaction."""
    from mcp_server.tools.ast_extractor import extract_function_ast
    res = extract_function_ast(project_id, file_path, function_name, STORAGE_PROJECTS_ROOT)
    if res.get("found") and "code_snippet" in res:
        from mcp_server.redaction import redact_code
        sanitized_code, _ = redact_code(res["code_snippet"])
        res["code_snippet"] = sanitized_code
    return res


def get_dependencies(project_id: str, file_path: str) -> Dict[str, Any]:
    """Extracts dependency imports/includes and calls from a source file."""
    from mcp_server.tools.dependency_graph import resolve_file_dependencies
    return resolve_file_dependencies(project_id, file_path, STORAGE_PROJECTS_ROOT)


# -------------------------------------------------------------------------
# Server Factory
# -------------------------------------------------------------------------
def create_server() -> MCPServer:
    """
    Factory function to instantiate and configure the Sandboxed MCP Server.
    Enforces defense-in-depth boundaries and registers allowlisted tools.
    """
    # Ensure physical storage directory exists
    ensure_storage_directories()

    server = FastMCP(
        name=MCP_SERVER_NAME,
        instructions=(
            "Sandboxed MCP Server providing secure, path-validated, "
            "and sanitized access to legacy codebases."
        )
    )

    # Register MCP tools
    @server.tool()
    def ping() -> str:
        """Health-check tool to verify that the MCP server is responsive."""
        logger.info("Executed tool: ping")
        return "pong"

    @server.tool()
    def get_server_status() -> Dict[str, Any]:
        """Returns the security status, storage boundary, and configuration of the MCP Server."""
        logger.info("Executed tool: get_server_status")
        return {
            "status": "healthy",
            "server_name": MCP_SERVER_NAME,
            "sandbox_root": str(STORAGE_PROJECTS_ROOT),
            "max_file_size_bytes": MAX_FILE_SIZE_BYTES,
            "allowed_extensions_count": len(ALLOWED_EXTENSIONS),
            "transport": "stdio/in-process",
            "security_mode": "strict-sandbox",
        }

    @server.tool()
    def read_file(file_path: str) -> Dict[str, Any]:
        """
        Securely reads and returns the content of a file located within the legacy repository.
        Validates path traversal, checks file size, and enforces the sandbox boundary.
        """
        logger.info(f"Executed tool: read_file for '{file_path}'")
        from mcp_server.tools.file_explorer import execute_read_file
        return execute_read_file(file_path)

    @server.tool()
    def list_project_files(project_id: str, sub_dir: str = "") -> List[Dict[str, Any]]:
        """Generates the hierarchical file structure for the UI file tree safely."""
        logger.info(f"Executed tool: list_project_files for '{project_id}', sub_dir='{sub_dir}'")
        from mcp_server.tools.file_explorer import safe_list_project_files
        return safe_list_project_files(project_id, sub_dir, STORAGE_PROJECTS_ROOT)

    @server.tool()
    def get_function_ast(project_id: str, file_path: str, function_name: str) -> Dict[str, Any]:
        """Extracts exact function code, byte offsets, and lines using Tree-sitter."""
        logger.info(f"Executed tool: get_function_ast for '{function_name}' in '{project_id}/{file_path}'")
        from mcp_server.tools.ast_extractor import extract_function_ast
        res = extract_function_ast(project_id, file_path, function_name, STORAGE_PROJECTS_ROOT)
        if res.get("found") and "code_snippet" in res:
            from mcp_server.redaction import redact_code
            sanitized_code, _ = redact_code(res["code_snippet"])
            res["code_snippet"] = sanitized_code
        return res

    @server.tool()
    def get_dependencies(project_id: str, file_path: str) -> Dict[str, Any]:
        """Extracts dependency imports/includes and calls from a source file."""
        logger.info(f"Executed tool: get_dependencies for '{project_id}/{file_path}'")
        from mcp_server.tools.dependency_graph import resolve_file_dependencies
        return resolve_file_dependencies(project_id, file_path, STORAGE_PROJECTS_ROOT)

    return server


# Global server instance
app = create_server()


if __name__ == "__main__":
    logger.info(f"Starting Sandboxed MCP Server [{MCP_SERVER_NAME}] on stdio transport...")
    app.run()
