import sys
import os
import anyio
from unittest.mock import patch
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_server.server import create_server
from mcp_server.security import validate_and_resolve_path, SymlinkSecurityError
from mcp_server.config import STORAGE_PROJECTS_ROOT

ORIGINAL_RESOLVE = Path.resolve


def selective_mock_resolve(self, *args, **kwargs):
    str_self = str(self).replace("\\", "/")
    if "fake_symlink" in str_self or "symlink_to_cmd" in str_self:
        # Simulate resolving an external symlink pointing outside the sandbox
        return Path("C:/Windows/System32/drivers/etc/hosts").resolve()
    return ORIGINAL_RESOLVE(self, *args, **kwargs)


def looping_mock_resolve(self, *args, **kwargs):
    str_self = str(self).replace("\\", "/")
    if "looping_link" in str_self:
        raise RuntimeError("Symlink loop detected: maximum recursion depth exceeded")
    return ORIGINAL_RESOLVE(self, *args, **kwargs)


async def test_symlink_security():
    print("=" * 65)
    print("PHASE 5 VERIFICATION: Symbolic Link Security Suite")
    print("=" * 65)

    server = create_server()

    # 1. Attempt real OS symlink creation if OS privileges allow
    real_symlink_tested = False
    test_link_external = STORAGE_PROJECTS_ROOT / "sample_legacy" / "test_external_link.c"
    external_target = PROJECT_ROOT / "backend" / ".env"

    try:
        os.symlink(external_target, test_link_external)
        real_symlink_tested = True
        print("[INFO] OS permitted real symlink creation on disk.")
    except (OSError, NotImplementedError):
        print("[INFO] Standard Windows user permissions detected (no symlink creation privilege).")
        print("[INFO] Testing security behavior via kernel resolution simulation.")

    if real_symlink_tested:
        try:
            print("\n--- Testing Real External Symlink Breakout ---")
            res = await server.call_tool("read_file", {"file_path": "sample_legacy/test_external_link.c"})
            data = res.structured_content.get("result", res.structured_content)
            print(f"Status: {data.get('status')}")
            print(f"Error Caught: {data.get('error_message')}")
            assert data.get("status") == "error", "External symlink must be blocked!"
            assert "symlink" in data.get("error_message", "").lower() or "outside" in data.get("error_message", "").lower()
            print("[OK] Real external symlink successfully neutralized.")
        finally:
            if test_link_external.exists() or test_link_external.is_symlink():
                os.unlink(test_link_external)

    # 2. Comprehensive Cross-Platform Mock Symlink Audit
    print("\n--- Test A: Symlink Pointing Outside Repository (e.g. to C:/Windows/...) ---")
    with patch("mcp_server.security.detect_symlink_components", return_value=True), \
         patch.object(Path, "resolve", selective_mock_resolve):
        try:
            validate_and_resolve_path("sample_legacy/fake_symlink.c")
            assert False, "SECURITY FAILED: External symlink should have been rejected!"
        except SymlinkSecurityError as e:
            print(f"[OK] Caught external symlink breakout: {e}")

    print("\n--- Test B: Internal Symlink under Strict Policy (allow_internal_symlinks=False) ---")
    with patch("mcp_server.security.detect_symlink_components", return_value=True):
        try:
            validate_and_resolve_path(
                "sample_legacy/internal_link.c",
                allow_internal_symlinks=False
            )
            assert False, "Strict policy must reject all symlinks!"
        except SymlinkSecurityError as e:
            print(f"[OK] Caught internal symlink under strict policy: {e}")

    print("\n--- Test C: Circular Symlink Loop Handling ---")
    with patch.object(Path, "resolve", looping_mock_resolve):
        try:
            validate_and_resolve_path("sample_legacy/looping_link.c")
            assert False, "Circular symlink should have raised SymlinkSecurityError!"
        except SymlinkSecurityError as e:
            print(f"[OK] Caught circular symlink loop: {e}")

    # 3. Test read_file tool with simulated malicious symlink request
    print("\n--- Test D: End-to-End read_file with Symlink Attack ---")
    with patch("mcp_server.security.detect_symlink_components", return_value=True), \
         patch.object(Path, "resolve", selective_mock_resolve):
        res = await server.call_tool("read_file", {"file_path": "sample_legacy/symlink_to_cmd.exe"})
        data = res.structured_content.get("result", res.structured_content)
        print(f"Tool Status: {data.get('status')}")
        print(f"Error Message: {data.get('error_message')}")
        assert data.get("status") == "error"
        assert "symlink" in data.get("error_message", "").lower()
        print("[OK] read_file tool gracefully neutralized simulated symlink attack.")

    print("\n" + "=" * 65)
    print("PHASE 5 VERIFICATION SUCCESSFUL: Symlink security is robust & active!")
    print("=" * 65)


if __name__ == "__main__":
    anyio.run(test_symlink_security)
