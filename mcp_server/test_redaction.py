import sys
import anyio
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_server.server import create_server
from mcp_server.redaction import redact_code, RedactionEngine


async def test_in_flight_redaction():
    print("=" * 65)
    print("PHASE 7 VERIFICATION: In-Flight Secret Redaction Suite")
    print("=" * 65)

    server = create_server()
    engine = RedactionEngine()

    # -------------------------------------------------------------------------
    # 1. Unit Tests on Specific Secret Categories
    # -------------------------------------------------------------------------
    print("\n--- Test 1: Category Unit Tests ---")

    # 1a. Database URI with Password
    raw_db = 'const char* conn = "postgresql://admin:TopSecretPassword99@10.0.0.1:5432/app_db";'
    sanitized_db, tags_db = engine.redact(raw_db)
    print(f"Original DB URI:  {raw_db}")
    print(f"Sanitized DB URI: {sanitized_db}")
    print(f"Tags Applied:     {tags_db}")
    assert "TopSecretPassword99" not in sanitized_db
    assert "[REDACTED]" in sanitized_db
    assert "database_uri" in tags_db
    print("[OK] Database URI credentials successfully redacted.")

    # 1b. Standalone API Keys & Assignments
    raw_api = 'OPENAI_API_KEY = "sk-live-abcdef1234567890abcdef1234567890"'
    sanitized_api, tags_api = engine.redact(raw_api)
    print(f"\nOriginal API Key:  {raw_api}")
    print(f"Sanitized API Key: {sanitized_api}")
    print(f"Tags Applied:      {tags_api}")
    assert "sk-live-abcdef" not in sanitized_api
    assert "[REDACTED]" in sanitized_api
    assert "api_key" in tags_api
    print("[OK] API Keys successfully redacted.")

    # 1c. Passwords in Code
    raw_pwd = 'char* user_password = "SuperUnsafePlaintextPassword!";'
    sanitized_pwd, tags_pwd = engine.redact(raw_pwd)
    print(f"\nOriginal Password:  {raw_pwd}")
    print(f"Sanitized Password: {sanitized_pwd}")
    print(f"Tags Applied:       {tags_pwd}")
    assert "SuperUnsafePlaintextPassword!" not in sanitized_pwd
    assert "[REDACTED]" in sanitized_pwd
    assert "password" in tags_pwd
    print("[OK] Passwords successfully redacted.")

    # 1d. Private IP Addresses
    raw_ip = 'ping_host("192.168.1.100"); connect_db("172.16.5.20"); proxy("10.200.1.5");'
    sanitized_ip, tags_ip = engine.redact(raw_ip)
    print(f"\nOriginal IPs:  {raw_ip}")
    print(f"Sanitized IPs: {sanitized_ip}")
    print(f"Tags Applied:  {tags_ip}")
    assert "192.168.1.100" not in sanitized_ip
    assert "172.16.5.20" not in sanitized_ip
    assert "10.200.1.5" not in sanitized_ip
    assert "private_ip" in tags_ip
    print("[OK] Private IP addresses successfully redacted.")

    # 1e. Bearer Tokens & Private Keys
    raw_bearer = 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.sig'
    sanitized_bearer, tags_bearer = engine.redact(raw_bearer)
    assert "eyJhbGci" not in sanitized_bearer
    assert "bearer_token" in tags_bearer
    print("[OK] Bearer tokens successfully redacted.")

    raw_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0m...\n-----END RSA PRIVATE KEY-----"
    sanitized_key, tags_key = engine.redact(raw_key)
    assert "MIIEowIBAAKCAQEA0m..." not in sanitized_key
    assert "private_key" in tags_key
    print("[OK] Private cryptographic keys successfully redacted.")

    # -------------------------------------------------------------------------
    # 2. End-to-End read_file Tests on Legacy Fixtures
    # -------------------------------------------------------------------------
    print("\n--- Test 2: End-to-End read_file on sample_auth.c ---")
    auth_result = await server.call_tool("read_file", {"file_path": "sample_legacy/sample_auth.c"})
    auth_data = auth_result.structured_content.get("result", auth_result.structured_content)

    print(f"Status: {auth_data.get('status')}")
    print(f"Redactions Applied: {auth_data.get('redactions_applied')}")
    print("Sanitized Code Preview:\n" + "-" * 50)
    print(auth_data.get("sanitized_code"))
    print("-" * 50)

    # Verify no raw secrets leaked
    assert "SuperSecretDBPassword123!" not in auth_data.get("sanitized_code"), "CRITICAL LEAK: DB Password present!"
    assert "AdminPassword#2024" not in auth_data.get("sanitized_code"), "CRITICAL LEAK: Admin Password present!"
    assert "sk-live-99887766554433221100aabbccddeeff" not in auth_data.get("sanitized_code"), "CRITICAL LEAK: API Key present!"
    assert "192.168.1.50" not in auth_data.get("sanitized_code"), "CRITICAL LEAK: Private IP present!"

    # Verify audit tags
    expected_auth_tags = {"api_key", "database_uri", "password", "private_ip"}
    assert expected_auth_tags.issubset(set(auth_data.get("redactions_applied"))), "Missing expected redaction audit tags"
    print("[OK] sample_auth.c fully sanitized with zero raw secrets!")

    print("\n--- Test 3: End-to-End read_file on sample_payment.c ---")
    pay_result = await server.call_tool("read_file", {"file_path": "sample_legacy/sample_payment.c"})
    pay_data = pay_result.structured_content.get("result", pay_result.structured_content)

    print(f"Status: {pay_data.get('status')}")
    print(f"Redactions Applied: {pay_data.get('redactions_applied')}")
    print("Sanitized Code Preview:\n" + "-" * 50)
    print(pay_data.get("sanitized_code"))
    print("-" * 50)

    assert "MySqlSecretPW987" not in pay_data.get("sanitized_code"), "CRITICAL LEAK: MySQL password present!"
    assert "sk_test_FAKE_KEY_FOR_REDACTION_TESTING_ONLY" not in pay_data.get("sanitized_code"), "CRITICAL LEAK: Stripe key present!"
    assert "10.0.4.15" not in pay_data.get("sanitized_code"), "CRITICAL LEAK: Private IP present!"
    assert "172.16.0.10" not in pay_data.get("sanitized_code"), "CRITICAL LEAK: Private IP present!"

    print("[OK] sample_payment.c fully sanitized with zero raw secrets!")

    print("\n" + "=" * 65)
    print("PHASE 7 VERIFICATION SUCCESSFUL: In-Flight Redaction is operational!")
    print("=" * 65)


if __name__ == "__main__":
    anyio.run(test_in_flight_redaction)
