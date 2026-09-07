import os
import re
import stat
import urllib.parse
from pathlib import Path
from mcp_server.config import (
    STORAGE_PROJECTS_ROOT,
    ALLOW_INTERNAL_SYMLINKS,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
)


class SecurityError(Exception):
    """Base exception for all security violations."""
    pass


class PathTraversalError(SecurityError):
    """Raised when an attempt to escape the sandbox directory using traversal is detected."""
    pass


class SymlinkSecurityError(SecurityError):
    """Raised when an unauthorized or out-of-bounds symbolic link is detected."""
    pass


class FileTypeSecurityError(SecurityError):
    """Raised when an unsupported, executable, or binary file type is accessed."""
    pass


class FileSizeSecurityError(SecurityError):
    """Raised when a file exceeds the maximum allowed read size."""
    pass


class InvalidPathError(SecurityError):
    """Raised when an input path contains malformed or illegal characters."""
    pass


# Windows drive letter pattern (e.g. C:, D:)
DRIVE_LETTER_REGEX = re.compile(r"^[a-zA-Z]:")

# UNC network path pattern (e.g. \\server\share)
UNC_PATH_REGEX = re.compile(r"^\\\\[^\\]+")

# Known binary and executable extensions forbidden from code RAG ingestion
BLOCKED_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".com",
    ".o", ".obj", ".a", ".lib", ".pyc", ".pyo", ".pyd",
    ".zip", ".tar", ".gz", ".7z", ".rar", ".iso",
    ".db", ".sqlite", ".sqlite3", ".class", ".jar",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf"
}


def sanitize_input_path(raw_path: str) -> str:
    r"""
    Sanitizes raw path inputs by decoding URL encoding and checking for illegal characters.

    Protections:
    - Rejects null bytes (\x00 / %00) which can bypass string checks.
    - Decodes single and double URL-encoded characters (e.g. %2e%2e -> ..).
    - Rejects absolute Windows drive letters (e.g. C:\...)
    - Rejects UNC network paths (e.g. \\host\share)
    """
    if raw_path is None or not isinstance(raw_path, str):
        raise InvalidPathError("Invalid path: Path must be a non-null string.")

    cleaned = raw_path.strip()
    if not cleaned:
        raise InvalidPathError("Invalid path: Path cannot be empty.")

    # 1. Reject null bytes
    if "\x00" in cleaned or "%00" in cleaned.lower():
        raise InvalidPathError("Invalid path: Null bytes are not permitted in file paths.")

    # 2. Decode URL encoding (e.g. %2e%2e%2f -> ../)
    try:
        decoded = urllib.parse.unquote(cleaned)
        if "%" in decoded:
            decoded = urllib.parse.unquote(decoded)
    except Exception as e:
        raise InvalidPathError(f"Invalid path encoding: {e}")

    # Re-check null byte after decoding
    if "\x00" in decoded:
        raise InvalidPathError("Invalid path: Decoded path contains null byte.")

    # 3. Reject Windows drive letters
    if DRIVE_LETTER_REGEX.match(decoded):
        raise PathTraversalError(f"Access Denied: Absolute drive path '{raw_path}' is forbidden.")

    # 4. Reject UNC network shares
    if UNC_PATH_REGEX.match(decoded) or decoded.startswith("//"):
        raise PathTraversalError("Access Denied: UNC/Network paths are forbidden.")

    # Normalize backslashes to forward slashes
    normalized = decoded.replace("\\", "/")

    # Reject POSIX root attempts (e.g. /etc/passwd)
    if normalized.startswith("/"):
        stripped = normalized.lstrip("/")
        if stripped.startswith("etc/") or stripped.startswith("windows/") or stripped.startswith("system32/"):
            raise PathTraversalError(f"Access Denied: Path '{raw_path}' targets a restricted system directory.")
        normalized = stripped

    if not normalized:
        raise InvalidPathError("Invalid path: Path cannot resolve to root after normalization.")

    return normalized


def detect_symlink_components(unresolved_path: Path, canonical_root: Path) -> bool:
    """
    Checks if the target path or any intermediate directory between canonical_root
    and unresolved_path is a symbolic link or junction point.
    """
    try:
        current = unresolved_path
        while current != canonical_root and current != current.parent:
            if current.is_symlink():
                return True
            current = current.parent
    except (OSError, ValueError):
        pass
    return False


def validate_and_resolve_path(
    raw_path: str,
    base_root: Path = STORAGE_PROJECTS_ROOT,
    allow_internal_symlinks: bool = ALLOW_INTERNAL_SYMLINKS
) -> Path:
    """
    Validates, normalizes, and resolves a path strictly within the allowed base_root sandbox.
    """
    sanitized_rel = sanitize_input_path(raw_path)
    canonical_root = base_root.resolve()
    unresolved_path = canonical_root / sanitized_rel

    has_symlink = detect_symlink_components(unresolved_path, canonical_root)
    if has_symlink and not allow_internal_symlinks:
        raise SymlinkSecurityError(
            f"Access Denied: Symbolic link detected in '{raw_path}', which is forbidden by policy."
        )

    try:
        target_path = unresolved_path.resolve()
    except (RuntimeError, OSError) as e:
        raise SymlinkSecurityError(f"Access Denied: Circular symlink loop detected in '{raw_path}': {e}")

    try:
        target_path.relative_to(canonical_root)
    except ValueError:
        if has_symlink:
            raise SymlinkSecurityError(
                f"Access Denied: Symlink '{raw_path}' points outside the repository sandbox."
            )
        raise PathTraversalError(
            f"Access Denied: Path traversal detected. Path '{raw_path}' attempts to escape the repository sandbox."
        )

    if target_path == canonical_root:
        raise PathTraversalError("Access Denied: Targeting the root repository directory is not permitted.")

    return target_path


def validate_file_type_and_size(
    target_path: Path,
    max_size_bytes: int = MAX_FILE_SIZE_BYTES,
    allowed_extensions: set = ALLOWED_EXTENSIONS
) -> int:
    """
    Strictly verifies file type, checks against binary formats, and enforces size bounds.

    Returns:
        file_size in bytes.

    Raises:
        FileNotFoundError: If the file does not exist.
        FileTypeSecurityError: If directory, FIFO, device, socket, blocked extension, or binary.
        FileSizeSecurityError: If the file size exceeds max_size_bytes.
    """
    if not target_path.exists():
        raise FileNotFoundError(f"File not found: '{target_path.name}'")

    file_stat = target_path.stat()

    # 1. Must be a regular file (reject directories, character/block devices, FIFOs, sockets)
    if not stat.S_ISREG(file_stat.st_mode):
        mode_desc = "directory" if stat.S_ISDIR(file_stat.st_mode) else "special device/pipe"
        raise FileTypeSecurityError(
            f"Access Denied: Target is a {mode_desc} (not a regular file), only regular source files are permitted."
        )

    # 2. Check blocked extensions
    extension = target_path.suffix.lower()
    if extension in BLOCKED_EXTENSIONS:
        raise FileTypeSecurityError(
            f"Access Denied: Blocked extension '{extension}'. Executables and binary formats are forbidden."
        )

    # 3. Check allowed extensions (if configured)
    if allowed_extensions and extension not in allowed_extensions:
        raise FileTypeSecurityError(
            f"Access Denied: Unsupported file extension '{extension}'. Allowed extensions: {sorted(allowed_extensions)}"
        )

    # 4. Check file size limits before reading into memory
    file_size = file_stat.st_size
    if file_size > max_size_bytes:
        raise FileSizeSecurityError(
            f"Access Denied: File size ({file_size} bytes) exceeds limit of {max_size_bytes} bytes ({max_size_bytes // 1024} KB)."
        )

    # 5. Sniff first 1024 bytes for binary content (null byte detection)
    try:
        with open(target_path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                raise FileTypeSecurityError(
                    f"Access Denied: Binary content detected in file '{target_path.name}'. Only text source files are permitted."
                )
    except (OSError, IOError) as e:
        raise FileTypeSecurityError(f"Failed to inspect file format: {e}")

    return file_size
