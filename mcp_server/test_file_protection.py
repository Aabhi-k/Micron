import sys
import anyio
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_server.server import create_server
from mcp_server.config import STORAGE_PROJECTS_ROOT


async def test_file_type_and_size_protection():
    print("=" * 65)
    print("PHASE 6 VERIFICATION: File Type & File Size Protection Suite")
    print("=" * 65)

    server = create_server()
    legacy_dir = STORAGE_PROJECTS_ROOT / "sample_legacy"

    # Temporary fixture paths
    test_exe = legacy_dir / "malicious_binary.exe"
    test_spoofed_binary = legacy_dir / "spoofed_binary.c"
    test_oversized = legacy_dir / "huge_dump.c"

    try:
        # 1. Test Blocked File Extension (.exe)
        print("\n--- Test 1: Blocked Executable Extension (.exe) ---")
        test_exe.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00")
        res_exe = await server.call_tool("read_file", {"file_path": "sample_legacy/malicious_binary.exe"})
        data_exe = res_exe.structured_content.get("result", res_exe.structured_content)

        print(f"Status: {data_exe.get('status')}")
        print(f"Error Caught: {data_exe.get('error_message')}")
        assert data_exe.get("status") == "error", "Executable files must be rejected!"
        assert "blocked extension" in data_exe.get("error_message", "").lower()
        print("[OK] Blocked extension (.exe) rejected successfully.")

        # 2. Test Binary Sniffing with Spoofed Extension (.c containing raw binary bytes)
        print("\n--- Test 2: Binary Sniffing Protection (Spoofed .c Extension) ---")
        # Null bytes embedded inside a file masquerading as a .c file
        test_spoofed_binary.write_bytes(b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        res_bin = await server.call_tool("read_file", {"file_path": "sample_legacy/spoofed_binary.c"})
        data_bin = res_bin.structured_content.get("result", res_bin.structured_content)

        print(f"Status: {data_bin.get('status')}")
        print(f"Error Caught: {data_bin.get('error_message')}")
        assert data_bin.get("status") == "error", "Binary files must be rejected even with code extension!"
        assert "binary content" in data_bin.get("error_message", "").lower()
        print("[OK] Binary content sniffing successfully caught spoofed file.")

        # 3. Test File Size Protection (> 1 MB)
        print("\n--- Test 3: Oversized File Protection (> MAX_FILE_SIZE_BYTES) ---")
        # Create 1.2 MB file
        test_oversized.write_bytes(b"// Legacy codebase line comment\n" * 40000)
        oversized_bytes = test_oversized.stat().st_size
        print(f"Created test file with size: {oversized_bytes} bytes ({oversized_bytes // 1024} KB)")

        res_huge = await server.call_tool("read_file", {"file_path": "sample_legacy/huge_dump.c"})
        data_huge = res_huge.structured_content.get("result", res_huge.structured_content)

        print(f"Status: {data_huge.get('status')}")
        print(f"Error Caught: {data_huge.get('error_message')}")
        assert data_huge.get("status") == "error", "Oversized files must be blocked!"
        assert "exceeds limit" in data_huge.get("error_message", "").lower()
        print("[OK] Oversized file blocked before loading into memory.")

        # 4. Test Directory Rejection
        print("\n--- Test 4: Directory Target Rejection ---")
        res_dir = await server.call_tool("read_file", {"file_path": "sample_legacy"})
        data_dir = res_dir.structured_content.get("result", res_dir.structured_content)
        print(f"Status: {data_dir.get('status')}")
        print(f"Error Caught: {data_dir.get('error_message')}")
        assert data_dir.get("status") == "error"
        assert "directory" in data_dir.get("error_message", "").lower()
        print("[OK] Directory access safely rejected.")

    finally:
        # Cleanup temporary test fixtures
        for temp_file in [test_exe, test_spoofed_binary, test_oversized]:
            if temp_file.exists():
                temp_file.unlink()

    print("\n" + "=" * 65)
    print("PHASE 6 VERIFICATION SUCCESSFUL: File type & size protection verified!")
    print("=" * 65)


if __name__ == "__main__":
    anyio.run(test_file_type_and_size_protection)
