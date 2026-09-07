"""
Micron - Langfuse Cloud Observability Verification Script
---------------------------------------------------------
Runs authentication diagnostics against Langfuse Cloud and tests trace export.
Usage:
    python verify_langfuse.py
"""

import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.observability import verify_langfuse_connection, observe, trace_tenant_context


def main():
    print("=" * 60)
    print("      MICRON - LANGFUSE CLOUD OBSERVABILITY CHECK")
    print("=" * 60)

    host = settings.LANGFUSE_HOST or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    pub_key = settings.LANGFUSE_PUBLIC_KEY or os.getenv("LANGFUSE_PUBLIC_KEY", "")
    sec_key = settings.LANGFUSE_SECRET_KEY or os.getenv("LANGFUSE_SECRET_KEY", "")

    print(f"\n[1] Configuration Check:")
    print(f"  - Host / Region:      {host}")
    print(f"  - Public Key:         {pub_key[:12] + '...' if pub_key else '<NOT SET>'}")
    print(f"  - Secret Key:         {'*' * 8 + sec_key[-4:] if len(sec_key) > 4 else ('<SET>' if sec_key else '<NOT SET>')}")

    if not pub_key or not sec_key:
        print("\n[!] Keys are not set in your environment or .env file.")
        print("    To connect to Langfuse Cloud:")
        print("    1. Go to https://cloud.langfuse.com (or https://us.cloud.langfuse.com)")
        print("    2. Navigate to Project Settings -> API Keys")
        print("    3. Copy your Public Key and Secret Key into .env:")
        print("       LANGFUSE_PUBLIC_KEY=pk-lf-...")
        print("       LANGFUSE_SECRET_KEY=sk-lf-...")
        print("       LANGFUSE_HOST=https://cloud.langfuse.com")
        print("\n  Status: UNCONFIGURED (Graceful fallback active, tracing disabled)\n")
        return 0

    print("\n[2] Testing Authentication with Langfuse Cloud...")
    result = verify_langfuse_connection()
    status = result.get("status")

    if status == "connected":
        print("  [+] Authentication successful!")
        print(f"  [+] Connected to: {result.get('host')}")

        print("\n[3] Sending Test Diagnostic Trace...")
        try:
            @observe(name="micron_cloud_verification")
            def test_trace():
                with trace_tenant_context(
                    tenant_id="test-tenant",
                    project_id="micron-test-project",
                    tags=["diagnostic", "verification"],
                    metadata={"test_run": True, "source": "verify_langfuse.py"}
                ):
                    return "verification_successful"

            val = test_trace()
            print(f"  [+] Diagnostic span emitted successfully (result: {val})")
            print(f"\n[SUCCESS] Langfuse Cloud is ready and capturing observability traces!")
            print(f"Check your dashboard at: {host}\n")
            return 0
        except Exception as e:
            print(f"  [-] Error exporting test trace: {e}\n")
            return 1
    else:
        print(f"  [-] {result.get('message')}")
        print("\nTroubleshooting tips:")
        print("  - Confirm your keys match your project at " + host)
        print("  - If your project is hosted in the US region, ensure LANGFUSE_HOST=https://us.cloud.langfuse.com")
        print("  - If your project is in the EU region, ensure LANGFUSE_HOST=https://cloud.langfuse.com\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
