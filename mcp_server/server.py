import logging
from typing import Dict, Any

# Compatible import across MCP 2.x (MCPServer) and FastMCP v1
try:
    from mcp.server.mcpserver import MCPServer
    FastMCP = MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP

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

    # -------------------------------------------------------------------------
    # Core Diagnostics & Boundary Status Tools
    # -------------------------------------------------------------------------
    @server.tool()
    def ping() -> str:
        """
        Health-check tool to verify that the MCP server is responsive.
        """
        logger.info("Executed tool: ping")
        return "pong"

    @server.tool()
    def get_server_status() -> Dict[str, Any]:
        """
        Returns the security status, storage boundary, and configuration of the MCP Server.
        """
        logger.info("Executed tool: get_server_status")
        return {
            "status": "healthy",
            "server_name": MCP_SERVER_NAME,
            "sandbox_root": str(STORAGE_PROJECTS_ROOT),
            "max_file_size_bytes": MAX_FILE_SIZE_BYTES,
            "allowed_extensions_count": len(ALLOWED_EXTENSIONS),
            "transport": "stdio/in-process",
            "security_mode": "strict-sandbox"
        }

    # -------------------------------------------------------------------------
    # Core Secure Code Access Tools
    # -------------------------------------------------------------------------
    @server.tool()
    def read_file(file_path: str) -> Dict[str, Any]:
        """
        Securely reads and returns the content of a file located within the legacy repository.
        Validates path traversal, checks file size, and enforces the sandbox boundary.

        Args:
            file_path: Relative path to the file inside the legacy repository (e.g. 'sample_legacy/sample_auth.c').

        Returns:
            Dict with status, file_path, sanitized_code, redactions_applied, size_bytes, error_message.
        """
        logger.info(f"Executed tool: read_file for '{file_path}'")
        from mcp_server.tools.file_explorer import execute_read_file
        return execute_read_file(file_path)

    return server



# Global server instance
app = create_server()


if __name__ == "__main__":
    logger.info(f"Starting Sandboxed MCP Server [{MCP_SERVER_NAME}] on stdio transport...")
    app.run()
