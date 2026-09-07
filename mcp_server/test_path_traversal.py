import sys
import anyio
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_server.server import create_server


async def test_path_traversal_protection():
    print("=" * 65)
    print("PHASE 4 VERIFICATION: Path Traversal Attack Defense Suite")
    print("=" * 65)

    server = create_server()

    # Matrix of adversarial inputs attempting path traversal and sandbox escapes
    malicious_inputs = [
        ("../../secret.txt", "Parent directory traversal (..)"),
        ("../../../Windows/System32", "Deep system traversal"),
        ("/etc/passwd", "POSIX root file escape"),
        ("C:\\Windows\\System32\\calc.exe", "Windows absolute drive letter (backslash)"),
        ("C:/Windows/System32/calc.exe", "Windows absolute drive letter (forward slash)"),
        ("\\\\malicious-host\\share\\secret.c", "UNC network share breakout"),
        ("//malicious-host/share/secret.c", "POSIX network share breakout"),
        ("sample_legacy/../../backend/.env", "Subpath traversal to backend .env"),
        ("sample_legacy/../../../backend/main.py", "Subpath breakout to backend code"),
        ("%2e%2e%2f%2e%2e%2fbackend%2f.env", "URL encoded traversal (%2e%2e%2f)"),
        ("sample_legacy/%2e%2e/%2e%2e/backend/.env", "Mixed URL encoded traversal"),
        ("sample_legacy/sample_auth.c\x00.png", "Null byte injection (raw \\x00)"),
        ("sample_legacy/sample_auth.c%00", "Null byte injection (URL encoded %00)"),
        ("", "Empty path"),
        ("   ", "Whitespace path"),
        (".", "Targeting current directory / sandbox root"),
    ]

    blocked_count = 0
    total_attacks = len(malicious_inputs)

    for attack_path, description in malicious_inputs:
        print(f"\nTesting Attack Vector: {description}")
        print(f"Payload: {repr(attack_path)}")

        result = await server.call_tool("read_file", {"file_path": attack_path})
        data = result.structured_content.get("result", result.structured_content)

        status = data.get("status")
        error_msg = data.get("error_message", "")

        print(f"Result Status: {status}")
        print(f"Error Caught: {error_msg}")

        # Assert that EVERY attack is blocked
        assert status == "error", f"SECURITY CRITICAL: Attack payload '{attack_path}' was NOT blocked!"
        assert error_msg is not None and len(error_msg) > 0, "Error message must explain the rejection"

        # Assert no sensitive data or arbitrary content was leaked
        assert data.get("sanitized_code") == "", "Code content must be empty on security rejection"

        print("[BLOCKED] Attack successfully mitigated.")
        blocked_count += 1

    print("\n" + "=" * 65)
    print(f"SECURITY AUDIT PASSED: {blocked_count}/{total_attacks} attack vectors neutralized!")
    print("=" * 65)


if __name__ == "__main__":
    anyio.run(test_path_traversal_protection)
