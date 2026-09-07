import sys
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def verify_phase_1():
    print("=" * 65)
    print("PHASE 1 VERIFICATION: MCP Development Environment Setup")
    print("=" * 65)

    # 1. Verify mcp package
    try:
        import mcp
        print(f"[OK] MCP SDK installed successfully: version {getattr(mcp, '__version__', 'detected')}")
    except ImportError as e:
        print(f"[FAIL] MCP SDK not installed: {e}")
        return False

    # 2. Verify pydantic
    try:
        import pydantic
        print(f"[OK] Pydantic installed: version {pydantic.__version__}")
    except ImportError as e:
        print(f"[FAIL] Pydantic not installed: {e}")
        return False

    # 3. Verify config & storage directories
    try:
        from mcp_server.config import STORAGE_PROJECTS_ROOT, MAX_FILE_SIZE_BYTES, ensure_storage_directories
        ensure_storage_directories()
        print(f"[OK] Storage projects root verified at: {STORAGE_PROJECTS_ROOT}")
        print(f"[OK] Max file size limit: {MAX_FILE_SIZE_BYTES} bytes ({MAX_FILE_SIZE_BYTES // 1024} KB)")
    except Exception as e:
        print(f"[FAIL] Config verification failed: {e}")
        return False

    # 4. Verify sample legacy codebase
    sample_files = [
        STORAGE_PROJECTS_ROOT / "sample_legacy" / "sample_auth.c",
        STORAGE_PROJECTS_ROOT / "sample_legacy" / "sample_payment.c"
    ]
    all_files_exist = True
    for sample_file in sample_files:
        if sample_file.exists():
            print(f"[OK] Legacy fixture exists: {sample_file.name} ({sample_file.stat().st_size} bytes)")
        else:
            print(f"[WARN] Missing test fixture: {sample_file}")
            all_files_exist = False

    print("=" * 65)
    if all_files_exist:
        print("PHASE 1 VERIFICATION SUCCESSFUL: MCP Environment is ready!")
    else:
        print("PHASE 1 COMPLETED WITH WARNINGS.")
    print("=" * 65)
    return all_files_exist

if __name__ == "__main__":
    success = verify_phase_1()
    sys.exit(0 if success else 1)
