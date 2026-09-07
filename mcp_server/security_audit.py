import sys
import anyio
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_server.server import create_server
from mcp_server.config import STORAGE_PROJECTS_ROOT


class SecurityAuditor:
    """
    Automated Adversarial Security Audit Suite.
    Executes attacks against the MCP Server across all threat categories:
    1. Directory Traversal & Sandbox Escapes
    2. Null Byte & Encoding Bypasses
    3. Binary & Executable File Injection
    4. Denial-of-Service & Resource Exhaustion (Oversized files)
    5. Host System Path Breakouts (Windows Drive & POSIX Root)
    6. Credential & Secret Leakage Verification
    """

    def __init__(self):
        self.server = create_server()
        self.results: List[Dict[str, Any]] = []

    async def run_single_test(
        self,
        category: str,
        name: str,
        payload: str,
        expected_status: str = "error",
        must_not_contain: List[str] = None
    ) -> bool:
        start_time = time.perf_counter()
        response = await self.server.call_tool("read_file", {"file_path": payload})
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        data = response.structured_content.get("result", response.structured_content)
        status = data.get("status")
        error_msg = data.get("error_message") or ""
        code = data.get("sanitized_code") or ""

        passed = (status == expected_status)

        # Check for forbidden leaked strings
        leak_detected = False
        if must_not_contain:
            for forbidden in must_not_contain:
                if forbidden in code:
                    passed = False
                    leak_detected = True
                    break

        self.results.append({
            "category": category,
            "name": name,
            "payload": payload,
            "status": status,
            "passed": passed,
            "error_msg": error_msg,
            "leak_detected": leak_detected,
            "elapsed_ms": elapsed_ms
        })
        return passed

    async def run_audit(self):
        print("=" * 70)
        print("PHASE 8 SECURITY AUDIT: Adversarial Penetration Test Suite")
        print("=" * 70)

        # Category 1: Directory Traversal
        traversal_attacks = [
            ("Relative Parent Traversal", "../../backend/.env"),
            ("Deep Upward Traversal", "../../../../../Windows/System32/drivers/etc/hosts"),
            ("Subpath Traversal Breakout", "sample_legacy/../../backend/main.py"),
            ("Nested Directory Traversal", "sample_legacy/....//....//backend/.env"),
        ]
        for name, payload in traversal_attacks:
            await self.run_single_test("Directory Traversal", name, payload, "error")

        # Category 2: Encoding & Injection Attacks
        encoding_attacks = [
            ("Single URL Encoded Traversal", "%2e%2e%2f%2e%2e%2fbackend%2f.env"),
            ("Double URL Encoded Traversal", "%252e%252e%252fbackend%2f.env"),
            ("Null Byte File Extension Bypass", "sample_legacy/sample_auth.c\x00.exe"),
            ("URL Encoded Null Byte", "sample_legacy/sample_auth.c%00.png"),
            ("Empty String Payload", ""),
            ("Whitespace Only Payload", "     "),
            ("Targeting Root Directory", "."),
        ]
        for name, payload in encoding_attacks:
            await self.run_single_test("Encoding & Injection", name, payload, "error")

        # Category 3: System Host Paths & UNC
        system_attacks = [
            ("Windows Drive Letter (C:)", "C:\\Windows\\System32\\cmd.exe"),
            ("Windows Forward Slash Drive", "C:/Windows/System32/cmd.exe"),
            ("POSIX System File (/etc/passwd)", "/etc/passwd"),
            ("POSIX System Log (/var/log/syslog)", "/var/log/syslog"),
            ("UNC Network Share Path", "\\\\attacker-host\\share\\payload.c"),
            ("POSIX Double Slash Share", "//attacker-host/share/payload.c"),
        ]
        for name, payload in system_attacks:
            await self.run_single_test("System Path Breakout", name, payload, "error")

        # Category 4: File Type, Executable, & DoS Attacks
        legacy_dir = STORAGE_PROJECTS_ROOT / "sample_legacy"
        test_exe = legacy_dir / "audit_test.exe"
        test_bin = legacy_dir / "audit_disguised.c"
        test_huge = legacy_dir / "audit_huge.c"

        try:
            # Create test fixtures
            test_exe.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00")
            test_bin.write_bytes(b"\x7fELF\x02\x01\x01\x00\x00\x00")
            test_huge.write_bytes(b"/* huge code line */\n" * 50000)  # ~1.1 MB

            await self.run_single_test(
                "File Type & Size",
                "Blocked Executable (.exe)",
                "sample_legacy/audit_test.exe",
                "error"
            )
            await self.run_single_test(
                "File Type & Size",
                "Binary Disguised as .c File",
                "sample_legacy/audit_disguised.c",
                "error"
            )
            await self.run_single_test(
                "File Type & Size",
                "Oversized File (>1MB DoS)",
                "sample_legacy/audit_huge.c",
                "error"
            )
            await self.run_single_test(
                "File Type & Size",
                "Directory Access as File",
                "sample_legacy",
                "error"
            )
        finally:
            for f in [test_exe, test_bin, test_huge]:
                if f.exists():
                    f.unlink()

        # Category 5: Credential In-Flight Redaction Leakage Test
        await self.run_single_test(
            "Secret Redaction",
            "Authentication Module Redaction",
            "sample_legacy/sample_auth.c",
            expected_status="success",
            must_not_contain=[
                "SuperSecretDBPassword123!",
                "sk-live-99887766554433221100aabbccddeeff",
                "AdminPassword#2024",
                "192.168.1.50"
            ]
        )
        await self.run_single_test(
            "Secret Redaction",
            "Payment Module Redaction",
            "sample_legacy/sample_payment.c",
            expected_status="success",
            must_not_contain=[
                "MySqlSecretPW987",
                "sk_test_FAKE_KEY_FOR_REDACTION_TESTING_ONLY",
                "10.0.4.15",
                "172.16.0.10"
            ]
        )

        # ---------------------------------------------------------------------
        # Report Generation
        # ---------------------------------------------------------------------
        print("\n" + "-" * 70)
        print(f"{'Category':<22} | {'Test Vector':<32} | {'Result':<8}")
        print("-" * 70)

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])

        for r in self.results:
            status_str = "[PASS]" if r["passed"] else "[FAIL]"
            print(f"{r['category']:<22} | {r['name']:<32} | {status_str}")

        score = (passed_tests / total_tests) * 100
        print("-" * 70)
        print(f"AUDIT SCORE: {passed_tests}/{total_tests} ({score:.1f}%) Test Vectors Successfully Defended")
        print("=" * 70)

        assert passed_tests == total_tests, f"Security Audit Failed: {total_tests - passed_tests} vulnerabilities detected!"
        print("ALL ATTACK VECTORS NEUTRALIZED - ZERO VULNERABILITIES DETECTED.")



if __name__ == "__main__":
    auditor = SecurityAuditor()
    anyio.run(auditor.run_audit)
