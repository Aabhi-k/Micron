import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths calculation
MCP_SERVER_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = MCP_SERVER_DIR.parent

# Load environment variables from backend/.env or root .env
dotenv_candidates = [
    WORKSPACE_ROOT / "backend" / ".env",
    WORKSPACE_ROOT / ".env"
]
for env_path in dotenv_candidates:
    if env_path.exists():
        load_dotenv(env_path)
        break

# Storage root for uploaded/cloned legacy codebases
DEFAULT_STORAGE_ROOT = WORKSPACE_ROOT / "storage" / "projects"
STORAGE_ROOT_ENV = os.getenv("STORAGE_PROJECTS_ROOT") or os.getenv("LEGACY_REPO_ROOT")

if STORAGE_ROOT_ENV:
    STORAGE_PROJECTS_ROOT = Path(STORAGE_ROOT_ENV).resolve()
else:
    STORAGE_PROJECTS_ROOT = DEFAULT_STORAGE_ROOT.resolve()

# Security thresholds
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_BYTES", 1024 * 1024))  # 1 MB default
MCP_SERVER_NAME = os.getenv("MCP_SERVER_NAME", "legacy-code-security-server")

# Supported file extensions for code analysis
ALLOWED_EXTENSIONS = {
    ".c", ".h", ".cpp", ".hpp", ".cc",
    ".py", ".java", ".js", ".ts", ".jsx", ".tsx",
    ".sql", ".sh", ".bash", ".txt", ".md",
    ".json", ".yaml", ".yml", ".xml", ".properties", ".ini"
}

# Symlink security policy:
# If False: Reject all symlinks unconditionally (highest security).
# If True: Allow symlinks ONLY if their canonical resolved target stays inside STORAGE_PROJECTS_ROOT.
ALLOW_INTERNAL_SYMLINKS = os.getenv("ALLOW_INTERNAL_SYMLINKS", "true").lower() in ("true", "1", "yes")


def ensure_storage_directories() -> None:
    """Ensure that the storage directory exists on disk."""
    STORAGE_PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
