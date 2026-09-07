import re
from typing import Tuple, List, Set

# =============================================================================
# Regular Expression Patterns for In-Flight Secret Redaction
# =============================================================================

# 1. Database connection strings (Postgres, MySQL, MongoDB, Redis, etc.)
# Matches: scheme://user:password@host... and redacts the password portion
DB_URI_PATTERN = re.compile(
    r"((?:postgres|postgresql|mysql|mongodb(?:\+srv)?|redis|mssql)://[^\s:]+:)([^@\s]+)(@[^\s\"';]+)",
    re.IGNORECASE
)

# 2. Standalone API Keys (OpenAI, Stripe, OpenRouter, AWS, generic live keys)
API_KEY_PATTERNS = [
    # sk-live-..., sk-test-..., sk-proj-..., sk-or-...
    re.compile(r"\b(sk[_-](?:live|test|proj|or)[_-][a-zA-Z0-9_\-]{16,})\b"),
    # Stripe live secret keys: sk_live_...
    re.compile(r"\b(sk_live_[a-zA-Z0-9]{20,})\b"),
    # Generic high-entropy hex/base64 tokens in assignments (api_key = "...")
    re.compile(
        r"(?i)(api[_-]?key|secret[_-]?key|master[_-]?key|access[_-]?token|auth[_-]?token)"
        r"(\s*[:=]\s*[\"']?)([a-zA-Z0-9_\-\.]{16,})([\"']?)"
    ),
]

# 3. Passwords and credentials in assignments
# Matches: password = "...", db_password: "...", ADMIN_PASSWORD = "..."
PASSWORD_PATTERN = re.compile(
    r"(?i)(password|passwd|pwd|db_password|admin_password|user_password|secret)"
    r"(\s*[:=]\s*[\"']?)([^\s\r\n\"';,]{3,})([\"']?)"
)

# 4. Bearer tokens in headers or strings
BEARER_TOKEN_PATTERN = re.compile(
    r"(?i)(bearer\s+)([a-zA-Z0-9_\-\.]{20,})"
)

# 5. Private cryptographic keys (RSA, OpenSSH, PGP, EC)
PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
)

# 6. Private IP Addresses (RFC 1918)
# 10.0.0.0 - 10.255.255.255
# 172.16.0.0 - 172.31.255.255
# 192.168.0.0 - 192.168.255.255
PRIVATE_IP_PATTERN = re.compile(
    r"\b(?:10(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}|"
    r"172\.(?:1[6-9]|2[0-9]|3[0-1])(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){2}|"
    r"192\.168(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){2})\b"
)


class RedactionEngine:
    """
    In-flight secret redaction engine for legacy codebases.
    Scans source text and replaces identified credentials, keys, URIs, and IPs with [REDACTED].
    """

    def __init__(self, placeholder: str = "[REDACTED]"):
        self.placeholder = placeholder

    def redact(self, text: str) -> Tuple[str, List[str]]:
        """
        Sanitizes text by replacing sensitive patterns.

        Returns:
            Tuple of (sanitized_code, list_of_redaction_tags_applied)
        """
        if not text:
            return "", []

        sanitized = text
        applied: Set[str] = set()

        # 1. Redact Private Cryptographic Keys
        if PRIVATE_KEY_PATTERN.search(sanitized):
            sanitized = PRIVATE_KEY_PATTERN.sub(
                f"-----BEGIN PRIVATE KEY-----\n{self.placeholder}\n-----END PRIVATE KEY-----",
                sanitized
            )
            applied.add("private_key")

        # 2. Redact Database Connection Credentials
        if DB_URI_PATTERN.search(sanitized):
            sanitized = DB_URI_PATTERN.sub(
                rf"\1{self.placeholder}\3",
                sanitized
            )
            applied.add("database_uri")

        # 3. Redact Bearer Tokens
        if BEARER_TOKEN_PATTERN.search(sanitized):
            sanitized = BEARER_TOKEN_PATTERN.sub(
                rf"\1{self.placeholder}",
                sanitized
            )
            applied.add("bearer_token")

        # 4. Redact Specific API Key Patterns
        for api_pat in API_KEY_PATTERNS:
            if api_pat.search(sanitized):
                if api_pat.groups == 4:
                    # Pattern with key name and quotes: key = "..."
                    sanitized = api_pat.sub(
                        rf"\1\2{self.placeholder}\4",
                        sanitized
                    )
                else:
                    # Standalone token: sk-live-...
                    sanitized = api_pat.sub(self.placeholder, sanitized)
                applied.add("api_key")

        # 5. Redact Password & Credential Assignments
        if PASSWORD_PATTERN.search(sanitized):
            sanitized = PASSWORD_PATTERN.sub(
                rf"\1\2{self.placeholder}\4",
                sanitized
            )
            applied.add("password")

        # 6. Redact Private IP Addresses
        if PRIVATE_IP_PATTERN.search(sanitized):
            sanitized = PRIVATE_IP_PATTERN.sub(self.placeholder, sanitized)
            applied.add("private_ip")

        return sanitized, sorted(list(applied))


# Default singleton instance
default_redaction_engine = RedactionEngine()


def redact_code(text: str) -> Tuple[str, List[str]]:
    """Convenience function to redact code using the default engine."""
    return default_redaction_engine.redact(text)
