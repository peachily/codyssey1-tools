import re
from pathlib import PurePosixPath

MASK = "[MASKED]"
SECRET_NAME = (
    r"[\w.-]*(?:api[_-]?key|password|passwd|pwd|token|secret|access[_-]?key)"
    r"[\w.-]*"
)
ASSIGNMENT = re.compile(
    rf"(?P<prefix>\b{SECRET_NAME}[\"']?\s*[:=]\s*)"
    r"(?:\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'|[^\s,;#}\]]+)",
    re.IGNORECASE,
)


def is_sensitive_file(path: str) -> bool:
    file = PurePosixPath(path.lower())
    name = file.name
    return (
        name == ".env"
        or name.startswith(".env.")
        or name.startswith(("id_rsa", "id_ed25519", "id_dsa", "id_ecdsa"))
        or file.suffix in {".pem", ".key", ".p12", ".pfx", ".keystore"}
        or name in {".netrc", ".npmrc", ".pypirc", "credentials", "credentials.json"}
        or name.startswith(("secrets.", "credentials.", "service-account", "service_account"))
        or any(part in {".ssh", ".aws", ".gnupg"} for part in file.parts)
    )


def mask_sensitive_data(text: str, api_key: str = "") -> str:
    if api_key:
        text = text.replace(api_key, MASK)
    text = re.sub(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        MASK,
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"\b(?:sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]+|AKIA[A-Z0-9]{16})\b", MASK, text)
    text = re.sub(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+", r"\1 " + MASK, text)
    text = ASSIGNMENT.sub(lambda match: match["prefix"] + MASK, text)
    return re.sub(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", MASK, text)
